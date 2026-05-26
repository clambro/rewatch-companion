"""Pydantic AI hero image search agent."""

import base64
from io import BytesIO
from typing import Any

import httpx
from ddgs import DDGS
from ddgs.exceptions import DDGSException
from openai import OpenAI
from PIL import Image, UnidentifiedImageError
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.messages import ImageUrl
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings
from pydantic_ai.providers.openai import OpenAIProvider

from common.rate_limit_retry import RateLimitRetryCapability
from common.settings import settings
from common.telemetry import configure_logfire
from hero_images.prompt import (
    HERO_IMAGE_AGENT_INSTRUCTIONS,
    HERO_IMAGE_SELECTION_INSTRUCTIONS,
    build_hero_image_prompt,
    build_hero_image_selection_input,
)
from hero_images.rules import (
    ASPECT_RATIO_TOLERANCE,
    HERO_IMAGE_HEIGHT,
    HERO_IMAGE_WIDTH,
    TARGET_ASPECT_RATIO,
)
from hero_images.schemas import (
    FoundHeroImage,
    HeroImageArticle,
    HeroImageSearchResult,
    HeroImageSelection,
    HeroImageWorkspace,
)

MODEL = "gpt-5.4-mini"
MODEL_SETTINGS: OpenAIResponsesModelSettings = {
    "openai_reasoning_effort": "low",
    "openai_reasoning_summary": "concise",
}
MAX_IMAGE_SEARCH_RESULTS = 12
MAX_FILTERED_IMAGE_SEARCH_RESULTS = 5
MIN_HERO_IMAGE_CANDIDATES = 3
SELECTION_IMAGE_MAX_SIZE = (768, 432)


def find_hero_image_for_article(*, article: HeroImageArticle) -> FoundHeroImage:
    """Find one online hero image candidate for a completed article."""
    agent = build_hero_image_agent()
    workspace = HeroImageWorkspace(article=article)
    prompt = build_hero_image_prompt(workspace=workspace)
    agent.run_sync(prompt, deps=workspace)

    return select_hero_image_from_candidates(
        article=article,
        candidates=workspace.candidates,
        image_data_urls=workspace.candidate_image_data_urls,
    )


def build_hero_image_agent() -> Agent[HeroImageWorkspace, str]:
    """Build the hero image search agent."""
    configure_logfire()
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
        ],
        capabilities=[RateLimitRetryCapability[HeroImageWorkspace]()],
        instructions=HERO_IMAGE_AGENT_INSTRUCTIONS,
    )
    agent.output_validator(validate_final_state)
    return agent


def search_show_images(
    ctx: RunContext[HeroImageWorkspace],
    query: str,
) -> list[HeroImageSearchResult] | str:
    """Search the web for show-image candidates."""
    search_query = query
    show_slug = ctx.deps.article.show.value
    if show_slug not in query.lower():
        search_query = f"{show_slug} {query}"

    try:
        results = DDGS().images(
            query=search_query,
            safesearch="moderate",
            max_results=MAX_IMAGE_SEARCH_RESULTS,
        )
    except DDGSException:
        return f"No image search results found for query: {search_query}"

    filtered_results = [
        image_search_result
        for result in results
        if (image_search_result := image_search_result_from_ddgs_result(result=result)) is not None
    ][:MAX_FILTERED_IMAGE_SEARCH_RESULTS]
    if filtered_results:
        return filtered_results

    return (
        f"No image search results found for query: {search_query} "
        f"at or above {HERO_IMAGE_WIDTH}x{HERO_IMAGE_HEIGHT} and near 16:9."
    )


def add_hero_image_candidate(
    ctx: RunContext[HeroImageWorkspace],
    image: FoundHeroImage,
) -> str:
    """Add one plausible hero image candidate before final selection."""
    try:
        image_data_url = selection_image_data_url(candidate=image)
    except (httpx.HTTPError, OSError, UnidentifiedImageError, ValueError) as error:
        return f"Candidate rejected: image URL did not download as a valid image: {error}"

    ctx.deps.candidates.append(
        FoundHeroImage(
            image_url=image.image_url.strip(),
            source_page_url=image.source_page_url.strip(),
            alt=image.alt.strip(),
            width=image.width,
            height=image.height,
        ),
    )
    ctx.deps.candidate_image_data_urls.append(image_data_url)
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


def select_hero_image_from_candidates(
    *,
    article: HeroImageArticle,
    candidates: list[FoundHeroImage],
    image_data_urls: list[str],
) -> FoundHeroImage:
    """Choose the final hero image with a direct non-agent model call."""
    if not candidates:
        raise RuntimeError("Hero image search finished without any candidates.")

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.responses.parse(
        model=MODEL,
        instructions=HERO_IMAGE_SELECTION_INSTRUCTIONS,
        input=build_hero_image_selection_input(
            article=article,
            candidates=candidates,
            image_data_urls=image_data_urls,
        ),
        text_format=HeroImageSelection,
    )
    if response.output_parsed is None:
        raise RuntimeError("Hero image selection did not return structured output.")

    return selected_hero_image_from_selection(
        candidates=candidates,
        selection=response.output_parsed,
    )


def selection_image_data_url(*, candidate: FoundHeroImage) -> str:
    """Return a normalized JPEG data URL for one candidate image."""
    response = httpx.get(candidate.image_url, follow_redirects=True, timeout=30)
    response.raise_for_status()
    with Image.open(BytesIO(response.content)) as source_image:
        selection_image = source_image.convert("RGB")
        selection_image.thumbnail(SELECTION_IMAGE_MAX_SIZE)

        buffer = BytesIO()
        selection_image.save(buffer, format="JPEG", quality=85, optimize=True)

    encoded_image = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded_image}"


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

    return candidates[selection.candidate_index]


def image_search_result_from_ddgs_result(*, result: dict[str, Any]) -> HeroImageSearchResult | None:
    """Normalize one sufficiently large DDGS image result for the agent."""
    image_url = str(result.get("image") or "")
    width = int(result["width"]) if result.get("width") else None
    height = int(result["height"]) if result.get("height") else None
    if width is None or height is None:
        return None
    if not image_search_result_has_valid_shape(width=width, height=height):
        return None

    return HeroImageSearchResult(
        title=str(result.get("title") or ""),
        image_url=image_url,
        image=ImageUrl(url=image_url, media_type="image/jpeg"),
        source_page_url=str(result.get("url") or ""),
        thumbnail_url=str(result.get("thumbnail") or ""),
        source_name=str(result.get("source") or ""),
        width=width,
        height=height,
    )


def image_search_result_has_valid_shape(*, width: int, height: int) -> bool:
    """Return whether image dimensions are large enough and close to 16:9."""
    if width < HERO_IMAGE_WIDTH or height < HERO_IMAGE_HEIGHT:
        return False

    ratio = width / height
    return abs(ratio - TARGET_ASPECT_RATIO) <= ASPECT_RATIO_TOLERANCE
