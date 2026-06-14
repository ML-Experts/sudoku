from __future__ import annotations

from intersection_candidates import (
    _collect_candidate_intersections,
)
from intersection_frame import (
    _apply_frame_side,
    _find_logical_line_frames,
    _select_best_frame,
)
from intersection_models import (
    LogicalLineFrame,
    LogicalLineIntersection,
    LogicalLineIntersectionAnalysis,
)
from intersection_ordering import (
    _assign_boundary_orders,
    _build_public_intersections,
    _clear_logical_line_metadata,
)
from intersection_pruning import (
    _build_candidate_lookup,
    _prune_lines_by_minimum_intersection_count,
)
from logical_line_core import LogicalLine
from models import LineFamilyName


def analyze_logical_line_intersections(
    horizontal_logical_lines: list[LogicalLine],
    vertical_logical_lines: list[LogicalLine],
) -> LogicalLineIntersectionAnalysis:
    _clear_logical_line_metadata(
        horizontal_logical_lines,
        vertical_logical_lines,
    )
    candidate_intersections = _collect_candidate_intersections(
        horizontal_logical_lines,
        vertical_logical_lines,
    )
    (
        active_horizontal_lines,
        active_vertical_lines,
        active_intersections,
    ) = _prune_lines_by_minimum_intersection_count(
        horizontal_logical_lines,
        vertical_logical_lines,
        candidate_intersections,
        minimum_intersection_count=2,
    )
    lines_by_key, intersections_by_key = _build_candidate_lookup(
        active_horizontal_lines,
        active_vertical_lines,
        active_intersections,
    )
    _assign_boundary_orders(
        lines_by_key,
        intersections_by_key,
        LineFamilyName.HORIZONTAL,
    )
    _assign_boundary_orders(
        lines_by_key,
        intersections_by_key,
        LineFamilyName.VERTICAL,
    )
    candidate_frames = _find_logical_line_frames(
        active_intersections,
        active_horizontal_lines,
        active_vertical_lines,
    )
    best_frame = _select_best_frame(
        candidate_frames,
        intersections_by_key,
    )
    protected_line_keys = (
        {id(logical_line) for logical_line in best_frame.lines}
        if best_frame is not None
        else set()
    )
    (
        active_horizontal_lines,
        active_vertical_lines,
        active_intersections,
    ) = _prune_lines_by_minimum_intersection_count(
        active_horizontal_lines,
        active_vertical_lines,
        active_intersections,
        minimum_intersection_count=10,
        protected_line_keys=protected_line_keys,
    )
    public_intersections = _build_public_intersections(
        active_horizontal_lines,
        active_vertical_lines,
        active_intersections,
    )
    _apply_frame_side(best_frame)
    return LogicalLineIntersectionAnalysis(
        frame=best_frame,
        horizontal_lines=active_horizontal_lines,
        vertical_lines=active_vertical_lines,
        intersections=public_intersections,
    )


def find_logical_line_frames(
    intersections: list[LogicalLineIntersection],
    horizontal_logical_lines: list[LogicalLine],
    vertical_logical_lines: list[LogicalLine],
) -> list[LogicalLineFrame]:
    return _find_logical_line_frames(
        intersections,
        horizontal_logical_lines,
        vertical_logical_lines,
    )


def find_logical_line_intersections(
    horizontal_logical_lines: list[LogicalLine],
    vertical_logical_lines: list[LogicalLine],
) -> list[LogicalLineIntersection]:
    analysis = analyze_logical_line_intersections(
        horizontal_logical_lines,
        vertical_logical_lines,
    )
    return analysis.intersections


__all__ = [
    "analyze_logical_line_intersections",
    "find_logical_line_frames",
    "find_logical_line_intersections",
]
