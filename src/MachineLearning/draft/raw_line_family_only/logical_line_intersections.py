from __future__ import annotations

from dataclasses import dataclass

from intersection_models import (
    IntersectionOrder,
    LogicalLineIntersection,
    LogicalLineIntersectionKind,
)
from logical_line_core import LogicalLine
from logical_line_segment_geometry import (
    point_on_segment_axis,
    supporting_line_intersection_point,
)
from models import LineFamilyName, LineSegment, SegmentOrigin


@dataclass(frozen=True, slots=True)
class _SegmentPairIntersectionCandidate:
    horizontal_line: LogicalLine
    vertical_line: LogicalLine
    horizontal_segment: LineSegment
    vertical_segment: LineSegment
    point: tuple[int, int]
    kind: LogicalLineIntersectionKind

    @property
    def selection_key(self) -> tuple[int, int, float]:
        return (
            0 if self.kind == LogicalLineIntersectionKind.CROSS else 1,
            _segment_origin_priority(self.horizontal_segment.origin)
            + _segment_origin_priority(self.vertical_segment.origin),
            -(self.horizontal_segment.length + self.vertical_segment.length),
        )


def _segment_origin_priority(segment_origin: SegmentOrigin) -> int:
    if segment_origin == SegmentOrigin.RAW:
        return 0
    if segment_origin == SegmentOrigin.SAME_AXIS_CONNECTION:
        return 1
    if segment_origin == SegmentOrigin.CROSS_AXIS_CONNECTION:
        return 2
    return 3


def _classify_segment_order(
    line_segment: LineSegment,
    point: tuple[int, int],
) -> IntersectionOrder:
    axis_value = _point_axis_value_for_segment(line_segment, point)
    if (
        axis_value == line_segment.axis_start
        and axis_value == line_segment.axis_end
    ):
        return IntersectionOrder.BOTH
    if axis_value == line_segment.axis_start:
        return IntersectionOrder.START
    if axis_value == line_segment.axis_end:
        return IntersectionOrder.END
    return IntersectionOrder.MIDDLE


def _is_point_within_segment_axis(
    line_segment: LineSegment,
    point: tuple[int, int],
) -> bool:
    axis_value = _point_axis_value_for_segment(line_segment, point)
    return line_segment.axis_start <= axis_value <= line_segment.axis_end


def _point_axis_value_for_segment(
    line_segment: LineSegment,
    point: tuple[int, int],
) -> int:
    if line_segment.family_name == LineFamilyName.HORIZONTAL:
        return point[0]
    if line_segment.family_name == LineFamilyName.VERTICAL:
        return point[1]

    raise NotImplementedError(
        "Intersection point axis value is available only for classified segments."
    )


def _point_matches_segment_geometry(
    line_segment: LineSegment,
    point: tuple[int, int],
    tolerance_px: int = 1,
) -> bool:
    if not _is_point_within_segment_axis(line_segment, point):
        return False

    point_on_segment = point_on_segment_axis(
        line_segment,
        _point_axis_value_for_segment(line_segment, point),
    )
    return (
        abs(point_on_segment[0] - point[0]) <= tolerance_px
        and abs(point_on_segment[1] - point[1]) <= tolerance_px
    )


def _build_segment_pair_candidate(
    horizontal_line: LogicalLine,
    vertical_line: LogicalLine,
    horizontal_segment: LineSegment,
    vertical_segment: LineSegment,
) -> _SegmentPairIntersectionCandidate | None:
    intersection_point = supporting_line_intersection_point(
        horizontal_segment,
        vertical_segment,
    )
    if intersection_point is None:
        return None

    rounded_point = (
        int(round(intersection_point[0])),
        int(round(intersection_point[1])),
    )
    if not _point_matches_segment_geometry(horizontal_segment, rounded_point):
        return None
    if not _point_matches_segment_geometry(vertical_segment, rounded_point):
        return None

    horizontal_segment_order = _classify_segment_order(
        horizontal_segment,
        rounded_point,
    )
    vertical_segment_order = _classify_segment_order(
        vertical_segment,
        rounded_point,
    )
    kind = (
        LogicalLineIntersectionKind.CROSS
        if (
            horizontal_segment_order == IntersectionOrder.MIDDLE
            and vertical_segment_order == IntersectionOrder.MIDDLE
        )
        else LogicalLineIntersectionKind.TOUCH
    )
    return _SegmentPairIntersectionCandidate(
        horizontal_line=horizontal_line,
        vertical_line=vertical_line,
        horizontal_segment=horizontal_segment,
        vertical_segment=vertical_segment,
        point=rounded_point,
        kind=kind,
    )


def _select_best_candidate(
    candidates: list[_SegmentPairIntersectionCandidate],
) -> _SegmentPairIntersectionCandidate | None:
    if not candidates:
        return None

    unique_candidates_by_point: dict[
        tuple[int, int],
        _SegmentPairIntersectionCandidate,
    ] = {}
    for candidate in candidates:
        current_best = unique_candidates_by_point.get(candidate.point)
        if current_best is None or candidate.selection_key < current_best.selection_key:
            unique_candidates_by_point[candidate.point] = candidate

    return min(
        unique_candidates_by_point.values(),
        key=lambda current_candidate: current_candidate.selection_key,
    )


def build_logical_line_intersections(
    horizontal_logical_lines: list[LogicalLine],
    vertical_logical_lines: list[LogicalLine],
) -> list[LogicalLineIntersection]:
    logical_line_intersections: list[LogicalLineIntersection] = []

    for horizontal_line in horizontal_logical_lines:
        for vertical_line in vertical_logical_lines:
            pair_candidates = [
                segment_pair_candidate
                for horizontal_segment in horizontal_line.line_segments
                for vertical_segment in vertical_line.line_segments
                if (
                    segment_pair_candidate := _build_segment_pair_candidate(
                        horizontal_line,
                        vertical_line,
                        horizontal_segment,
                        vertical_segment,
                    )
                )
                is not None
            ]
            best_candidate = _select_best_candidate(pair_candidates)
            if best_candidate is None:
                continue

            logical_line_intersections.append(
                LogicalLineIntersection(
                    ref_horizontal_line=best_candidate.horizontal_line,
                    ref_vertical_line=best_candidate.vertical_line,
                    ref_horizontal_segment=best_candidate.horizontal_segment,
                    ref_vertical_segment=best_candidate.vertical_segment,
                    point=best_candidate.point,
                    kind=best_candidate.kind,
                )
            )

    return logical_line_intersections


__all__ = ["build_logical_line_intersections"]
