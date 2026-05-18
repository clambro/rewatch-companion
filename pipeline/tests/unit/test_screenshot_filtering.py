"""Unit tests for screenshot candidate filtering."""

from typing import TYPE_CHECKING

import numpy as np

import screenshot_extraction
import screenshot_filtering
from manifest import ManifestEpisode
from schemas import Show
from screenshot_filtering import (
    CandidateScores,
    FilteringSettings,
    ModerationDecision,
    duplicate_match_for,
    filter_episode_screenshot_candidates,
    filtered_dir_for_episode,
    filtering_report_path,
    rejection_for,
    tile_blur_score_for,
)

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

EXPECTED_DUPLICATE_DISTANCE = 2
EXPECTED_REJECTED_COUNT = 2
EXPECTED_WHOLE_FRAME_SCORE = 20.0
EXPECTED_MEAN_LUMA = 50.0
EXPECTED_LUMA_STDDEV = 15.0
DEFAULT_FILTERING_SETTINGS = FilteringSettings(
    min_blur_score=80.0,
    min_mean_luma=12.0,
    max_mean_luma=245.0,
    min_luma_stddev=8.0,
    tile_grid_size=8,
    duplicate_hash_distance=6,
)
SAFE_MODERATION_DECISION = ModerationDecision(
    flagged=False,
    rejected_categories=[],
    category_scores={"sexual": 0.01, "violence/graphic": 0.01},
)


def test_rejection_for_blurry_candidate() -> None:
    """Candidates below the blur threshold are rejected."""
    reason = rejection_for(
        scores=CandidateScores(tile_blur_score=79.9, mean_luma=50.0, luma_stddev=15.0),
        settings=DEFAULT_FILTERING_SETTINGS,
    )

    assert reason == "blurry"


def test_duplicate_match_for_near_duplicate_candidate() -> None:
    """Candidates near an already-kept hash are matched as duplicates."""
    result_index, duplicate_of, hash_distance = duplicate_match_for(
        image_hash=0b1111_0000,
        kept_hashes=[(0, "scene-0001.jpg", 0b1111_0011)],
        settings=DEFAULT_FILTERING_SETTINGS.model_copy(update={"duplicate_hash_distance": 2}),
    )

    assert result_index == 0
    assert duplicate_of == "scene-0001.jpg"
    assert hash_distance == EXPECTED_DUPLICATE_DISTANCE


def test_rejection_for_bad_luma() -> None:
    """Dark, bright, and flat frames are rejected before blur and duplicate checks."""
    settings = DEFAULT_FILTERING_SETTINGS.model_copy(update={"duplicate_hash_distance": 2})

    assert (
        rejection_for(
            scores=CandidateScores(tile_blur_score=200.0, mean_luma=11.9, luma_stddev=20.0),
            settings=settings,
        )
        == "too_dark"
    )
    assert (
        rejection_for(
            scores=CandidateScores(tile_blur_score=200.0, mean_luma=245.1, luma_stddev=20.0),
            settings=settings,
        )
        == "too_bright"
    )
    assert (
        rejection_for(
            scores=CandidateScores(tile_blur_score=200.0, mean_luma=50.0, luma_stddev=7.9),
            settings=settings,
        )
        == "too_flat"
    )


def test_filter_paths_use_screenshot_layout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Filtered output lives beside the raw candidate folder."""
    monkeypatch.setattr(
        screenshot_extraction,
        "SCREENSHOT_ROOT",
        tmp_path / ".local" / "screenshots",
    )
    episode = ManifestEpisode(season=1, episode=2, title="Shit Show at the Fuck Factory")
    root = tmp_path / ".local" / "screenshots" / "succession" / "s01" / "e02"

    assert filtered_dir_for_episode(show=Show.SUCCESSION, episode=episode) == root / "filtered"
    assert filtering_report_path(show=Show.SUCCESSION, episode=episode) == (
        root / "filtering_report.json"
    )


def test_filter_episode_copies_kept_candidates_and_writes_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Filtering copies kept files and records rejection reasons."""
    monkeypatch.setattr(screenshot_extraction, "SCREENSHOT_ROOT", tmp_path / "screenshots")
    monkeypatch.setattr(screenshot_filtering, "read_image", lambda **_: object())
    luma_metrics = iter([(50.0, 15.0), (50.0, 15.0), (50.0, 15.0)])
    tile_scores = iter([130.0, 30.0, 130.0])
    whole_frame_scores = iter([20.0, 5.0, 20.0])
    hashes = iter([0b1111_0000, 0b0000_1111, 0b1111_0011])
    monkeypatch.setattr(screenshot_filtering, "luma_metrics_for", lambda **_: next(luma_metrics))
    monkeypatch.setattr(
        screenshot_filtering,
        "tile_blur_score_for",
        lambda **_: next(tile_scores),
    )
    monkeypatch.setattr(
        screenshot_filtering,
        "whole_frame_blur_score_for",
        lambda **_: next(whole_frame_scores),
    )
    monkeypatch.setattr(screenshot_filtering, "average_hash", lambda **_: next(hashes))
    monkeypatch.setattr(
        screenshot_filtering,
        "moderate_image",
        lambda **_: SAFE_MODERATION_DECISION,
    )
    episode = ManifestEpisode(season=1, episode=2, title="Shit Show at the Fuck Factory")
    candidate_dir = screenshot_extraction.candidate_dir_for_episode(
        show=Show.SUCCESSION,
        episode=episode,
    )
    candidate_dir.mkdir(parents=True)
    for name in ["scene-0001.jpg", "scene-0002.jpg", "scene-0003.jpg"]:
        (candidate_dir / name).write_text(name, encoding="utf-8")

    report = filter_episode_screenshot_candidates(
        show=Show.SUCCESSION,
        episode=episode,
        settings=DEFAULT_FILTERING_SETTINGS.model_copy(update={"duplicate_hash_distance": 2}),
    )

    output_dir = filtered_dir_for_episode(show=Show.SUCCESSION, episode=episode)
    assert report.kept_count == 1
    assert report.rejected_count == EXPECTED_REJECTED_COUNT
    assert (output_dir / "scene-0001.jpg").is_file()
    assert not (output_dir / "scene-0002.jpg").is_file()
    assert not (output_dir / "scene-0003.jpg").is_file()
    assert report.results[1].rejected_reason == "blurry"
    assert report.results[2].rejected_reason == "near_duplicate"
    assert report.results[0].whole_frame_blur_score == EXPECTED_WHOLE_FRAME_SCORE
    assert report.results[0].mean_luma == EXPECTED_MEAN_LUMA
    assert report.results[0].luma_stddev == EXPECTED_LUMA_STDDEV
    assert filtering_report_path(show=Show.SUCCESSION, episode=episode).is_file()


def test_filter_episode_keeps_sharper_near_duplicate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Near-duplicate groups keep the candidate with the highest tile blur score."""
    monkeypatch.setattr(screenshot_extraction, "SCREENSHOT_ROOT", tmp_path / "screenshots")
    monkeypatch.setattr(screenshot_filtering, "read_image", lambda **_: object())
    luma_metrics = iter([(50.0, 15.0), (50.0, 15.0)])
    tile_scores = iter([100.0, 180.0])
    whole_frame_scores = iter([100.0, 180.0])
    hashes = iter([0b1111_0000, 0b1111_0011])
    monkeypatch.setattr(screenshot_filtering, "luma_metrics_for", lambda **_: next(luma_metrics))
    monkeypatch.setattr(
        screenshot_filtering,
        "tile_blur_score_for",
        lambda **_: next(tile_scores),
    )
    monkeypatch.setattr(
        screenshot_filtering,
        "whole_frame_blur_score_for",
        lambda **_: next(whole_frame_scores),
    )
    monkeypatch.setattr(screenshot_filtering, "average_hash", lambda **_: next(hashes))
    monkeypatch.setattr(
        screenshot_filtering,
        "moderate_image",
        lambda **_: SAFE_MODERATION_DECISION,
    )
    episode = ManifestEpisode(season=1, episode=2, title="Shit Show at the Fuck Factory")
    candidate_dir = screenshot_extraction.candidate_dir_for_episode(
        show=Show.SUCCESSION,
        episode=episode,
    )
    candidate_dir.mkdir(parents=True)
    for name in ["scene-0001.jpg", "scene-0002.jpg"]:
        (candidate_dir / name).write_text(name, encoding="utf-8")

    report = filter_episode_screenshot_candidates(
        show=Show.SUCCESSION,
        episode=episode,
        settings=DEFAULT_FILTERING_SETTINGS.model_copy(update={"duplicate_hash_distance": 2}),
    )

    output_dir = filtered_dir_for_episode(show=Show.SUCCESSION, episode=episode)
    assert report.kept_count == 1
    assert not report.results[0].kept
    assert report.results[0].rejected_reason == "near_duplicate"
    assert report.results[0].duplicate_of == "scene-0002.jpg"
    assert report.results[1].kept
    assert not (output_dir / "scene-0001.jpg").is_file()
    assert (output_dir / "scene-0002.jpg").is_file()


def test_filter_episode_rejects_moderated_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Moderation can reject otherwise viable candidates."""
    monkeypatch.setattr(screenshot_extraction, "SCREENSHOT_ROOT", tmp_path / "screenshots")
    monkeypatch.setattr(screenshot_filtering, "read_image", lambda **_: object())
    monkeypatch.setattr(screenshot_filtering, "luma_metrics_for", lambda **_: (50.0, 15.0))
    monkeypatch.setattr(screenshot_filtering, "tile_blur_score_for", lambda **_: 130.0)
    monkeypatch.setattr(screenshot_filtering, "whole_frame_blur_score_for", lambda **_: 20.0)
    monkeypatch.setattr(screenshot_filtering, "average_hash", lambda **_: 0b1111_0000)
    monkeypatch.setattr(
        screenshot_filtering,
        "moderate_image",
        lambda **_: ModerationDecision(
            flagged=True,
            rejected_categories=["sexual"],
            category_scores={"sexual": 0.99},
        ),
    )
    episode = ManifestEpisode(season=1, episode=2, title="Shit Show at the Fuck Factory")
    candidate_dir = screenshot_extraction.candidate_dir_for_episode(
        show=Show.SUCCESSION,
        episode=episode,
    )
    candidate_dir.mkdir(parents=True)
    (candidate_dir / "scene-0001.jpg").write_text("scene-0001.jpg", encoding="utf-8")

    report = filter_episode_screenshot_candidates(
        show=Show.SUCCESSION,
        episode=episode,
        settings=DEFAULT_FILTERING_SETTINGS,
    )

    output_dir = filtered_dir_for_episode(show=Show.SUCCESSION, episode=episode)
    assert report.kept_count == 0
    assert report.results[0].rejected_reason == "unsafe_content"
    assert report.results[0].moderation_flagged is True
    assert report.results[0].moderation_rejected_categories == ["sexual"]
    assert not (output_dir / "scene-0001.jpg").is_file()


def test_tile_blur_uses_sharp_regions() -> None:
    """Tile blur can keep frames with one sharp region and a soft background."""
    image = np.full((80, 80, 3), 128, dtype=np.uint8)
    image[10:30, 10:30] = np.indices((20, 20)).sum(axis=0)[:, :, None] % 2 * 255

    assert tile_blur_score_for(image=image, tile_grid_size=4) > 0
