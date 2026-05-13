"""CLI entrypoint for series thesis generation."""

import argparse

from pydantic import BaseModel

from agent import run_essay_agent
from generate_essay import load_article_sources, write_article
from manifest import load_manifest
from schemas import EssayKind, EssayTarget, Show


class AboutCommand(BaseModel):
    """Parsed CLI command for series thesis generation."""

    show: Show


def generate_about() -> None:
    """Generate a series thesis essay."""
    parser = argparse.ArgumentParser(description="Generate a series thesis essay.")
    parser.add_argument("--show", choices=[show.value for show in Show], required=True)
    command = AboutCommand.model_validate(vars(parser.parse_args()))
    manifest = load_manifest(show=command.show)
    target = EssayTarget(
        show=command.show,
        kind=EssayKind.ABOUT,
        title=manifest.about.title,
        prompt=manifest.about.prompt,
    )

    sources = load_article_sources(
        show=target.show,
        sections=[EssayKind.THEMES, EssayKind.CHARACTERS],
    )
    write_article(
        target=target,
        draft=run_essay_agent(target=target, sources=sources),
    )


if __name__ == "__main__":
    generate_about()
