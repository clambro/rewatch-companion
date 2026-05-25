"""Pydantic AI hero image search agent."""

from typing import Any

import logfire
from ddgs import DDGS
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.common_tools.web_fetch import web_fetch_tool
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings
from pydantic_ai.providers.openai import OpenAIProvider

from hero_image_prompt import HERO_IMAGE_AGENT_INSTRUCTIONS, build_hero_image_prompt
from schemas import FoundHeroImage, HeroImageArticle, HeroImageSearchResult, HeroImageWorkspace
from settings import settings

MODEL = "gpt-5.4-nano"
MODEL_SETTINGS: OpenAIResponsesModelSettings = {
    "openai_reasoning_effort": "medium",
    "openai_reasoning_summary": "concise",
}
MAX_IMAGE_SEARCH_RESULTS = 12

logfire.configure(
    service_name="rewatch-pipeline",
    token=settings.logfire_token,
    metrics=logfire.MetricsOptions(collect_in_spans=True),
    scrubbing=False,
)
logfire.instrument_pydantic_ai(use_aggregated_usage_attribute_names=True)
logfire.instrument_openai(version="latest")
logfire.instrument_httpx(capture_all=True)


def find_hero_image_for_article(*, article: HeroImageArticle) -> FoundHeroImage:
    """Find one online hero image candidate for a completed article."""
    agent = build_hero_image_agent()
    workspace = HeroImageWorkspace(article=article)
    prompt = build_hero_image_prompt(workspace=workspace)
    agent.run_sync(prompt, deps=workspace)

    if workspace.selected_image is None:
        raise RuntimeError("Hero image search finished without a selected image.")

    return workspace.selected_image


def build_hero_image_agent() -> Agent[HeroImageWorkspace, str]:
    """Build the hero image search agent."""
    openai_model = OpenAIResponsesModel(
        MODEL,
        provider=OpenAIProvider(api_key=settings.openai_api_key),
    )
    agent = Agent(
        openai_model,
        deps_type=HeroImageWorkspace,
        output_type=str,
        model_settings=MODEL_SETTINGS,
        tools=[
            search_show_images,
            set_hero_image,
            web_fetch_tool(),
        ],
        instructions=HERO_IMAGE_AGENT_INSTRUCTIONS,
    )
    agent.output_validator(validate_final_state)
    return agent


def search_show_images(
    ctx: RunContext[HeroImageWorkspace],
    query: str,
) -> list[HeroImageSearchResult]:
    """Search the web for show-image candidates."""
    search_query = query
    show_slug = ctx.deps.article.show.value
    if show_slug not in query.lower():
        search_query = f"{show_slug} {query}"

    results = DDGS().images(
        query=search_query,
        safesearch="moderate",
        max_results=MAX_IMAGE_SEARCH_RESULTS,
    )
    return [image_search_result_from_ddgs_result(result=result) for result in results]


def set_hero_image(
    ctx: RunContext[HeroImageWorkspace],
    image: FoundHeroImage,
) -> str:
    """Store the selected hero image candidate."""
    ctx.deps.selected_image = image.model_copy(
        update={
            "image_url": image.image_url.strip(),
            "source_page_url": image.source_page_url.strip(),
            "title": image.title.strip(),
            "credit": image.credit.strip(),
            "rationale": image.rationale.strip(),
        },
    )
    return "Hero image selected."


def validate_final_state(ctx: RunContext[HeroImageWorkspace], output: str) -> str:
    """Reject final output until the workspace contains a selected image."""
    if ctx.deps.selected_image is None:
        raise ModelRetry("Select a hero image with set_hero_image before final output.")

    return output


def image_search_result_from_ddgs_result(*, result: dict[str, Any]) -> HeroImageSearchResult:
    """Normalize one DDGS image result for the agent."""
    return HeroImageSearchResult(
        title=str(result.get("title") or ""),
        image_url=str(result.get("image") or ""),
        source_page_url=str(result.get("url") or ""),
        thumbnail_url=str(result.get("thumbnail") or ""),
        source_name=str(result.get("source") or ""),
        width=int(result["width"]) if result.get("width") else None,
        height=int(result["height"]) if result.get("height") else None,
    )
