from __future__ import annotations

import numpy as np

from raw_line_family_only_models import DetectedLineSegment


def build_line_segment(raw_segment: np.ndarray) -> DetectedLineSegment:
    x1, y1, x2, y2 = (int(value) for value in raw_segment)
    delta_x = float(x2 - x1)
    delta_y = float(y2 - y1)
    return DetectedLineSegment(
        start=(x1, y1),
        end=(x2, y2),
        length=float(np.hypot(delta_x, delta_y)),
        angle_degrees=float(np.degrees(np.arctan2(delta_y, delta_x)) % 180.0),
    )


def angle_difference_degrees(first_angle: float, second_angle: float) -> float:
    raw_difference = abs(first_angle - second_angle) % 180.0
    return min(raw_difference, 180.0 - raw_difference)


def signed_angle_offset_degrees(angle_degrees: float, reference_angle_degrees: float) -> float:
    return ((angle_degrees - reference_angle_degrees + 90.0) % 180.0) - 90.0


__all__ = [
    "angle_difference_degrees",
    "build_line_segment",
    "signed_angle_offset_degrees",
]
