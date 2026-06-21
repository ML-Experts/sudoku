from __future__ import annotations

import numpy as np

from logical_line_core import LogicalLine
from logical_line_search_area import build_search_area, is_point_in_search_area
from logical_line_search_pathfinding import try_find_path, try_find_straight_path
from logical_line_search_window_points import build_logical_line_window_points
from models import LineFamilyName, ToleranceRectangle


def try_find_white_path_from_point_to_logical_line(
    binary_image: np.ndarray,
    perspective_vertex: tuple[int, int],
    target_line: LogicalLine,
) -> list[tuple[int, int]] | None:
    perspective_x, perspective_y = perspective_vertex

    vector_length = 20
    if target_line.family_name == LineFamilyName.HORIZONTAL:
        target_axis_start = target_line.axis_start
        target_axis_end = target_line.axis_end
        target_cross_min = min(
            target_line.cross_axis_start,
            target_line.cross_axis_end,
        )
        target_cross_max = max(
            target_line.cross_axis_start,
            target_line.cross_axis_end,
        )

        if perspective_y < target_cross_min:
            direction = (0.0, 1.0)
        elif perspective_y > target_cross_max:
            direction = (0.0, -1.0)
        elif perspective_x < target_axis_start:
            direction = (1.0, 0.0)
        elif perspective_x > target_axis_end:
            direction = (-1.0, 0.0)
        else:
            distance_up = abs(perspective_y - target_cross_min)
            distance_down = abs(target_cross_max - perspective_y)
            if distance_up <= distance_down:
                direction = (0.0, -1.0)
            else:
                direction = (0.0, 1.0)

        axis_offset = 0
        if perspective_x < target_axis_start:
            axis_offset = target_axis_start - perspective_x
        elif perspective_x > target_axis_end:
            axis_offset = perspective_x - target_axis_end

        padding = max(2, axis_offset + 2)

    elif target_line.family_name == LineFamilyName.VERTICAL:
        target_axis_start = target_line.axis_start
        target_axis_end = target_line.axis_end
        target_cross_min = min(
            target_line.cross_axis_start,
            target_line.cross_axis_end,
        )
        target_cross_max = max(
            target_line.cross_axis_start,
            target_line.cross_axis_end,
        )

        if perspective_x < target_cross_min:
            direction = (1.0, 0.0)
        elif perspective_x > target_cross_max:
            direction = (-1.0, 0.0)
        elif perspective_y < target_axis_start:
            direction = (0.0, 1.0)
        elif perspective_y > target_axis_end:
            direction = (0.0, -1.0)
        else:
            distance_left = abs(perspective_x - target_cross_min)
            distance_right = abs(target_cross_max - perspective_x)
            if distance_left <= distance_right:
                direction = (-1.0, 0.0)
            else:
                direction = (1.0, 0.0)

        axis_offset = 0
        if perspective_y < target_axis_start:
            axis_offset = target_axis_start - perspective_y
        elif perspective_y > target_axis_end:
            axis_offset = perspective_y - target_axis_end

        padding = max(2, axis_offset + 2)

    else:
        raise NotImplementedError(
            "Point-to-line white path search is available only for classified logical lines."
        )

    tolerance_rectangle = ToleranceRectangle(
        reference_point=perspective_vertex,
        recognition_vector=direction,
        vector_length=max(1, vector_length),
        padding=padding,
    )
    search_area = build_search_area(
        binary_image.shape,
        tolerance_rectangle,
    )

    start_points: list[tuple[int, int]] = []
    for delta_y in (0, -1, 1):
        for delta_x in (0, -1, 1):
            point = (perspective_x + delta_x, perspective_y + delta_y)
            if not is_point_in_search_area(point, search_area):
                continue
            point_x, point_y = point
            if binary_image[point_y, point_x] != 255:
                continue
            start_points.append(point)

    start_points = sorted(
        set(start_points),
        key=lambda point: (
            max(abs(point[0] - perspective_x), abs(point[1] - perspective_y)),
            abs(point[0] - perspective_x) + abs(point[1] - perspective_y),
        ),
    )
    if not start_points:
        return None

    goal_points = build_logical_line_window_points(
        binary_image,
        target_line,
        search_area,
    )
    if not goal_points:
        return None

    goal_set = set(goal_points)
    for start_point in start_points:
        if start_point in goal_set:
            return [start_point]

    straight_path = try_find_straight_path(
        binary_image,
        search_area,
        start_points,
        goal_points,
    )
    if straight_path is not None:
        return straight_path

    return try_find_path(
        binary_image,
        search_area,
        start_points,
        [goal_points],
    )


__all__ = [
    "try_find_white_path_from_point_to_logical_line",
]
