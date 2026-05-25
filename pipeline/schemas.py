"""Schemas for essay generation."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Show(StrEnum):
    """Supported show slugs."""

    SUCCESSION = "succession"


class EssayKind(StrEnum):
    """Supported generated essay kinds."""

    THEMES = "themes"
    CHARACTERS = "characters"
    EPISODES = "episodes"


class EssayTarget(BaseModel):
    """Minimal user-provided target for an essay run."""

    show: Show
    kind: EssayKind
    title: str
    prompt: str
    slug: str
    season: int | None = None
    episode: int | None = None


class EssaySource(BaseModel):
    """Reference source supplied to an essay run."""

    label: str
    title: str
    subtitle: str
    summary_mdx: str


class EssayWorkspace(BaseModel):
    """Mutable state for an essay run."""

    target: EssayTarget
    sources: list[EssaySource] = Field(default_factory=list)
    subtitle: str = ""
    draft: str = ""
    research_searches: int = 0
    research_fetches: int = 0


class GeneratedEssay(BaseModel):
    """Structured output returned by the LLM."""

    subtitle: str
    body_mdx: str


class HeroImageArticle(BaseModel):
    """Completed article used as input for hero image search."""

    show: Show
    title: str
    subtitle: str
    article_mdx: str


class HeroImageSearchResult(BaseModel):
    """One image-search result exposed to the agent."""

    title: str
    image_url: str
    image: Any
    source_page_url: str
    thumbnail_url: str = ""
    source_name: str = ""
    width: int | None = None
    height: int | None = None


class FoundHeroImage(BaseModel):
    """Selected online image result for a completed article."""

    image_url: str
    source_page_url: str
    alt: str
    rationale: str
    width: int | None = None
    height: int | None = None


class HeroImageSelection(BaseModel):
    """Direct model selection from collected hero image candidates."""

    candidate_index: int
    rationale: str


class HeroImageWorkspace(BaseModel):
    """Mutable state for a hero image search run."""

    article: HeroImageArticle
    candidates: list[FoundHeroImage] = Field(default_factory=list)
