"""Unit tests for hero image search helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import find_hero_image
from find_hero_image import (
    HeroImageCommand,
    article_body_without_frontmatter,
    article_path_for_command,
    image_extension,
    load_completed_article,
    public_image_path_for_article,
    public_image_src,
    update_article_metadata,
)
from hero_image_agent import image_search_result_from_ddgs_result
from manifest import ManifestEpisode, ShowManifest
from schemas import EssayKind, FoundHeroImage, Show

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

EXPECTED_WIDTH = 1200
EXPECTED_HEIGHT = 675


def test_load_completed_article_reads_metadata_and_body(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Completed article loading uses sibling metadata and strips frontmatter."""
    show_root = tmp_path / "content" / "shows"
    article_dir = show_root / "succession" / "themes" / "love-as-leverage"
    article_dir.mkdir(parents=True)
    (article_dir / "article.yaml").write_text(
        "show: succession\n"
        'title: "Love as Leverage"\n'
        'slug: "love-as-leverage"\n'
        "seo:\n"
        '  description: "Love becomes leverage."',
        encoding="utf-8",
    )
    (article_dir / "index.mdx").write_text(
        '---\ntitle: "Love as Leverage"\n---\n\nArticle body.',
        encoding="utf-8",
    )
    monkeypatch.setattr(find_hero_image, "CONTENT_SHOWS_ROOT", show_root)

    article = load_completed_article(article_path=article_dir / "index.mdx")

    assert article.show == Show.SUCCESSION
    assert article.title == "Love as Leverage"
    assert article.subtitle == "Love becomes leverage."
    assert article.article_mdx == "Article body."


def test_article_path_for_episode_command_uses_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Hero image search resolves episode content paths from the manifest."""
    manifest = ShowManifest(
        show="succession",
        themes=[],
        characters=[],
        episodes=[
            ManifestEpisode(
                season=2,
                episode=2,
                title="Vaulter",
            ),
        ],
    )
    monkeypatch.setattr(find_hero_image, "CONTENT_SHOWS_ROOT", tmp_path / "content" / "shows")
    monkeypatch.setattr(find_hero_image, "load_manifest", lambda **_: manifest)

    article_path = article_path_for_command(
        command=HeroImageCommand(
            show=Show.SUCCESSION,
            kind=EssayKind.EPISODES,
            season=2,
            episode=2,
        ),
    )

    assert article_path == (
        tmp_path
        / "content"
        / "shows"
        / "succession"
        / "episodes"
        / "s02"
        / "e02-vaulter"
        / "index.mdx"
    )


def test_article_body_without_frontmatter_keeps_body_only() -> None:
    """Frontmatter is removed before article text goes to the agent."""
    article = "---\ntitle: Example\n---\n\n# Heading\n\nBody."

    assert article_body_without_frontmatter(article) == "# Heading\n\nBody."


def test_image_search_result_from_ddgs_result_normalizes_known_fields() -> None:
    """DDGS image results are reduced to the fields the agent needs."""
    result = image_search_result_from_ddgs_result(
        result={
            "title": "Succession Vaulter",
            "image": "https://example.com/image.jpg",
            "url": "https://example.com/article",
            "thumbnail": "https://example.com/thumb.jpg",
            "source": "Example",
            "width": str(EXPECTED_WIDTH),
            "height": str(EXPECTED_HEIGHT),
        },
    )

    assert result.title == "Succession Vaulter"
    assert result.image_url == "https://example.com/image.jpg"
    assert result.source_page_url == "https://example.com/article"
    assert result.width == EXPECTED_WIDTH
    assert result.height == EXPECTED_HEIGHT


def test_update_article_metadata_writes_hero_image_block(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Hero image selection is recorded in article metadata."""
    content_root = tmp_path / "content" / "shows"
    public_root = tmp_path / "site" / "public" / "images" / "shows"
    monkeypatch.setattr(find_hero_image, "CONTENT_SHOWS_ROOT", content_root)
    monkeypatch.setattr(find_hero_image, "PUBLIC_IMAGE_ROOT", public_root)
    article_dir = content_root / "succession" / "episodes" / "s02" / "e02-vaulter"
    article_dir.mkdir(parents=True)
    article_path = article_dir / "index.mdx"
    image_path = public_root / "succession" / "episodes" / "s02" / "e02-vaulter" / "hero.jpg"
    (article_dir / "article.yaml").write_text(
        "show: succession\n"
        'title: "Vaulter"\n'
        'slug: "e02-vaulter"\n'
        "seo:\n"
        '  title: "Vaulter"\n'
        '  description: "Description."\n',
        encoding="utf-8",
    )

    update_article_metadata(
        article_path=article_path,
        image_path=image_path,
        hero_image=FoundHeroImage(
            image_url="https://example.com/image.jpg",
            source_page_url="https://example.com/article",
            title="Succession Vaulter",
            credit="HBO",
            rationale="Matches the article.",
        ),
    )

    metadata = find_hero_image.yaml.safe_load(
        (article_dir / "article.yaml").read_text(encoding="utf-8"),
    )

    assert metadata["hero_image"] == {
        "src": "/images/shows/succession/episodes/s02/e02-vaulter/hero.jpg",
        "image_url": "https://example.com/image.jpg",
        "credit": "HBO",
        "title": "Succession Vaulter",
        "rationale": "Matches the article.",
    }


def test_image_extension_prefers_supported_url_extension() -> None:
    """URL extensions are used before response content type."""
    response = find_hero_image.httpx.Response(
        200,
        headers={"content-type": "image/png"},
    )

    extension = image_extension(
        hero_image=FoundHeroImage(
            image_url="https://example.com/image.jpeg?width=1200",
            source_page_url="https://example.com/article",
            title="Image",
            credit="HBO",
            rationale="Good image.",
        ),
        response=response,
    )

    assert extension == ".jpg"


def test_public_image_path_and_src_use_article_content_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Hero images export to site/public using the content article path."""
    content_root = tmp_path / "content" / "shows"
    public_root = tmp_path / "site" / "public" / "images" / "shows"
    article_path = content_root / "succession" / "episodes" / "s02" / "e02-vaulter" / "index.mdx"
    monkeypatch.setattr(find_hero_image, "CONTENT_SHOWS_ROOT", content_root)
    monkeypatch.setattr(find_hero_image, "PUBLIC_IMAGE_ROOT", public_root)

    image_path = public_image_path_for_article(article_path=article_path, extension=".jpg")

    assert (
        image_path == public_root / "succession" / "episodes" / "s02" / "e02-vaulter" / "hero.jpg"
    )
    assert public_image_src(image_path=image_path) == (
        "/images/shows/succession/episodes/s02/e02-vaulter/hero.jpg"
    )
