"""Post-processing filters for extracted screenshot candidates."""

from __future__ import annotations

import base64
import json
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np
from openai import OpenAI
from pydantic import BaseModel
from tqdm import tqdm

from screenshot_extraction import (
    candidate_dir_for_episode,
    episode_code,
    screenshot_root_for_episode,
)
from settings import settings as pipeline_settings

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from manifest import ManifestEpisode
    from schemas import Show

HASH_SIZE = 8
MODERATION_MODEL = "omni-moderation-latest"
MODERATION_REJECTED_CATEGORIES = ("sexual", "violence/graphic")


class FilteringSettings(BaseModel):
    """Settings for screenshot candidate filtering."""

    min_blur_score: float
    min_mean_luma: float
    max_mean_luma: float
    min_luma_stddev: float
    tile_grid_size: int
    duplicate_hash_distance: int


class FilteredCandidate(BaseModel):
    """Filtering result for one screenshot candidate."""

    source_path: str
    destination_path: str | None
    kept: bool
    tile_blur_score: float
    whole_frame_blur_score: float
    mean_luma: float
    luma_stddev: float
    hash: str
    moderation_flagged: bool | None = None
    moderation_rejected_categories: list[str]
    moderation_category_scores: dict[str, float]
    rejected_reason: str | None = None
    duplicate_of: str | None = None
    duplicate_hash_distance: int | None = None


class CandidateScores(BaseModel):
    """Computed image scores used for filtering decisions."""

    tile_blur_score: float
    mean_luma: float
    luma_stddev: float


class ModerationDecision(BaseModel):
    """Moderation result for one candidate image."""

    flagged: bool
    rejected_categories: list[str]
    category_scores: dict[str, float]


class FilteringReport(BaseModel):
    """Report for one screenshot candidate filtering run."""

    show: str
    season: int
    episode: int
    code: str
    settings: FilteringSettings
    source_count: int
    kept_count: int
    rejected_count: int
    results: list[FilteredCandidate]


def filter_episode_screenshot_candidates(
    *,
    show: Show,
    episode: ManifestEpisode,
    settings: FilteringSettings,
    overwrite: bool = False,
) -> FilteringReport:
    """Filter an episode's raw screenshot candidates into a local filtered folder."""
    source_dir = candidate_dir_for_episode(show=show, episode=episode)
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Missing screenshot candidate directory: {source_dir}")

    output_dir = filtered_dir_for_episode(show=show, episode=episode)
    if output_dir.exists():
        if not overwrite:
            raise FileExistsError(f"Filtered screenshot output already exists: {output_dir}")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    kept_hashes: list[tuple[int, str, int]] = []
    results = []
    image_paths = sorted(source_dir.glob("*.jpg"))
    for image_path in tqdm(
        image_paths, desc=f"Filtering {episode_code(episode=episode)}", unit="image"
    ):
        result, image_hash = evaluate_candidate(path=image_path, settings=settings)
        kept_hashes = resolve_duplicate_candidate(
            result=result,
            image_hash=image_hash,
            results=results,
            kept_hashes=kept_hashes,
            settings=settings,
        )
        results.append(result)
        if result.kept:
            kept_hashes.append((len(results) - 1, image_path.name, image_hash))

    for result in results:
        if result.kept:
            source = Path(result.source_path)
            destination = output_dir / source.name
            shutil.copy2(source, destination)
            result.destination_path = destination.as_posix()

    report = FilteringReport(
        show=show.value,
        season=episode.season,
        episode=episode.episode,
        code=episode_code(episode=episode),
        settings=settings,
        source_count=len(results),
        kept_count=sum(result.kept for result in results),
        rejected_count=sum(not result.kept for result in results),
        results=results,
    )
    write_filtering_report(report=report, path=filtering_report_path(show=show, episode=episode))
    return report


def filtered_dir_for_episode(*, show: Show, episode: ManifestEpisode) -> Path:
    """Return the filtered screenshot candidate directory for an episode."""
    return screenshot_root_for_episode(show=show, episode=episode) / "filtered"


def filtering_report_path(*, show: Show, episode: ManifestEpisode) -> Path:
    """Return the filtering report path for an episode."""
    return screenshot_root_for_episode(show=show, episode=episode) / "filtering_report.json"


def resolve_duplicate_candidate(
    *,
    result: FilteredCandidate,
    image_hash: int,
    results: list[FilteredCandidate],
    kept_hashes: list[tuple[int, str, int]],
    settings: FilteringSettings,
) -> list[tuple[int, str, int]]:
    """Update duplicate state so near-duplicate groups keep the sharpest candidate."""
    if result.rejected_reason is not None:
        return kept_hashes

    duplicate_index, duplicate_of, hash_distance = duplicate_match_for(
        image_hash=image_hash,
        kept_hashes=kept_hashes,
        settings=settings,
    )
    if duplicate_index is None:
        return kept_hashes

    duplicate = results[duplicate_index]
    if result.tile_blur_score <= duplicate.tile_blur_score:
        result.kept = False
        result.rejected_reason = "near_duplicate"
        result.duplicate_of = duplicate_of
        result.duplicate_hash_distance = hash_distance
        return kept_hashes

    duplicate.kept = False
    duplicate.destination_path = None
    duplicate.rejected_reason = "near_duplicate"
    duplicate.duplicate_of = Path(result.source_path).name
    duplicate.duplicate_hash_distance = hash_distance
    return [
        (index, name, kept_hash)
        for index, name, kept_hash in kept_hashes
        if index != duplicate_index
    ]


def evaluate_candidate(*, path: Path, settings: FilteringSettings) -> tuple[FilteredCandidate, int]:
    """Score one candidate and run mandatory moderation when local quality checks pass."""
    image = read_image(path=path)
    mean_luma, luma_stddev = luma_metrics_for(image=image)
    whole_frame_blur_score = whole_frame_blur_score_for(image=image)
    tile_blur_score = tile_blur_score_for(image=image, tile_grid_size=settings.tile_grid_size)
    image_hash = average_hash(image=image)
    rejected_reason = rejection_for(
        scores=CandidateScores(
            tile_blur_score=tile_blur_score,
            mean_luma=mean_luma,
            luma_stddev=luma_stddev,
        ),
        settings=settings,
    )
    moderation = None
    if rejected_reason is None:
        moderation = moderate_image(path=path)
        if moderation.rejected_categories:
            rejected_reason = "unsafe_content"

    return (
        FilteredCandidate(
            source_path=path.as_posix(),
            destination_path=None,
            kept=rejected_reason is None,
            tile_blur_score=round(tile_blur_score, 3),
            whole_frame_blur_score=round(whole_frame_blur_score, 3),
            mean_luma=round(mean_luma, 3),
            luma_stddev=round(luma_stddev, 3),
            hash=format_hash(image_hash),
            moderation_flagged=moderation.flagged if moderation else None,
            moderation_rejected_categories=moderation.rejected_categories if moderation else [],
            moderation_category_scores=moderation.category_scores if moderation else {},
            rejected_reason=rejected_reason,
        ),
        image_hash,
    )


def read_image(*, path: Path) -> NDArray[np.integer | np.floating]:
    """Read a local image with OpenCV."""
    image = cv2.imread(str(path))
    if image is None:
        raise RuntimeError(f"Could not read screenshot candidate: {path}")
    return image


def whole_frame_blur_score_for(*, image: NDArray[np.integer | np.floating]) -> float:
    """Return a whole-frame Laplacian-variance blur score."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def luma_metrics_for(*, image: NDArray[np.integer | np.floating]) -> tuple[float, float]:
    """Return mean and standard deviation for grayscale luma."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(gray.mean()), float(gray.std())


def tile_blur_score_for(
    *,
    image: NDArray[np.integer | np.floating],
    tile_grid_size: int,
) -> float:
    """Return the 80th percentile Laplacian variance across image tiles."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape[:2]
    tile_height = height // tile_grid_size
    tile_width = width // tile_grid_size
    if tile_height == 0 or tile_width == 0:
        return float(cv2.Laplacian(gray, cv2.CV_64F).var())

    scores = []
    for row in range(tile_grid_size):
        for column in range(tile_grid_size):
            y0 = row * tile_height
            x0 = column * tile_width
            y1 = height if row == tile_grid_size - 1 else y0 + tile_height
            x1 = width if column == tile_grid_size - 1 else x0 + tile_width
            tile = gray[y0:y1, x0:x1]
            scores.append(float(cv2.Laplacian(tile, cv2.CV_64F).var()))

    return float(np.percentile(scores, 80))


def average_hash(*, image: NDArray[np.integer | np.floating]) -> int:
    """Return a compact average hash for duplicate detection."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, (HASH_SIZE, HASH_SIZE), interpolation=cv2.INTER_AREA)
    threshold = resized.mean()
    bits = resized > threshold
    image_hash = 0
    for bit in bits.flatten():
        image_hash = (image_hash << 1) | int(bit)
    return image_hash


def moderate_image(*, path: Path) -> ModerationDecision:
    """Moderate one candidate image with OpenAI image moderation."""
    if not pipeline_settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is required for screenshot moderation. "
            "Set it in pipeline/.env before filtering screenshot candidates.",
        )

    data_url = f"data:image/jpeg;base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"
    response = OpenAI(api_key=pipeline_settings.openai_api_key).moderations.create(
        model=MODERATION_MODEL,
        input=[
            {
                "type": "image_url",
                "image_url": {"url": data_url},
            },
        ],
    )
    result = response.results[0]
    categories = result.categories.model_dump()
    category_scores = result.category_scores.model_dump()
    rejected_categories = [
        category for category in MODERATION_REJECTED_CATEGORIES if categories.get(category) is True
    ]

    return ModerationDecision(
        flagged=result.flagged,
        rejected_categories=rejected_categories,
        category_scores=category_scores,
    )


def rejection_for(
    *,
    scores: CandidateScores,
    settings: FilteringSettings,
) -> str | None:
    """Return a rejection decision for a candidate image."""
    if scores.mean_luma < settings.min_mean_luma:
        return "too_dark"

    if scores.mean_luma > settings.max_mean_luma:
        return "too_bright"

    if scores.luma_stddev < settings.min_luma_stddev:
        return "too_flat"

    if scores.tile_blur_score < settings.min_blur_score:
        return "blurry"

    return None


def duplicate_match_for(
    *,
    image_hash: int,
    kept_hashes: list[tuple[int, str, int]],
    settings: FilteringSettings,
) -> tuple[int | None, str | None, int | None]:
    """Return the first existing kept candidate close enough to count as a duplicate."""
    for result_index, kept_name, kept_hash in kept_hashes:
        distance = hamming_distance(image_hash, kept_hash)
        if distance <= settings.duplicate_hash_distance:
            return result_index, kept_name, distance

    return None, None, None


def hamming_distance(left: int, right: int) -> int:
    """Return the Hamming distance between two integer hashes."""
    return (left ^ right).bit_count()


def format_hash(image_hash: int) -> str:
    """Format an image hash as fixed-width hex."""
    return f"{image_hash:016x}"


def write_filtering_report(*, report: FilteringReport, path: Path) -> None:
    """Write a screenshot filtering report."""
    path.write_text(
        json.dumps(report.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
