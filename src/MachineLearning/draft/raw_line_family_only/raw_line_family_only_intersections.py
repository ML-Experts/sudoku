from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from raw_line_family_only_logical_line_core import LogicalLine
from raw_line_family_only_models import LineFamilyName, LineSegment


_EPSILON = 1e-6


class LogicalLineIntersectionKind(Enum):
    CROSS = "cross"
    TOUCH = "touch"


@dataclass(frozen=True, slots=True)
class LogicalLineIntersection:
    horizontal_line_index: int
    vertical_line_index: int
    horizontal_segment_index: int
    vertical_segment_index: int
    point: tuple[int, int]
    kind: LogicalLineIntersectionKind


def _cross_product(
    first_vector: tuple[float, float],
    second_vector: tuple[float, float],
) -> float:
    return (
        first_vector[0] * second_vector[1]
        - first_vector[1] * second_vector[0]
    )


def _subtract_points(
    first_point: tuple[int, int],
    second_point: tuple[int, int],
) -> tuple[float, float]:
    return (
        float(first_point[0] - second_point[0]),
        float(first_point[1] - second_point[1]),
    )


def _is_point_on_segment(
    point: tuple[int, int],
    line_segment: LineSegment,
) -> bool:
    x, y = point
    x1, y1 = line_segment.start
    x2, y2 = line_segment.end

    cross_value = (x - x1) * (y2 - y1) - (y - y1) * (x2 - x1)
    if abs(cross_value) > _EPSILON:
        return False

    min_x = min(x1, x2) - _EPSILON
    max_x = max(x1, x2) + _EPSILON
    min_y = min(y1, y2) - _EPSILON
    max_y = max(y1, y2) + _EPSILON
    return min_x <= x <= max_x and min_y <= y <= max_y


def _is_endpoint_intersection(
    t_value: float,
    u_value: float,
) -> bool:
    return (
        abs(t_value) <= _EPSILON
        or abs(t_value - 1.0) <= _EPSILON
        or abs(u_value) <= _EPSILON
        or abs(u_value - 1.0) <= _EPSILON
    )


def find_segment_intersection(
    horizontal_segment: LineSegment,
    vertical_segment: LineSegment,
) -> tuple[tuple[int, int], LogicalLineIntersectionKind] | None:
    if horizontal_segment.family_name != LineFamilyName.HORIZONTAL:
        raise ValueError("horizontal_segment must belong to the horizontal family.")
    if vertical_segment.family_name != LineFamilyName.VERTICAL:
        raise ValueError("vertical_segment must belong to the vertical family.")

    horizontal_start = horizontal_segment.start
    vertical_start = vertical_segment.start
    horizontal_vector = _subtract_points(horizontal_segment.end, horizontal_start)
    vertical_vector = _subtract_points(vertical_segment.end, vertical_start)
    cross_value = _cross_product(horizontal_vector, vertical_vector)
    offset_vector = _subtract_points(vertical_start, horizontal_start)

    if abs(cross_value) <= _EPSILON:
        shared_points = [
            point
            for point in (
                horizontal_segment.start,
                horizontal_segment.end,
                vertical_segment.start,
                vertical_segment.end,
            )
            if (
                _is_point_on_segment(point, horizontal_segment)
                and _is_point_on_segment(point, vertical_segment)
            )
        ]
        if not shared_points:
            return None

        first_shared_point = min(shared_points)
        return first_shared_point, LogicalLineIntersectionKind.TOUCH

    t_value = _cross_product(offset_vector, vertical_vector) / cross_value
    u_value = _cross_product(offset_vector, horizontal_vector) / cross_value
    if not (
        -_EPSILON <= t_value <= 1.0 + _EPSILON
        and -_EPSILON <= u_value <= 1.0 + _EPSILON
    ):
        return None

    intersection_x = horizontal_start[0] + horizontal_vector[0] * t_value
    intersection_y = horizontal_start[1] + horizontal_vector[1] * t_value
    intersection_point = (
        int(round(intersection_x)),
        int(round(intersection_y)),
    )
    if _is_endpoint_intersection(t_value, u_value):
        return intersection_point, LogicalLineIntersectionKind.TOUCH
    return intersection_point, LogicalLineIntersectionKind.CROSS


def find_first_logical_line_intersection(
    horizontal_line: LogicalLine,
    vertical_line: LogicalLine,
    horizontal_line_index: int,
    vertical_line_index: int,
) -> LogicalLineIntersection | None:
    if horizontal_line.family_name != LineFamilyName.HORIZONTAL:
        raise ValueError("horizontal_line must belong to the horizontal family.")
    if vertical_line.family_name != LineFamilyName.VERTICAL:
        raise ValueError("vertical_line must belong to the vertical family.")

    for horizontal_segment_index, horizontal_segment in enumerate(
        horizontal_line.line_segments
    ):
        for vertical_segment_index, vertical_segment in enumerate(
            vertical_line.line_segments
        ):
            intersection_result = find_segment_intersection(
                horizontal_segment,
                vertical_segment,
            )
            if intersection_result is None:
                continue

            intersection_point, intersection_kind = intersection_result
            return LogicalLineIntersection(
                horizontal_line_index=horizontal_line_index,
                vertical_line_index=vertical_line_index,
                horizontal_segment_index=horizontal_segment_index,
                vertical_segment_index=vertical_segment_index,
                point=intersection_point,
                kind=intersection_kind,
            )

    return None


def find_logical_line_intersections(
    horizontal_logical_lines: list[LogicalLine],
    vertical_logical_lines: list[LogicalLine],
) -> list[LogicalLineIntersection]:
    intersections: list[LogicalLineIntersection] = []
    for horizontal_line_index, horizontal_line in enumerate(horizontal_logical_lines):
        for vertical_line_index, vertical_line in enumerate(vertical_logical_lines):
            intersection = find_first_logical_line_intersection(
                horizontal_line,
                vertical_line,
                horizontal_line_index=horizontal_line_index,
                vertical_line_index=vertical_line_index,
            )
            if intersection is not None:
                intersections.append(intersection)

    return intersections


__all__ = [
    "LogicalLineIntersection",
    "LogicalLineIntersectionKind",
    "find_first_logical_line_intersection",
    "find_logical_line_intersections",
    "find_segment_intersection",
]
