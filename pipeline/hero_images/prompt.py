"""Prompts for hero image search."""

import json
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from openai.types.responses import ResponseInputParam

    from hero_images.schemas import FoundHeroImage, HeroImageArticle, HeroImageWorkspace

HERO_IMAGE_AGENT_INSTRUCTIONS = """
# Identity

You are the hero image search agent for Rewatch Companion, a static site for
serious full-series television criticism.

# Product

Each article needs one strong hero image. The image should be a still,
publicity image, or review-site image from the show itself, not a generated
image, generic stock image, poster replacement, meme, collage, or unrelated
symbolic image.

The image will be downloaded later and stored locally in the content tree. Your
job is to find viable candidates and preserve enough provenance for that later
download step. A separate selection prompt will choose the final image from the
candidate set.

# Selection Rules

- Prefer images from the show, episode, character, or scene discussed by the
  article.
- Prefer an image URL that points directly to the image file or a stable CDN
  image.
- Write the `alt` field yourself, using the article, search result, and visible
  image context available during research. The alt must describe what is
  actually in the image. Do not write a generic caption, do not copy a
  search-result title or page headline, and do not describe article ideas that
  are not visible in the image.
- Always include the source page URL where the image was found.
- Do not invent rights status, dimensions, or provenance.
- Do not choose generic office, city, object, or mood images unless no show
  image can be found.
- Do not choose images that are obviously low-resolution, watermarked,
  distorted, fan-edited, AI-generated, or unrelated to the article.

# Workflow

1. Read the article context.
2. Search for candidate images using the image search tool. Try several queries
   if needed. The search results include image previews, so judge the visible
   image, not just the title or URL.
3. Use `add_hero_image_candidate` to collect several viable candidates.
4. Return `DONE` only after the candidate set has been collected.
""".strip()

HERO_IMAGE_SELECTION_INSTRUCTIONS = """
You choose one final hero image from candidates collected by a separate search
agent for Rewatch Companion, a static site for serious full-series television
criticism.

Pick the candidate that best fits the article by looking at the visible images.
Use candidate alt text as supporting context, but the visible image is
authoritative. If the alt text conflicts with the visible image, trust the
image.

Return the zero-based candidate index and a concise rationale that describes
why the visible image fits the article. Do not invent a new image or choose
anything outside the candidate list.
""".strip()

HERO_IMAGE_PROMPT_TEMPLATE = """
# Task

Find one online hero image candidate for this completed Rewatch Companion
article.

# Article

<article>
Show: {show}
Title: {title}
Subtitle: {subtitle}

{article_mdx}
</article>
""".strip()

HERO_IMAGE_SELECTION_CONTEXT_TEMPLATE = """
# Task

Choose the best hero image candidate for this completed article.

# Article

<article>
Show: {show}
Title: {title}
Subtitle: {subtitle}

{article_mdx}
</article>

# Candidates

<candidates>
{candidates}
</candidates>
""".strip()

CANDIDATE_TEMPLATE = """
<candidate index="{index}">
{candidate_json}
</candidate>
""".strip()


def build_hero_image_prompt(*, workspace: HeroImageWorkspace) -> str:
    """Build the runtime prompt for hero image search."""
    article = workspace.article
    return HERO_IMAGE_PROMPT_TEMPLATE.format(
        show=article.show.value,
        title=article.title,
        subtitle=article.subtitle,
        article_mdx=article.article_mdx,
    )


def build_hero_image_selection_prompt(
    *,
    article: HeroImageArticle,
    candidates: list[FoundHeroImage],
) -> str:
    """Build the text context for direct final hero image selection."""
    return HERO_IMAGE_SELECTION_CONTEXT_TEMPLATE.format(
        show=article.show.value,
        title=article.title,
        subtitle=article.subtitle,
        article_mdx=article.article_mdx,
        candidates="\n\n".join(
            CANDIDATE_TEMPLATE.format(
                index=index,
                candidate_json=json.dumps(
                    candidate.model_dump(mode="json"),
                    ensure_ascii=False,
                ),
            )
            for index, candidate in enumerate(candidates)
        ),
    )


def build_hero_image_selection_input(
    *,
    article: HeroImageArticle,
    candidates: list[FoundHeroImage],
    image_data_urls: list[str],
) -> ResponseInputParam:
    """Build multimodal input for direct final hero image selection."""
    content: list[dict[str, Any]] = [
        {
            "type": "input_text",
            "text": build_hero_image_selection_prompt(article=article, candidates=candidates),
        },
    ]
    for index, image_data_url in enumerate(image_data_urls):
        content.extend(
            [
                {
                    "type": "input_text",
                    "text": f"Candidate {index} image:",
                },
                {
                    "type": "input_image",
                    "image_url": image_data_url,
                    "detail": "low",
                },
            ],
        )

    return cast(
        "ResponseInputParam",
        [
            {
                "role": "user",
                "content": content,
            },
        ],
    )
