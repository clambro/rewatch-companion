"""CLI entrypoint for episode essay generation."""

import argparse

from pydantic import BaseModel

from agent import run_essay_agent
from generate_essay import episode_slug, find_episode, load_article_sources, write_article
from manifest import load_manifest
from schemas import EssayKind, EssayTarget, Show


class EpisodeCommand(BaseModel):
    """Parsed CLI command for episode generation."""

    show: Show
    season: int
    episode: int


def generate_episode() -> None:
    """Generate an episode essay."""
    parser = argparse.ArgumentParser(description="Generate an episode essay.")
    parser.add_argument("--show", choices=[show.value for show in Show], required=True)
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--episode", type=int, required=True)
    command = EpisodeCommand.model_validate(vars(parser.parse_args()))
    manifest = load_manifest(show=command.show)
    episode = find_episode(
        entries=manifest.episodes,
        season=command.season,
        episode=command.episode,
    )
    code = f"S{episode.season:02}E{episode.episode:02}"
    target = EssayTarget(
        show=command.show,
        kind=EssayKind.EPISODES,
        title=episode.title,
        prompt=f"A full-series rewatch essay about {code}, {episode.title}.",
        slug=episode_slug(episode=episode),
        season=episode.season,
        episode=episode.episode,
    )

    sources = load_article_sources(
        show=target.show,
        sections=[EssayKind.ABOUT, EssayKind.THEMES, EssayKind.CHARACTERS],
    )
    write_article(target=target, draft=run_essay_agent(target=target, sources=sources))


if __name__ == "__main__":
    generate_episode()
