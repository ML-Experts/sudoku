from __future__ import annotations

import math

import numpy as np

from .logical_line_core import (
    LogicalLine,
    LogicalLineVertexKind,
)
from .logical_line_search_area import (
    SearchArea,
    build_search_area,
    is_point_in_search_area,
)
from .logical_line_search_goals import (
    build_cross_axis_goal_sets,
    build_same_axis_goal_sets,
)
from .logical_line_search_pathfinding import (
    add_path_segments,
    try_find_path,
    try_find_straight_path,
)
from .logical_line_search_window_points import (
    build_start_points,
)
from .logical_line_segment_geometry import (
    supporting_line_intersection_point,
)
from .models import LineFamilyName, SegmentOrigin
from .logical_line_connection_types import ConnectionCandidate


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


def _flatten_goal_sets(
    goal_sets: list[list[tuple[int, int]]],
) -> list[tuple[int, int]]:
    seen_points: set[tuple[int, int]] = set()
    flattened_points: list[tuple[int, int]] = []
    for goal_points in goal_sets:
        for point in goal_points:
            if point in seen_points:
                continue
            seen_points.add(point)
            flattened_points.append(point)
    return flattened_points


def _build_extension_vector(
    logical_line: LogicalLine,
    vertex_kind: LogicalLineVertexKind,
) -> tuple[int, int]:
    vertex_segment = logical_line.get_vertex_segment(vertex_kind)
    if vertex_kind == LogicalLineVertexKind.START:
        return (
            vertex_segment.start[0] - vertex_segment.end[0],
            vertex_segment.start[1] - vertex_segment.end[1],
        )
    return (
        vertex_segment.end[0] - vertex_segment.start[0],
        vertex_segment.end[1] - vertex_segment.start[1],
    )


def _is_forward_extension_point(
    source_vertex: tuple[int, int],
    extension_vector: tuple[int, int],
    target_point: tuple[int, int],
) -> bool:
    delta_x = target_point[0] - source_vertex[0]
    delta_y = target_point[1] - source_vertex[1]
    if delta_x == 0 and delta_y == 0:
        return False

    return (delta_x * extension_vector[0] + delta_y * extension_vector[1]) > 0


def _compute_turn_angle_degrees(
    base_vector: tuple[int, int],
    candidate_vector: tuple[int, int],
) -> float:
    base_norm = math.hypot(base_vector[0], base_vector[1])
    candidate_norm = math.hypot(candidate_vector[0], candidate_vector[1])
    if base_norm <= 1e-6 or candidate_norm <= 1e-6:
        return float("inf")

    base_angle = math.degrees(math.atan2(base_vector[1], base_vector[0]))
    candidate_angle = math.degrees(
        math.atan2(candidate_vector[1], candidate_vector[0])
    )
    angle_delta = (candidate_angle - base_angle + 180.0) % 360.0 - 180.0
    return abs(angle_delta)


def _choose_min_turn_contact_point(
    source_vertex: tuple[int, int],
    extension_vector: tuple[int, int],
    candidate_points: list[tuple[int, int]],
    preferred_contact_point: tuple[int, int] | None = None,
) -> tuple[int, int] | None:
    best_point: tuple[int, int] | None = None
    best_key: tuple[float, float, float] | None = None

    for candidate_point in candidate_points:
        if not _is_forward_extension_point(
            source_vertex,
            extension_vector,
            candidate_point,
        ):
            continue

        candidate_vector = (
            candidate_point[0] - source_vertex[0],
            candidate_point[1] - source_vertex[1],
        )
        turn_angle_degrees = _compute_turn_angle_degrees(
            extension_vector,
            candidate_vector,
        )
        point_distance = math.hypot(candidate_vector[0], candidate_vector[1])
        preferred_distance = 0.0
        if preferred_contact_point is not None:
            preferred_distance = math.hypot(
                candidate_point[0] - preferred_contact_point[0],
                candidate_point[1] - preferred_contact_point[1],
            )
        candidate_key = (
            turn_angle_degrees,
            point_distance,
            preferred_distance,
        )
        if best_key is None or candidate_key < best_key:
            best_key = candidate_key
            best_point = candidate_point

    return best_point


def _add_direct_connection_segment(
    logical_line: LogicalLine,
    vertex_kind: LogicalLineVertexKind,
    target_point: tuple[int, int],
) -> int:
    source_vertex = logical_line.get_vertex(vertex_kind)
    if source_vertex == target_point:
        return 0

    return add_path_segments(
        logical_line,
        [source_vertex, target_point],
        origin=SegmentOrigin.CROSS_AXIS_CONNECTION,
    )


def _choose_cross_axis_meeting_point(
    source_line: LogicalLine,
    source_vertex_kind: LogicalLineVertexKind,
    source_search_area: SearchArea,
    source_goal_points: list[tuple[int, int]],
    target_line: LogicalLine,
    target_vertex_kind: LogicalLineVertexKind,
    reciprocal_search_area: SearchArea,
    reciprocal_goal_points: list[tuple[int, int]],
) -> tuple[int, int] | None:
    source_vertex = source_line.get_vertex(source_vertex_kind)
    target_vertex = target_line.get_vertex(target_vertex_kind)
    source_extension_vector = _build_extension_vector(
        source_line,
        source_vertex_kind,
    )
    target_extension_vector = _build_extension_vector(
        target_line,
        target_vertex_kind,
    )

    candidate_meeting_points: list[tuple[int, int]] = []

    supporting_intersection = supporting_line_intersection_point(
        source_line.get_vertex_segment(source_vertex_kind),
        target_line.get_vertex_segment(target_vertex_kind),
    )
    if supporting_intersection is not None:
        candidate_meeting_points.append(
            (
                int(round(supporting_intersection[0])),
                int(round(supporting_intersection[1])),
            )
        )

    if source_line.family_name == LineFamilyName.HORIZONTAL:
        candidate_meeting_points.append((target_vertex[0], source_vertex[1]))
    else:
        candidate_meeting_points.append((source_vertex[0], target_vertex[1]))

    candidate_meeting_points.extend(
        sorted(set(source_goal_points).intersection(reciprocal_goal_points))
    )

    best_point: tuple[int, int] | None = None
    best_key: tuple[float, float, float] | None = None
    for meeting_point in candidate_meeting_points:
        if not is_point_in_search_area(meeting_point, source_search_area):
            continue
        if not is_point_in_search_area(meeting_point, reciprocal_search_area):
            continue
        if not _is_forward_extension_point(
            source_vertex,
            source_extension_vector,
            meeting_point,
        ):
            continue
        if not _is_forward_extension_point(
            target_vertex,
            target_extension_vector,
            meeting_point,
        ):
            continue

        source_turn_angle = _compute_turn_angle_degrees(
            source_extension_vector,
            (
                meeting_point[0] - source_vertex[0],
                meeting_point[1] - source_vertex[1],
            ),
        )
        target_turn_angle = _compute_turn_angle_degrees(
            target_extension_vector,
            (
                meeting_point[0] - target_vertex[0],
                meeting_point[1] - target_vertex[1],
            ),
        )
        source_distance = math.hypot(
            meeting_point[0] - source_vertex[0],
            meeting_point[1] - source_vertex[1],
        )
        target_distance = math.hypot(
            meeting_point[0] - target_vertex[0],
            meeting_point[1] - target_vertex[1],
        )
        candidate_key = (
            source_turn_angle + target_turn_angle,
            max(source_turn_angle, target_turn_angle),
            source_distance + target_distance,
        )
        if best_key is None or candidate_key < best_key:
            best_key = candidate_key
            best_point = meeting_point

    return best_point


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

    source_goal_sets = build_cross_axis_goal_sets(
        binary_image,
        search_area,
        source_line,
        candidate.target_line,
        candidate.target_vertex_kind,
    )
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
        source_goal_sets,
    )

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
    reciprocal_goal_sets = build_cross_axis_goal_sets(
        binary_image,
        reciprocal_search_area,
        candidate.target_line,
        source_line,
        source_vertex_kind,
    )
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
        reciprocal_goal_sets,
    )

    if source_path_points is not None and reciprocal_path_points is not None:
        meeting_point = _choose_cross_axis_meeting_point(
            source_line,
            source_vertex_kind,
            search_area,
            _flatten_goal_sets(source_goal_sets),
            candidate.target_line,
            candidate.target_vertex_kind,
            reciprocal_search_area,
            _flatten_goal_sets(reciprocal_goal_sets),
        )
        if meeting_point is not None:
            source_added_segment_count = _add_direct_connection_segment(
                source_line,
                source_vertex_kind,
                meeting_point,
            )
            target_added_segment_count = _add_direct_connection_segment(
                candidate.target_line,
                candidate.target_vertex_kind,
                meeting_point,
            )
            if source_added_segment_count + target_added_segment_count > 0:
                return True

        source_added_segment_count = _add_direct_connection_segment(
            source_line,
            source_vertex_kind,
            source_path_points[-1],
        )
        target_added_segment_count = _add_direct_connection_segment(
            candidate.target_line,
            candidate.target_vertex_kind,
            reciprocal_path_points[-1],
        )
        if source_added_segment_count + target_added_segment_count > 0:
            return True

    if source_path_points is not None:
        return (
            _add_direct_connection_segment(
                source_line,
                source_vertex_kind,
                source_path_points[-1],
            )
            > 0
        )

    if reciprocal_path_points is not None:
        return (
            _add_direct_connection_segment(
                candidate.target_line,
                candidate.target_vertex_kind,
                reciprocal_path_points[-1],
            )
            > 0
        )

    return False


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

    source_vertex = source_line.get_vertex(source_vertex_kind)
    source_extension_vector = _build_extension_vector(
        source_line,
        source_vertex_kind,
    )
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

    contact_point = _choose_min_turn_contact_point(
        source_vertex,
        source_extension_vector,
        list(candidate.goal_points),
        preferred_contact_point=candidate.preferred_contact_point,
    )
    if contact_point is None:
        return False

    return _add_direct_connection_segment(
        source_line,
        source_vertex_kind,
        contact_point,
    ) > 0


__all__ = [
    "contains_logical_line",
    "remove_logical_line",
    "try_connect_cross_axis_candidate",
    "try_connect_cross_axis_span_candidate",
    "try_connect_same_axis_candidate",
]
