"""CLI entrypoint for essay generation."""

import argparse
import json
import sys
from pathlib import Path

from pydantic import BaseModel

from agent import run_essay_agent
from manifest import ManifestSluggedArticle, ShowManifest, load_manifest
from schemas import EssayKind, EssayTarget, GeneratedEssay, Show

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_ROOT = REPO_ROOT / "content" / "shows"


def main() -> None:
    """Run the essay generation CLI."""
    parser = argparse.ArgumentParser(description="Generate a rewatch companion essay draft.")
    subparsers = parser.add_subparsers(dest="kind", required=True)

    about_parser = subparsers.add_parser("about")
    about_parser.add_argument("--show", choices=[show.value for show in Show], required=True)

    themes_parser = subparsers.add_parser("themes")
    themes_parser.add_argument("--show", choices=[show.value for show in Show], required=True)
    themes_parser.add_argument("--slug", required=True)

    subparsers.add_parser("characters")

    subparsers.add_parser("episodes")

    command = GenerateEssayCommand.model_validate(vars(parser.parse_args()))
    if command.kind == EssayKind.CHARACTERS:
        parser.error("Character generation is not implemented yet.")
    if command.kind == EssayKind.EPISODES:
        parser.error("Episode generation is not implemented yet.")

    manifest = load_manifest(show=command.show)
    target = build_target(
        command=command,
        manifest=manifest,
    )
    draft = run_essay_agent(target=target)
    output_dir = output_path(target=target)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "index.mdx").write_text(
        render_draft(target=target, draft=draft),
        encoding="utf-8",
    )
    (output_dir / "article.yaml").write_text(
        render_article_metadata(target=target, draft=draft),
        encoding="utf-8",
    )
    sys.stdout.write(f"Wrote {output_dir / 'index.mdx'}\n")


class GenerateEssayCommand(BaseModel):
    """Parsed CLI command for essay generation."""

    kind: EssayKind
    show: Show
    slug: str | None = None


def build_target(
    *,
    command: GenerateEssayCommand,
    manifest: ShowManifest,
) -> EssayTarget:
    """Build the essay target for a CLI command."""
    if command.kind == EssayKind.ABOUT:
        return EssayTarget(
            show=command.show,
            kind=EssayKind.ABOUT,
            title=manifest.about.title,
            prompt=manifest.about.prompt,
        )

    if command.kind == EssayKind.THEMES:
        theme = find_slugged_article(entries=manifest.themes, slug=command.slug)
        return EssayTarget(
            show=command.show,
            kind=EssayKind.THEMES,
            title=theme.title,
            prompt=theme.prompt,
            slug=theme.slug,
        )

    raise ValueError(f"Unsupported essay command: {command.kind.value}")


def output_path(*, target: EssayTarget) -> Path:
    """Return the content output path for a generated essay."""
    if target.kind == EssayKind.ABOUT:
        return CONTENT_ROOT / target.show.value / EssayKind.ABOUT.value

    if target.kind == EssayKind.THEMES:
        if target.slug is None:
            raise ValueError("Theme generation requires a slug.")
        return CONTENT_ROOT / target.show.value / EssayKind.THEMES.value / target.slug

    raise ValueError(f"Unsupported essay kind: {target.kind.value}")


def find_slugged_article(
    *,
    entries: list[ManifestSluggedArticle],
    slug: str | None,
) -> ManifestSluggedArticle:
    """Find a slugged manifest article."""
    if slug is None:
        raise ValueError("Slug is required.")

    for entry in entries:
        if entry.slug == slug:
            return entry

    available_slugs = ", ".join(entry.slug for entry in entries)
    raise ValueError(f"Unknown article slug: {slug}. Available slugs: {available_slugs}")


def render_draft(*, target: EssayTarget, draft: GeneratedEssay) -> str:
    """Render the generated draft as a simple MDX document."""
    return (
        "---\n"
        f"title: {json.dumps(target.title)}\n"
        f"dek: {json.dumps(draft.subtitle)}\n"
        "---\n\n"
        f"{draft.body_mdx.rstrip()}\n"
    )


def render_article_metadata(
    *,
    target: EssayTarget,
    draft: GeneratedEssay,
) -> str:
    """Render article metadata for the static site content collection."""
    slug = f"slug: {json.dumps(target.slug)}\n" if target.slug is not None else ""
    return (
        f"show: {target.show.value}\n"
        f"title: {json.dumps(target.title)}\n"
        f"{slug}"
        "\n"
        "seo:\n"
        f"  title: {json.dumps(target.title)}\n"
        f"  description: {json.dumps(draft.subtitle)}\n"
    )


if __name__ == "__main__":
    main()
