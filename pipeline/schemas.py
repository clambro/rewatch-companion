"""Schemas for essay generation."""

from enum import StrEnum

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
    slug: str | None = None
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


class GeneratedEssay(BaseModel):
    """Structured output returned by the LLM."""

    subtitle: str
    body_mdx: str
