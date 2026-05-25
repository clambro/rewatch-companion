"""Tests for missing hero image generation."""

import importlib
from typing import TYPE_CHECKING

from common.manifest import ManifestSluggedArticle, ShowManifest
from common.schemas import Show

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

find_missing_hero_images = importlib.import_module("hero_images.find_missing_hero_images")


def test_missing_hero_image_targets_skip_missing_articles(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Hero image backfill only targets generated articles."""
    manifest = ShowManifest(
        show="succession",
        themes=[
            ManifestSluggedArticle(
                slug="love-as-leverage",
                title="Love as Leverage",
                prompt="Theme prompt.",
            ),
        ],
        characters=[],
        episodes=[],
    )
    monkeypatch.setattr(find_missing_hero_images, "CONTENT_ROOT", tmp_path / "content" / "shows")
    monkeypatch.setattr(find_missing_hero_images, "load_manifest", lambda **_: manifest)

    assert find_missing_hero_images.missing_hero_image_targets(show=Show.SUCCESSION) == []


def test_missing_hero_image_targets_target_articles_without_local_images(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Hero image backfill targets generated articles missing hero metadata."""
    manifest = ShowManifest(
        show="succession",
        themes=[
            ManifestSluggedArticle(
                slug="love-as-leverage",
                title="Love as Leverage",
                prompt="Theme prompt.",
            ),
        ],
        characters=[],
        episodes=[],
    )
    article_dir = tmp_path / "content" / "shows" / "succession" / "themes" / "love-as-leverage"
    article_dir.mkdir(parents=True)
    (article_dir / "index.mdx").write_text("# Love as Leverage\n", encoding="utf-8")
    (article_dir / "article.yaml").write_text(
        "show: succession\n"
        'title: "Love as Leverage"\n'
        'slug: "love-as-leverage"\n'
        "seo:\n"
        '  title: "Love as Leverage"\n'
        '  description: "Description."\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(find_missing_hero_images, "CONTENT_ROOT", tmp_path / "content" / "shows")
    monkeypatch.setattr(find_missing_hero_images, "load_manifest", lambda **_: manifest)

    targets = find_missing_hero_images.missing_hero_image_targets(show=Show.SUCCESSION)

    assert len(targets) == 1
    assert targets[0].kind == find_missing_hero_images.EssayKind.THEMES
    assert targets[0].slug == "love-as-leverage"
