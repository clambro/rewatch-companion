"""Root command-line interface for pipeline workflows."""

from __future__ import annotations

import argparse
from enum import StrEnum
from typing import TYPE_CHECKING

from generate_character import generate_character_essay
from generate_episode import generate_episode_essay
from generate_missing_essays import generate_missing_essays
from generate_theme import generate_theme_essay
from hero_images import HeroImageCommand, find_article_hero_image, find_missing_hero_images
from schemas import EssayKind, Show

if TYPE_CHECKING:
    from collections.abc import Sequence


class PipelineCommand(StrEnum):
    """Top-level pipeline commands."""

    ESSAY = "essay"
    IMAGE = "image"


class EssayCommand(StrEnum):
    """Essay-generation commands."""

    THEME = "theme"
    CHARACTER = "character"
    EPISODE = "episode"
    MISSING = "missing"


class ImageCommand(StrEnum):
    """Hero-image commands."""

    THEME = "theme"
    CHARACTER = "character"
    EPISODE = "episode"
    MISSING = "missing"


def main(argv: Sequence[str] | None = None) -> None:
    """Run the pipeline CLI."""
    args = build_parser().parse_args(argv)
    match PipelineCommand(args.command):
        case PipelineCommand.ESSAY:
            run_essay_command(args=args)
        case PipelineCommand.IMAGE:
            run_image_command(args=args)


def build_parser() -> argparse.ArgumentParser:
    """Build the root pipeline argument parser."""
    parser = argparse.ArgumentParser(description="Run Rewatch Companion pipeline workflows.")
    commands = parser.add_subparsers(dest="command", required=True)

    essay_parser = commands.add_parser(PipelineCommand.ESSAY.value, help="Generate essays.")
    add_essay_commands(parser=essay_parser)

    image_parser = commands.add_parser(PipelineCommand.IMAGE.value, help="Find hero images.")
    add_image_commands(parser=image_parser)

    return parser


def run_essay_command(*, args: argparse.Namespace) -> None:
    """Run one essay-generation command."""
    show = Show(args.show)
    match EssayCommand(args.essay_command):
        case EssayCommand.THEME:
            generate_theme_essay(show=show, slug=args.slug)
        case EssayCommand.CHARACTER:
            generate_character_essay(show=show, slug=args.slug)
        case EssayCommand.EPISODE:
            generate_episode_essay(show=show, season=args.season, episode_number=args.episode)
        case EssayCommand.MISSING:
            generate_missing_essays(show=show, dry_run=args.dry_run)


def run_image_command(*, args: argparse.Namespace) -> None:
    """Run one hero-image command."""
    show = Show(args.show)
    match ImageCommand(args.image_command):
        case ImageCommand.THEME:
            find_article_hero_image(
                command=HeroImageCommand(show=show, kind=EssayKind.THEMES, slug=args.slug),
            )
        case ImageCommand.CHARACTER:
            find_article_hero_image(
                command=HeroImageCommand(show=show, kind=EssayKind.CHARACTERS, slug=args.slug),
            )
        case ImageCommand.EPISODE:
            find_article_hero_image(
                command=HeroImageCommand(
                    show=show,
                    kind=EssayKind.EPISODES,
                    season=args.season,
                    episode=args.episode,
                ),
            )
        case ImageCommand.MISSING:
            find_missing_hero_images(show=show, dry_run=args.dry_run)


def add_essay_commands(*, parser: argparse.ArgumentParser) -> None:
    """Add essay-generation subcommands to a parser."""
    commands = parser.add_subparsers(dest="essay_command", required=True)

    theme_parser = commands.add_parser(EssayCommand.THEME.value, help="Generate a theme essay.")
    add_show_argument(parser=theme_parser)
    theme_parser.add_argument("--slug", required=True)

    character_parser = commands.add_parser(
        EssayCommand.CHARACTER.value,
        help="Generate a character essay.",
    )
    add_show_argument(parser=character_parser)
    character_parser.add_argument("--slug", required=True)

    episode_parser = commands.add_parser(
        EssayCommand.EPISODE.value,
        help="Generate an episode essay.",
    )
    add_show_argument(parser=episode_parser)
    episode_parser.add_argument("--season", type=int, required=True)
    episode_parser.add_argument("--episode", type=int, required=True)

    missing_parser = commands.add_parser(
        EssayCommand.MISSING.value,
        help="Generate missing essays.",
    )
    add_show_argument(parser=missing_parser)
    missing_parser.add_argument("--dry-run", action="store_true")


def add_image_commands(*, parser: argparse.ArgumentParser) -> None:
    """Add hero-image subcommands to a parser."""
    commands = parser.add_subparsers(dest="image_command", required=True)

    theme_parser = commands.add_parser(ImageCommand.THEME.value, help="Find a theme hero image.")
    add_show_argument(parser=theme_parser)
    theme_parser.add_argument("--slug", required=True)

    character_parser = commands.add_parser(
        ImageCommand.CHARACTER.value,
        help="Find a character hero image.",
    )
    add_show_argument(parser=character_parser)
    character_parser.add_argument("--slug", required=True)

    episode_parser = commands.add_parser(
        ImageCommand.EPISODE.value,
        help="Find an episode hero image.",
    )
    add_show_argument(parser=episode_parser)
    episode_parser.add_argument("--season", type=int, required=True)
    episode_parser.add_argument("--episode", type=int, required=True)

    missing_parser = commands.add_parser(
        ImageCommand.MISSING.value,
        help="Find missing hero images.",
    )
    add_show_argument(parser=missing_parser)
    missing_parser.add_argument("--dry-run", action="store_true")


def add_show_argument(*, parser: argparse.ArgumentParser) -> None:
    """Add the standard show selector to a parser."""
    parser.add_argument("--show", choices=[show.value for show in Show], required=True)


if __name__ == "__main__":
    main()
