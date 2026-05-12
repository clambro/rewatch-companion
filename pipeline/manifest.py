"""Manifest loading for essay generation."""

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


class ManifestSeason(BaseModel):
    """A manifest entry for one season."""

    season: int
    episodes: int


class ShowManifest(BaseModel):
    """Generation manifest for one show."""

    show: str
    about: ManifestArticle
    themes: list[ManifestSluggedArticle]
    characters: list[ManifestSluggedArticle]
    seasons: list[ManifestSeason]


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
    paths = {"about"}

    for theme in manifest.themes:
        paths.add(f"themes/{theme.slug}")

    for character in manifest.characters:
        paths.add(f"characters/{character.slug}")

    for season in manifest.seasons:
        for episode in range(1, season.episodes + 1):
            paths.add(f"episodes/s{season.season:02}/e{episode:02}")

    return paths


def content_paths(*, show: Show, content_root: Path) -> set[str]:
    """Return content paths present for a show."""
    show_root = content_root / "shows" / show.value
    paths: set[str] = set()

    if (show_root / "about" / "index.mdx").exists():
        paths.add("about")

    paths.update(slugged_article_paths(show_root=show_root, section="themes"))
    paths.update(slugged_article_paths(show_root=show_root, section="characters"))
    paths.update(episode_paths(show_root=show_root))
    return paths


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
    for path in episodes_root.glob("s*/e*/episode.yaml"):
        episode = yaml.safe_load(path.read_text(encoding="utf-8"))
        paths.add(f"episodes/s{episode['season']:02}/e{episode['episode']:02}")

    return paths
