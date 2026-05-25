"""Generate manifest essays that are missing from content."""

from __future__ import annotations

import argparse
import sys
from typing import TYPE_CHECKING

from pydantic import BaseModel

from generate_character import generate_character_essay
from generate_episode import generate_episode_essay
from generate_essay import CONTENT_ROOT
from generate_theme import generate_theme_essay
from manifest import episode_slug, load_manifest
from schemas import EssayKind, Show

if TYPE_CHECKING:
    from pathlib import Path


class GenerateMissingEssaysCommand(BaseModel):
    """Parsed CLI command for missing essay generation."""

    show: Show
    dry_run: bool = False


class MissingEssay(BaseModel):
    """One missing manifest essay target."""

    kind: EssayKind
    slug: str | None = None
    season: int | None = None
    episode: int | None = None


def main() -> None:
    """Generate missing manifest essays in dependency order."""
    parser = argparse.ArgumentParser(description="Generate missing manifest essays.")
    parser.add_argument("--show", choices=[show.value for show in Show], required=True)
    parser.add_argument("--dry-run", action="store_true")
    command = GenerateMissingEssaysCommand.model_validate(vars(parser.parse_args()))

    missing_essays = missing_manifest_essays(show=command.show)
    if not missing_essays:
        sys.stdout.write("No missing essays.\n")
        return

    for missing_essay in missing_essays:
        rendered_command = render_essay_command(show=command.show, essay=missing_essay)
        sys.stdout.write(f"Running: {rendered_command}\n")
        if not command.dry_run:
            generate_missing_essay(show=command.show, essay=missing_essay)


def missing_manifest_essays(*, show: Show) -> list[MissingEssay]:
    """Return missing manifest essays in dependency order."""
    manifest = load_manifest(show=show)
    show_root = CONTENT_ROOT / show.value
    essays: list[MissingEssay] = []

    for theme in manifest.themes:
        output_dir = show_root / EssayKind.THEMES.value / theme.slug
        if is_missing_essay(output_dir=output_dir):
            essays.append(MissingEssay(kind=EssayKind.THEMES, slug=theme.slug))

    for character in manifest.characters:
        output_dir = show_root / EssayKind.CHARACTERS.value / character.slug
        if is_missing_essay(output_dir=output_dir):
            essays.append(MissingEssay(kind=EssayKind.CHARACTERS, slug=character.slug))

    for episode in manifest.episodes:
        output_dir = (
            show_root
            / EssayKind.EPISODES.value
            / f"s{episode.season:02}"
            / episode_slug(episode=episode)
        )
        if is_missing_essay(output_dir=output_dir):
            essays.append(
                MissingEssay(
                    kind=EssayKind.EPISODES,
                    season=episode.season,
                    episode=episode.episode,
                ),
            )

    return essays


def generate_missing_essay(*, show: Show, essay: MissingEssay) -> None:
    """Generate one missing essay."""
    match essay.kind:
        case EssayKind.THEMES:
            if essay.slug is None:
                raise ValueError("Missing theme slug.")
            generate_theme_essay(show=show, slug=essay.slug)
        case EssayKind.CHARACTERS:
            if essay.slug is None:
                raise ValueError("Missing character slug.")
            generate_character_essay(show=show, slug=essay.slug)
        case EssayKind.EPISODES:
            if essay.season is None or essay.episode is None:
                raise ValueError("Missing episode season or number.")
            generate_episode_essay(show=show, season=essay.season, episode_number=essay.episode)


def render_essay_command(*, show: Show, essay: MissingEssay) -> str:
    """Return the equivalent single-target essay generation command."""
    match essay.kind:
        case EssayKind.THEMES:
            return f"uv run python generate_theme.py --show {show.value} --slug {essay.slug}"
        case EssayKind.CHARACTERS:
            return f"uv run python generate_character.py --show {show.value} --slug {essay.slug}"
        case EssayKind.EPISODES:
            return (
                f"uv run python generate_episode.py --show {show.value} "
                f"--season {essay.season} --episode {essay.episode}"
            )


def is_missing_essay(*, output_dir: Path) -> bool:
    """Return whether a generated essay output is incomplete."""
    return not all(
        (output_dir / file_name).is_file()
        for file_name in ("index.mdx", "article.yaml", "summary.mdx")
    )


if __name__ == "__main__":
    main()
