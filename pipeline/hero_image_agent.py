"""Pydantic AI hero image search agent."""

from typing import Any

import logfire
from ddgs import DDGS
from openai import OpenAI
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.common_tools.web_fetch import web_fetch_tool
from pydantic_ai.messages import ImageUrl
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings
from pydantic_ai.providers.openai import OpenAIProvider

from hero_image_prompt import (
    HERO_IMAGE_AGENT_INSTRUCTIONS,
    HERO_IMAGE_SELECTION_INSTRUCTIONS,
    build_hero_image_prompt,
    build_hero_image_selection_input,
)
from hero_image_rules import (
    ASPECT_RATIO_TOLERANCE,
    HERO_IMAGE_HEIGHT,
    HERO_IMAGE_WIDTH,
    TARGET_ASPECT_RATIO,
)
from rate_limit_retry import RateLimitRetryCapability
from schemas import (
    FoundHeroImage,
    HeroImageArticle,
    HeroImageSearchResult,
    HeroImageSelection,
    HeroImageWorkspace,
)
from settings import settings

MODEL = "gpt-5.4-mini"
MODEL_SETTINGS: OpenAIResponsesModelSettings = {
    "openai_reasoning_effort": "low",
    "openai_reasoning_summary": "concise",
}
MAX_IMAGE_SEARCH_RESULTS = 12
MIN_HERO_IMAGE_CANDIDATES = 3

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

    return select_hero_image_from_candidates(article=article, candidates=workspace.candidates)


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
            add_hero_image_candidate,
            web_fetch_tool(),
        ],
        capabilities=[RateLimitRetryCapability[HeroImageWorkspace]()],
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


def add_hero_image_candidate(
    ctx: RunContext[HeroImageWorkspace],
    image: FoundHeroImage,
) -> str:
    """Add one plausible hero image candidate before final selection."""
    rejection_message = hero_image_rejection_message(image=image)
    if rejection_message:
        return (
            f"Candidate rejected: {rejection_message} "
            "Choose another image-search result and call add_hero_image_candidate again."
        )

    ctx.deps.candidates.append(normalized_hero_image(image=image))
    return (
        f"Candidate added. Current candidate count: {len(ctx.deps.candidates)}. "
        f"Collect at least {MIN_HERO_IMAGE_CANDIDATES} viable candidates before choosing, "
        "unless search results genuinely cannot support that many."
    )


def validate_final_state(ctx: RunContext[HeroImageWorkspace], output: str) -> str:
    """Reject final output until the workspace contains at least one candidate image."""
    if not ctx.deps.candidates:
        raise ModelRetry("Collect at least one viable candidate with add_hero_image_candidate.")

    return output


def validate_selected_image_aspect_ratio(*, image: FoundHeroImage) -> None:
    """Reject selected image dimensions that cannot produce the standard hero image."""
    rejection_message = hero_image_rejection_message(image=image)
    if rejection_message:
        raise ModelRetry(rejection_message)


def hero_image_rejection_message(*, image: FoundHeroImage) -> str:
    """Return why a candidate image should be rejected, or an empty string."""
    if image.width is None or image.height is None:
        return ""

    if image.width < HERO_IMAGE_WIDTH or image.height < HERO_IMAGE_HEIGHT:
        return (
            f"Choose a hero image at least {HERO_IMAGE_WIDTH}x{HERO_IMAGE_HEIGHT}. "
            f"The selected image is {image.width}x{image.height}."
        )

    ratio = image.width / image.height
    if abs(ratio - TARGET_ASPECT_RATIO) <= ASPECT_RATIO_TOLERANCE:
        return ""

    return (
        f"Choose a hero image closer to 16:9. The selected image is "
        f"{image.width}x{image.height} ({ratio:.2f}:1)."
    )


def select_hero_image_from_candidates(
    *,
    article: HeroImageArticle,
    candidates: list[FoundHeroImage],
) -> FoundHeroImage:
    """Choose the final hero image with a direct non-agent model call."""
    if not candidates:
        raise RuntimeError("Hero image search finished without any candidates.")

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.responses.parse(
        model=MODEL,
        instructions=HERO_IMAGE_SELECTION_INSTRUCTIONS,
        input=build_hero_image_selection_input(article=article, candidates=candidates),
        text_format=HeroImageSelection,
    )
    if response.output_parsed is None:
        raise RuntimeError("Hero image selection did not return structured output.")

    return selected_hero_image_from_selection(
        candidates=candidates,
        selection=response.output_parsed,
    )


def selected_hero_image_from_selection(
    *,
    candidates: list[FoundHeroImage],
    selection: HeroImageSelection,
) -> FoundHeroImage:
    """Return the candidate chosen by the direct selection prompt."""
    if selection.candidate_index < 0 or selection.candidate_index >= len(candidates):
        raise RuntimeError(
            f"Hero image selection returned invalid candidate index "
            f"{selection.candidate_index}. Candidate count: {len(candidates)}.",
        )

    return candidates[selection.candidate_index].model_copy(
        update={"rationale": selection.rationale.strip()},
    )


def normalized_hero_image(*, image: FoundHeroImage) -> FoundHeroImage:
    """Return a selected image with normalized string fields."""
    return image.model_copy(
        update={
            "image_url": image.image_url.strip(),
            "source_page_url": image.source_page_url.strip(),
            "alt": image.alt.strip(),
            "rationale": image.rationale.strip(),
        },
    )


def image_search_result_from_ddgs_result(*, result: dict[str, Any]) -> HeroImageSearchResult:
    """Normalize one DDGS image result for the agent."""
    image_url = str(result.get("image") or "")
    return HeroImageSearchResult(
        title=str(result.get("title") or ""),
        image_url=image_url,
        image=ImageUrl(url=image_url, media_type="image/jpeg"),
        source_page_url=str(result.get("url") or ""),
        thumbnail_url=str(result.get("thumbnail") or ""),
        source_name=str(result.get("source") or ""),
        width=int(result["width"]) if result.get("width") else None,
        height=int(result["height"]) if result.get("height") else None,
    )
