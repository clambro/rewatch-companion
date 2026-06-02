"""Shared pipeline enums."""

from enum import StrEnum


class Show(StrEnum):
    """Supported show slugs."""

    BREAKING_BAD = "breaking-bad"
    SUCCESSION = "succession"


class EssayKind(StrEnum):
    """Supported generated essay kinds."""

    THEMES = "themes"
    CHARACTERS = "characters"
    EPISODES = "episodes"
