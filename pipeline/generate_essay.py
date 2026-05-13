"""Shared helpers for essay generation."""

import json
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from schemas import EssayKind, EssaySource, EssayTarget, GeneratedEssay, Show

if TYPE_CHECKING:
    from manifest import ManifestEpisode, ManifestSluggedArticle

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_ROOT = REPO_ROOT / "content" / "shows"


def write_article(*, target: EssayTarget, draft: GeneratedEssay) -> None:
    """Write a generated article to content."""
    output_dir = output_path(target=target)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "index.mdx").write_text(
        render_draft(target=target, draft=draft),
        encoding="utf-8",
    )

    match target.kind:
        case EssayKind.EPISODES:
            metadata_file = "episode.yaml"
            metadata = render_episode_metadata(target=target, draft=draft)
        case _:
            metadata_file = "article.yaml"
            metadata = render_article_metadata(target=target, draft=draft)

    (output_dir / metadata_file).write_text(metadata, encoding="utf-8")
    sys.stdout.write(f"Wrote {output_dir / 'index.mdx'}\n")


def load_article_sources(*, show: Show, sections: list[EssayKind]) -> list[EssaySource]:
    """Load committed article essays as context sources."""
    show_root = CONTENT_ROOT / show.value
    sources = []
    for section in sections:
        match section:
            case EssayKind.ABOUT:
                path = show_root / EssayKind.ABOUT.value / "index.mdx"
                if path.is_file():
                    sources.append(load_article_source(path=path))
            case EssayKind.THEMES | EssayKind.CHARACTERS:
                section_root = show_root / section.value
                sources.extend(
                    load_article_source(path=path)
                    for path in sorted(section_root.glob("*/index.mdx"))
                    if path.is_file()
                )
            case EssayKind.EPISODES:
                raise ValueError("Episode essays are not supported as generation sources yet.")

    return sources


def output_path(*, target: EssayTarget) -> Path:
    """Return the content output path for a generated essay."""
    match target.kind:
        case EssayKind.ABOUT:
            return CONTENT_ROOT / target.show.value / EssayKind.ABOUT.value
        case EssayKind.THEMES:
            if target.slug is None:
                raise ValueError("Theme generation requires a slug.")
            return CONTENT_ROOT / target.show.value / EssayKind.THEMES.value / target.slug
        case EssayKind.CHARACTERS:
            if target.slug is None:
                raise ValueError("Character generation requires a slug.")
            return CONTENT_ROOT / target.show.value / EssayKind.CHARACTERS.value / target.slug
        case EssayKind.EPISODES:
            if target.slug is None or target.season is None:
                raise ValueError("Episode generation requires a season and slug.")
            return (
                CONTENT_ROOT
                / target.show.value
                / EssayKind.EPISODES.value
                / f"s{target.season:02}"
                / target.slug
            )

    raise ValueError(f"Unsupported essay kind: {target.kind.value}")


def find_slugged_article(
    *,
    entries: list[ManifestSluggedArticle],
    slug: str,
) -> ManifestSluggedArticle:
    """Find a slugged manifest article."""
    for entry in entries:
        if entry.slug == slug:
            return entry

    available_slugs = ", ".join(entry.slug for entry in entries)
    raise ValueError(f"Unknown article slug: {slug}. Available slugs: {available_slugs}")


def find_episode(
    *,
    entries: list[ManifestEpisode],
    season: int,
    episode: int,
) -> ManifestEpisode:
    """Find an episode manifest entry."""
    for entry in entries:
        if entry.season == season and entry.episode == episode:
            return entry

    available_episodes = ", ".join(f"S{entry.season:02}E{entry.episode:02}" for entry in entries)
    raise ValueError(
        f"Unknown episode: S{season:02}E{episode:02}. Available episodes: {available_episodes}",
    )


def episode_slug(*, episode: ManifestEpisode) -> str:
    """Build the content slug for an episode."""
    title_slug = re.sub(r"[^a-z0-9]+", "-", episode.title.lower().replace("&", "and")).strip("-")
    return f"e{episode.episode:02}-{title_slug}"


def load_article_source(*, path: Path) -> EssaySource:
    """Load one committed article essay as source context."""
    metadata = yaml.safe_load(path.with_name("article.yaml").read_text(encoding="utf-8"))
    return EssaySource(
        title=metadata["title"],
        subtitle=metadata["seo"]["description"],
        body_mdx=path.read_text(encoding="utf-8").strip(),
    )


def render_draft(*, target: EssayTarget, draft: GeneratedEssay) -> str:
    """Render the generated draft as a simple MDX document."""
    return (
        "---\n"
        f"title: {json.dumps(target.title)}\n"
        f"dek: {json.dumps(draft.subtitle)}\n"
        "---\n\n"
        f"{draft.body_mdx.rstrip()}\n"
    )


def render_article_metadata(*, target: EssayTarget, draft: GeneratedEssay) -> str:
    """Render article metadata for the static site content collection."""
    slug = f"slug: {json.dumps(target.slug)}\n" if target.slug is not None else ""
    return (
        f"show: {target.show.value}\n"
        f"title: {json.dumps(target.title)}\n"
        f"{slug}"
        "\n"
        "seo:\n"
        f"  title: {json.dumps(target.title)}\n"
        f"  description: {json.dumps(draft.subtitle)}\n"
    )


def render_episode_metadata(*, target: EssayTarget, draft: GeneratedEssay) -> str:
    """Render episode metadata for the static site content collection."""
    if target.season is None or target.episode is None or target.slug is None:
        raise ValueError("Episode metadata requires season, episode, and slug.")

    code = f"S{target.season:02}E{target.episode:02}"
    return (
        f"show: {target.show.value}\n"
        f"season: {target.season}\n"
        f"episode: {target.episode}\n"
        f"code: {json.dumps(code)}\n"
        f"title: {json.dumps(target.title)}\n"
        f"slug: {json.dumps(target.slug)}\n"
        "\n"
        "seo:\n"
        f"  title: {json.dumps(target.title)}\n"
        f"  description: {json.dumps(draft.subtitle)}\n"
    )
