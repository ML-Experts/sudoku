from __future__ import annotations

import numpy as np

from sudoku_board_threshold_line_geometry import angle_difference_degrees
from sudoku_board_threshold_models import DetectedLineSegment


def get_dominant_angle_degrees(
    line_segments: list[DetectedLineSegment],
) -> float | None:
    if not line_segments:
        return None

    angle_histogram = np.zeros(180, dtype=np.float32)
    for line_segment in line_segments:
        angle_bucket = int(round(line_segment.angle_degrees)) % 180
        angle_histogram[angle_bucket] += line_segment.length
    return float(np.argmax(angle_histogram))


def collect_line_family(
    line_segments: list[DetectedLineSegment],
    target_angle_degrees: float,
    angle_tolerance_degrees: float,
) -> list[DetectedLineSegment]:
    return [
        line_segment
        for line_segment in line_segments
        if angle_difference_degrees(
            line_segment.angle_degrees,
            target_angle_degrees,
        )
        <= angle_tolerance_degrees
    ]


def is_horizontal_like(angle_degrees: float) -> bool:
    return angle_difference_degrees(angle_degrees, 0.0) <= angle_difference_degrees(
        angle_degrees,
        90.0,
    )


__all__ = [
    "collect_line_family",
    "get_dominant_angle_degrees",
    "is_horizontal_like",
]
