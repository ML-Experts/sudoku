from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace

import numpy as np

from .models import (
    LineFamilyName,
    LineSegment,
    SegmentOrigin,
)


@dataclass(frozen=True)
class LineSegmentIntersectionResult:
    intersects: bool
    bridge_segment: LineSegment | None = None


def build_line_segment(raw_segment: np.ndarray) -> LineSegment:
    x1, y1, x2, y2 = (int(value) for value in raw_segment)
    delta_x = float(x2 - x1)
    delta_y = float(y2 - y1)
    return LineSegment(
        family_name=LineFamilyName.UNCLASSIFIED,
        start=(x1, y1),
        end=(x2, y2),
        length=float(np.hypot(delta_x, delta_y)),
        angle_degrees=float(np.degrees(np.arctan2(delta_y, delta_x)) % 180.0),
        origin=SegmentOrigin.RAW,
    )


def angle_difference_degrees(first_angle: float, second_angle: float) -> float:
    raw_difference = abs(first_angle - second_angle) % 180.0
    return min(raw_difference, 180.0 - raw_difference)


def signed_angle_offset_degrees(angle_degrees: float, reference_angle_degrees: float) -> float:
    return ((angle_degrees - reference_angle_degrees + 90.0) % 180.0) - 90.0


def classify_line_segment(
    line_segment: LineSegment,
    family_name: LineFamilyName,
) -> LineSegment:
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


def build_line_segment_from_points(
    start: tuple[int, int],
    end: tuple[int, int],
    family_name: LineFamilyName,
    origin: SegmentOrigin = SegmentOrigin.RAW,
) -> LineSegment:
    delta_x = float(end[0] - start[0])
    delta_y = float(end[1] - start[1])
    return classify_line_segment(
        LineSegment(
            family_name=family_name,
            start=start,
            end=end,
            length=float(np.hypot(delta_x, delta_y)),
            angle_degrees=float(np.degrees(np.arctan2(delta_y, delta_x)) % 180.0),
            origin=origin,
        ),
        family_name,
    )


def _build_tolerance_bridge_segment(
    first_segment: LineSegment,
    second_segment: LineSegment,
) -> LineSegment | None:
    leading_segment, trailing_segment = sorted(
        (first_segment, second_segment),
        key=lambda current_segment: (
            current_segment.axis_start,
            current_segment.axis_end,
        ),
    )
    axis_gap = trailing_segment.axis_start - leading_segment.axis_end
    if axis_gap <= 0:
        return None

    return build_line_segment_from_points(
        start=leading_segment.end,
        end=trailing_segment.start,
        family_name=leading_segment.family_name,
        origin=SegmentOrigin.SAME_AXIS_CONNECTION,
    )


def _get_cross_axis_distance(
    first_segment: LineSegment,
    second_segment: LineSegment,
) -> int:
    first_cross_min = min(
        first_segment.cross_axis_start,
        first_segment.cross_axis_end,
    )
    first_cross_max = max(
        first_segment.cross_axis_start,
        first_segment.cross_axis_end,
    )
    second_cross_min = min(
        second_segment.cross_axis_start,
        second_segment.cross_axis_end,
    )
    second_cross_max = max(
        second_segment.cross_axis_start,
        second_segment.cross_axis_end,
    )

    if first_cross_max < second_cross_min:
        return second_cross_min - first_cross_max
    if second_cross_max < first_cross_min:
        return first_cross_min - second_cross_max
    return 0


def line_segments_intersect(
    first_segment: LineSegment,
    second_segment: LineSegment,
    cross_axis_thickness_px: int = 0,
    axis_gap_tolerance_px: int = 0,
) -> LineSegmentIntersectionResult:
    if first_segment.family_name != second_segment.family_name:
        return LineSegmentIntersectionResult(intersects=False)
    if (
        first_segment.family_name == LineFamilyName.UNCLASSIFIED
        or second_segment.family_name == LineFamilyName.UNCLASSIFIED
    ):
        return LineSegmentIntersectionResult(intersects=False)

    cross_axis_distance = _get_cross_axis_distance(first_segment, second_segment)
    if cross_axis_distance > cross_axis_thickness_px:
        return LineSegmentIntersectionResult(intersects=False)

    leading_segment, trailing_segment = sorted(
        (first_segment, second_segment),
        key=lambda current_segment: (
            current_segment.axis_start,
            current_segment.axis_end,
        ),
    )
    axis_gap = trailing_segment.axis_start - leading_segment.axis_end
    if axis_gap > axis_gap_tolerance_px:
        return LineSegmentIntersectionResult(intersects=False)

    bridge_segment = _build_tolerance_bridge_segment(
        leading_segment,
        trailing_segment,
    )
    return LineSegmentIntersectionResult(
        intersects=True,
        bridge_segment=bridge_segment,
    )


__all__ = [
    "angle_difference_degrees",
    "build_line_segment",
    "build_line_segment_from_points",
    "classify_line_segment",
    "LineSegmentIntersectionResult",
    "line_segments_intersect",
    "signed_angle_offset_degrees",
]
