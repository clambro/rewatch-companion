"""Pydantic AI essay agent."""

import functools
import time
from typing import TYPE_CHECKING

import anyio.to_thread
import logfire
from ddgs.ddgs import DDGS
from ddgs.exceptions import DDGSException
from openai import OpenAI, RateLimitError
from pydantic_ai import Agent, ModelRetry, RunContext, Tool
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings
from pydantic_ai.providers.openai import OpenAIProvider

from common.rate_limit_retry import RateLimitRetryCapability
from common.settings import settings
from common.telemetry import configure_logfire
from essay_generation.prompt import (
    AGENT_INSTRUCTIONS,
    DRAFTING_MODEL_INSTRUCTIONS,
    SUBTITLE_MODEL_INSTRUCTIONS,
    build_drafting_prompt,
    build_essay_prompt,
    build_subtitle_prompt,
)
from essay_generation.research_fetch import fetch_research_source
from essay_generation.research_limits import (
    AGENT_USAGE_LIMITS,
    MAX_RESEARCH_FETCHES,
    MAX_RESEARCH_SEARCHES,
    SEARCH_RESULTS_PER_QUERY,
)
from essay_generation.schemas import (
    EssayResearchSource,
    EssaySource,
    EssayTarget,
    EssayWorkspace,
    GeneratedEssay,
    ResearchFetchResponse,
)

if TYPE_CHECKING:
    from openai.types.shared_params.reasoning import Reasoning

CONTROLLER_MODEL = "gpt-5.4-mini"
DRAFTING_MODEL = "gpt-5.5"
MODEL_SETTINGS: OpenAIResponsesModelSettings = {
    "openai_reasoning_effort": "medium",
    "openai_reasoning_summary": "concise",
}
DIRECT_MODEL_REASONING: Reasoning = {"effort": "medium", "summary": "concise"}
DIRECT_MODEL_RATE_LIMIT_RETRIES = 5
DIRECT_MODEL_RATE_LIMIT_SLEEP_SECONDS = 20.0


def run_essay_agent(
    *,
    target: EssayTarget,
    sources: list[EssaySource] | None = None,
) -> GeneratedEssay:
    """Generate an essay for a target."""
    agent = build_essay_agent()
    workspace = EssayWorkspace(target=target, sources=sources or [])
    prompt = build_essay_prompt(workspace=workspace)
    agent.run_sync(prompt, deps=workspace, usage_limits=AGENT_USAGE_LIMITS)
    workspace.subtitle = generate_subtitle_with_drafting_model(workspace=workspace).strip()
    return generated_essay_from_workspace(workspace=workspace)


def generated_essay_from_workspace(*, workspace: EssayWorkspace) -> GeneratedEssay:
    """Build the public essay output from the final agent workspace."""
    missing_fields = []
    if not workspace.subtitle.strip():
        missing_fields.append("subtitle")
    if not workspace.draft.strip():
        missing_fields.append("draft")

    if missing_fields:
        raise RuntimeError(f"Essay generation finished without: {', '.join(missing_fields)}")

    return GeneratedEssay(
        subtitle=workspace.subtitle.strip(),
        body_mdx=workspace.draft.strip(),
    )


def build_essay_agent() -> Agent[EssayWorkspace, str]:
    """Build the essay generation agent."""
    configure_logfire()
    openai_model = OpenAIResponsesModel(
        CONTROLLER_MODEL,
        provider=OpenAIProvider(api_key=settings.openai_api_key),
    )
    agent = Agent(
        openai_model,
        deps_type=EssayWorkspace,
        output_type=str,
        model_settings=MODEL_SETTINGS,
        tools=[
            update_draft,
            Tool(search_research_web, takes_ctx=True, sequential=True),
            Tool(fetch_research_source_for_agent, takes_ctx=True, sequential=True),
        ],
        capabilities=[RateLimitRetryCapability[EssayWorkspace]()],
        instructions=AGENT_INSTRUCTIONS,
        max_concurrency=1,
    )
    agent.output_validator(validate_final_state)
    return agent


def update_draft(ctx: RunContext[EssayWorkspace], instructions: str) -> str:
    """
    Write or revise the full article draft using the full-sized drafting model.

    The draft should read as one developing critical argument, not a stack of
    self-contained mini-essays. Prefer precise, varied, scene-aware prose over
    smooth symmetrical paragraphing. Provide drafting or revision instructions;
    do not provide the draft prose yourself.
    """
    ctx.deps.draft = generate_draft_with_drafting_model(
        workspace=ctx.deps,
        instructions=instructions,
    ).strip()
    return "Draft updated."


async def search_research_web(
    ctx: RunContext[EssayWorkspace],
    query: str,
) -> str:
    """Search the web for essay research and report the remaining search budget."""
    if ctx.deps.research_searches >= MAX_RESEARCH_SEARCHES:
        return "No web searches remain."

    ctx.deps.research_searches += 1
    search = functools.partial(DDGS().text, max_results=SEARCH_RESULTS_PER_QUERY)
    searches_remaining = max(0, MAX_RESEARCH_SEARCHES - ctx.deps.research_searches)
    try:
        results = await anyio.to_thread.run_sync(search, query)
    except DDGSException:
        return (
            f"No search results found for query: {query}\nSearches remaining: {searches_remaining}"
        )

    return render_search_results(
        results=results,
        searches_remaining=searches_remaining,
    )


async def fetch_research_source_for_agent(
    ctx: RunContext[EssayWorkspace],
    url: str,
) -> ResearchFetchResponse | str:
    """Fetch a research source and report the remaining fetch budget."""
    if ctx.deps.research_fetches >= MAX_RESEARCH_FETCHES:
        return "No source fetches remain."

    ctx.deps.research_fetches += 1
    fetches_remaining = max(0, MAX_RESEARCH_FETCHES - ctx.deps.research_fetches)
    source = await fetch_research_source(url)
    ctx.deps.research_sources.append(
        EssayResearchSource(
            url=source.url,
            title=source.title,
            content=source.content,
            summarized=source.summarized,
        ),
    )
    return ResearchFetchResponse(
        source=source,
        fetches_remaining=fetches_remaining,
    )


def validate_final_state(ctx: RunContext[EssayWorkspace], output: str) -> str:
    """Reject final output until the workspace contains a complete draft."""
    if not ctx.deps.draft.strip():
        raise ModelRetry("Update the draft before final output.")

    return output


def render_search_results(
    *,
    results: list[dict[str, object]],
    searches_remaining: int,
) -> str:
    """Render transient search results for the controller agent."""
    lines = [
        f"Searches remaining: {searches_remaining}",
        "",
        "Results:",
    ]
    for index, result in enumerate(results, start=1):
        lines.extend(
            [
                f"{index}. {result.get('title', '')}",
                f"   URL: {result.get('href', '')}",
                f"   Snippet: {result.get('body', '')}",
            ],
        )

    return "\n".join(lines)


def generate_draft_with_drafting_model(*, workspace: EssayWorkspace, instructions: str) -> str:
    """Generate or revise an article draft with the full-sized model."""
    return call_drafting_model(
        instructions=DRAFTING_MODEL_INSTRUCTIONS,
        input_text=build_drafting_prompt(workspace=workspace, request=instructions),
    )


def generate_subtitle_with_drafting_model(*, workspace: EssayWorkspace) -> str:
    """Generate the final article dek with the full-sized model."""
    return call_drafting_model(
        instructions=SUBTITLE_MODEL_INSTRUCTIONS,
        input_text=build_subtitle_prompt(workspace=workspace),
    )


def call_drafting_model(
    *,
    instructions: str,
    input_text: str,
) -> str:
    """Call the full-sized model with rate-limit retries inside the agent loop."""
    client = OpenAI(api_key=settings.openai_api_key)
    attempts_remaining = DIRECT_MODEL_RATE_LIMIT_RETRIES
    while True:
        try:
            response = client.responses.create(
                model=DRAFTING_MODEL,
                instructions=instructions,
                input=input_text,
                reasoning=DIRECT_MODEL_REASONING,
            )
        except RateLimitError as error:
            if attempts_remaining <= 0:
                raise
            if "Request too large" in str(error):
                raise

            retry_number = DIRECT_MODEL_RATE_LIMIT_RETRIES - attempts_remaining + 1
            logfire.warning(
                "Direct model rate limit hit; waiting "
                f"{DIRECT_MODEL_RATE_LIMIT_SLEEP_SECONDS:.1f}s before retry "
                f"{retry_number}/{DIRECT_MODEL_RATE_LIMIT_RETRIES}.",
            )
            time.sleep(DIRECT_MODEL_RATE_LIMIT_SLEEP_SECONDS)
            attempts_remaining -= 1
        else:
            return response.output_text
