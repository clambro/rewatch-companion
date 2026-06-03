"""Root command-line interface for pipeline workflows."""

import argparse
import sys
from enum import StrEnum
from typing import TYPE_CHECKING

from common.network_preflight import assert_network_baseline, write_network_baseline
from common.schemas import EssayKind, Show
from essay_generation import (
    generate_character_essay,
    generate_episode_essay,
    generate_missing_essays,
    generate_theme_essay,
)
from hero_images import HeroImageCommand, find_article_hero_image, find_missing_hero_images

if TYPE_CHECKING:
    from collections.abc import Sequence


class PipelineCommand(StrEnum):
    """Top-level pipeline commands."""

    ESSAY = "essay"
    IMAGE = "image"
    NETWORK = "network"


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


class NetworkCommand(StrEnum):
    """Network preflight commands."""

    BASELINE = "baseline"
    CHECK = "check"


def main(argv: Sequence[str] | None = None) -> None:
    """Run the pipeline CLI."""
    args = build_parser().parse_args(argv)
    match PipelineCommand(args.command):
        case PipelineCommand.ESSAY:
            run_essay_command(args=args)
        case PipelineCommand.IMAGE:
            run_image_command(args=args)
        case PipelineCommand.NETWORK:
            run_network_command(args=args)


def build_parser() -> argparse.ArgumentParser:
    """Build the root pipeline argument parser."""
    parser = argparse.ArgumentParser(description="Run Rewatch Companion pipeline workflows.")
    commands = parser.add_subparsers(dest="command", required=True)

    essay_parser = commands.add_parser(PipelineCommand.ESSAY.value, help="Generate essays.")
    add_essay_commands(parser=essay_parser)

    image_parser = commands.add_parser(PipelineCommand.IMAGE.value, help="Find hero images.")
    add_image_commands(parser=image_parser)

    network_parser = commands.add_parser(
        PipelineCommand.NETWORK.value,
        help="Manage network preflight checks.",
    )
    add_network_commands(parser=network_parser)

    return parser


def run_essay_command(*, args: argparse.Namespace) -> None:
    """Run one essay-generation command."""
    show = Show(args.show)
    match EssayCommand(args.essay_command):
        case EssayCommand.THEME:
            assert_network_baseline()
            generate_theme_essay(show=show, slug=args.slug)
        case EssayCommand.CHARACTER:
            assert_network_baseline()
            generate_character_essay(show=show, slug=args.slug)
        case EssayCommand.EPISODE:
            assert_network_baseline()
            generate_episode_essay(show=show, season=args.season, episode_number=args.episode)
        case EssayCommand.MISSING:
            if not args.dry_run:
                assert_network_baseline()
            generate_missing_essays(show=show, dry_run=args.dry_run)


def run_image_command(*, args: argparse.Namespace) -> None:
    """Run one hero-image command."""
    show = Show(args.show)
    match ImageCommand(args.image_command):
        case ImageCommand.THEME:
            assert_network_baseline()
            find_article_hero_image(
                command=HeroImageCommand(show=show, kind=EssayKind.THEMES, slug=args.slug),
            )
        case ImageCommand.CHARACTER:
            assert_network_baseline()
            find_article_hero_image(
                command=HeroImageCommand(show=show, kind=EssayKind.CHARACTERS, slug=args.slug),
            )
        case ImageCommand.EPISODE:
            assert_network_baseline()
            find_article_hero_image(
                command=HeroImageCommand(
                    show=show,
                    kind=EssayKind.EPISODES,
                    season=args.season,
                    episode=args.episode,
                ),
            )
        case ImageCommand.MISSING:
            if not args.dry_run:
                assert_network_baseline()
            find_missing_hero_images(show=show, dry_run=args.dry_run)


def run_network_command(*, args: argparse.Namespace) -> None:
    """Run one network preflight command."""
    match NetworkCommand(args.network_command):
        case NetworkCommand.BASELINE:
            identity = write_network_baseline()
            sys.stdout.write(f"Saved no-VPN network baseline: {identity.ip} ({identity.loc}).\n")
        case NetworkCommand.CHECK:
            identity = assert_network_baseline()
            sys.stdout.write(f"Network preflight passed: {identity.ip} ({identity.loc}).\n")


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


def add_network_commands(*, parser: argparse.ArgumentParser) -> None:
    """Add network preflight subcommands to a parser."""
    commands = parser.add_subparsers(dest="network_command", required=True)
    commands.add_parser(
        NetworkCommand.BASELINE.value,
        help="Save the current public IP as the no-VPN baseline.",
    )
    commands.add_parser(
        NetworkCommand.CHECK.value,
        help="Verify the current public IP matches the no-VPN baseline.",
    )


def add_show_argument(*, parser: argparse.ArgumentParser) -> None:
    """Add the standard show selector to a parser."""
    parser.add_argument("--show", choices=[show.value for show in Show], required=True)


if __name__ == "__main__":
    main()
