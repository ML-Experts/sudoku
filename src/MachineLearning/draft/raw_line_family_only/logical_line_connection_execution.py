from __future__ import annotations

import numpy as np

from logical_line_core import (
    LogicalLine,
    LogicalLineVertexKind,
)
from logical_line_search_area import (
    SearchArea,
    build_search_area,
    is_point_in_search_area,
)
from logical_line_search_goals import (
    build_cross_axis_goal_sets,
    build_same_axis_goal_sets,
)
from logical_line_search_pathfinding import (
    add_path_segments,
    try_find_path,
    try_find_straight_path,
)
from logical_line_search_window_points import (
    build_start_points,
)
from models import SegmentOrigin
from logical_line_connection_types import ConnectionCandidate


def remove_logical_line(
    logical_lines: list[LogicalLine],
    target_line: LogicalLine,
) -> None:
    for line_index, logical_line in enumerate(logical_lines):
        if logical_line is target_line:
            del logical_lines[line_index]
            return


def contains_logical_line(
    logical_lines: list[LogicalLine],
    target_line: LogicalLine,
) -> bool:
    return any(logical_line is target_line for logical_line in logical_lines)


def try_connect_same_axis_candidate(
    binary_image: np.ndarray,
    source_line: LogicalLine,
    source_vertex_kind: LogicalLineVertexKind,
    search_area: SearchArea,
    candidate: ConnectionCandidate,
    axis_gap_tolerance_px: int,
    same_axis_lines: list[LogicalLine],
) -> bool:
    if candidate.target_vertex_kind is None:
        return False

    start_points = build_start_points(
        binary_image,
        source_line,
        source_vertex_kind,
        search_area,
        start_tolerance_px=axis_gap_tolerance_px,
    )
    path_points = try_find_path(
        binary_image,
        search_area,
        start_points,
        build_same_axis_goal_sets(
            binary_image,
            search_area,
            candidate.target_line,
            candidate.target_vertex_kind,
        ),
    )
    if path_points is None:
        return False

    add_path_segments(
        source_line,
        path_points,
        origin=SegmentOrigin.SAME_AXIS_CONNECTION,
    )
    source_line.merge_logical_line(candidate.target_line)
    remove_logical_line(same_axis_lines, candidate.target_line)
    return True


def try_connect_cross_axis_candidate(
    binary_image: np.ndarray,
    source_line: LogicalLine,
    source_vertex_kind: LogicalLineVertexKind,
    search_area: SearchArea,
    candidate: ConnectionCandidate,
    axis_gap_tolerance_px: int,
    cross_axis_thickness_px: int,
    rectangle_vector_length_px: int,
    rectangle_padding_px: int,
) -> bool:
    if candidate.target_vertex_kind is None:
        return False

    source_start_points = build_start_points(
        binary_image,
        source_line,
        source_vertex_kind,
        search_area,
        start_tolerance_px=max(cross_axis_thickness_px, axis_gap_tolerance_px),
    )
    source_path_points = try_find_path(
        binary_image,
        search_area,
        source_start_points,
        build_cross_axis_goal_sets(
            binary_image,
            search_area,
            source_line,
            candidate.target_line,
            candidate.target_vertex_kind,
        ),
    )
    if source_path_points is None:
        return False

    reciprocal_vertex = source_line.get_vertex(source_vertex_kind)
    reciprocal_rectangle = candidate.target_line.build_tolerance_rectangle(
        reference_vertex=candidate.target_line.get_vertex(
            candidate.target_vertex_kind
        ),
        direction_length=rectangle_vector_length_px,
        padding=rectangle_padding_px,
    )
    reciprocal_search_area = build_search_area(
        binary_image.shape,
        reciprocal_rectangle,
    )
    if not is_point_in_search_area(reciprocal_vertex, reciprocal_search_area):
        return False

    reciprocal_start_points = build_start_points(
        binary_image,
        candidate.target_line,
        candidate.target_vertex_kind,
        reciprocal_search_area,
        start_tolerance_px=max(cross_axis_thickness_px, axis_gap_tolerance_px),
    )
    reciprocal_path_points = try_find_path(
        binary_image,
        reciprocal_search_area,
        reciprocal_start_points,
        build_cross_axis_goal_sets(
            binary_image,
            reciprocal_search_area,
            candidate.target_line,
            source_line,
            source_vertex_kind,
        ),
    )
    if reciprocal_path_points is None:
        return False

    source_added_segment_count = add_path_segments(
        source_line,
        source_path_points,
        origin=SegmentOrigin.CROSS_AXIS_CONNECTION,
    )
    target_added_segment_count = add_path_segments(
        candidate.target_line,
        reciprocal_path_points,
        origin=SegmentOrigin.CROSS_AXIS_CONNECTION,
    )
    return (source_added_segment_count + target_added_segment_count) > 0


def try_connect_cross_axis_span_candidate(
    binary_image: np.ndarray,
    source_line: LogicalLine,
    source_vertex_kind: LogicalLineVertexKind,
    search_area: SearchArea,
    candidate: ConnectionCandidate,
    axis_gap_tolerance_px: int,
    cross_axis_thickness_px: int,
) -> bool:
    if not candidate.goal_points:
        return False

    source_start_points = build_start_points(
        binary_image,
        source_line,
        source_vertex_kind,
        search_area,
        start_tolerance_px=max(cross_axis_thickness_px, axis_gap_tolerance_px),
    )
    if not source_start_points:
        return False

    source_path_points = try_find_straight_path(
        binary_image,
        search_area,
        source_start_points,
        list(candidate.goal_points),
    )
    if source_path_points is None:
        source_path_points = try_find_path(
            binary_image,
            search_area,
            source_start_points,
            [list(candidate.goal_points)],
        )
    if source_path_points is None:
        return False

    return (
        add_path_segments(
            source_line,
            source_path_points,
            origin=SegmentOrigin.CROSS_AXIS_CONNECTION,
        )
        > 0
    )


__all__ = [
    "contains_logical_line",
    "remove_logical_line",
    "try_connect_cross_axis_candidate",
    "try_connect_cross_axis_span_candidate",
    "try_connect_same_axis_candidate",
]
