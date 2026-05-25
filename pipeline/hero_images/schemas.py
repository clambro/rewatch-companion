"""Schemas for hero image workflows."""

from typing import Any

from pydantic import BaseModel, Field

from schemas import Show  # noqa: TC001 - Pydantic needs the enum at runtime.


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
