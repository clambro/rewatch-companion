"""Unit tests for hero image search helpers."""

from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, cast

import pytest
from ddgs.exceptions import DDGSException
from PIL import Image

from common.manifest import ManifestEpisode, ShowManifest
from common.schemas import EssayKind, Show
from hero_images import find_hero_image
from hero_images import prompt as hero_image_prompt
from hero_images.agent import (
    add_hero_image_candidate,
    image_search_result_from_ddgs_result,
    infer_image_media_type,
    search_show_images,
    selected_hero_image_from_selection,
)
from hero_images.find_hero_image import (
    HeroImageCommand,
    article_body_without_frontmatter,
    article_path_for_command,
    download_hero_image,
    load_completed_article,
    public_image_path_for_article,
    public_image_src,
    update_article_metadata,
    validate_hero_image_size,
    write_jpeg_hero_image,
)
from hero_images.schemas import (
    FoundHeroImage,
    HeroImageArticle,
    HeroImageSelection,
    HeroImageWorkspace,
)

if TYPE_CHECKING:
    from pathlib import Path

    from pydantic_ai import RunContext

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

    assert result is not None
    assert result.title == "Succession Vaulter"
    assert result.image_url == "https://example.com/image.jpg"
    assert result.image.url == "https://example.com/image.jpg"
    assert result.image.media_type == "image/jpeg"
    assert result.source_page_url == "https://example.com/article"
    assert result.width == EXPECTED_WIDTH
    assert result.height == EXPECTED_HEIGHT


def test_infer_image_media_type_uses_url_path() -> None:
    """Known image extensions are inferred without fetching."""
    assert (
        infer_image_media_type(image_url="https://example.com/image.webp?width=1200")
        == "image/webp"
    )


def test_infer_image_media_type_uses_content_type_for_extensionless_urls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Extensionless CDN URLs are inferred from response content type."""

    class StubResponse:
        def __init__(self) -> None:
            self.headers = {"content-type": "image/png; charset=utf-8"}

        def raise_for_status(self) -> None:
            return None

    def stub_head(*_args: object, **_kwargs: object) -> StubResponse:
        return StubResponse()

    monkeypatch.setattr("hero_images.agent.httpx.head", stub_head)

    assert infer_image_media_type(image_url="https://example.com/image?id=123") == "image/png"


def test_image_search_result_from_ddgs_result_rejects_small_images() -> None:
    """Image search results below the hero size are filtered out."""
    result = image_search_result_from_ddgs_result(
        result={
            "title": "Small Succession Image",
            "image": "https://example.com/small.jpg",
            "url": "https://example.com/article",
            "width": "800",
            "height": "450",
        },
    )

    assert result is None


def test_image_search_result_from_ddgs_result_rejects_wrong_shape() -> None:
    """Image search results far from 16:9 are filtered out."""
    result = image_search_result_from_ddgs_result(
        result={
            "title": "Tall Succession Image",
            "image": "https://example.com/tall.jpg",
            "url": "https://example.com/article",
            "width": "1200",
            "height": "1200",
        },
    )

    assert result is None


def test_search_show_images_returns_top_five_valid_images(monkeypatch: pytest.MonkeyPatch) -> None:
    """The search tool should expose only the first five large 16:9-ish image results."""
    workspace = HeroImageWorkspace(
        article=HeroImageArticle(
            show=Show.SUCCESSION,
            title="Shiv Roy",
            subtitle="Dek.",
            article_mdx="Article.",
        ),
    )
    ctx = cast("RunContext[HeroImageWorkspace]", SimpleNamespace(deps=workspace))

    class StubDDGS:
        def images(self, **_kwargs: object) -> list[dict[str, object]]:
            return [
                {
                    "title": f"Image {index}",
                    "image": f"https://example.com/image-{index}.jpg",
                    "url": "https://example.com/article",
                    "width": str(EXPECTED_WIDTH),
                    "height": str(EXPECTED_HEIGHT),
                }
                for index in range(7)
            ]

    monkeypatch.setattr("hero_images.agent.DDGS", StubDDGS)

    result = search_show_images(ctx=ctx, query="Shiv Roy Succession")

    assert isinstance(result, list)
    assert [image.image_url for image in result] == [
        "https://example.com/image-0.jpg",
        "https://example.com/image-1.jpg",
        "https://example.com/image-2.jpg",
        "https://example.com/image-3.jpg",
        "https://example.com/image-4.jpg",
    ]


def test_search_show_images_returns_message_when_search_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Image search failures should not crash the agent loop."""
    workspace = HeroImageWorkspace(
        article=HeroImageArticle(
            show=Show.SUCCESSION,
            title="Shiv Roy",
            subtitle="Dek.",
            article_mdx="Article.",
        ),
    )
    ctx = cast("RunContext[HeroImageWorkspace]", SimpleNamespace(deps=workspace))

    class FailingDDGS:
        def images(self, **_kwargs: object) -> list[dict[str, object]]:
            raise DDGSException("No results found.")

    monkeypatch.setattr("hero_images.agent.DDGS", FailingDDGS)

    result = search_show_images(ctx=ctx, query="Shiv Roy Succession")

    assert result == "No image search results found for query: Shiv Roy Succession"


def test_update_article_metadata_writes_hero_image_block(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Hero image selection is recorded in article metadata."""
    content_root = tmp_path / "content" / "shows"
    asset_root = tmp_path / "site" / "src" / "assets" / "images" / "shows"
    monkeypatch.setattr(find_hero_image, "CONTENT_SHOWS_ROOT", content_root)
    monkeypatch.setattr(find_hero_image, "ASSET_IMAGE_ROOT", asset_root)
    article_dir = content_root / "succession" / "episodes" / "s02" / "e02-vaulter"
    article_dir.mkdir(parents=True)
    article_path = article_dir / "index.mdx"
    image_path = asset_root / "succession" / "episodes" / "s02" / "e02-vaulter" / "hero.jpg"
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
            alt="Roman Roy standing in the Vaulter office.",
        ),
    )

    metadata = find_hero_image.yaml.safe_load(
        (article_dir / "article.yaml").read_text(encoding="utf-8"),
    )

    assert metadata["hero_image"] == {
        "src": "/images/shows/succession/episodes/s02/e02-vaulter/hero.jpg",
        "alt": "Roman Roy standing in the Vaulter office.",
    }


def test_add_hero_image_candidate_collects_candidate(monkeypatch: pytest.MonkeyPatch) -> None:
    """The agent should collect candidates before separate final selection."""
    workspace = HeroImageWorkspace(
        article=HeroImageArticle(
            show=Show.SUCCESSION,
            title="Shiv Roy",
            subtitle="Dek.",
            article_mdx="Article.",
        ),
    )
    ctx = cast("RunContext[HeroImageWorkspace]", SimpleNamespace(deps=workspace))
    image = FoundHeroImage(
        image_url="https://example.com/image.jpg",
        source_page_url="https://example.com/article",
        alt="Shiv Roy.",
        width=EXPECTED_WIDTH,
        height=EXPECTED_HEIGHT,
    )
    monkeypatch.setattr(
        "hero_images.agent.selection_image_data_url",
        lambda **_: "data:image/jpeg;base64,abc123",
    )

    add_hero_image_candidate(ctx=ctx, image=image)

    assert len(workspace.candidates) == 1
    assert workspace.candidates[0].image_url == "https://example.com/image.jpg"
    assert workspace.candidates[0].alt == "Shiv Roy."
    assert workspace.candidate_image_data_urls == ["data:image/jpeg;base64,abc123"]


def test_add_hero_image_candidate_returns_rejection_for_invalid_download(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Candidate download failures should not exhaust tool retry limits."""
    workspace = HeroImageWorkspace(
        article=HeroImageArticle(
            show=Show.SUCCESSION,
            title="Shiv Roy",
            subtitle="Dek.",
            article_mdx="Article.",
        ),
    )
    ctx = cast("RunContext[HeroImageWorkspace]", SimpleNamespace(deps=workspace))

    def reject_image(**_kwargs: object) -> str:
        raise ValueError("Not an image.")

    monkeypatch.setattr("hero_images.agent.selection_image_data_url", reject_image)

    result = add_hero_image_candidate(
        ctx=ctx,
        image=FoundHeroImage(
            image_url="https://example.com/not-image.jpg",
            source_page_url="https://example.com/article",
            alt="Not an image.",
            width=EXPECTED_WIDTH,
            height=EXPECTED_HEIGHT,
        ),
    )

    assert result.startswith("Candidate rejected:")
    assert workspace.candidates == []


def test_selected_hero_image_from_selection_uses_candidate_index() -> None:
    """Final image selection should come from the direct selector output."""
    candidates = [
        FoundHeroImage(
            image_url="https://example.com/generic-office.jpg",
            source_page_url="https://example.com/gallery",
            alt="A generic office.",
            width=EXPECTED_WIDTH,
            height=EXPECTED_HEIGHT,
        ),
        FoundHeroImage(
            image_url="https://assets.example.com/shiv-roy-succession.jpg",
            source_page_url="https://variety.com/tv/recaps/succession-shiv-roy",
            alt="Shiv Roy in Succession.",
            width=EXPECTED_WIDTH,
            height=EXPECTED_HEIGHT,
        ),
        FoundHeroImage(
            image_url="https://example.com/latest-bad-choice.jpg",
            source_page_url="https://example.com/gallery",
            alt="A vague image.",
            width=EXPECTED_WIDTH,
            height=EXPECTED_HEIGHT,
        ),
    ]

    selected = selected_hero_image_from_selection(
        candidates=candidates,
        selection=HeroImageSelection(candidate_index=1, rationale="Best fit."),
    )

    assert selected.image_url == "https://assets.example.com/shiv-roy-succession.jpg"
    assert selected.alt == "Shiv Roy in Succession."


def test_hero_image_selection_input_includes_images() -> None:
    """The direct selector should see candidate images, not only metadata text."""
    article = HeroImageArticle(
        show=Show.SUCCESSION,
        title="Shiv Roy",
        subtitle="Dek.",
        article_mdx="Article.",
    )
    candidates = [
        FoundHeroImage(
            image_url="https://example.com/shiv.jpg",
            source_page_url="https://example.com/article",
            alt="Shiv Roy.",
            width=EXPECTED_WIDTH,
            height=EXPECTED_HEIGHT,
        ),
    ]

    selection_input = hero_image_prompt.build_hero_image_selection_input(
        article=article,
        candidates=candidates,
        image_data_urls=["data:image/jpeg;base64,abc123"],
    )

    raw_selection_input = cast("list[dict[str, Any]]", selection_input)
    content = raw_selection_input[0]["content"]
    assert {
        "type": "input_image",
        "image_url": "data:image/jpeg;base64,abc123",
        "detail": "low",
    } in content


def test_selected_hero_image_from_selection_rejects_invalid_index() -> None:
    """The direct selector must choose a real candidate."""
    with pytest.raises(RuntimeError, match="invalid candidate index"):
        selected_hero_image_from_selection(
            candidates=[],
            selection=HeroImageSelection(candidate_index=0, rationale="Bad index."),
        )


def test_public_image_path_and_src_use_article_content_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Hero images export to site assets using the content article path."""
    content_root = tmp_path / "content" / "shows"
    asset_root = tmp_path / "site" / "src" / "assets" / "images" / "shows"
    article_path = content_root / "succession" / "episodes" / "s02" / "e02-vaulter" / "index.mdx"
    monkeypatch.setattr(find_hero_image, "CONTENT_SHOWS_ROOT", content_root)
    monkeypatch.setattr(find_hero_image, "ASSET_IMAGE_ROOT", asset_root)

    image_path = public_image_path_for_article(article_path=article_path)

    assert image_path == asset_root / "succession" / "episodes" / "s02" / "e02-vaulter" / "hero.jpg"
    assert public_image_src(image_path=image_path) == (
        "/images/shows/succession/episodes/s02/e02-vaulter/hero.jpg"
    )


def test_write_jpeg_hero_image_converts_input_bytes(tmp_path: Path) -> None:
    """Downloaded image bytes are normalized to a JPEG file."""
    source_path = tmp_path / "source.png"
    output_path = tmp_path / "hero.jpg"
    Image.new("RGBA", (EXPECTED_WIDTH, EXPECTED_HEIGHT), color=(10, 20, 30, 255)).save(source_path)

    write_jpeg_hero_image(
        image_path=output_path,
        content=source_path.read_bytes(),
    )

    with Image.open(output_path) as image:
        assert image.format == "JPEG"
        assert image.mode == "RGB"
        assert image.size == (EXPECTED_WIDTH, EXPECTED_HEIGHT)


def test_hero_image_size_rejects_small_sources() -> None:
    """Hero image sources must be large enough for the fixed output size."""
    with pytest.raises(ValueError, match="at least 1200x675"):
        validate_hero_image_size(width=800, height=450)


def test_download_hero_image_preserves_existing_file_when_validation_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A rejected replacement should not delete an existing hero image."""
    content_root = tmp_path / "content" / "shows"
    asset_root = tmp_path / "site" / "src" / "assets" / "images" / "shows"
    article_path = content_root / "succession" / "episodes" / "s02" / "e02-vaulter" / "index.mdx"
    image_path = asset_root / "succession" / "episodes" / "s02" / "e02-vaulter" / "hero.jpg"
    image_path.parent.mkdir(parents=True)
    Image.new("RGB", (EXPECTED_WIDTH, EXPECTED_HEIGHT), color=(10, 20, 30)).save(image_path)

    square_source_path = tmp_path / "square.png"
    Image.new("RGB", (EXPECTED_WIDTH, EXPECTED_WIDTH), color=(200, 10, 10)).save(square_source_path)
    monkeypatch.setattr(find_hero_image, "CONTENT_SHOWS_ROOT", content_root)
    monkeypatch.setattr(find_hero_image, "ASSET_IMAGE_ROOT", asset_root)

    def fake_get(*_args: object, **_kwargs: object) -> find_hero_image.httpx.Response:
        return find_hero_image.httpx.Response(
            200,
            content=square_source_path.read_bytes(),
            request=find_hero_image.httpx.Request("GET", "https://example.com/square.png"),
        )

    monkeypatch.setattr(find_hero_image.httpx, "get", fake_get)

    with pytest.raises(ValueError, match="close to 16:9"):
        download_hero_image(
            article_path=article_path,
            hero_image=FoundHeroImage(
                image_url="https://example.com/square.png",
                source_page_url="https://example.com/article",
                alt="A square image.",
            ),
        )

    with Image.open(image_path) as image:
        assert image.size == (EXPECTED_WIDTH, EXPECTED_HEIGHT)
