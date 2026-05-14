"""Shared helpers for essay generation."""

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml
from openai import OpenAI

from prompt import (
    CHARACTER_SOURCE_TYPE,
    PREVIOUS_EPISODE_SOURCE_TYPE,
    SUMMARY_INSTRUCTIONS,
    THEME_SOURCE_TYPE,
    build_summary_prompt,
)
from schemas import EssayKind, EssaySource, EssayTarget, GeneratedEssay, Show
from settings import settings

if TYPE_CHECKING:
    from manifest import ManifestEpisode, ManifestSluggedArticle

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_ROOT = REPO_ROOT / "content" / "shows"
SUMMARY_MODEL = "gpt-5.4-nano"


def write_article(*, target: EssayTarget, draft: GeneratedEssay) -> None:
    """Write a generated article to content."""
    output_dir = output_path(target=target)
    summary = summarize_essay(target=target, draft=draft).strip()

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "index.mdx").write_text(
        render_draft(target=target, draft=draft),
        encoding="utf-8",
    )

    match target.kind:
        case EssayKind.EPISODES:
            metadata = render_episode_metadata(target=target, draft=draft)
        case _:
            metadata = render_article_metadata(target=target, draft=draft)

    (output_dir / "article.yaml").write_text(metadata, encoding="utf-8")
    (output_dir / "summary.mdx").write_text(f"{summary}\n", encoding="utf-8")
    rebuild_show_index(show=target.show)
    sys.stdout.write(f"Wrote {output_dir / 'index.mdx'}\n")


def summarize_essay(*, target: EssayTarget, draft: GeneratedEssay) -> str:
    """Generate the compact internal summary for an essay."""
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.responses.create(
        model=SUMMARY_MODEL,
        instructions=SUMMARY_INSTRUCTIONS,
        input=build_summary_prompt(
            title=target.title,
            subtitle=draft.subtitle,
            body_mdx=draft.body_mdx,
        ),
    )
    return response.output_text.strip()


def rebuild_show_index(*, show: Show) -> None:
    """Rebuild the frontend show index from generated content files."""
    show_root = CONTENT_ROOT / show.value
    show_index_path = show_root / "show.yaml"
    current_index = yaml.safe_load(show_index_path.read_text(encoding="utf-8"))

    show_index: dict[str, Any] = {
        "title": current_index["title"],
        "slug": current_index["slug"],
    }

    themes = load_article_listing(show_root=show_root, section=EssayKind.THEMES)
    if themes:
        show_index["themes"] = themes

    characters = load_article_listing(show_root=show_root, section=EssayKind.CHARACTERS)
    if characters:
        show_index["characters"] = characters

    show_index["seasons"] = load_episode_listing(show_root=show_root)
    show_index_path.write_text(render_show_index(show_index=show_index), encoding="utf-8")


def load_article_sources(*, show: Show, sections: list[EssayKind]) -> list[EssaySource]:
    """Load committed article essays as context sources."""
    show_root = CONTENT_ROOT / show.value
    sources = []
    for section in sections:
        match section:
            case EssayKind.THEMES | EssayKind.CHARACTERS:
                section_root = show_root / section.value
                for article_path in sorted(section_root.glob("*/index.mdx")):
                    summary_path = article_path.with_name("summary.mdx")
                    if not summary_path.is_file():
                        raise ValueError(f"Missing source summary: {summary_path}")
                    sources.append(load_article_source(path=summary_path, kind=section))
            case EssayKind.EPISODES:
                raise ValueError("Episode essays are not supported as generation sources yet.")

    return sources


def load_article_listing(*, show_root: Path, section: EssayKind) -> list[dict[str, str]]:
    """Load generated article entries for the frontend show index."""
    article_root = show_root / section.value
    entries = []
    for metadata_path in sorted(article_root.glob("*/article.yaml")):
        article_path = metadata_path.with_name("index.mdx")
        if not article_path.is_file():
            continue

        metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
        entries.append(
            {
                "title": metadata["title"],
                "path": metadata_path.parent.relative_to(show_root).as_posix(),
            },
        )

    return entries


def load_episode_listing(*, show_root: Path) -> list[dict[str, Any]]:
    """Load generated episode entries for the frontend show index."""
    seasons_by_number: dict[int, list[dict[str, Any]]] = {}
    for metadata_path in sorted((show_root / EssayKind.EPISODES.value).glob("s*/e*/article.yaml")):
        article_path = metadata_path.with_name("index.mdx")
        if not article_path.is_file():
            continue

        metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
        seasons_by_number.setdefault(metadata["season"], []).append(
            {
                "episode": metadata["episode"],
                "code": metadata["code"],
                "title": metadata["title"],
                "path": metadata_path.parent.relative_to(show_root).as_posix(),
            },
        )

    seasons = []
    for season_number, episodes in sorted(seasons_by_number.items()):
        seasons.append(
            {
                "season": season_number,
                "episodes": [
                    {
                        "code": episode["code"],
                        "title": episode["title"],
                        "path": episode["path"],
                    }
                    for episode in sorted(episodes, key=lambda entry: entry["episode"])
                ],
            },
        )

    return seasons


def output_path(*, target: EssayTarget) -> Path:
    """Return the content output path for a generated essay."""
    match target.kind:
        case EssayKind.THEMES:
            return CONTENT_ROOT / target.show.value / EssayKind.THEMES.value / target.slug
        case EssayKind.CHARACTERS:
            return CONTENT_ROOT / target.show.value / EssayKind.CHARACTERS.value / target.slug
        case EssayKind.EPISODES:
            if target.season is None:
                raise ValueError("Episode generation requires a season.")
            return (
                CONTENT_ROOT
                / target.show.value
                / EssayKind.EPISODES.value
                / f"s{target.season:02}"
                / target.slug
            )

    raise ValueError(f"Unsupported essay kind: {target.kind.value}")


def find_slugged_article(
    *,
    entries: list[ManifestSluggedArticle],
    slug: str,
) -> ManifestSluggedArticle:
    """Find a slugged manifest article."""
    for entry in entries:
        if entry.slug == slug:
            return entry

    available_slugs = ", ".join(entry.slug for entry in entries)
    raise ValueError(f"Unknown article slug: {slug}. Available slugs: {available_slugs}")


def find_episode(
    *,
    entries: list[ManifestEpisode],
    season: int,
    episode: int,
) -> ManifestEpisode:
    """Find an episode manifest entry."""
    for entry in entries:
        if entry.season == season and entry.episode == episode:
            return entry

    available_episodes = ", ".join(f"S{entry.season:02}E{entry.episode:02}" for entry in entries)
    raise ValueError(
        f"Unknown episode: S{season:02}E{episode:02}. Available episodes: {available_episodes}",
    )


def load_article_source(
    *,
    path: Path,
    kind: EssayKind,
) -> EssaySource:
    """Load one committed article summary as source context."""
    match kind:
        case EssayKind.THEMES:
            label = THEME_SOURCE_TYPE
        case EssayKind.CHARACTERS:
            label = CHARACTER_SOURCE_TYPE
        case EssayKind.EPISODES:
            label = PREVIOUS_EPISODE_SOURCE_TYPE

    metadata = yaml.safe_load(path.with_name("article.yaml").read_text(encoding="utf-8"))
    return EssaySource(
        label=label,
        title=metadata["title"],
        subtitle=metadata["seo"]["description"],
        summary_mdx=path.read_text(encoding="utf-8").strip(),
    )


def render_draft(*, target: EssayTarget, draft: GeneratedEssay) -> str:
    """Render the generated draft as a simple MDX document."""
    return (
        "---\n"
        f"title: {json.dumps(target.title)}\n"
        f"dek: {json.dumps(draft.subtitle)}\n"
        "---\n\n"
        f"{draft.body_mdx.rstrip()}\n"
    )


def render_article_metadata(*, target: EssayTarget, draft: GeneratedEssay) -> str:
    """Render article metadata for the static site content collection."""
    return (
        f"show: {target.show.value}\n"
        f"title: {json.dumps(target.title)}\n"
        f"slug: {json.dumps(target.slug)}\n"
        "\n"
        "seo:\n"
        f"  title: {json.dumps(target.title)}\n"
        f"  description: {json.dumps(draft.subtitle)}\n"
    )


def render_episode_metadata(*, target: EssayTarget, draft: GeneratedEssay) -> str:
    """Render episode metadata for the static site content collection."""
    if target.season is None or target.episode is None:
        raise ValueError("Episode metadata requires season and episode.")

    code = f"S{target.season:02}E{target.episode:02}"
    return (
        f"show: {target.show.value}\n"
        f"season: {target.season}\n"
        f"episode: {target.episode}\n"
        f"code: {json.dumps(code)}\n"
        f"title: {json.dumps(target.title)}\n"
        f"slug: {json.dumps(target.slug)}\n"
        "\n"
        "seo:\n"
        f"  title: {json.dumps(target.title)}\n"
        f"  description: {json.dumps(draft.subtitle)}\n"
    )


def render_show_index(*, show_index: dict[str, Any]) -> str:
    """Render show.yaml for the static site show page."""
    lines = [
        f"title: {json.dumps(show_index['title'])}",
        f"slug: {json.dumps(show_index['slug'])}",
    ]

    if "themes" in show_index:
        lines.extend(["", "themes:"])
        for theme in show_index["themes"]:
            lines.extend(
                [
                    f"  - title: {json.dumps(theme['title'])}",
                    f"    path: {json.dumps(theme['path'])}",
                ],
            )

    if "characters" in show_index:
        lines.extend(["", "characters:"])
        for character in show_index["characters"]:
            lines.extend(
                [
                    f"  - title: {json.dumps(character['title'])}",
                    f"    path: {json.dumps(character['path'])}",
                ],
            )

    lines.extend(["", "seasons:"])
    for season in show_index["seasons"]:
        lines.append(f"  - season: {season['season']}")
        lines.append("    episodes:")
        for episode in season["episodes"]:
            lines.extend(
                [
                    f"      - code: {json.dumps(episode['code'])}",
                    f"        title: {json.dumps(episode['title'])}",
                    f"        path: {json.dumps(episode['path'])}",
                ],
            )

    if not show_index["seasons"]:
        lines[-1] = "seasons: []"

    return "\n".join(lines) + "\n"
