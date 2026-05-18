"""Unit tests for screenshot candidate extraction."""

from typing import TYPE_CHECKING

import pytest

import screenshot_extraction
from manifest import ManifestEpisode
from schemas import Show
from screenshot_extraction import (
    CandidateFrame,
    ExtractionSettings,
    candidate_dir_for_episode,
    candidate_manifest_path,
    extract_episode_screenshot_candidates,
    media_path_for_episode,
    screenshot_root_for_episode,
    selected_manifest_episodes,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_media_path_resolution_uses_season_folders(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Episode media resolves from .local/media/<show>/sXX/eYY."""
    monkeypatch.setattr(screenshot_extraction, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(screenshot_extraction, "MEDIA_ROOT", tmp_path / ".local" / "media")
    episode = ManifestEpisode(season=1, episode=2, title="Shit Show at the Fuck Factory")
    media_path = tmp_path / ".local" / "media" / "succession" / "s01" / "e02.mkv"
    media_path.parent.mkdir(parents=True)
    media_path.touch()

    assert media_path_for_episode(show=Show.SUCCESSION, episode=episode) == media_path


def test_missing_media_error_lists_expected_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing media errors include every supported filename."""
    monkeypatch.setattr(screenshot_extraction, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(screenshot_extraction, "MEDIA_ROOT", tmp_path / ".local" / "media")
    episode = ManifestEpisode(season=1, episode=2, title="Shit Show at the Fuck Factory")

    with pytest.raises(FileNotFoundError) as error:
        media_path_for_episode(show=Show.SUCCESSION, episode=episode)

    message = str(error.value)
    assert "S01E02" in message
    assert ".local/media/succession/s01/e02.mkv" in message
    assert ".local/media/succession/s01/e02.mp4" in message
    assert ".local/media/succession/s01/e02.mov" in message
    assert ".local/media/succession/s01/e02.m4v" in message


def test_output_paths_use_screenshot_candidate_layout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Screenshot artifacts are rooted under .local/screenshots."""
    monkeypatch.setattr(
        screenshot_extraction,
        "SCREENSHOT_ROOT",
        tmp_path / ".local" / "screenshots",
    )
    episode = ManifestEpisode(season=1, episode=2, title="Shit Show at the Fuck Factory")

    root = screenshot_root_for_episode(show=Show.SUCCESSION, episode=episode)

    assert root == tmp_path / ".local" / "screenshots" / "succession" / "s01" / "e02"
    assert candidate_dir_for_episode(show=Show.SUCCESSION, episode=episode) == root / "candidates"
    assert candidate_manifest_path(show=Show.SUCCESSION, episode=episode) == (
        root / "candidate_manifest.json"
    )


def test_selected_manifest_episodes_filters_by_season_and_episode() -> None:
    """Season and episode filters select manifest episodes deterministically."""
    episodes = [
        ManifestEpisode(season=1, episode=1, title="Celebration"),
        ManifestEpisode(season=1, episode=2, title="Shit Show at the Fuck Factory"),
        ManifestEpisode(season=2, episode=1, title="The Summer Palace"),
    ]

    assert selected_manifest_episodes(episodes=episodes, season=1, episode=None) == episodes[:2]
    assert selected_manifest_episodes(episodes=episodes, season=1, episode=2) == [episodes[1]]


def test_episode_filter_requires_season() -> None:
    """Episode filters are invalid without a season."""
    with pytest.raises(ValueError, match="--episode requires --season"):
        selected_manifest_episodes(
            episodes=[ManifestEpisode(season=1, episode=1, title="Celebration")],
            season=None,
            episode=1,
        )


def test_extract_episode_writes_candidate_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Extraction writes the expected local manifest shape without content writes."""
    monkeypatch.setattr(screenshot_extraction, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(screenshot_extraction, "MEDIA_ROOT", tmp_path / ".local" / "media")
    monkeypatch.setattr(
        screenshot_extraction,
        "SCREENSHOT_ROOT",
        tmp_path / ".local" / "screenshots",
    )
    episode = ManifestEpisode(season=1, episode=2, title="Shit Show at the Fuck Factory")
    media_path = tmp_path / ".local" / "media" / "succession" / "s01" / "e02.mkv"
    media_path.parent.mkdir(parents=True)
    media_path.touch()

    monkeypatch.setattr(screenshot_extraction, "detect_episode_scenes", lambda **_: [])
    monkeypatch.setattr(
        screenshot_extraction,
        "save_scene_midpoints",
        lambda **_: [
            CandidateFrame(
                scene_number=1,
                image_path=".local/screenshots/succession/s01/e02/candidates/scene-0001.jpg",
                start_frame=10,
                end_frame=50,
                midpoint_frame=30,
                start_seconds=1.0,
                end_seconds=5.0,
                midpoint_seconds=3.0,
                start_timecode="00:00:01.000",
                end_timecode="00:00:05.000",
                midpoint_timecode="00:00:03.000",
            ),
        ],
    )

    manifest = extract_episode_screenshot_candidates(
        show=Show.SUCCESSION,
        episode=episode,
        settings=ExtractionSettings(threshold=31.0, min_scene_length=20, image_width=960),
    )

    manifest_path = candidate_manifest_path(show=Show.SUCCESSION, episode=episode)
    assert manifest_path.is_file()
    assert manifest.show == "succession"
    assert manifest.code == "S01E02"
    assert manifest.detector == {
        "name": "ContentDetector",
        "threshold": 31.0,
        "min_scene_length": 20,
    }
    assert manifest.image_settings == {
        "format": "jpg",
        "width": 960,
        "jpeg_quality": 90,
    }
    assert manifest.candidates[0].image_path.endswith("scene-0001.jpg")
