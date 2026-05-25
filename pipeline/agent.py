"""Pydantic AI essay agent."""

import functools

import anyio.to_thread
import logfire
from ddgs.ddgs import DDGS
from pydantic import BaseModel, TypeAdapter
from pydantic_ai import Agent, ModelRetry, RunContext, Tool
from pydantic_ai.common_tools.duckduckgo import DuckDuckGoResult
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings
from pydantic_ai.providers.openai import OpenAIProvider

from prompt import (
    AGENT_INSTRUCTIONS,
    build_essay_prompt,
)
from rate_limit_retry import RateLimitRetryCapability
from research_fetch import CleanedResearchSource, fetch_research_source
from research_limits import (
    AGENT_USAGE_LIMITS,
    MAX_RESEARCH_FETCHES,
    MAX_RESEARCH_SEARCHES,
    SEARCH_RESULTS_PER_QUERY,
)
from schemas import EssaySource, EssayTarget, EssayWorkspace, GeneratedEssay
from settings import settings

MODEL = "gpt-5.4-mini"
MODEL_SETTINGS: OpenAIResponsesModelSettings = {
    "openai_reasoning_effort": "medium",
    "openai_reasoning_summary": "concise",
}
LOW_FETCH_BUDGET_THRESHOLD = 2

duckduckgo_result_adapter = TypeAdapter(list[DuckDuckGoResult])

logfire.configure(
    service_name="rewatch-pipeline",
    token=settings.logfire_token,
    metrics=logfire.MetricsOptions(collect_in_spans=True),
    scrubbing=False,
)
logfire.instrument_pydantic_ai(use_aggregated_usage_attribute_names=True)
logfire.instrument_openai(version="latest")
logfire.instrument_httpx(capture_all=True)


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
    openai_model = OpenAIResponsesModel(
        MODEL,
        provider=OpenAIProvider(api_key=settings.openai_api_key),
    )
    agent = Agent(
        openai_model,
        deps_type=EssayWorkspace,
        output_type=str,
        model_settings=MODEL_SETTINGS,
        tools=[
            update_subtitle,
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


class ResearchSearchResponse(BaseModel):
    """Search results plus the remaining search budget."""

    results: list[DuckDuckGoResult]
    searches_remaining: int
    guidance: str


class ResearchFetchResponse(BaseModel):
    """Fetched source plus the remaining fetch budget."""

    source: CleanedResearchSource
    fetches_remaining: int
    guidance: str


def update_subtitle(ctx: RunContext[EssayWorkspace], subtitle: str) -> str:
    """
    Update the article dek.

    A good dek is a single short sentence meant to be read alongside the fixed
    title. It is plain text only and does not support formatting of any kind.
    """
    ctx.deps.subtitle = subtitle.strip()
    return "Subtitle updated."


def update_draft(ctx: RunContext[EssayWorkspace], body_mdx: str) -> str:
    """Rewrite the full article draft."""
    ctx.deps.draft = body_mdx.strip()
    return "Draft updated."


async def search_research_web(
    ctx: RunContext[EssayWorkspace],
    query: str,
) -> ResearchSearchResponse | str:
    """Search the web for essay research and report the remaining search budget."""
    if ctx.deps.research_searches >= MAX_RESEARCH_SEARCHES:
        return (
            "No web searches remain. You may still fetch relevant URLs already found if "
            "fetch budget remains, or draft from the evidence already gathered."
        )

    ctx.deps.research_searches += 1
    search = functools.partial(DDGS().text, max_results=SEARCH_RESULTS_PER_QUERY)
    results = await anyio.to_thread.run_sync(search, query)
    searches_remaining = max(0, MAX_RESEARCH_SEARCHES - ctx.deps.research_searches)
    return ResearchSearchResponse(
        results=duckduckgo_result_adapter.validate_python(results),
        searches_remaining=searches_remaining,
        guidance=(
            "Inspect these results before deciding whether another search is needed. "
            "Do not spend the next search on the same angle."
            if searches_remaining > 1
            else "Only one search remains. Reserve it for a specific gap after drafting."
        ),
    )


async def fetch_research_source_for_agent(
    ctx: RunContext[EssayWorkspace],
    url: str,
) -> ResearchFetchResponse | str:
    """Fetch a research source and report the remaining fetch budget."""
    if ctx.deps.research_fetches >= MAX_RESEARCH_FETCHES:
        return (
            "No source fetches remain. You may still use search if search budget remains, "
            "or draft from the evidence already gathered."
        )

    ctx.deps.research_fetches += 1
    fetches_remaining = max(0, MAX_RESEARCH_FETCHES - ctx.deps.research_fetches)
    return ResearchFetchResponse(
        source=await fetch_research_source(url),
        fetches_remaining=fetches_remaining,
        guidance=(
            "Use this source before fetching another. Fetch only if this source exposes a "
            "specific factual or interpretive gap."
            if fetches_remaining > LOW_FETCH_BUDGET_THRESHOLD
            else (
                "Fetch budget is low. Stop fetching unless a concrete factual claim still "
                "needs verification."
            )
        ),
    )


def validate_final_state(ctx: RunContext[EssayWorkspace], output: str) -> str:
    """Reject final output until the workspace contains a complete essay."""
    missing_fields = []
    if not ctx.deps.subtitle.strip():
        missing_fields.append("subtitle")
    if not ctx.deps.draft.strip():
        missing_fields.append("draft")

    if missing_fields:
        raise ModelRetry(
            f"Update the essay state before final output. Missing: {', '.join(missing_fields)}.",
        )

    return output
