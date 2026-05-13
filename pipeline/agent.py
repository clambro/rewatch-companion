"""Pydantic AI essay agent."""

from typing import cast

import logfire
from pydantic_ai import Agent
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool
from pydantic_ai.common_tools.web_fetch import web_fetch_tool
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

from prompt import AGENT_INSTRUCTIONS, build_essay_prompt
from schemas import EssayTarget, GeneratedEssay
from settings import settings

MODEL = "gpt-5.4-nano"

logfire.configure(
    service_name="rewatch-pipeline",
    token=settings.logfire_token,
    metrics=logfire.MetricsOptions(collect_in_spans=True),
    scrubbing=False,
)
logfire.instrument_pydantic_ai(use_aggregated_usage_attribute_names=True)
logfire.instrument_openai(version="latest")
logfire.instrument_httpx(capture_all=True)


def run_essay_agent(*, target: EssayTarget) -> GeneratedEssay:
    """Generate an essay for a target."""
    agent = build_essay_agent()
    prompt = build_essay_prompt(target=target)
    return agent.run_sync(prompt, deps=target).output


def build_essay_agent() -> Agent[EssayTarget, GeneratedEssay]:
    """Build the essay generation agent."""
    openai_model = OpenAIResponsesModel(
        MODEL,
        provider=OpenAIProvider(api_key=settings.openai_api_key),
    )
    return cast(
        "Agent[EssayTarget, GeneratedEssay]",
        Agent(
            openai_model,
            deps_type=EssayTarget,
            output_type=GeneratedEssay,
            tools=[
                duckduckgo_search_tool(),
                web_fetch_tool(),
            ],
            instructions=AGENT_INSTRUCTIONS,
        ),
    )
