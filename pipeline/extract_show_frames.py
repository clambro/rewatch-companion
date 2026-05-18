"""CLI entrypoint for show-level screenshot candidate extraction."""

import argparse
import sys

from pydantic import BaseModel

from manifest import load_manifest
from schemas import Show
from screenshot_extraction import (
    ExtractionSettings,
    extract_episode_screenshot_candidates,
    selected_manifest_episodes,
)

DEFAULT_DETECTOR_THRESHOLD = 27.0
DEFAULT_MIN_SCENE_LENGTH = 15
DEFAULT_IMAGE_WIDTH = 1280


class ExtractShowFramesCommand(BaseModel):
    """Parsed CLI command for screenshot candidate extraction."""

    show: Show
    season: int | None = None
    episode: int | None = None
    threshold: float
    min_scene_length: int
    image_width: int
    overwrite: bool = False


def extract_show_frames() -> None:
    """Extract screenshot candidates for manifest episodes."""
    parser = argparse.ArgumentParser(description="Extract local screenshot candidates for a show.")
    parser.add_argument("--show", choices=[show.value for show in Show], required=True)
    parser.add_argument("--season", type=int)
    parser.add_argument("--episode", type=int)
    parser.add_argument("--threshold", type=float, default=DEFAULT_DETECTOR_THRESHOLD)
    parser.add_argument("--min-scene-length", type=int, default=DEFAULT_MIN_SCENE_LENGTH)
    parser.add_argument("--image-width", type=int, default=DEFAULT_IMAGE_WIDTH)
    parser.add_argument("--overwrite", action="store_true")
    command = ExtractShowFramesCommand.model_validate(vars(parser.parse_args()))
    manifest = load_manifest(show=command.show)
    settings = ExtractionSettings(
        threshold=command.threshold,
        min_scene_length=command.min_scene_length,
        image_width=command.image_width,
    )
    episodes = selected_manifest_episodes(
        episodes=manifest.episodes,
        season=command.season,
        episode=command.episode,
    )

    for manifest_episode in episodes:
        sys.stdout.write(f"Extracting {manifest_episode.title}\n")
        candidate_manifest = extract_episode_screenshot_candidates(
            show=command.show,
            episode=manifest_episode,
            settings=settings,
            overwrite=command.overwrite,
        )
        sys.stdout.write(
            f"{candidate_manifest.code}: {len(candidate_manifest.candidates)} candidates\n",
        )


if __name__ == "__main__":
    extract_show_frames()
