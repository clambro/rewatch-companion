"""CLI entrypoint for finding a hero image for a completed article."""

import json
import sys
from io import BytesIO
from pathlib import Path

import httpx
import yaml
from PIL import Image, ImageOps
from pydantic import BaseModel

from common.manifest import episode_slug, load_manifest
from common.schemas import EssayKind, Show
from essay_generation.generate_essay import find_episode, find_slugged_article
from hero_images.agent import find_hero_image_for_article
from hero_images.rules import (
    ASPECT_RATIO_TOLERANCE,
    HERO_IMAGE_HEIGHT,
    HERO_IMAGE_WIDTH,
    TARGET_ASPECT_RATIO,
)
from hero_images.schemas import FoundHeroImage, HeroImageArticle

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTENT_SHOWS_ROOT = REPO_ROOT / "content" / "shows"
ASSET_IMAGE_ROOT = REPO_ROOT / "site" / "src" / "assets" / "images" / "shows"
HERO_IMAGE_FILENAME = "hero.jpg"


class HeroImageCommand(BaseModel):
    """Parsed CLI command for hero image search."""

    show: Show
    kind: EssayKind
    slug: str | None = None
    season: int | None = None
    episode: int | None = None


def find_hero_image(*, command: HeroImageCommand) -> Path:
    """Find, download, and record a hero image for a manifest article reference."""
    article_path = article_path_for_command(command=command)
    article = load_completed_article(article_path=article_path)
    hero_image = find_hero_image_for_article(article=article)
    image_path = download_hero_image(article_path=article_path, hero_image=hero_image)
    update_article_metadata(article_path=article_path, image_path=image_path, hero_image=hero_image)

    sys.stdout.write(f"Wrote {image_path}\n")
    sys.stdout.write(f"Updated {article_path.with_name('article.yaml')}\n")
    sys.stdout.write(f"{json.dumps(hero_image.model_dump(mode='json'), indent=2)}\n")
    return image_path


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
    """Download the selected hero image into the Astro asset image tree."""
    response = httpx.get(hero_image.image_url, follow_redirects=True, timeout=30)
    response.raise_for_status()
    image_path = public_image_path_for_article(article_path=article_path)
    image_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_image_path = image_path.with_name(f".{image_path.stem}.tmp{image_path.suffix}")
    write_jpeg_hero_image(image_path=temporary_image_path, content=response.content)
    try:
        validate_hero_image_aspect_ratio(image_path=temporary_image_path)
    except ValueError:
        temporary_image_path.unlink(missing_ok=True)
        raise

    temporary_image_path.replace(image_path)
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
        "alt": hero_image.alt,
    }
    metadata_path.write_text(yaml.safe_dump(metadata, sort_keys=False), encoding="utf-8")


def public_image_path_for_article(*, article_path: Path) -> Path:
    """Return the local hero image asset path for one article."""
    relative_article_dir = article_path.parent.relative_to(CONTENT_SHOWS_ROOT)
    return ASSET_IMAGE_ROOT / relative_article_dir / HERO_IMAGE_FILENAME


def public_image_src(*, image_path: Path) -> str:
    """Return the stable content image reference for an exported hero image."""
    return f"/images/{image_path.relative_to(ASSET_IMAGE_ROOT.parent).as_posix()}"


def validate_hero_image_aspect_ratio(*, image_path: Path) -> None:
    """Fail loudly when the selected hero image is not close to 16:9."""
    with Image.open(image_path) as image:
        validate_hero_image_dimensions(width=image.width, height=image.height)


def write_jpeg_hero_image(*, image_path: Path, content: bytes) -> None:
    """Convert downloaded image bytes to a fixed-size RGB JPEG file."""
    with Image.open(BytesIO(content)) as image:
        validate_hero_image_dimensions(width=image.width, height=image.height)
        resized_image = ImageOps.fit(
            image.convert("RGB"),
            (HERO_IMAGE_WIDTH, HERO_IMAGE_HEIGHT),
            method=Image.Resampling.LANCZOS,
        )
        resized_image.save(image_path, format="JPEG", quality=88, optimize=True)


def validate_hero_image_dimensions(*, width: int, height: int) -> None:
    """Reject images that cannot produce the fixed hero image output."""
    validate_hero_image_size(width=width, height=height)
    ratio = width / height
    if abs(ratio - TARGET_ASPECT_RATIO) <= ASPECT_RATIO_TOLERANCE:
        return

    raise ValueError(
        f"Hero image must be close to 16:9. Got {width}x{height} ({ratio:.2f}:1).",
    )


def validate_hero_image_size(*, width: int, height: int) -> None:
    """Reject images that are too small for the fixed hero image output."""
    if width >= HERO_IMAGE_WIDTH and height >= HERO_IMAGE_HEIGHT:
        return

    raise ValueError(
        f"Hero image must be at least {HERO_IMAGE_WIDTH}x{HERO_IMAGE_HEIGHT}. "
        f"Got {width}x{height}.",
    )
