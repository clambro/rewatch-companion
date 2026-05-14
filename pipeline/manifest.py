"""Manifest loading for essay generation."""

import re
from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from pydantic import BaseModel

if TYPE_CHECKING:
    from schemas import Show

MANIFEST_ROOT = Path(__file__).resolve().parent / "manifests"


class ManifestArticle(BaseModel):
    """A manifest entry for one generated article."""

    title: str
    prompt: str


class ManifestSluggedArticle(ManifestArticle):
    """A manifest entry for one slugged generated article."""

    slug: str


class ManifestEpisode(BaseModel):
    """A manifest entry for one episode."""

    season: int
    episode: int
    title: str


class ShowManifest(BaseModel):
    """Generation manifest for one show."""

    show: str
    themes: list[ManifestSluggedArticle]
    characters: list[ManifestSluggedArticle]
    episodes: list[ManifestEpisode]


def load_manifest(*, show: Show) -> ShowManifest:
    """Load the manifest for a show."""
    path = MANIFEST_ROOT / f"{show.value}.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    manifest = ShowManifest.model_validate(data)
    if manifest.show != show.value:
        raise ValueError(f"Manifest {path} declares show {manifest.show}, expected {show.value}.")

    return manifest


def manifest_content_paths(*, manifest: ShowManifest) -> set[str]:
    """Return content paths expected for a manifest."""
    paths: set[str] = set()

    for theme in manifest.themes:
        paths.add(f"themes/{theme.slug}")

    for character in manifest.characters:
        paths.add(f"characters/{character.slug}")

    for episode in manifest.episodes:
        paths.add(f"episodes/s{episode.season:02}/{episode_slug(episode=episode)}")

    return paths


def manifest_episode_titles(*, manifest: ShowManifest) -> dict[str, str]:
    """Return episode titles expected for a manifest."""
    return {
        f"episodes/s{episode.season:02}/{episode_slug(episode=episode)}": episode.title
        for episode in manifest.episodes
    }


def content_paths(*, show: Show, content_root: Path) -> set[str]:
    """Return content paths present for a show."""
    show_root = content_root / "shows" / show.value
    paths: set[str] = set()

    paths.update(slugged_article_paths(show_root=show_root, section="themes"))
    paths.update(slugged_article_paths(show_root=show_root, section="characters"))
    paths.update(episode_paths(show_root=show_root))
    return paths


def content_episode_titles(*, show: Show, content_root: Path) -> dict[str, str]:
    """Return episode titles present for a show."""
    show_root = content_root / "shows" / show.value
    episodes_root = show_root / "episodes"
    if not episodes_root.exists():
        return {}

    titles: dict[str, str] = {}
    for path in episodes_root.glob("s*/e*/article.yaml"):
        episode = yaml.safe_load(path.read_text(encoding="utf-8"))
        key = path.parent.relative_to(show_root).as_posix()
        titles[key] = episode["title"]

    return titles


def slugged_article_paths(*, show_root: Path, section: str) -> set[str]:
    """Return slugged article paths for a content section."""
    section_root = show_root / section
    if not section_root.exists():
        return set()

    return {f"{section}/{path.parent.name}" for path in section_root.glob("*/index.mdx")}


def episode_paths(*, show_root: Path) -> set[str]:
    """Return episode article paths."""
    episodes_root = show_root / "episodes"
    if not episodes_root.exists():
        return set()

    paths: set[str] = set()
    for path in episodes_root.glob("s*/e*/article.yaml"):
        paths.add(path.parent.relative_to(show_root).as_posix())

    return paths


def episode_slug(*, episode: ManifestEpisode) -> str:
    """Build the content slug for an episode."""
    title_slug = re.sub(r"[^a-z0-9]+", "-", episode.title.lower().replace("&", "and")).strip("-")
    return f"e{episode.episode:02}-{title_slug}"
