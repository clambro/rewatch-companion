"""CLI entrypoint for theme essay generation."""

import argparse

from pydantic import BaseModel

from agent import run_essay_agent
from generate_essay import find_slugged_article, write_article
from manifest import load_manifest
from schemas import EssayKind, EssayTarget, Show


class ThemeCommand(BaseModel):
    """Parsed CLI command for theme generation."""

    show: Show
    slug: str


def generate_theme() -> None:
    """Generate a theme essay."""
    parser = argparse.ArgumentParser(description="Generate a theme essay.")
    parser.add_argument("--show", choices=[show.value for show in Show], required=True)
    parser.add_argument("--slug", required=True)
    command = ThemeCommand.model_validate(vars(parser.parse_args()))
    manifest = load_manifest(show=command.show)
    theme = find_slugged_article(entries=manifest.themes, slug=command.slug)
    target = EssayTarget(
        show=command.show,
        kind=EssayKind.THEMES,
        title=theme.title,
        prompt=theme.prompt,
        slug=theme.slug,
    )

    write_article(target=target, draft=run_essay_agent(target=target))


if __name__ == "__main__":
    generate_theme()
