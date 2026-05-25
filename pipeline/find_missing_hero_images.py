"""Find hero images for generated manifest essays missing local image metadata."""

import argparse
import sys
from pathlib import Path

import yaml
from pydantic import BaseModel

from find_hero_image import HeroImageCommand, find_hero_image
from generate_essay import CONTENT_ROOT
from manifest import episode_slug, load_manifest
from schemas import EssayKind, Show

REPO_ROOT = Path(__file__).resolve().parent.parent
SITE_PUBLIC_ROOT = REPO_ROOT / "site" / "public"


class FindMissingHeroImagesCommand(BaseModel):
    """Parsed CLI command for missing hero image search."""

    show: Show
    dry_run: bool = False


def main() -> None:
    """Find hero images for generated articles that do not have them yet."""
    parser = argparse.ArgumentParser(description="Find missing hero images.")
    parser.add_argument("--show", choices=[show.value for show in Show], required=True)
    parser.add_argument("--dry-run", action="store_true")
    command = FindMissingHeroImagesCommand.model_validate(vars(parser.parse_args()))

    missing_images = missing_hero_image_targets(show=command.show)
    if not missing_images:
        sys.stdout.write("No missing hero images.\n")
        return

    for missing_image in missing_images:
        sys.stdout.write(f"Running: {render_hero_image_command(command=missing_image)}\n")
        if not command.dry_run:
            find_hero_image(command=missing_image)


def missing_hero_image_targets(*, show: Show) -> list[HeroImageCommand]:
    """Return generated manifest articles missing hero images."""
    manifest = load_manifest(show=show)
    show_root = CONTENT_ROOT / show.value
    targets: list[HeroImageCommand] = []

    for theme in manifest.themes:
        article_dir = show_root / EssayKind.THEMES.value / theme.slug
        if is_missing_article(article_dir=article_dir):
            sys.stdout.write(f"Skipping missing article: {article_dir}\n")
        elif is_missing_hero_image(article_dir=article_dir):
            targets.append(HeroImageCommand(show=show, kind=EssayKind.THEMES, slug=theme.slug))

    for character in manifest.characters:
        article_dir = show_root / EssayKind.CHARACTERS.value / character.slug
        if is_missing_article(article_dir=article_dir):
            sys.stdout.write(f"Skipping missing article: {article_dir}\n")
        elif is_missing_hero_image(article_dir=article_dir):
            targets.append(
                HeroImageCommand(show=show, kind=EssayKind.CHARACTERS, slug=character.slug),
            )

    for episode in manifest.episodes:
        article_dir = (
            show_root
            / EssayKind.EPISODES.value
            / f"s{episode.season:02}"
            / episode_slug(episode=episode)
        )
        if is_missing_article(article_dir=article_dir):
            sys.stdout.write(f"Skipping missing article: {article_dir}\n")
        elif is_missing_hero_image(article_dir=article_dir):
            targets.append(
                HeroImageCommand(
                    show=show,
                    kind=EssayKind.EPISODES,
                    season=episode.season,
                    episode=episode.episode,
                ),
            )

    return targets


def render_hero_image_command(*, command: HeroImageCommand) -> str:
    """Return the equivalent single-target hero image command."""
    match command.kind:
        case EssayKind.THEMES | EssayKind.CHARACTERS:
            return (
                f"uv run python find_hero_image.py --show {command.show.value} "
                f"{command.kind.value} --slug {command.slug}"
            )
        case EssayKind.EPISODES:
            return (
                f"uv run python find_hero_image.py --show {command.show.value} "
                f"{command.kind.value} --season {command.season} --episode {command.episode}"
            )


def is_missing_article(*, article_dir: Path) -> bool:
    """Return whether the article files needed for image search are missing."""
    return not (article_dir / "index.mdx").is_file() or not (article_dir / "article.yaml").is_file()


def is_missing_hero_image(*, article_dir: Path) -> bool:
    """Return whether an article has incomplete local hero image metadata."""
    metadata = yaml.safe_load((article_dir / "article.yaml").read_text(encoding="utf-8"))
    hero_image = metadata.get("hero_image")
    if not isinstance(hero_image, dict):
        return True

    src = hero_image.get("src")
    alt = hero_image.get("alt")
    if not isinstance(src, str) or not src.startswith("/"):
        return True
    if not isinstance(alt, str) or not alt.strip():
        return True

    return not local_public_path(src=src).is_file()


def local_public_path(*, src: str) -> Path:
    """Return the local public file path for a site-root image src."""
    return SITE_PUBLIC_ROOT / src.removeprefix("/")


if __name__ == "__main__":
    main()
