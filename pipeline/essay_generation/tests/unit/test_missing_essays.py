"""Tests for missing essay generation."""

import importlib
from typing import TYPE_CHECKING

from common.manifest import ManifestEpisode, ManifestSluggedArticle, ShowManifest
from common.schemas import Show

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

generate_missing_essays = importlib.import_module("essay_generation.generate_missing_essays")


def test_missing_manifest_essays_follow_manifest_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing essay generation runs themes, characters, then episodes."""
    manifest = ShowManifest(
        show="succession",
        themes=[
            ManifestSluggedArticle(
                slug="love-as-leverage",
                title="Love as Leverage",
                prompt="Theme prompt.",
            ),
        ],
        characters=[
            ManifestSluggedArticle(
                slug="kendall-roy",
                title="Kendall Roy",
                prompt="Character prompt.",
            ),
        ],
        episodes=[
            ManifestEpisode(season=1, episode=1, title="Celebration"),
        ],
    )
    monkeypatch.setattr(generate_missing_essays, "CONTENT_ROOT", tmp_path / "content" / "shows")
    monkeypatch.setattr(generate_missing_essays, "load_manifest", lambda **_: manifest)

    essays = generate_missing_essays.missing_manifest_essays(show=Show.SUCCESSION)

    assert [essay.kind for essay in essays] == [
        generate_missing_essays.EssayKind.THEMES,
        generate_missing_essays.EssayKind.CHARACTERS,
        generate_missing_essays.EssayKind.EPISODES,
    ]
