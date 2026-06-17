from __future__ import annotations

import numpy as np

from logical_line_core import (
    LogicalLine,
    LogicalLineVertexKind,
)
from logical_line_connection_candidates import (
    collect_connection_candidates,
)
from logical_line_connection_execution import (
    contains_logical_line,
    try_connect_cross_axis_candidate,
    try_connect_cross_axis_span_candidate,
    try_connect_same_axis_candidate,
)
from logical_line_connection_types import ConnectionKind
from logical_line_search_area import build_search_area

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
