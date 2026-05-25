"""CLI entrypoint for theme essay generation."""

from common.manifest import load_manifest
from common.schemas import EssayKind, Show
from essay_generation.agent import run_essay_agent
from essay_generation.generate_essay import find_slugged_article, write_article
from essay_generation.schemas import EssayTarget


def generate_theme_essay(*, show: Show, slug: str) -> None:
    """Generate one theme essay from the manifest."""
    manifest = load_manifest(show=show)
    theme = find_slugged_article(entries=manifest.themes, slug=slug)
    target = EssayTarget(
        show=show,
        kind=EssayKind.THEMES,
        title=theme.title,
        prompt=theme.prompt,
        slug=theme.slug,
    )

    write_article(target=target, draft=run_essay_agent(target=target))
