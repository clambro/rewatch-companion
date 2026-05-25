"""Tests for manifest backfill scripts."""

from typing import TYPE_CHECKING

import find_missing_hero_images
import generate_missing_essays
from common.manifest import ManifestEpisode, ManifestSluggedArticle, ShowManifest
from schemas import Show

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


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
