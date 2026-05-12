"""CLI entrypoint for essay generation."""

import argparse
import json
import sys
from pathlib import Path

from agent import run_essay_agent
from schemas import EssayKind, EssayTarget, GeneratedEssay, Show

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_ROOT = REPO_ROOT / "content" / "shows"


def main() -> None:
    """Run the essay generation CLI."""
    parser = argparse.ArgumentParser(description="Generate a rewatch companion essay draft.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    about_parser = subparsers.add_parser("about")
    about_parser.add_argument("--show", choices=[show.value for show in Show], required=True)
    about_parser.add_argument("--description", required=True)

    themes_parser = subparsers.add_parser("themes")
    themes_parser.set_defaults(not_implemented="Theme generation is not implemented yet.")

    characters_parser = subparsers.add_parser("characters")
    characters_parser.set_defaults(not_implemented="Character generation is not implemented yet.")

    episodes_parser = subparsers.add_parser("episodes")
    episodes_parser.set_defaults(not_implemented="Episode generation is not implemented yet.")

    args = parser.parse_args()
    if message := getattr(args, "not_implemented", None):
        parser.error(message)

    target = EssayTarget(kind=EssayKind.ABOUT, description=args.description)
    draft = run_essay_agent(target=target)
    show = Show(args.show)
    output_dir = CONTENT_ROOT / show.value / EssayKind.ABOUT
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "index.mdx").write_text(render_draft(draft=draft), encoding="utf-8")
    (output_dir / "article.yaml").write_text(
        render_article_metadata(show=show, draft=draft),
        encoding="utf-8",
    )
    sys.stdout.write(f"Wrote {output_dir / 'index.mdx'}\n")


def render_draft(*, draft: GeneratedEssay) -> str:
    """Render the generated draft as a simple MDX document."""
    return (
        "---\n"
        f"title: {json.dumps(draft.title)}\n"
        f"dek: {json.dumps(draft.subtitle)}\n"
        "---\n\n"
        f"{draft.body_mdx.rstrip()}\n"
    )


def render_article_metadata(*, show: Show, draft: GeneratedEssay) -> str:
    """Render article metadata for the static site content collection."""
    return (
        f"show: {show.value}\n"
        f"title: {json.dumps(draft.title)}\n"
        "\n"
        "seo:\n"
        f"  title: {json.dumps(draft.title)}\n"
        f"  description: {json.dumps(draft.subtitle)}\n"
    )


if __name__ == "__main__":
    main()
