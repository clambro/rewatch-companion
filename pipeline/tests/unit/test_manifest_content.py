"""Tests for show generation manifests."""

from pathlib import Path

from common.manifest import (
    content_episode_titles,
    content_paths,
    load_manifest,
    manifest_content_paths,
    manifest_episode_titles,
)
from schemas import Show

CONTENT_ROOT = Path(__file__).resolve().parents[3] / "content"


def test_succession_manifest_matches_content_tree() -> None:
    """Manifest targets should match the committed content tree."""
    manifest = load_manifest(show=Show.SUCCESSION)

    assert content_paths(show=Show.SUCCESSION, content_root=CONTENT_ROOT) == manifest_content_paths(
        manifest=manifest,
    )


def test_succession_manifest_episode_titles_match_content() -> None:
    """Manifest episode titles should match committed episode metadata."""
    manifest = load_manifest(show=Show.SUCCESSION)

    assert content_episode_titles(
        show=Show.SUCCESSION,
        content_root=CONTENT_ROOT,
    ) == manifest_episode_titles(manifest=manifest)
