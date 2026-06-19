from __future__ import annotations

from intersection_model import (
    IntersectionOrder,
    LogicalLineIntersection,
    LogicalLineIntersectionDebugCandidate,
    LogicalLineIntersectionKind,
)
from logical_line_debug import get_logical_line_debug_name
from logical_line_core import LogicalLine
from models import LineFamilyName, LineSegment, SegmentOrigin


def classify_logical_line_intersection_kind(
    axis_segment: LineSegment,
    point: tuple[int, int],
) -> LogicalLineIntersectionKind:
    axis_value = _axis_value_for_segment(axis_segment, point)

    if axis_segment.axis_start < axis_value < axis_segment.axis_end:
        return LogicalLineIntersectionKind.CROSS

    return LogicalLineIntersectionKind.TOUCH


def classify_logical_line_intersection_order(
    intersection_index: int,
    total_intersections: int,
) -> IntersectionOrder:
    if total_intersections <= 0:
        return IntersectionOrder.NONE

    if total_intersections == 1:
        return IntersectionOrder.BOTH

    if intersection_index == 0:
        return IntersectionOrder.START

    if intersection_index == total_intersections - 1:
        return IntersectionOrder.END

    return IntersectionOrder.MIDDLE


def find_logical_line_intersection_candidates(
    axis_line: LogicalLine,
    cross_axis_lines: list[LogicalLine],
    geometry_tolerance_px: int = 1,
) -> list[LogicalLineIntersectionDebugCandidate]:
    if axis_line.family_name == LineFamilyName.HORIZONTAL:
        expected_cross_family = LineFamilyName.VERTICAL
    elif axis_line.family_name == LineFamilyName.VERTICAL:
        expected_cross_family = LineFamilyName.HORIZONTAL
    else:
        raise NotImplementedError(
            "Logical line intersections require classified logical lines."
        )

    raw_candidates: list[LogicalLineIntersectionDebugCandidate] = []

    for axis_segment in axis_line.line_segments:
        for cross_axis_line in cross_axis_lines:
            if cross_axis_line.family_name != expected_cross_family:
                raise ValueError("cross_axis_lines contain invalid family.")

            for cross_axis_segment in cross_axis_line.line_segments:
                candidate = _build_intersection_candidate(
                    axis_line=axis_line,
                    axis_segment=axis_segment,
                    cross_axis_line=cross_axis_line,
                    cross_axis_segment=cross_axis_segment,
                    geometry_tolerance_px=geometry_tolerance_px,
                )
                if candidate is None:
                    continue

                raw_candidates.append(candidate)

    return _annotate_duplicate_candidates(raw_candidates)


def find_logical_line_intersections(
    axis_line: LogicalLine,
    cross_axis_lines: list[LogicalLine],
    geometry_tolerance_px: int = 1,
) -> list[LogicalLineIntersection]:
    debug_candidates = find_logical_line_intersection_candidates(
        axis_line=axis_line,
        cross_axis_lines=cross_axis_lines,
        geometry_tolerance_px=geometry_tolerance_px,
    )
    selected_candidates = _select_preferred_candidates_for_line(debug_candidates)
    return _build_logical_line_intersections_from_candidates(selected_candidates)


def assign_logical_line_intersections(
    horizontal_logical_lines: list[LogicalLine],
    vertical_logical_lines: list[LogicalLine],
    geometry_tolerance_px: int = 1,
) -> None:
    raw_candidates_by_line_name: dict[
        str,
        list[LogicalLineIntersectionDebugCandidate],
    ] = {}

    for horizontal_logical_line in horizontal_logical_lines:
        line_debug_name = get_logical_line_debug_name(horizontal_logical_line)
        horizontal_debug_candidates = find_logical_line_intersection_candidates(
            axis_line=horizontal_logical_line,
            cross_axis_lines=vertical_logical_lines,
            geometry_tolerance_px=geometry_tolerance_px,
        )
        raw_candidates_by_line_name[line_debug_name] = horizontal_debug_candidates

    for vertical_logical_line in vertical_logical_lines:
        line_debug_name = get_logical_line_debug_name(vertical_logical_line)
        vertical_debug_candidates = find_logical_line_intersection_candidates(
            axis_line=vertical_logical_line,
            cross_axis_lines=horizontal_logical_lines,
            geometry_tolerance_px=geometry_tolerance_px,
        )
        raw_candidates_by_line_name[line_debug_name] = vertical_debug_candidates

    canonical_candidates_by_pair: dict[
        tuple[str, str],
        LogicalLineIntersectionDebugCandidate,
    ] = {}
    final_candidates_by_line_name: dict[
        str,
        dict[str, LogicalLineIntersectionDebugCandidate],
    ] = {
        get_logical_line_debug_name(logical_line): {}
        for logical_line in (horizontal_logical_lines + vertical_logical_lines)
    }

    for logical_line in horizontal_logical_lines + vertical_logical_lines:
        line_debug_name = get_logical_line_debug_name(logical_line)
        preferred_candidates = _select_preferred_candidates_for_line(
            raw_candidates_by_line_name[line_debug_name]
        )
        for preferred_candidate in preferred_candidates:
            pair_key = _build_line_pair_key(preferred_candidate)
            canonical_candidate = canonical_candidates_by_pair.get(pair_key)
            if canonical_candidate is None:
                canonical_candidates_by_pair[pair_key] = preferred_candidate
                final_candidates_by_line_name[line_debug_name][
                    preferred_candidate.intersected_line_cross_axis_debug_name
                ] = preferred_candidate
                continue

            synchronized_candidate = _synchronize_candidate_with_pair(
                preferred_candidate=preferred_candidate,
                canonical_candidate=canonical_candidate,
                debug_candidates=raw_candidates_by_line_name[line_debug_name],
            )
            final_candidates_by_line_name[line_debug_name][
                synchronized_candidate.intersected_line_cross_axis_debug_name
            ] = synchronized_candidate

    for logical_line in horizontal_logical_lines + vertical_logical_lines:
        line_debug_name = get_logical_line_debug_name(logical_line)
        final_candidates = list(final_candidates_by_line_name[line_debug_name].values())
        logical_line.intersection_debug_candidates = _annotate_duplicate_candidates(
            final_candidates
        )
        logical_line.intersections = _build_logical_line_intersections_from_candidates(
            final_candidates
        )

    return None


def _build_logical_line_intersections_from_candidates(
    debug_candidates: list[LogicalLineIntersectionDebugCandidate],
) -> list[LogicalLineIntersection]:
    ordered_candidates = sorted(
        debug_candidates,
        key=lambda candidate: (
            candidate.axis_value,
            candidate.cross_axis_value,
            candidate.point[0],
            candidate.point[1],
        ),
    )

    intersections: list[LogicalLineIntersection] = []
    total_intersections = len(ordered_candidates)
    for intersection_index, candidate in enumerate(ordered_candidates):
        intersections.append(
            LogicalLineIntersection(
                intersected_line_axis_debug_name=(
                    candidate.intersected_line_axis_debug_name
                ),
                intersected_segment_axis=candidate.intersected_segment_axis,
                intersected_line_cross_axis_debug_name=(
                    candidate.intersected_line_cross_axis_debug_name
                ),
                intersected_segment_cross_axis=candidate.intersected_segment_cross_axis,
                point=candidate.point,
                kind=candidate.kind,
                order=classify_logical_line_intersection_order(
                    intersection_index=intersection_index,
                    total_intersections=total_intersections,
                ),
            )
        )

    return intersections


def _select_preferred_candidates_for_line(
    debug_candidates: list[LogicalLineIntersectionDebugCandidate],
) -> list[LogicalLineIntersectionDebugCandidate]:
    selected_candidates: list[LogicalLineIntersectionDebugCandidate] = []
    candidate_groups = _build_candidate_groups_by_cross_axis_line(debug_candidates)
    total_groups = len(candidate_groups)

    for group_index, candidate_group in enumerate(candidate_groups):
        group_order = classify_logical_line_intersection_order(
            intersection_index=group_index,
            total_intersections=total_groups,
        )
        selected_candidates.append(
            _select_candidate_from_group(
                candidate_group,
                group_order,
            )
        )

    return sorted(
        selected_candidates,
        key=lambda candidate: (
            candidate.axis_value,
            candidate.cross_axis_value,
            candidate.point[0],
            candidate.point[1],
        ),
    )


def _select_candidate_from_group(
    candidate_group: list[LogicalLineIntersectionDebugCandidate],
    group_order: IntersectionOrder,
) -> LogicalLineIntersectionDebugCandidate:
    ordered_group = sorted(
        candidate_group,
        key=lambda candidate: (
            candidate.axis_value,
            candidate.cross_axis_value,
            candidate.point[0],
            candidate.point[1],
        ),
    )
    if group_order == IntersectionOrder.START:
        return ordered_group[-1]
    return ordered_group[0]


def _build_candidate_groups_by_cross_axis_line(
    debug_candidates: list[LogicalLineIntersectionDebugCandidate],
) -> list[list[LogicalLineIntersectionDebugCandidate]]:
    grouped_candidates: dict[str, list[LogicalLineIntersectionDebugCandidate]] = {}
    for debug_candidate in debug_candidates:
        grouped_candidates.setdefault(
            debug_candidate.intersected_line_cross_axis_debug_name,
            [],
        ).append(debug_candidate)

    ordered_groups = [
        sorted(
            candidate_group,
            key=lambda candidate: (
                candidate.axis_value,
                candidate.cross_axis_value,
                candidate.point[0],
                candidate.point[1],
            ),
        )
        for candidate_group in grouped_candidates.values()
    ]
    ordered_groups.sort(
        key=lambda candidate_group: (
            candidate_group[0].axis_value,
            candidate_group[0].cross_axis_value,
            candidate_group[0].point[0],
            candidate_group[0].point[1],
            candidate_group[0].intersected_line_cross_axis_debug_name,
        )
    )
    return ordered_groups


def _build_line_pair_key(
    candidate: LogicalLineIntersectionDebugCandidate,
) -> tuple[str, str]:
    if candidate.intersected_segment_axis.family_name == LineFamilyName.HORIZONTAL:
        return (
            candidate.intersected_line_axis_debug_name,
            candidate.intersected_line_cross_axis_debug_name,
        )
    return (
        candidate.intersected_line_cross_axis_debug_name,
        candidate.intersected_line_axis_debug_name,
    )


def _synchronize_candidate_with_pair(
    preferred_candidate: LogicalLineIntersectionDebugCandidate,
    canonical_candidate: LogicalLineIntersectionDebugCandidate,
    debug_candidates: list[LogicalLineIntersectionDebugCandidate],
) -> LogicalLineIntersectionDebugCandidate:
    synchronized_candidate = _find_candidate_with_same_point(
        debug_candidates=debug_candidates,
        cross_axis_line_debug_name=(
            preferred_candidate.intersected_line_cross_axis_debug_name
        ),
        point=canonical_candidate.point,
    )
    if synchronized_candidate is not None:
        return synchronized_candidate
    return _mirror_candidate(canonical_candidate)


def _find_candidate_with_same_point(
    debug_candidates: list[LogicalLineIntersectionDebugCandidate],
    cross_axis_line_debug_name: str,
    point: tuple[int, int],
) -> LogicalLineIntersectionDebugCandidate | None:
    matching_candidates = [
        debug_candidate
        for debug_candidate in debug_candidates
        if (
            debug_candidate.intersected_line_cross_axis_debug_name
            == cross_axis_line_debug_name
            and debug_candidate.point == point
        )
    ]
    if not matching_candidates:
        return None
    return min(matching_candidates, key=_selection_key)


def _mirror_candidate(
    candidate: LogicalLineIntersectionDebugCandidate,
) -> LogicalLineIntersectionDebugCandidate:
    mirrored_axis_segment = candidate.intersected_segment_cross_axis
    mirrored_cross_axis_segment = candidate.intersected_segment_axis
    return LogicalLineIntersectionDebugCandidate(
        intersected_line_axis_debug_name=(
            candidate.intersected_line_cross_axis_debug_name
        ),
        intersected_segment_axis=mirrored_axis_segment,
        intersected_line_cross_axis_debug_name=(
            candidate.intersected_line_axis_debug_name
        ),
        intersected_segment_cross_axis=mirrored_cross_axis_segment,
        point=candidate.point,
        kind=classify_logical_line_intersection_kind(
            axis_segment=mirrored_axis_segment,
            point=candidate.point,
        ),
        axis_value=_axis_value_for_segment(mirrored_axis_segment, candidate.point),
        cross_axis_value=_cross_axis_value_for_segment(
            mirrored_axis_segment,
            candidate.point,
        ),
        duplicate_index=0,
        duplicate_count=1,
    )


def _build_intersection_candidate(
    axis_line: LogicalLine,
    axis_segment: LineSegment,
    cross_axis_line: LogicalLine,
    cross_axis_segment: LineSegment,
    geometry_tolerance_px: int,
) -> LogicalLineIntersectionDebugCandidate | None:
    intersection_point = _solve_supporting_line_intersection(
        axis_segment,
        cross_axis_segment,
    )
    if intersection_point is None:
        return None

    rounded_point = (
        int(round(intersection_point[0])),
        int(round(intersection_point[1])),
    )

    if not _point_matches_segment(
        axis_segment,
        rounded_point,
        tolerance_px=geometry_tolerance_px,
    ):
        return None

    if not _point_matches_segment(
        cross_axis_segment,
        rounded_point,
        tolerance_px=geometry_tolerance_px,
    ):
        return None

    return LogicalLineIntersectionDebugCandidate(
        intersected_line_axis_debug_name=get_logical_line_debug_name(axis_line),
        intersected_segment_axis=axis_segment,
        intersected_line_cross_axis_debug_name=get_logical_line_debug_name(
            cross_axis_line
        ),
        intersected_segment_cross_axis=cross_axis_segment,
        point=rounded_point,
        kind=classify_logical_line_intersection_kind(
            axis_segment=axis_segment,
            point=rounded_point,
        ),
        axis_value=_axis_value_for_segment(axis_segment, rounded_point),
        cross_axis_value=_cross_axis_value_for_segment(axis_segment, rounded_point),
    )


def _annotate_duplicate_candidates(
    candidates: list[LogicalLineIntersectionDebugCandidate],
) -> list[LogicalLineIntersectionDebugCandidate]:
    annotated_candidates: list[LogicalLineIntersectionDebugCandidate] = []
    for candidate_group in _build_candidate_groups_by_cross_axis_line(candidates):
        for duplicate_index, candidate in enumerate(candidate_group):
            annotated_candidates.append(
                LogicalLineIntersectionDebugCandidate(
                    intersected_line_axis_debug_name=(
                        candidate.intersected_line_axis_debug_name
                    ),
                    intersected_segment_axis=candidate.intersected_segment_axis,
                    intersected_line_cross_axis_debug_name=(
                        candidate.intersected_line_cross_axis_debug_name
                    ),
                    intersected_segment_cross_axis=(
                        candidate.intersected_segment_cross_axis
                    ),
                    point=candidate.point,
                    kind=candidate.kind,
                    axis_value=candidate.axis_value,
                    cross_axis_value=candidate.cross_axis_value,
                    duplicate_index=duplicate_index,
                    duplicate_count=len(candidate_group),
                )
            )

    return annotated_candidates


def _selection_key(
    candidate: LogicalLineIntersectionDebugCandidate,
) -> tuple[int, int, float]:
    return (
        0 if candidate.kind == LogicalLineIntersectionKind.CROSS else 1,
        _segment_origin_priority(candidate.intersected_segment_axis.origin)
        + _segment_origin_priority(candidate.intersected_segment_cross_axis.origin),
        -(
            candidate.intersected_segment_axis.length
            + candidate.intersected_segment_cross_axis.length
        ),
    )


def _solve_supporting_line_intersection(
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


def _point_matches_segment(
    line_segment: LineSegment,
    point: tuple[int, int],
    tolerance_px: int,
) -> bool:
    axis_value = _axis_value_for_segment(line_segment, point)

    if axis_value < line_segment.axis_start or axis_value > line_segment.axis_end:
        return False

    projected_point = _project_point_on_segment_axis(
        line_segment,
        axis_value,
    )

    return (
        abs(projected_point[0] - point[0]) <= tolerance_px
        and abs(projected_point[1] - point[1]) <= tolerance_px
    )


def _project_point_on_segment_axis(
    line_segment: LineSegment,
    axis_value: int,
) -> tuple[int, int]:
    if line_segment.family_name == LineFamilyName.HORIZONTAL:
        start_axis = line_segment.start[0]
        end_axis = line_segment.end[0]

        if end_axis == start_axis:
            return line_segment.start

        ratio = (axis_value - start_axis) / float(end_axis - start_axis)
        projected_y = line_segment.start[1] + (
            line_segment.end[1] - line_segment.start[1]
        ) * ratio
        return int(axis_value), int(round(projected_y))

    if line_segment.family_name == LineFamilyName.VERTICAL:
        start_axis = line_segment.start[1]
        end_axis = line_segment.end[1]

        if end_axis == start_axis:
            return line_segment.start

        ratio = (axis_value - start_axis) / float(end_axis - start_axis)
        projected_x = line_segment.start[0] + (
            line_segment.end[0] - line_segment.start[0]
        ) * ratio
        return int(round(projected_x)), int(axis_value)

    raise NotImplementedError(
        "Point projection is available only for classified segments."
    )


def _axis_value_for_segment(
    line_segment: LineSegment,
    point: tuple[int, int],
) -> int:
    if line_segment.family_name == LineFamilyName.HORIZONTAL:
        return point[0]

    if line_segment.family_name == LineFamilyName.VERTICAL:
        return point[1]

    raise NotImplementedError(
        "Axis value is available only for classified segments."
    )


def _cross_axis_value_for_segment(
    line_segment: LineSegment,
    point: tuple[int, int],
) -> int:
    if line_segment.family_name == LineFamilyName.HORIZONTAL:
        return point[1]

    if line_segment.family_name == LineFamilyName.VERTICAL:
        return point[0]

    raise NotImplementedError(
        "Cross-axis value is available only for classified segments."
    )


def _segment_origin_priority(segment_origin: SegmentOrigin) -> int:
    if segment_origin == SegmentOrigin.RAW:
        return 0

    if segment_origin == SegmentOrigin.SAME_AXIS_CONNECTION:
        return 1

    if segment_origin == SegmentOrigin.CROSS_AXIS_CONNECTION:
        return 2

    return 3


__all__ = [
    "assign_logical_line_intersections",
    "find_logical_line_intersection_candidates",
    "classify_logical_line_intersection_kind",
    "classify_logical_line_intersection_order",
    "find_logical_line_intersections",
]