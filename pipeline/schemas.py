"""Schemas for essay generation."""

from enum import StrEnum

from pydantic import BaseModel


class EssayKind(StrEnum):
    """Supported generated essay kinds."""

    ABOUT = "about"
    THEME = "theme"
    CHARACTER = "character"
    EPISODE = "episode"


class EssayTarget(BaseModel):
    """Minimal user-provided target for an essay run."""

    kind: EssayKind
    description: str


class GeneratedEssay(BaseModel):
    """Structured output returned by the LLM."""

    title: str
    subtitle: str
    body_mdx: str


class EssayDraft(GeneratedEssay):
    """Generated essay plus orchestration-owned metadata."""

    slug: str
