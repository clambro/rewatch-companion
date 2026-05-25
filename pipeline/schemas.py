"""Schemas for essay generation."""

from enum import StrEnum


class Show(StrEnum):
    """Supported show slugs."""

    SUCCESSION = "succession"


class EssayKind(StrEnum):
    """Supported generated essay kinds."""

    THEMES = "themes"
    CHARACTERS = "characters"
    EPISODES = "episodes"
