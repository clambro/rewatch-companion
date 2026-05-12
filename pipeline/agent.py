"""Pydantic AI essay agent."""

import asyncio
from typing import cast

from loguru import logger
from pydantic_ai import Agent
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool
from pydantic_ai.common_tools.web_fetch import web_fetch_tool
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

from prompt import AGENT_INSTRUCTIONS, build_essay_prompt
from schemas import EssayTarget, GeneratedEssay
from settings import settings

MODEL = "gpt-5.4-nano"


def run_essay_agent(*, target: EssayTarget) -> GeneratedEssay:
    """Generate an essay for a target."""
    return asyncio.run(_run_essay_agent_iteratively(target=target))


async def _run_essay_agent_iteratively(*, target: EssayTarget) -> GeneratedEssay:
    """Generate an essay while logging intermediate agent graph nodes."""
    agent = build_essay_agent()
    prompt = build_essay_prompt(target=target)

    logger.info(f"Starting essay agent run for show={target.show.value} kind={target.kind.value}")
    async with agent.iter(prompt, deps=target) as agent_run:
        async for node in agent_run:
            logger.info(f"Agent step: {node.__class__.__name__}")
            logger.debug(f"Agent step detail: {node!r}")

    logger.info("Essay agent run completed")
    return agent_run.result.output


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
