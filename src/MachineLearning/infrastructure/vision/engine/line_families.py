from __future__ import annotations

import numpy as np

from .geometry import angle_difference_degrees
from .models import LineSegment


def get_dominant_angle_degrees(
    line_segments: list[LineSegment],
) -> float | None:
    if not line_segments:
        return None

    angle_histogram = np.zeros(180, dtype=np.float32)
    for line_segment in line_segments:
        angle_bucket = int(round(line_segment.angle_degrees)) % 180
        angle_histogram[angle_bucket] += line_segment.length
    return float(np.argmax(angle_histogram))


def refine_family_angle_degrees(
    line_segments: list[LineSegment],
    fallback_angle_degrees: float,
) -> float:
    if not line_segments:
        return float(fallback_angle_degrees)

    doubled_angles_radians = np.deg2rad(
        [2.0 * line_segment.angle_degrees for line_segment in line_segments]
    )
    weights = np.array(
        [max(line_segment.length, 1e-3) for line_segment in line_segments],
        dtype=np.float32,
    )
    sin_sum = float(np.sum(np.sin(doubled_angles_radians) * weights))
    cos_sum = float(np.sum(np.cos(doubled_angles_radians) * weights))
    if abs(sin_sum) <= 1e-6 and abs(cos_sum) <= 1e-6:
        return float(fallback_angle_degrees)

    return float(
        (np.degrees(np.arctan2(sin_sum, cos_sum)) / 2.0) % 180.0
    )


def collect_line_family(
    line_segments: list[LineSegment],
    target_angle_degrees: float,
    angle_tolerance_degrees: float,
) -> list[LineSegment]:
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
    "refine_family_angle_degrees",
]
