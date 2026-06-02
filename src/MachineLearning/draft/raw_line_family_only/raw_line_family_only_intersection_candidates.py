from __future__ import annotations

from raw_line_family_only_intersection_models import (
    LogicalLineIntersection,
    LogicalLineIntersectionKind,
    _LogicalLineIntersectionCandidate,
)
from raw_line_family_only_intersection_segment_geometry import (
    find_segment_intersection,
)
from raw_line_family_only_logical_line_core import LogicalLine
from raw_line_family_only_models import LineFamilyName, LineSegment


def _family_key(family_name: object) -> object:
    return getattr(family_name, "value", family_name)


def _collect_segment_intersection_candidates(
    horizontal_line: LogicalLine,
    vertical_line: LogicalLine,
) -> list[
    tuple[
        LineSegment,
        LineSegment,
        tuple[int, int],
        LogicalLineIntersectionKind,
    ]
]:
    if _family_key(horizontal_line.family_name) != LineFamilyName.HORIZONTAL.value:
        raise ValueError("horizontal_line must belong to the horizontal family.")
    if _family_key(vertical_line.family_name) != LineFamilyName.VERTICAL.value:
        raise ValueError("vertical_line must belong to the vertical family.")

    candidates: list[
        tuple[
            LineSegment,
            LineSegment,
            tuple[int, int],
            LogicalLineIntersectionKind,
        ]
    ] = []
    for horizontal_segment in horizontal_line.line_segments:
        for vertical_segment in vertical_line.line_segments:
            intersection_result = find_segment_intersection(
                horizontal_segment,
                vertical_segment,
            )
            if intersection_result is None:
                continue

            intersection_point, intersection_kind = intersection_result
            candidates.append(
                (
                    horizontal_segment,
                    vertical_segment,
                    intersection_point,
                    intersection_kind,
                )
            )

    return candidates


def _select_representative_segment_intersection(
    candidates: list[
        tuple[
            LineSegment,
            LineSegment,
            tuple[int, int],
            LogicalLineIntersectionKind,
        ]
    ],
) -> tuple[
    LineSegment,
    LineSegment,
    tuple[int, int],
    LogicalLineIntersectionKind,
] | None:
    if not candidates:
        return None

    sorted_candidates = sorted(
        candidates,
        key=lambda candidate: (
            candidate[2][0],
            candidate[2][1],
            0 if candidate[3] == LogicalLineIntersectionKind.CROSS else 1,
            candidate[0].axis_start,
            candidate[1].axis_start,
        ),
    )
    return sorted_candidates[0]


def _find_logical_line_intersection_candidate(
    horizontal_line: LogicalLine,
    vertical_line: LogicalLine,
) -> _LogicalLineIntersectionCandidate | None:
    candidates = _collect_segment_intersection_candidates(
        horizontal_line,
        vertical_line,
    )
    representative_intersection = _select_representative_segment_intersection(
        candidates
    )
    if representative_intersection is None:
        return None

    (
        horizontal_segment,
        vertical_segment,
        intersection_point,
        intersection_kind,
    ) = representative_intersection
    return _LogicalLineIntersectionCandidate(
        ref_horizontal_line=horizontal_line,
        ref_vertical_line=vertical_line,
        ref_horizontal_segment=horizontal_segment,
        ref_vertical_segment=vertical_segment,
        point=intersection_point,
        kind=intersection_kind,
    )


def _collect_candidate_intersections(
    horizontal_logical_lines: list[LogicalLine],
    vertical_logical_lines: list[LogicalLine],
) -> list[_LogicalLineIntersectionCandidate]:
    intersections: list[_LogicalLineIntersectionCandidate] = []
    for horizontal_line in horizontal_logical_lines:
        for vertical_line in vertical_logical_lines:
            intersection = _find_logical_line_intersection_candidate(
                horizontal_line,
                vertical_line,
            )
            if intersection is not None:
                intersections.append(intersection)
    return intersections


def find_logical_line_intersection(
    horizontal_line: LogicalLine,
    vertical_line: LogicalLine,
) -> LogicalLineIntersection | None:
    candidate = _find_logical_line_intersection_candidate(
        horizontal_line,
        vertical_line,
    )
    if candidate is None:
        return None
    return LogicalLineIntersection(
        ref_horizontal_line=candidate.ref_horizontal_line,
        ref_vertical_line=candidate.ref_vertical_line,
        ref_horizontal_segment=candidate.ref_horizontal_segment,
        ref_vertical_segment=candidate.ref_vertical_segment,
        point=candidate.point,
        kind=candidate.kind,
    )


__all__ = [
    "find_logical_line_intersection",
    "_LogicalLineIntersectionCandidate",
    "_collect_candidate_intersections",
    "_find_logical_line_intersection_candidate",
]
