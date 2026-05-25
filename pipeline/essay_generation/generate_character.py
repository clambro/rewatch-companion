"""CLI entrypoint for character essay generation."""

from common.manifest import load_manifest
from common.schemas import EssayKind, Show
from essay_generation.agent import run_essay_agent
from essay_generation.generate_essay import find_slugged_article, write_article
from essay_generation.schemas import EssayTarget


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
