"""CLI entrypoint for episode essay generation."""

import argparse

from pydantic import BaseModel

from agent import run_essay_agent
from common.manifest import ManifestEpisode, ShowManifest, episode_slug, load_manifest
from generate_essay import (
    CONTENT_ROOT,
    find_episode,
    load_article_source,
    load_article_sources,
    write_article,
)
from schemas import EssayKind, EssaySource, EssayTarget, Show


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
    generate_episode_essay(
        show=command.show,
        season=command.season,
        episode_number=command.episode,
    )


def generate_episode_essay(*, show: Show, season: int, episode_number: int) -> None:
    """Generate one episode essay from the manifest."""
    manifest = load_manifest(show=show)
    episode = find_episode(
        entries=manifest.episodes,
        season=season,
        episode=episode_number,
    )
    code = f"S{episode.season:02}E{episode.episode:02}"
    target = EssayTarget(
        show=show,
        kind=EssayKind.EPISODES,
        title=episode.title,
        prompt=f"A full-series rewatch essay about {code}, {episode.title}.",
        slug=episode_slug(episode=episode),
        season=episode.season,
        episode=episode.episode,
    )

    sources = load_article_sources(
        show=target.show,
        sections=[EssayKind.THEMES, EssayKind.CHARACTERS],
    )
    previous_episode_source = load_previous_episode_source(
        show=target.show,
        manifest=manifest,
        episode=episode,
    )
    if previous_episode_source is not None:
        sources.append(previous_episode_source)

    write_article(target=target, draft=run_essay_agent(target=target, sources=sources))


def load_previous_episode_source(
    *,
    show: Show,
    manifest: ShowManifest,
    episode: ManifestEpisode,
) -> EssaySource | None:
    """Load the previous episode summary required for sequential episode generation."""
    previous_episode = previous_manifest_episode(manifest=manifest, episode=episode)
    if previous_episode is None:
        return None

    summary_path = (
        CONTENT_ROOT
        / show.value
        / EssayKind.EPISODES.value
        / f"s{previous_episode.season:02}"
        / episode_slug(episode=previous_episode)
        / "summary.mdx"
    )
    if not summary_path.is_file():
        raise ValueError(
            "Episode generation must run in manifest order. "
            f"Missing previous episode summary: {summary_path}",
        )

    return load_article_source(path=summary_path, kind=EssayKind.EPISODES)


def previous_manifest_episode(
    *,
    manifest: ShowManifest,
    episode: ManifestEpisode,
) -> ManifestEpisode | None:
    """Return the previous episode in manifest order."""
    for index, manifest_episode in enumerate(manifest.episodes):
        if (
            manifest_episode.season == episode.season
            and manifest_episode.episode == episode.episode
        ):
            if index == 0:
                return None
            return manifest.episodes[index - 1]

    raise ValueError(
        f"Episode is not listed in manifest: S{episode.season:02}E{episode.episode:02}",
    )


if __name__ == "__main__":
    generate_episode()
