"""Tests for show generation manifests."""

from pathlib import Path

from manifest import content_paths, load_manifest, manifest_content_paths
from schemas import Show

CONTENT_ROOT = Path(__file__).resolve().parents[3] / "content"


def test_succession_manifest_matches_content_tree() -> None:
    """Manifest targets should match the committed content tree."""
    manifest = load_manifest(show=Show.SUCCESSION)

    assert content_paths(show=Show.SUCCESSION, content_root=CONTENT_ROOT) == manifest_content_paths(
        manifest=manifest,
    )
