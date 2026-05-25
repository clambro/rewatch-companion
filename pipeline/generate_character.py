"""CLI entrypoint for character essay generation."""

import argparse

from pydantic import BaseModel

from agent import run_essay_agent
from common.manifest import load_manifest
from generate_essay import find_slugged_article, write_article
from schemas import EssayKind, EssayTarget, Show


class CharacterCommand(BaseModel):
    """Parsed CLI command for character generation."""

    show: Show
    slug: str


def generate_character() -> None:
    """Generate a character essay."""
    parser = argparse.ArgumentParser(description="Generate a character essay.")
    parser.add_argument("--show", choices=[show.value for show in Show], required=True)
    parser.add_argument("--slug", required=True)
    command = CharacterCommand.model_validate(vars(parser.parse_args()))
    generate_character_essay(show=command.show, slug=command.slug)


def generate_character_essay(*, show: Show, slug: str) -> None:
    """Generate one character essay from the manifest."""
    manifest = load_manifest(show=show)
    character = find_slugged_article(entries=manifest.characters, slug=slug)
    target = EssayTarget(
        show=show,
        kind=EssayKind.CHARACTERS,
        title=character.title,
        prompt=character.prompt,
        slug=character.slug,
    )

    write_article(target=target, draft=run_essay_agent(target=target))


if __name__ == "__main__":
    generate_character()
