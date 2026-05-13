"""Pydantic AI essay agent."""

import logfire
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool
from pydantic_ai.common_tools.web_fetch import web_fetch_tool
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings
from pydantic_ai.providers.openai import OpenAIProvider

from prompt import AGENT_INSTRUCTIONS, build_essay_prompt
from schemas import EssaySource, EssayTarget, EssayWorkspace, GeneratedEssay
from settings import settings

MODEL = "gpt-5.4-nano"
MODEL_SETTINGS: OpenAIResponsesModelSettings = {
    "openai_reasoning_effort": "medium",
    "openai_reasoning_summary": "concise",
}

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
    agent.run_sync(prompt, deps=workspace)
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
            duckduckgo_search_tool(),
            web_fetch_tool(),
        ],
        instructions=AGENT_INSTRUCTIONS,
    )
    agent.output_validator(validate_final_state)
    return agent


def update_subtitle(ctx: RunContext[EssayWorkspace], subtitle: str) -> str:
    """Update the article subtitle."""
    ctx.deps.subtitle = subtitle.strip()
    return "Subtitle updated."


def update_draft(ctx: RunContext[EssayWorkspace], body_mdx: str) -> str:
    """Update the full article draft."""
    ctx.deps.draft = body_mdx.strip()
    return "Draft updated."


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
