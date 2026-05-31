from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math

import numpy as np

from raw_line_family_only_logical_line_core import (
    LogicalLine,
    LogicalLineVertexKind,
)
from raw_line_family_only_logical_line_search import (
    SearchArea,
    add_path_segments,
    build_cross_axis_goal_sets,
    build_cross_axis_span_goal_points,
    build_same_axis_goal_sets,
    build_search_area,
    build_start_points,
    is_point_in_search_area,
    try_find_straight_path,
    try_find_path,
)
from raw_line_family_only_models import SegmentOrigin


class ConnectionKind(Enum):
    SAME_AXIS = "same_axis"
    CROSS_AXIS = "cross_axis"
    CROSS_AXIS_SPAN = "cross_axis_span"


@dataclass(frozen=True, slots=True)
class ConnectionCandidate:
    connection_kind: ConnectionKind
    target_line: LogicalLine
    target_vertex_kind: LogicalLineVertexKind | None
    distance_px: float
    goal_points: tuple[tuple[int, int], ...] = ()
    preferred_contact_point: tuple[int, int] | None = None


def distance_between_vertices(
    first_vertex: tuple[int, int],
    second_vertex: tuple[int, int],
) -> float:
    return math.hypot(
        first_vertex[0] - second_vertex[0],
        first_vertex[1] - second_vertex[1],
    )


def build_candidate_sort_key(
    candidate: ConnectionCandidate,
) -> tuple[int, float]:
    connection_kind_priority = {
        ConnectionKind.SAME_AXIS: 0,
        ConnectionKind.CROSS_AXIS: 1,
        ConnectionKind.CROSS_AXIS_SPAN: 2,
    }[candidate.connection_kind]
    return connection_kind_priority, candidate.distance_px


def get_source_cross_axis_anchor(
    source_line: LogicalLine,
    source_vertex_kind: LogicalLineVertexKind,
) -> int:
    if source_vertex_kind == LogicalLineVertexKind.START:
        return source_line.cross_axis_start
    return source_line.cross_axis_end


def collect_connection_candidates(
    binary_image: np.ndarray,
    source_line: LogicalLine,
    source_vertex_kind: LogicalLineVertexKind,
    search_area: SearchArea,
    same_axis_lines: list[LogicalLine],
    cross_axis_lines: list[LogicalLine],
) -> list[ConnectionCandidate]:
    source_vertex = source_line.get_vertex(source_vertex_kind)
    source_cross_axis_anchor = get_source_cross_axis_anchor(
        source_line,
        source_vertex_kind,
    )
    candidates: list[ConnectionCandidate] = []

    def collect_from_lines(
        target_lines: list[LogicalLine],
        connection_kind: ConnectionKind,
    ) -> None:
        for target_line in target_lines:
            if target_line is source_line:
                continue
            for target_vertex_kind in LogicalLineVertexKind:
                target_vertex = target_line.get_vertex(target_vertex_kind)
                if not is_point_in_search_area(target_vertex, search_area):
                    continue
                candidates.append(
                    ConnectionCandidate(
                        connection_kind=connection_kind,
                        target_line=target_line,
                        target_vertex_kind=target_vertex_kind,
                        distance_px=distance_between_vertices(
                            source_vertex,
                            target_vertex,
                        ),
                    )
                )

    def collect_cross_axis_span_candidates() -> None:
        for target_line in cross_axis_lines:
            if not (
                target_line.axis_start
                <= source_cross_axis_anchor
                <= target_line.axis_end
            ):
                continue

            goal_points = build_cross_axis_span_goal_points(
                binary_image,
                search_area,
                source_line,
                target_line,
                source_cross_axis_anchor,
            )
            if not goal_points:
                continue

            preferred_contact_point = min(
                goal_points,
                key=lambda point: distance_between_vertices(source_vertex, point),
            )
            candidates.append(
                ConnectionCandidate(
                    connection_kind=ConnectionKind.CROSS_AXIS_SPAN,
                    target_line=target_line,
                    target_vertex_kind=None,
                    distance_px=distance_between_vertices(
                        source_vertex,
                        preferred_contact_point,
                    ),
                    goal_points=tuple(goal_points),
                    preferred_contact_point=preferred_contact_point,
                )
            )

    collect_from_lines(same_axis_lines, ConnectionKind.SAME_AXIS)
    collect_from_lines(cross_axis_lines, ConnectionKind.CROSS_AXIS)
    collect_cross_axis_span_candidates()
    candidates.sort(key=build_candidate_sort_key)
    return candidates


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


def connect_logical_lines_by_pixels(
    binary_image: np.ndarray,
    horizontal_logical_lines: list[LogicalLine],
    vertical_logical_lines: list[LogicalLine],
    axis_gap_tolerance_px: int,
    cross_axis_thickness_px: int,
    rectangle_vector_length_px: int,
    rectangle_padding_px: int,
) -> tuple[list[LogicalLine], list[LogicalLine]]:
    connected_horizontal_lines = list(horizontal_logical_lines)
    connected_vertical_lines = list(vertical_logical_lines)
    has_changes = True

    while has_changes:
        has_changes = False
        for source_lines, same_axis_lines, cross_axis_lines in (
            (
                connected_horizontal_lines,
                connected_horizontal_lines,
                connected_vertical_lines,
            ),
            (
                connected_vertical_lines,
                connected_vertical_lines,
                connected_horizontal_lines,
            ),
        ):
            for source_line in list(source_lines):
                if not contains_logical_line(source_lines, source_line):
                    continue
                for source_vertex_kind in LogicalLineVertexKind:
                    source_vertex = source_line.get_vertex(source_vertex_kind)
                    tolerance_rectangle = source_line.build_tolerance_rectangle(
                        reference_vertex=source_vertex,
                        direction_length=rectangle_vector_length_px,
                        padding=rectangle_padding_px,
                    )
                    search_area = build_search_area(
                        binary_image.shape,
                        tolerance_rectangle,
                    )
                    connection_candidates = collect_connection_candidates(
                        binary_image,
                        source_line,
                        source_vertex_kind,
                        search_area,
                        same_axis_lines,
                        cross_axis_lines,
                    )
                    for candidate in connection_candidates:
                        if candidate.connection_kind == ConnectionKind.SAME_AXIS:
                            was_connected = try_connect_same_axis_candidate(
                                binary_image,
                                source_line,
                                source_vertex_kind,
                                search_area,
                                candidate,
                                axis_gap_tolerance_px=axis_gap_tolerance_px,
                                same_axis_lines=same_axis_lines,
                            )
                        elif candidate.connection_kind == ConnectionKind.CROSS_AXIS:
                            was_connected = try_connect_cross_axis_candidate(
                                binary_image,
                                source_line,
                                source_vertex_kind,
                                search_area,
                                candidate,
                                axis_gap_tolerance_px=axis_gap_tolerance_px,
                                cross_axis_thickness_px=cross_axis_thickness_px,
                                rectangle_vector_length_px=rectangle_vector_length_px,
                                rectangle_padding_px=rectangle_padding_px,
                            )
                        else:
                            was_connected = try_connect_cross_axis_span_candidate(
                                binary_image,
                                source_line,
                                source_vertex_kind,
                                search_area,
                                candidate,
                                axis_gap_tolerance_px=axis_gap_tolerance_px,
                                cross_axis_thickness_px=cross_axis_thickness_px,
                            )

                        if not was_connected:
                            continue

                        has_changes = True
                        break

                    if has_changes:
                        break
                if has_changes:
                    break
            if has_changes:
                break

    return connected_horizontal_lines, connected_vertical_lines


__all__ = [
    "connect_logical_lines_by_pixels",
]
