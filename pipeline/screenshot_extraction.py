"""Screenshot candidate extraction from local episode media."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, cast

import cv2
from pydantic import BaseModel
from scenedetect import ContentDetector, SceneManager, open_video

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray

    from manifest import ManifestEpisode
    from schemas import Show

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCAL_ROOT = REPO_ROOT / ".local"
MEDIA_ROOT = LOCAL_ROOT / "media"
SCREENSHOT_ROOT = LOCAL_ROOT / "screenshots"
SUPPORTED_MEDIA_EXTENSIONS = [".mkv", ".mp4", ".mov", ".m4v"]
JPEG_QUALITY = 90


class SceneTimecode(Protocol):
    """FrameTimecode surface used by the extraction pipeline."""

    frame_num: int
    seconds: float

    def get_timecode(self) -> str:
        """Return an HH:MM:SS.mmm timecode."""


type SceneRange = tuple[SceneTimecode, SceneTimecode]


class CandidateFrame(BaseModel):
    """One extracted screenshot candidate."""

    scene_number: int
    image_path: str
    start_frame: int
    end_frame: int
    midpoint_frame: int
    start_seconds: float
    end_seconds: float
    midpoint_seconds: float
    start_timecode: str
    end_timecode: str
    midpoint_timecode: str


class ExtractionSettings(BaseModel):
    """Scene detection and image extraction settings."""

    threshold: float
    min_scene_length: int
    image_width: int


class CandidateManifest(BaseModel):
    """Manifest for extracted screenshot candidates."""

    show: str
    season: int
    episode: int
    code: str
    title: str
    source_video: str
    detector: dict[str, float | int | str]
    image_settings: dict[str, int | str]
    candidates: list[CandidateFrame]


def extract_episode_screenshot_candidates(
    *,
    show: Show,
    episode: ManifestEpisode,
    settings: ExtractionSettings,
    overwrite: bool = False,
) -> CandidateManifest:
    """Extract reusable screenshot candidates for one episode."""
    output_root = screenshot_root_for_episode(show=show, episode=episode)
    manifest_path = candidate_manifest_path(show=show, episode=episode)
    if output_root.exists() and not overwrite:
        if manifest_path.is_file():
            return CandidateManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
        raise FileExistsError(f"Screenshot output already exists without a manifest: {output_root}")

    if overwrite and output_root.exists():
        shutil.rmtree(output_root)

    video_path = media_path_for_episode(show=show, episode=episode)
    sys.stdout.write(f"  media: {video_path.relative_to(REPO_ROOT).as_posix()}\n")
    sys.stdout.write("  detecting scenes...\n")
    candidate_dir = candidate_dir_for_episode(show=show, episode=episode)
    candidate_dir.mkdir(parents=True, exist_ok=True)
    scenes = detect_episode_scenes(
        video_path=video_path,
        threshold=settings.threshold,
        min_scene_length=settings.min_scene_length,
    )
    sys.stdout.write(f"  detected {len(scenes)} scenes\n")
    sys.stdout.write("  writing midpoint frames...\n")
    candidates = save_scene_midpoints(
        video_path=video_path,
        scenes=scenes,
        output_dir=candidate_dir,
        image_width=settings.image_width,
    )
    manifest = CandidateManifest(
        show=show.value,
        season=episode.season,
        episode=episode.episode,
        code=episode_code(episode=episode),
        title=episode.title,
        source_video=video_path.relative_to(REPO_ROOT).as_posix(),
        detector={
            "name": "ContentDetector",
            "threshold": settings.threshold,
            "min_scene_length": settings.min_scene_length,
        },
        image_settings={
            "format": "jpg",
            "width": settings.image_width,
            "jpeg_quality": JPEG_QUALITY,
        },
        candidates=candidates,
    )
    write_candidate_manifest(manifest=manifest, path=manifest_path)
    return manifest


def selected_manifest_episodes(
    *,
    episodes: list[ManifestEpisode],
    season: int | None,
    episode: int | None,
) -> list[ManifestEpisode]:
    """Return manifest episodes selected by optional season and episode filters."""
    if episode is not None and season is None:
        raise ValueError("--episode requires --season.")

    selected = []
    for manifest_episode in episodes:
        if season is not None and manifest_episode.season != season:
            continue
        if episode is not None and manifest_episode.episode != episode:
            continue
        selected.append(manifest_episode)

    if not selected:
        raise ValueError("No manifest episodes matched the requested filters.")

    return selected


def media_path_for_episode(*, show: Show, episode: ManifestEpisode) -> Path:
    """Resolve the local media path for an episode."""
    media_dir = MEDIA_ROOT / show.value / f"s{episode.season:02}"
    media_stem = f"e{episode.episode:02}"
    for extension in SUPPORTED_MEDIA_EXTENSIONS:
        path = media_dir / f"{media_stem}{extension}"
        if path.is_file():
            return path

    expected = ", ".join(
        (media_dir / f"{media_stem}{extension}").relative_to(REPO_ROOT).as_posix()
        for extension in SUPPORTED_MEDIA_EXTENSIONS
    )
    raise FileNotFoundError(
        f"Missing local media for {episode_code(episode=episode)}. Expected: {expected}",
    )


def screenshot_root_for_episode(*, show: Show, episode: ManifestEpisode) -> Path:
    """Return the local screenshot root for an episode."""
    return SCREENSHOT_ROOT / show.value / f"s{episode.season:02}" / f"e{episode.episode:02}"


def candidate_dir_for_episode(*, show: Show, episode: ManifestEpisode) -> Path:
    """Return the screenshot candidate directory for an episode."""
    return screenshot_root_for_episode(show=show, episode=episode) / "candidates"


def candidate_manifest_path(*, show: Show, episode: ManifestEpisode) -> Path:
    """Return the screenshot candidate manifest path for an episode."""
    return screenshot_root_for_episode(show=show, episode=episode) / "candidate_manifest.json"


def detect_episode_scenes(
    *,
    video_path: Path,
    threshold: float,
    min_scene_length: int,
) -> list[SceneRange]:
    """Detect scene ranges from a local episode video."""
    video = open_video(video_path)
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=threshold, min_scene_len=min_scene_length))
    scene_manager.detect_scenes(video=video, show_progress=True)
    return cast("list[SceneRange]", scene_manager.get_scene_list())


def save_scene_midpoints(
    *,
    video_path: Path,
    scenes: list[SceneRange],
    output_dir: Path,
    image_width: int,
) -> list[CandidateFrame]:
    """Save one midpoint screenshot for each detected scene."""
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise RuntimeError(f"Could not open video for frame extraction: {video_path}")

    candidates = []
    try:
        for index, scene in enumerate(scenes, start=1):
            if index == 1 or index == len(scenes) or index % 25 == 0:
                sys.stdout.write(f"    frame {index}/{len(scenes)}\n")
            start, end = scene
            midpoint_frame = start.frame_num + max((end.frame_num - start.frame_num) // 2, 0)
            capture.set(cv2.CAP_PROP_POS_FRAMES, midpoint_frame)
            ok, frame = capture.read()
            if not ok:
                raise RuntimeError(f"Could not read frame {midpoint_frame} from {video_path}")

            frame = resize_frame(frame=frame, image_width=image_width)
            image_path = output_dir / f"scene-{index:04}.jpg"
            cv2.imwrite(str(image_path), frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
            candidates.append(
                CandidateFrame(
                    scene_number=index,
                    image_path=image_path.relative_to(REPO_ROOT).as_posix(),
                    start_frame=start.frame_num,
                    end_frame=end.frame_num,
                    midpoint_frame=midpoint_frame,
                    start_seconds=round(start.seconds, 3),
                    end_seconds=round(end.seconds, 3),
                    midpoint_seconds=round((start.seconds + end.seconds) / 2, 3),
                    start_timecode=start.get_timecode(),
                    end_timecode=end.get_timecode(),
                    midpoint_timecode=format_seconds((start.seconds + end.seconds) / 2),
                ),
            )
    finally:
        capture.release()

    return candidates


def write_candidate_manifest(*, manifest: CandidateManifest, path: Path) -> None:
    """Write a candidate manifest."""
    path.write_text(
        json.dumps(manifest.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def episode_code(*, episode: ManifestEpisode) -> str:
    """Return the display code for an episode."""
    return f"S{episode.season:02}E{episode.episode:02}"


def resize_frame(
    *,
    frame: NDArray[np.integer | np.floating],
    image_width: int,
) -> NDArray[np.integer | np.floating]:
    """Resize a frame while preserving aspect ratio."""
    height, width = frame.shape[:2]
    if width <= image_width:
        return frame

    scale = image_width / width
    return cv2.resize(frame, (image_width, round(height * scale)), interpolation=cv2.INTER_AREA)


def format_seconds(seconds: float) -> str:
    """Format seconds as HH:MM:SS.mmm."""
    milliseconds = round(seconds * 1000)
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    whole_seconds, milliseconds = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{whole_seconds:02}.{milliseconds:03}"
