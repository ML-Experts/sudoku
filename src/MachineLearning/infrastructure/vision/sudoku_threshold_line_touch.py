from __future__ import annotations

from dataclasses import replace

import numpy as np

from infrastructure.vision.sudoku_threshold_geometry import (
    deduplicate_touch_points,
    direction_vector_from_angle,
    intersection_point_for_segments,
    normal_vector_from_angle,
    point_array,
    point_is_within_intervals,
    resolve_merged_line_vertices,
)
from infrastructure.vision.sudoku_threshold_models import EndpointConnection, MergedLine


def intersection_point_for_merged_lines(
    first_line: MergedLine,
    second_line: MergedLine,
) -> np.ndarray | None:
    first_direction = direction_vector_from_angle(first_line.family_angle_degrees)
    first_normal = normal_vector_from_angle(first_line.family_angle_degrees)
    second_direction = direction_vector_from_angle(second_line.family_angle_degrees)
    second_normal = normal_vector_from_angle(second_line.family_angle_degrees)
    first_anchor = first_normal * first_line.projection
    second_anchor = second_normal * second_line.projection
    system_matrix = np.column_stack((first_direction, -second_direction))
    determinant = float(np.linalg.det(system_matrix))
    if abs(determinant) <= 1e-6:
        return None

    try:
        first_scale, _ = np.linalg.solve(system_matrix, second_anchor - first_anchor)
    except np.linalg.LinAlgError:
        return None

    return first_anchor + first_direction * first_scale


def touch_points_for_merged_lines(
    first_line: MergedLine,
    second_line: MergedLine,
    touch_tolerance_px: float,
) -> tuple[tuple[int, int], ...]:
    raw_touch_points: list[np.ndarray] = []
    for first_segment in first_line.segments:
        for second_segment in second_line.segments:
            intersection_point = intersection_point_for_segments(
                first_segment,
                second_segment,
                touch_tolerance_px,
            )
            if intersection_point is not None:
                raw_touch_points.append(intersection_point)

    if raw_touch_points:
        return deduplicate_touch_points(raw_touch_points, touch_tolerance_px)

    intersection_point = intersection_point_for_merged_lines(first_line, second_line)
    if intersection_point is None:
        return ()

    first_direction = direction_vector_from_angle(first_line.family_angle_degrees)
    second_direction = direction_vector_from_angle(second_line.family_angle_degrees)
    first_position = float(np.dot(intersection_point, first_direction))
    second_position = float(np.dot(intersection_point, second_direction))
    if not (
        point_is_within_intervals(
            first_position,
            first_line.support_intervals,
            touch_tolerance_px,
        )
        and point_is_within_intervals(
            second_position,
            second_line.support_intervals,
            touch_tolerance_px,
        )
    ):
        return ()

    return deduplicate_touch_points([intersection_point], touch_tolerance_px)


def annotate_cross_family_touches(
    horizontal_lines: list[MergedLine],
    vertical_lines: list[MergedLine],
    touch_tolerance_px: float,
) -> tuple[list[MergedLine], list[MergedLine]]:
    horizontal_touch_indices: list[list[int]] = [[] for _ in horizontal_lines]
    vertical_touch_indices: list[list[int]] = [[] for _ in vertical_lines]
    horizontal_touch_points: list[list[np.ndarray]] = [[] for _ in horizontal_lines]
    vertical_touch_points: list[list[np.ndarray]] = [[] for _ in vertical_lines]

    for horizontal_index, horizontal_line in enumerate(horizontal_lines):
        for vertical_index, vertical_line in enumerate(vertical_lines):
            touch_points = touch_points_for_merged_lines(
                horizontal_line,
                vertical_line,
                touch_tolerance_px,
            )
            if not touch_points:
                continue
            horizontal_touch_indices[horizontal_index].append(vertical_index)
            vertical_touch_indices[vertical_index].append(horizontal_index)
            horizontal_touch_points[horizontal_index].extend(
                point_array(touch_point) for touch_point in touch_points
            )
            vertical_touch_points[vertical_index].extend(
                point_array(touch_point) for touch_point in touch_points
            )

    annotated_horizontal_lines = [
        replace(
            horizontal_line,
            touching_line_count=len(horizontal_touch_indices[index]),
            touching_line_indices=tuple(horizontal_touch_indices[index]),
            touching_point_count=len(
                deduplicate_touch_points(
                    horizontal_touch_points[index],
                    touch_tolerance_px,
                )
            ),
            touching_points=deduplicate_touch_points(
                horizontal_touch_points[index],
                touch_tolerance_px,
            ),
        )
        for index, horizontal_line in enumerate(horizontal_lines)
    ]
    annotated_vertical_lines = [
        replace(
            vertical_line,
            touching_line_count=len(vertical_touch_indices[index]),
            touching_line_indices=tuple(vertical_touch_indices[index]),
            touching_point_count=len(
                deduplicate_touch_points(
                    vertical_touch_points[index],
                    touch_tolerance_px,
                )
            ),
            touching_points=deduplicate_touch_points(
                vertical_touch_points[index],
                touch_tolerance_px,
            ),
        )
        for index, vertical_line in enumerate(vertical_lines)
    ]

    return annotated_horizontal_lines, annotated_vertical_lines


def filter_lines_by_min_cross_family_touch_points(
    horizontal_lines: list[MergedLine],
    vertical_lines: list[MergedLine],
    minimum_touch_point_count: int,
) -> tuple[list[MergedLine], list[MergedLine]]:
    if minimum_touch_point_count <= 0:
        return horizontal_lines, vertical_lines

    return (
        [
            horizontal_line
            for horizontal_line in horizontal_lines
            if horizontal_line.touching_point_count >= minimum_touch_point_count
        ],
        [
            vertical_line
            for vertical_line in vertical_lines
            if vertical_line.touching_point_count >= minimum_touch_point_count
        ],
    )


def refresh_cross_family_touches(
    horizontal_lines: list[MergedLine],
    vertical_lines: list[MergedLine],
    touch_tolerance_px: float,
) -> tuple[list[MergedLine], list[MergedLine]]:
    return annotate_cross_family_touches(
        horizontal_lines,
        vertical_lines,
        touch_tolerance_px,
    )


def iteratively_filter_lines_by_touch_points(
    horizontal_lines: list[MergedLine],
    vertical_lines: list[MergedLine],
    minimum_touch_point_count: int,
    touch_tolerance_px: float,
) -> tuple[list[MergedLine], list[MergedLine]]:
    if minimum_touch_point_count <= 0:
        return refresh_cross_family_touches(
            horizontal_lines,
            vertical_lines,
            touch_tolerance_px,
        )

    current_horizontal_lines, current_vertical_lines = refresh_cross_family_touches(
        horizontal_lines,
        vertical_lines,
        touch_tolerance_px,
    )
    while True:
        filtered_horizontal_lines, filtered_vertical_lines = (
            filter_lines_by_min_cross_family_touch_points(
                current_horizontal_lines,
                current_vertical_lines,
                minimum_touch_point_count,
            )
        )
        if (
            len(filtered_horizontal_lines) == len(current_horizontal_lines)
            and len(filtered_vertical_lines) == len(current_vertical_lines)
        ):
            return current_horizontal_lines, current_vertical_lines

        current_horizontal_lines, current_vertical_lines = refresh_cross_family_touches(
            filtered_horizontal_lines,
            filtered_vertical_lines,
            touch_tolerance_px,
        )


def _nearest_touch_candidate_for_vertex(
    line: MergedLine,
    line_index: int,
    vertex_index: int,
    opposite_lines: list[MergedLine],
    touch_tolerance_px: float,
) -> dict[str, int | tuple[int, int] | float] | None:
    line_vertices = resolve_merged_line_vertices(line)
    line_vertex = line_vertices[vertex_index]
    best_candidate: dict[str, int | tuple[int, int] | float] | None = None

    for opposite_index, opposite_line in enumerate(opposite_lines):
        touch_points = touch_points_for_merged_lines(
            line,
            opposite_line,
            touch_tolerance_px,
        )
        if not touch_points:
            continue

        opposite_vertices = resolve_merged_line_vertices(opposite_line)
        nearest_touch_point = min(
            touch_points,
            key=lambda touch_point: float(
                np.hypot(
                    touch_point[0] - line_vertex[0],
                    touch_point[1] - line_vertex[1],
                )
            ),
        )
        nearest_touch_distance = float(
            np.hypot(
                nearest_touch_point[0] - line_vertex[0],
                nearest_touch_point[1] - line_vertex[1],
            )
        )
        opposite_vertex_index = min(
            range(2),
            key=lambda candidate_index: float(
                np.hypot(
                    opposite_vertices[candidate_index][0] - line_vertex[0],
                    opposite_vertices[candidate_index][1] - line_vertex[1],
                )
            ),
        )
        opposite_vertex = opposite_vertices[opposite_vertex_index]
        vertex_distance = float(
            np.hypot(
                opposite_vertex[0] - line_vertex[0],
                opposite_vertex[1] - line_vertex[1],
            )
        )
        candidate = {
            "line_index": line_index,
            "vertex_index": vertex_index,
            "vertex": line_vertex,
            "opposite_line_index": opposite_index,
            "opposite_vertex_index": opposite_vertex_index,
            "opposite_vertex": opposite_vertex,
            "touch_point": nearest_touch_point,
            "touch_distance": nearest_touch_distance,
            "vertex_distance": vertex_distance,
        }
        if best_candidate is None:
            best_candidate = candidate
            continue
        if float(candidate["touch_distance"]) < float(best_candidate["touch_distance"]):
            best_candidate = candidate
            continue
        if (
            float(candidate["touch_distance"]) == float(best_candidate["touch_distance"])
            and float(candidate["vertex_distance"])
            < float(best_candidate["vertex_distance"])
        ):
            best_candidate = candidate

    return best_candidate


def resolve_last_touch_endpoint_connections(
    horizontal_lines: list[MergedLine],
    vertical_lines: list[MergedLine],
    touch_tolerance_px: float,
) -> tuple[
    tuple[tuple[tuple[int, int], tuple[int, int]], ...],
    tuple[tuple[tuple[int, int], tuple[int, int]], ...],
    tuple[EndpointConnection, ...],
]:
    horizontal_vertices = [
        list(resolve_merged_line_vertices(merged_line))
        for merged_line in horizontal_lines
    ]
    vertical_vertices = [
        list(resolve_merged_line_vertices(merged_line))
        for merged_line in vertical_lines
    ]
    horizontal_candidates: dict[
        tuple[int, int], dict[str, int | tuple[int, int] | float]
    ] = {}
    vertical_candidates: dict[
        tuple[int, int], dict[str, int | tuple[int, int] | float]
    ] = {}

    for horizontal_index, horizontal_line in enumerate(horizontal_lines):
        for vertex_index in range(2):
            candidate = _nearest_touch_candidate_for_vertex(
                horizontal_line,
                horizontal_index,
                vertex_index,
                vertical_lines,
                touch_tolerance_px,
            )
            if candidate is not None:
                horizontal_candidates[(horizontal_index, vertex_index)] = candidate

    for vertical_index, vertical_line in enumerate(vertical_lines):
        for vertex_index in range(2):
            candidate = _nearest_touch_candidate_for_vertex(
                vertical_line,
                vertical_index,
                vertex_index,
                horizontal_lines,
                touch_tolerance_px,
            )
            if candidate is not None:
                vertical_candidates[(vertical_index, vertex_index)] = candidate

    endpoint_connections: list[EndpointConnection] = []
    for horizontal_key, horizontal_candidate in horizontal_candidates.items():
        vertical_key = (
            int(horizontal_candidate["opposite_line_index"]),
            int(horizontal_candidate["opposite_vertex_index"]),
        )
        vertical_candidate = vertical_candidates.get(vertical_key)
        if vertical_candidate is None:
            continue
        if (
            int(vertical_candidate["opposite_line_index"]) != horizontal_key[0]
            or int(vertical_candidate["opposite_vertex_index"]) != horizontal_key[1]
        ):
            continue

        horizontal_vertex = (
            int(horizontal_candidate["vertex"][0]),
            int(horizontal_candidate["vertex"][1]),
        )
        vertical_vertex = (
            int(horizontal_candidate["opposite_vertex"][0]),
            int(horizontal_candidate["opposite_vertex"][1]),
        )
        aligned_point = (vertical_vertex[0], horizontal_vertex[1])
        touch_point = (
            int(horizontal_candidate["touch_point"][0]),
            int(horizontal_candidate["touch_point"][1]),
        )
        horizontal_vertices[horizontal_key[0]][horizontal_key[1]] = aligned_point
        vertical_vertices[vertical_key[0]][vertical_key[1]] = aligned_point
        endpoint_connections.append(
            EndpointConnection(
                horizontal_line_index=horizontal_key[0],
                horizontal_vertex_index=horizontal_key[1],
                vertical_line_index=vertical_key[0],
                vertical_vertex_index=vertical_key[1],
                horizontal_vertex=horizontal_vertex,
                vertical_vertex=vertical_vertex,
                aligned_point=aligned_point,
                touch_point=touch_point,
            )
        )

    return (
        tuple(
            (tuple(line_vertices[0]), tuple(line_vertices[1]))
            for line_vertices in horizontal_vertices
        ),
        tuple(
            (tuple(line_vertices[0]), tuple(line_vertices[1]))
            for line_vertices in vertical_vertices
        ),
        tuple(endpoint_connections),
    )
