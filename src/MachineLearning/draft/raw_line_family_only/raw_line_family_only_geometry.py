from __future__ import annotations

from dataclasses import replace

import numpy as np

from raw_line_family_only_models import DetectedLineSegment, LineFamilyName


def build_line_segment(raw_segment: np.ndarray) -> DetectedLineSegment:
    x1, y1, x2, y2 = (int(value) for value in raw_segment)
    delta_x = float(x2 - x1)
    delta_y = float(y2 - y1)
    return DetectedLineSegment(
        family_name=LineFamilyName.UNCLASSIFIED,
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


def classify_line_segment(
    line_segment: DetectedLineSegment,
    family_name: LineFamilyName,
) -> DetectedLineSegment:
    normalized_start = line_segment.start
    normalized_end = line_segment.end

    if family_name == LineFamilyName.HORIZONTAL and normalized_start[0] > normalized_end[0]:
        normalized_start, normalized_end = normalized_end, normalized_start
    elif family_name == LineFamilyName.VERTICAL and normalized_start[1] > normalized_end[1]:
        normalized_start, normalized_end = normalized_end, normalized_start

    return replace(
        line_segment,
        family_name=family_name,
        start=normalized_start,
        end=normalized_end,
    )


def line_segments_intersect(
    first_segment: DetectedLineSegment,
    second_segment: DetectedLineSegment,
) -> bool:
    first_start = first_segment.start
    first_end = first_segment.end
    second_start = second_segment.start
    second_end = second_segment.end

    def orientation(
        first_point: tuple[int, int],
        second_point: tuple[int, int],
        third_point: tuple[int, int],
    ) -> int:
        value = (
            (second_point[1] - first_point[1]) * (third_point[0] - second_point[0])
            - (second_point[0] - first_point[0]) * (third_point[1] - second_point[1])
        )
        if value == 0:
            return 0
        return 1 if value > 0 else 2

    def is_on_segment(
        first_point: tuple[int, int],
        second_point: tuple[int, int],
        third_point: tuple[int, int],
    ) -> bool:
        return (
            min(first_point[0], third_point[0]) <= second_point[0] <= max(first_point[0], third_point[0])
            and min(first_point[1], third_point[1]) <= second_point[1] <= max(first_point[1], third_point[1])
        )

    first_orientation = orientation(first_start, first_end, second_start)
    second_orientation = orientation(first_start, first_end, second_end)
    third_orientation = orientation(second_start, second_end, first_start)
    fourth_orientation = orientation(second_start, second_end, first_end)

    if first_orientation != second_orientation and third_orientation != fourth_orientation:
        return True

    if first_orientation == 0 and is_on_segment(first_start, second_start, first_end):
        return True
    if second_orientation == 0 and is_on_segment(first_start, second_end, first_end):
        return True
    if third_orientation == 0 and is_on_segment(second_start, first_start, second_end):
        return True
    if fourth_orientation == 0 and is_on_segment(second_start, first_end, second_end):
        return True

    return False


__all__ = [
    "angle_difference_degrees",
    "build_line_segment",
    "classify_line_segment",
    "line_segments_intersect",
    "signed_angle_offset_degrees",
]
