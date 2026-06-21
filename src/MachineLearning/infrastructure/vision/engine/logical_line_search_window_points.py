from __future__ import annotations

import numpy as np

from .logical_line_core import LogicalLine, LogicalLineVertexKind
from .logical_line_search_area import SearchArea, is_point_in_search_area
from .logical_line_segment_geometry import rasterize_line_points
from .models import LineSegment


def filter_white_points(
    binary_image: np.ndarray,
    points: list[tuple[int, int]],
    search_area: SearchArea,
) -> list[tuple[int, int]]:
    white_points: list[tuple[int, int]] = []
    for point in points:
        x_coord, y_coord = point
        if not is_point_in_search_area(point, search_area):
            continue
        if binary_image[y_coord, x_coord] != 255:
            continue
        white_points.append(point)
    return white_points


def build_segment_window_points(
    binary_image: np.ndarray,
    line_segment: LineSegment,
    search_area: SearchArea,
) -> list[tuple[int, int]]:
    return filter_white_points(
        binary_image,
        rasterize_line_points(line_segment.start, line_segment.end),
        search_area,
    )


def build_logical_line_window_points(
    binary_image: np.ndarray,
    logical_line: LogicalLine,
    search_area: SearchArea,
) -> list[tuple[int, int]]:
    seen_points: set[tuple[int, int]] = set()
    logical_line_points: list[tuple[int, int]] = []
    for line_segment in logical_line.line_segments:
        for point in build_segment_window_points(
            binary_image,
            line_segment,
            search_area,
        ):
            if point in seen_points:
                continue
            seen_points.add(point)
            logical_line_points.append(point)
    return logical_line_points


def build_start_points(
    binary_image: np.ndarray,
    source_line: LogicalLine,
    source_vertex_kind: LogicalLineVertexKind,
    search_area: SearchArea,
    start_tolerance_px: int,
) -> list[tuple[int, int]]:
    source_vertex = source_line.get_vertex(source_vertex_kind)
    source_segment = source_line.get_vertex_segment(source_vertex_kind)
    candidate_points = build_segment_window_points(
        binary_image,
        source_segment,
        search_area,
    )
    if (
        is_point_in_search_area(source_vertex, search_area)
        and binary_image[source_vertex[1], source_vertex[0]] == 255
        and source_vertex not in candidate_points
    ):
        candidate_points.append(source_vertex)

    start_points = [
        point
        for point in candidate_points
        if max(abs(point[0] - source_vertex[0]), abs(point[1] - source_vertex[1]))
        <= start_tolerance_px
    ]
    start_points.sort(
        key=lambda point: (
            max(
                abs(point[0] - source_vertex[0]),
                abs(point[1] - source_vertex[1]),
            ),
            abs(point[0] - source_vertex[0]) + abs(point[1] - source_vertex[1]),
        )
    )
    return start_points


__all__ = [
    "build_logical_line_window_points",
    "build_segment_window_points",
    "build_start_points",
]
