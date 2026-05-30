from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from raw_line_family_only_line_families import (
    collect_line_family,
    get_dominant_angle_degrees,
    is_horizontal_like,
    refine_family_angle_degrees,
)
from raw_line_family_only_geometry import (
    angle_difference_degrees,
    build_line_segment,
    signed_angle_offset_degrees,
)
from raw_line_family_only_models import DetectedLineSegment, ExperimentConfig


@dataclass(frozen=True)
class RawLineFamilyResult:
    raw_segment_count: int
    orientation_offset_degrees: float | None
    horizontal_angle_degrees: float | None
    vertical_angle_degrees: float | None
    horizontal_segments: list[DetectedLineSegment]
    vertical_segments: list[DetectedLineSegment]


def _build_empty_line_family_result(
) -> RawLineFamilyResult:
    return RawLineFamilyResult(
        raw_segment_count=0,
        orientation_offset_degrees=None,
        horizontal_angle_degrees=None,
        vertical_angle_degrees=None,
        horizontal_segments=[],
        vertical_segments=[],
    )


def _estimate_orientation_offset_degrees(
    line_segments: list[DetectedLineSegment],
    angle_tolerance_degrees: float,
) -> float | None:
    dominant_seed_angle = get_dominant_angle_degrees(line_segments)
    if dominant_seed_angle is None:
        return None

    dominant_segments = collect_line_family(
        line_segments,
        dominant_seed_angle,
        angle_tolerance_degrees,
    )
    dominant_angle = refine_family_angle_degrees(
        dominant_segments,
        dominant_seed_angle,
    )
    if is_horizontal_like(dominant_angle):
        return signed_angle_offset_degrees(dominant_angle, 0.0)

    return signed_angle_offset_degrees(dominant_angle, 90.0)


def _collect_family_by_reference_angle(
    line_segments: list[DetectedLineSegment],
    family_reference_angle_degrees: float,
    opposite_reference_angle_degrees: float,
    angle_tolerance_degrees: float,
) -> list[DetectedLineSegment]:
    family_segments: list[DetectedLineSegment] = []
    for line_segment in line_segments:
        family_angle_difference = angle_difference_degrees(
            line_segment.angle_degrees,
            family_reference_angle_degrees,
        )
        opposite_angle_difference = angle_difference_degrees(
            line_segment.angle_degrees,
            opposite_reference_angle_degrees,
        )
        if (
            family_angle_difference <= angle_tolerance_degrees
            and family_angle_difference <= opposite_angle_difference
        ):
            family_segments.append(line_segment)

    return family_segments


def detect_line_families(
    binary_image: np.ndarray,
    config: ExperimentConfig,
) -> RawLineFamilyResult:
    minimum_dimension = min(binary_image.shape[:2])
    min_line_length_px = max(
        8,
        int(round(minimum_dimension * config.raw_min_line_length_ratio)),
    )
    max_line_gap_px = max(
        2,
        int(round(minimum_dimension * config.raw_max_line_gap_ratio)),
    )

    raw_segments = cv2.HoughLinesP(
        binary_image,
        rho=1,
        theta=np.pi / 180.0,
        threshold=config.raw_hough_threshold,
        minLineLength=min_line_length_px,
        maxLineGap=max_line_gap_px,
    )
    if raw_segments is None:
        return _build_empty_line_family_result()

    line_segments = [build_line_segment(raw_segment[0]) for raw_segment in raw_segments]
    orientation_offset_degrees = _estimate_orientation_offset_degrees(
        line_segments,
        config.line_family_angle_tolerance_degrees,
    )
    if orientation_offset_degrees is None:
        return _build_empty_line_family_result()

    horizontal_reference_angle = orientation_offset_degrees % 180.0
    vertical_reference_angle = (horizontal_reference_angle + 90.0) % 180.0
    horizontal_segments = _collect_family_by_reference_angle(
        line_segments,
        horizontal_reference_angle,
        vertical_reference_angle,
        config.line_family_angle_tolerance_degrees,
    )
    vertical_segments = _collect_family_by_reference_angle(
        line_segments,
        vertical_reference_angle,
        horizontal_reference_angle,
        config.line_family_angle_tolerance_degrees,
    )
    horizontal_angle_degrees = refine_family_angle_degrees(
        horizontal_segments,
        horizontal_reference_angle,
    )
    vertical_angle_degrees = refine_family_angle_degrees(
        vertical_segments,
        vertical_reference_angle,
    )

    return RawLineFamilyResult(
        raw_segment_count=len(line_segments),
        orientation_offset_degrees=orientation_offset_degrees,
        horizontal_angle_degrees=horizontal_angle_degrees,
        vertical_angle_degrees=vertical_angle_degrees,
        horizontal_segments=horizontal_segments,
        vertical_segments=vertical_segments,
    )


__all__ = [
    "RawLineFamilyResult",
    "detect_line_families",
]
