"""CLI entrypoint for finding a hero image for a completed article."""

import argparse
import json
import mimetypes
import sys
from pathlib import Path
from urllib.parse import urlparse

import httpx
import yaml
from pydantic import BaseModel

from generate_essay import find_episode, find_slugged_article
from hero_image_agent import find_hero_image_for_article
from manifest import episode_slug, load_manifest
from schemas import EssayKind, FoundHeroImage, HeroImageArticle, Show

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_SHOWS_ROOT = REPO_ROOT / "content" / "shows"
PUBLIC_IMAGE_ROOT = REPO_ROOT / "site" / "public" / "images" / "shows"
SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


class HeroImageCommand(BaseModel):
    """Parsed CLI command for hero image search."""

    show: Show
    kind: EssayKind
    slug: str | None = None
    season: int | None = None
    episode: int | None = None


def main() -> None:
    """Find a hero image for a completed article."""
    parser = argparse.ArgumentParser(description="Find an online hero image for an article.")
    parser.add_argument("--show", choices=[show.value for show in Show], required=True)
    subparsers = parser.add_subparsers(dest="kind", required=True)

    themes_parser = subparsers.add_parser(EssayKind.THEMES.value)
    themes_parser.add_argument("--slug", required=True)

    characters_parser = subparsers.add_parser(EssayKind.CHARACTERS.value)
    characters_parser.add_argument("--slug", required=True)

    episodes_parser = subparsers.add_parser(EssayKind.EPISODES.value)
    episodes_parser.add_argument("--season", type=int, required=True)
    episodes_parser.add_argument("--episode", type=int, required=True)

    command = HeroImageCommand.model_validate(vars(parser.parse_args()))

    article_path = article_path_for_command(command=command)
    article = load_completed_article(article_path=article_path)
    hero_image = find_hero_image_for_article(article=article)
    image_path = download_hero_image(article_path=article_path, hero_image=hero_image)
    update_article_metadata(article_path=article_path, image_path=image_path, hero_image=hero_image)

    sys.stdout.write(f"Wrote {image_path}\n")
    sys.stdout.write(f"Updated {article_path.with_name('article.yaml')}\n")
    sys.stdout.write(f"{json.dumps(hero_image.model_dump(mode='json'), indent=2)}\n")


def article_path_for_command(*, command: HeroImageCommand) -> Path:
    """Resolve a manifest reference to a completed article path."""
    manifest = load_manifest(show=command.show)
    show_root = CONTENT_SHOWS_ROOT / command.show.value

    match command.kind:
        case EssayKind.THEMES:
            if command.slug is None:
                raise ValueError("Theme hero image search requires --slug.")
            theme = find_slugged_article(entries=manifest.themes, slug=command.slug)
            return show_root / EssayKind.THEMES.value / theme.slug / "index.mdx"
        case EssayKind.CHARACTERS:
            if command.slug is None:
                raise ValueError("Character hero image search requires --slug.")
            character = find_slugged_article(entries=manifest.characters, slug=command.slug)
            return show_root / EssayKind.CHARACTERS.value / character.slug / "index.mdx"
        case EssayKind.EPISODES:
            if command.season is None or command.episode is None:
                raise ValueError("Episode hero image search requires --season and --episode.")
            episode = find_episode(
                entries=manifest.episodes,
                season=command.season,
                episode=command.episode,
            )
            return (
                show_root
                / EssayKind.EPISODES.value
                / f"s{episode.season:02}"
                / episode_slug(episode=episode)
                / "index.mdx"
            )

    raise ValueError(f"Unsupported essay kind: {command.kind.value}")


def load_completed_article(*, article_path: Path) -> HeroImageArticle:
    """Load article metadata and MDX body for image search."""
    if article_path.name != "index.mdx":
        raise ValueError(f"Expected an index.mdx article path: {article_path}")
    try:
        article_path.parent.relative_to(CONTENT_SHOWS_ROOT)
    except ValueError as error:
        raise ValueError(f"Article must live under {CONTENT_SHOWS_ROOT}: {article_path}") from error

    metadata_path = article_path.with_name("article.yaml")
    if not metadata_path.is_file():
        raise ValueError(f"Missing article metadata: {metadata_path}")

    metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
    return HeroImageArticle(
        show=Show(metadata["show"]),
        title=metadata["title"],
        subtitle=metadata["seo"]["description"],
        article_mdx=article_body_without_frontmatter(
            article_path.read_text(encoding="utf-8"),
        ),
    )


def article_body_without_frontmatter(article_mdx: str) -> str:
    """Remove MDX frontmatter before sending article text to the image agent."""
    lines = article_mdx.splitlines()
    if not lines or lines[0] != "---":
        return article_mdx.strip()

    for index, line in enumerate(lines[1:], start=1):
        if line == "---":
            return "\n".join(lines[index + 1 :]).strip()

    return article_mdx.strip()


def download_hero_image(*, article_path: Path, hero_image: FoundHeroImage) -> Path:
    """Download the selected hero image into the static public image tree."""
    response = httpx.get(hero_image.image_url, follow_redirects=True, timeout=30)
    response.raise_for_status()
    image_path = public_image_path_for_article(
        article_path=article_path,
        extension=image_extension(hero_image=hero_image, response=response),
    )
    image_path.parent.mkdir(parents=True, exist_ok=True)
    image_path.write_bytes(response.content)
    return image_path


def update_article_metadata(
    *,
    article_path: Path,
    image_path: Path,
    hero_image: FoundHeroImage,
) -> None:
    """Write selected hero image metadata into article.yaml."""
    metadata_path = article_path.with_name("article.yaml")
    metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
    metadata["hero_image"] = {
        "src": public_image_src(image_path=image_path),
        "image_url": hero_image.image_url,
        "credit": hero_image.credit,
        "title": hero_image.title,
        "rationale": hero_image.rationale,
    }
    metadata_path.write_text(yaml.safe_dump(metadata, sort_keys=False), encoding="utf-8")


def image_extension(*, hero_image: FoundHeroImage, response: httpx.Response) -> str:
    """Return a supported image extension for a downloaded hero image."""
    url_extension = Path(urlparse(hero_image.image_url).path).suffix.lower()
    if url_extension in SUPPORTED_IMAGE_EXTENSIONS:
        return ".jpg" if url_extension == ".jpeg" else url_extension

    content_type = response.headers.get("content-type", "").split(";")[0].strip().lower()
    guessed_extension = mimetypes.guess_extension(content_type)
    if guessed_extension in SUPPORTED_IMAGE_EXTENSIONS:
        return ".jpg" if guessed_extension == ".jpeg" else guessed_extension

    raise ValueError(f"Unsupported hero image content type: {content_type or 'unknown'}")


def public_image_path_for_article(*, article_path: Path, extension: str) -> Path:
    """Return the public hero image path for one article."""
    relative_article_dir = article_path.parent.relative_to(CONTENT_SHOWS_ROOT)
    return PUBLIC_IMAGE_ROOT / relative_article_dir / f"hero{extension}"


def public_image_src(*, image_path: Path) -> str:
    """Return the site-public URL for an exported hero image."""
    return f"/images/{image_path.relative_to(PUBLIC_IMAGE_ROOT.parent).as_posix()}"


if __name__ == "__main__":
    main()
