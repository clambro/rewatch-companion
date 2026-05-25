"""CLI entrypoint for theme essay generation."""

from agent import run_essay_agent
from common.manifest import load_manifest
from generate_essay import find_slugged_article, write_article
from schemas import EssayKind, EssayTarget, Show


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
