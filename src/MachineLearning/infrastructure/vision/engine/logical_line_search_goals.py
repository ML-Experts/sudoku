from __future__ import annotations

import numpy as np

from .logical_line_core import LogicalLine, LogicalLineVertexKind
from .logical_line_search_area import SearchArea
from .logical_line_search_window_points import (
    build_logical_line_window_points,
    build_segment_window_points,
)
from .models import LineFamilyName


def build_cross_axis_span_goal_points(
    binary_image: np.ndarray,
    search_area: SearchArea,
    source_line: LogicalLine,
    target_line: LogicalLine,
    source_cross_axis_anchor: int,
) -> list[tuple[int, int]]:
    target_points = build_logical_line_window_points(
        binary_image,
        target_line,
        search_area,
    )
    if not target_points:
        return []

    if source_line.family_name == LineFamilyName.HORIZONTAL:
        best_anchor_distance = min(
            abs(point[1] - source_cross_axis_anchor) for point in target_points
        )
        return [
            point
            for point in target_points
            if abs(point[1] - source_cross_axis_anchor) == best_anchor_distance
        ]

    best_anchor_distance = min(
        abs(point[0] - source_cross_axis_anchor) for point in target_points
    )
    return [
        point
        for point in target_points
        if abs(point[0] - source_cross_axis_anchor) == best_anchor_distance
    ]


def build_same_axis_goal_sets(
    binary_image: np.ndarray,
    search_area: SearchArea,
    target_line: LogicalLine,
    target_vertex_kind: LogicalLineVertexKind,
) -> list[list[tuple[int, int]]]:
    goal_sets: list[list[tuple[int, int]]] = []
    target_vertex = target_line.get_vertex(target_vertex_kind)
    if (
        search_area.min_x <= target_vertex[0] <= search_area.max_x
        and search_area.min_y <= target_vertex[1] <= search_area.max_y
        and search_area.mask[target_vertex[1], target_vertex[0]]
        and binary_image[target_vertex[1], target_vertex[0]] == 255
    ):
        goal_sets.append([target_vertex])

    target_segment = target_line.get_vertex_segment(target_vertex_kind)
    segment_window_points = build_segment_window_points(
        binary_image,
        target_segment,
        search_area,
    )
    if segment_window_points:
        goal_sets.append(segment_window_points)

    return goal_sets


def build_cross_axis_goal_band(
    binary_image: np.ndarray,
    search_area: SearchArea,
    source_line: LogicalLine,
    target_vertex: tuple[int, int],
) -> list[tuple[int, int]]:
    goal_points: list[tuple[int, int]] = []
    if source_line.family_name == LineFamilyName.HORIZONTAL:
        target_x = target_vertex[0]
        if target_x < search_area.min_x or target_x > search_area.max_x:
            return []
        for y_coord in range(search_area.min_y, search_area.max_y + 1):
            if not search_area.mask[y_coord, target_x]:
                continue
            if binary_image[y_coord, target_x] != 255:
                continue
            goal_points.append((target_x, y_coord))
        return goal_points

    target_y = target_vertex[1]
    if target_y < search_area.min_y or target_y > search_area.max_y:
        return []
    for x_coord in range(search_area.min_x, search_area.max_x + 1):
        if not search_area.mask[target_y, x_coord]:
            continue
        if binary_image[target_y, x_coord] != 255:
            continue
        goal_points.append((x_coord, target_y))
    return goal_points


def build_cross_axis_goal_sets(
    binary_image: np.ndarray,
    search_area: SearchArea,
    source_line: LogicalLine,
    target_line: LogicalLine,
    target_vertex_kind: LogicalLineVertexKind,
) -> list[list[tuple[int, int]]]:
    target_vertex = target_line.get_vertex(target_vertex_kind)
    goal_sets = build_same_axis_goal_sets(
        binary_image,
        search_area,
        target_line,
        target_vertex_kind,
    )
    goal_band = build_cross_axis_goal_band(
        binary_image,
        search_area,
        source_line,
        target_vertex,
    )
    if goal_band:
        goal_sets.append(goal_band)
    return goal_sets


__all__ = [
    "build_cross_axis_goal_sets",
    "build_cross_axis_span_goal_points",
    "build_same_axis_goal_sets",
]
