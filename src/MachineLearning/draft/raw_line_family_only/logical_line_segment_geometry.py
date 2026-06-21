from __future__ import annotations

from geometry import build_line_segment_from_points
from models import LineFamilyName, LineSegment


def rasterize_line_points(
    start: tuple[int, int],
    end: tuple[int, int],
) -> list[tuple[int, int]]:
    delta_x = end[0] - start[0]
    delta_y = end[1] - start[1]
    step_count = max(abs(delta_x), abs(delta_y))
    if step_count == 0:
        return [start]

    points: list[tuple[int, int]] = []
    for step_index in range(step_count + 1):
        ratio = step_index / float(step_count)
        point = (
            int(round(start[0] + delta_x * ratio)),
            int(round(start[1] + delta_y * ratio)),
        )
        if not points or points[-1] != point:
            points.append(point)
    return points


def point_axis_value(
    family_name: LineFamilyName,
    point: tuple[int, int],
) -> int:
    if family_name == LineFamilyName.HORIZONTAL:
        return point[0]
    if family_name == LineFamilyName.VERTICAL:
        return point[1]
    raise NotImplementedError("Point axis value is available only for classified lines.")


def supporting_line_intersection_point(
    first_segment: LineSegment,
    second_segment: LineSegment,
) -> tuple[float, float] | None:
    x1, y1 = first_segment.start
    x2, y2 = first_segment.end
    x3, y3 = second_segment.start
    x4, y4 = second_segment.end
    denominator = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(float(denominator)) <= 1e-6:
        return None

    determinant_first = x1 * y2 - y1 * x2
    determinant_second = x3 * y4 - y3 * x4
    intersection_x = (
        determinant_first * (x3 - x4) - (x1 - x2) * determinant_second
    ) / float(denominator)
    intersection_y = (
        determinant_first * (y3 - y4) - (y1 - y2) * determinant_second
    ) / float(denominator)
    return float(intersection_x), float(intersection_y)


def point_on_segment_axis(
    line_segment: LineSegment,
    axis_value: int,
) -> tuple[int, int]:
    if line_segment.family_name == LineFamilyName.HORIZONTAL:
        axis_start = line_segment.start[0]
        axis_end = line_segment.end[0]
        if axis_end == axis_start:
            return line_segment.start
        ratio = (axis_value - axis_start) / float(axis_end - axis_start)
        return (
            int(axis_value),
            int(
                round(
                    line_segment.start[1]
                    + (line_segment.end[1] - line_segment.start[1]) * ratio
                )
            ),
        )

    if line_segment.family_name == LineFamilyName.VERTICAL:
        axis_start = line_segment.start[1]
        axis_end = line_segment.end[1]
        if axis_end == axis_start:
            return line_segment.start
        ratio = (axis_value - axis_start) / float(axis_end - axis_start)
        return (
            int(
                round(
                    line_segment.start[0]
                    + (line_segment.end[0] - line_segment.start[0]) * ratio
                )
            ),
            int(axis_value),
        )

    raise NotImplementedError(
        "Point interpolation is available only for classified segments."
    )


def rebuild_segment_axis_range(
    line_segment: LineSegment,
    axis_start: int | None = None,
    axis_end: int | None = None,
) -> LineSegment | None:
    updated_axis_start = line_segment.axis_start if axis_start is None else int(axis_start)
    updated_axis_end = line_segment.axis_end if axis_end is None else int(axis_end)
    if updated_axis_start >= updated_axis_end:
        return None

    updated_start = (
        line_segment.start
        if axis_start is None
        else point_on_segment_axis(line_segment, updated_axis_start)
    )
    updated_end = (
        line_segment.end
        if axis_end is None
        else point_on_segment_axis(line_segment, updated_axis_end)
    )
    repaired_segment = build_line_segment_from_points(
        start=updated_start,
        end=updated_end,
        family_name=line_segment.family_name,
        origin=line_segment.origin,
    )
    if repaired_segment.length <= 0.0:
        return None
    return repaired_segment


__all__ = [
    "point_axis_value",
    "point_on_segment_axis",
    "rasterize_line_points",
    "rebuild_segment_axis_range",
    "supporting_line_intersection_point",
]
