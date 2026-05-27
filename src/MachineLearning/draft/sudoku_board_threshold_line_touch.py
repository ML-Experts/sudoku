from __future__ import annotations

from dataclasses import replace

import numpy as np

from sudoku_board_threshold_line_geometry import (
    deduplicate_touch_points,
    direction_vector_from_angle,
    intersection_point_for_segments,
    normal_vector_from_angle,
    point_array,
    point_is_within_intervals,
)
from sudoku_board_threshold_models import MergedLine


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
            if intersection_point is None:
                continue
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


def merged_lines_touch(
    first_line: MergedLine,
    second_line: MergedLine,
    touch_tolerance_px: float,
) -> bool:
    return bool(
        touch_points_for_merged_lines(
            first_line,
            second_line,
            touch_tolerance_px,
        )
    )


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

    filtered_horizontal_lines = [
        horizontal_line
        for horizontal_line in horizontal_lines
        if horizontal_line.touching_point_count >= minimum_touch_point_count
    ]
    filtered_vertical_lines = [
        vertical_line
        for vertical_line in vertical_lines
        if vertical_line.touching_point_count >= minimum_touch_point_count
    ]
    return filtered_horizontal_lines, filtered_vertical_lines


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


def drop_zero_touch_lines(
    horizontal_lines: list[MergedLine],
    vertical_lines: list[MergedLine],
) -> tuple[list[MergedLine], list[MergedLine]]:
    filtered_horizontal_lines = [
        horizontal_line
        for horizontal_line in horizontal_lines
        if horizontal_line.touching_line_count > 0
    ]
    filtered_vertical_lines = [
        vertical_line
        for vertical_line in vertical_lines
        if vertical_line.touching_line_count > 0
    ]
    return filtered_horizontal_lines, filtered_vertical_lines


__all__ = [
    "annotate_cross_family_touches",
    "drop_zero_touch_lines",
    "filter_lines_by_min_cross_family_touch_points",
    "intersection_point_for_merged_lines",
    "iteratively_filter_lines_by_touch_points",
    "merged_lines_touch",
    "refresh_cross_family_touches",
    "touch_points_for_merged_lines",
]
