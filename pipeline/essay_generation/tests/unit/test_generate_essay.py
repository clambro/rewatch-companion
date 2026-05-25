"""Tests for essay export helpers."""

from typing import TYPE_CHECKING

import yaml

from essay_generation import generate_essay
from essay_generation.schemas import EssayTarget, GeneratedEssay
from schemas import EssayKind, Show

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
