"""Schemas for essay generation."""

from enum import StrEnum

from pydantic import BaseModel


class Show(StrEnum):
    """Supported show slugs."""

    SUCCESSION = "succession"


class EssayKind(StrEnum):
    """Supported generated essay kinds."""

    ABOUT = "about"
    THEMES = "themes"
    CHARACTERS = "characters"
    EPISODES = "episodes"


class EssayTarget(BaseModel):
    """Minimal user-provided target for an essay run."""

    show: Show
    kind: EssayKind
    title: str
    prompt: str


class GeneratedEssay(BaseModel):
    """Structured output returned by the LLM."""

    subtitle: str
    body_mdx: str
