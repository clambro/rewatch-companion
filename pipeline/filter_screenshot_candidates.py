"""CLI entrypoint for filtering extracted screenshot candidates."""

import argparse
import sys

from pydantic import BaseModel

from generate_essay import find_episode
from manifest import load_manifest
from schemas import Show
from screenshot_filtering import FilteringSettings, filter_episode_screenshot_candidates

DEFAULT_MIN_BLUR_SCORE = 40.0
DEFAULT_MIN_MEAN_LUMA = 12.0
DEFAULT_MAX_MEAN_LUMA = 245.0
DEFAULT_MIN_LUMA_STDDEV = 8.0
DEFAULT_TILE_GRID_SIZE = 8
DEFAULT_DUPLICATE_HASH_DISTANCE = 6


class FilterScreenshotCandidatesCommand(BaseModel):
    """Parsed CLI command for screenshot candidate filtering."""

    show: Show
    season: int
    episode: int
    min_blur_score: float
    min_mean_luma: float
    max_mean_luma: float
    min_luma_stddev: float
    tile_grid_size: int
    duplicate_hash_distance: int
    overwrite: bool = False


def filter_screenshot_candidates() -> None:
    """Filter an existing screenshot candidate folder."""
    parser = argparse.ArgumentParser(description="Filter local screenshot candidates.")
    parser.add_argument("--show", choices=[show.value for show in Show], required=True)
    parser.add_argument("--season", type=int, required=True)
    parser.add_argument("--episode", type=int, required=True)
    parser.add_argument("--min-blur-score", type=float, default=DEFAULT_MIN_BLUR_SCORE)
    parser.add_argument("--min-mean-luma", type=float, default=DEFAULT_MIN_MEAN_LUMA)
    parser.add_argument("--max-mean-luma", type=float, default=DEFAULT_MAX_MEAN_LUMA)
    parser.add_argument("--min-luma-stddev", type=float, default=DEFAULT_MIN_LUMA_STDDEV)
    parser.add_argument("--tile-grid-size", type=int, default=DEFAULT_TILE_GRID_SIZE)
    parser.add_argument(
        "--duplicate-hash-distance",
        type=int,
        default=DEFAULT_DUPLICATE_HASH_DISTANCE,
    )
    parser.add_argument("--overwrite", action="store_true")
    command = FilterScreenshotCandidatesCommand.model_validate(vars(parser.parse_args()))
    manifest = load_manifest(show=command.show)
    episode = find_episode(
        entries=manifest.episodes,
        season=command.season,
        episode=command.episode,
    )
    settings = FilteringSettings(
        min_blur_score=command.min_blur_score,
        min_mean_luma=command.min_mean_luma,
        max_mean_luma=command.max_mean_luma,
        min_luma_stddev=command.min_luma_stddev,
        tile_grid_size=command.tile_grid_size,
        duplicate_hash_distance=command.duplicate_hash_distance,
    )
    report = filter_episode_screenshot_candidates(
        show=command.show,
        episode=episode,
        settings=settings,
        overwrite=command.overwrite,
    )
    sys.stdout.write(
        f"{report.code}: {report.kept_count} kept, {report.rejected_count} rejected\n",
    )


if __name__ == "__main__":
    filter_screenshot_candidates()
