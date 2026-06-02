from __future__ import annotations

from raw_line_family_only_intersection_models import _LogicalLineIntersectionCandidate
from raw_line_family_only_intersection_ordering import _build_line_lookup
from raw_line_family_only_logical_line_core import LogicalLine


def _build_candidate_lookup(
    horizontal_logical_lines: list[LogicalLine],
    vertical_logical_lines: list[LogicalLine],
    intersections: list[_LogicalLineIntersectionCandidate],
) -> tuple[
    dict[int, LogicalLine],
    dict[int, list[_LogicalLineIntersectionCandidate]],
]:
    lines_by_key, intersections_by_key = _build_line_lookup(
        horizontal_logical_lines,
        vertical_logical_lines,
    )
    typed_lookup: dict[int, list[_LogicalLineIntersectionCandidate]] = {
        line_key: []
        for line_key in intersections_by_key
    }
    for intersection in intersections:
        typed_lookup[id(intersection.ref_horizontal_line)].append(intersection)
        typed_lookup[id(intersection.ref_vertical_line)].append(intersection)
    return lines_by_key, typed_lookup


def _prune_lines_by_minimum_intersection_count(
    horizontal_logical_lines: list[LogicalLine],
    vertical_logical_lines: list[LogicalLine],
    intersections: list[_LogicalLineIntersectionCandidate],
    minimum_intersection_count: int,
    protected_line_keys: set[int] | None = None,
) -> tuple[
    list[LogicalLine],
    list[LogicalLine],
    list[_LogicalLineIntersectionCandidate],
]:
    active_horizontal_lines = list(horizontal_logical_lines)
    active_vertical_lines = list(vertical_logical_lines)
    active_intersections = list(intersections)
    protected_keys = protected_line_keys or set()

    while True:
        _, intersections_by_key = _build_candidate_lookup(
            active_horizontal_lines,
            active_vertical_lines,
            active_intersections,
        )
        removable_line_keys = {
            line_key
            for line_key in intersections_by_key
            if (
                line_key not in protected_keys
                and len(intersections_by_key[line_key]) < minimum_intersection_count
            )
        }
        if not removable_line_keys:
            return (
                active_horizontal_lines,
                active_vertical_lines,
                active_intersections,
            )

        active_horizontal_lines = [
            logical_line
            for logical_line in active_horizontal_lines
            if id(logical_line) not in removable_line_keys
        ]
        active_vertical_lines = [
            logical_line
            for logical_line in active_vertical_lines
            if id(logical_line) not in removable_line_keys
        ]
        active_intersections = [
            intersection
            for intersection in active_intersections
            if (
                id(intersection.ref_horizontal_line) not in removable_line_keys
                and id(intersection.ref_vertical_line) not in removable_line_keys
            )
        ]


__all__ = [
    "_build_candidate_lookup",
    "_prune_lines_by_minimum_intersection_count",
]
