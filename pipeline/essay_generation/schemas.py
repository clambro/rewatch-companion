"""Schemas for essay generation."""

from pydantic import BaseModel, Field

from common.schemas import EssayKind, Show  # noqa: TC001 - Pydantic needs these enums at runtime.


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
