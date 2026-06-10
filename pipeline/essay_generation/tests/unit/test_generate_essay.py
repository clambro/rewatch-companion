"""Tests for essay export helpers."""

from typing import TYPE_CHECKING

import yaml

from common.manifest import ManifestEpisode, ManifestSluggedArticle, ShowManifest
from common.schemas import EssayKind, Show
from essay_generation import generate_essay
from essay_generation.schemas import EssayTarget, GeneratedEssay

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def test_write_article_preserves_existing_metadata_except_dek(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regenerating an article should not delete existing hero image metadata."""
    content_root = tmp_path / "content" / "shows"
    article_dir = content_root / "succession" / "characters" / "kendall-roy"
    article_dir.mkdir(parents=True)
    (article_dir / "article.yaml").write_text(
        "show: succession\n"
        "title: Kendall Roy\n"
        "slug: kendall-roy\n"
        "seo:\n"
        "  title: Kendall Roy\n"
        "  description: Old dek.\n"
        "hero_image:\n"
        "  src: /images/shows/succession/characters/kendall-roy/hero.jpg\n"
        "  alt: Jeremy Strong as Kendall Roy in Succession\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(generate_essay, "CONTENT_ROOT", content_root)
    monkeypatch.setattr(generate_essay, "summarize_essay", lambda **_: "Summary.")
    monkeypatch.setattr(generate_essay, "rebuild_show_index", lambda **_: None)

    generate_essay.write_article(
        target=EssayTarget(
            show=Show.SUCCESSION,
            kind=EssayKind.CHARACTERS,
            title="Kendall Roy",
            prompt="Prompt.",
            slug="kendall-roy",
        ),
        draft=GeneratedEssay(
            subtitle="New dek.",
            body_mdx="Generated body.",
        ),
    )

    metadata = yaml.safe_load((article_dir / "article.yaml").read_text(encoding="utf-8"))
    assert metadata == {
        "show": "succession",
        "title": "Kendall Roy",
        "slug": "kendall-roy",
        "seo": {
            "title": "Kendall Roy",
            "description": "New dek.",
        },
        "hero_image": {
            "src": "/images/shows/succession/characters/kendall-roy/hero.jpg",
            "alt": "Jeremy Strong as Kendall Roy in Succession",
        },
    }


def test_rebuild_show_index_orders_articles_by_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Show index article lists should follow manifest order."""
    content_root = tmp_path / "content" / "shows"
    show_root = content_root / "succession"
    show_root.mkdir(parents=True)
    (show_root / "show.yaml").write_text(
        'title: "Succession"\n'
        'slug: "succession"\n'
        "hero_image:\n"
        "  src: /images/shows/succession/hero.jpg\n"
        "  alt: Succession cast seated around a dining table.\n",
        encoding="utf-8",
    )

    for slug, title in [
        ("kendall-roy", "Kendall Roy"),
        ("logan-roy", "Logan Roy"),
        ("shiv-roy", "Shiv Roy"),
    ]:
        article_dir = show_root / "characters" / slug
        article_dir.mkdir(parents=True)
        (article_dir / "index.mdx").write_text("Essay.\n", encoding="utf-8")
        (article_dir / "article.yaml").write_text(
            f"show: succession\ntitle: {title}\nslug: {slug}\n",
            encoding="utf-8",
        )

    manifest = ShowManifest(
        show="succession",
        themes=[],
        characters=[
            ManifestSluggedArticle(
                slug="logan-roy",
                title="Logan Roy",
            ),
            ManifestSluggedArticle(
                slug="kendall-roy",
                title="Kendall Roy",
            ),
            ManifestSluggedArticle(
                slug="shiv-roy",
                title="Shiv Roy",
            ),
        ],
        episodes=[ManifestEpisode(season=1, episode=1, title="Celebration")],
    )
    monkeypatch.setattr(generate_essay, "CONTENT_ROOT", content_root)
    monkeypatch.setattr(generate_essay, "load_manifest", lambda **_: manifest)

    generate_essay.rebuild_show_index(show=Show.SUCCESSION)

    show_index = yaml.safe_load((show_root / "show.yaml").read_text(encoding="utf-8"))
    assert show_index["hero_image"] == {
        "src": "/images/shows/succession/hero.jpg",
        "alt": "Succession cast seated around a dining table.",
    }
    assert [character["path"] for character in show_index["characters"]] == [
        "characters/logan-roy",
        "characters/kendall-roy",
        "characters/shiv-roy",
    ]
