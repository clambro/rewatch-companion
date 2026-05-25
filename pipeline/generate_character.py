"""CLI entrypoint for character essay generation."""

from agent import run_essay_agent
from common.manifest import load_manifest
from generate_essay import find_slugged_article, write_article
from schemas import EssayKind, EssayTarget, Show


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
