from __future__ import annotations

from collections import deque

import numpy as np

from .geometry import build_line_segment_from_points
from .logical_line_core import LogicalLine
from .logical_line_search_area import SearchArea, is_point_in_search_area
from .logical_line_segment_geometry import rasterize_line_points
from .models import LineFamilyName, LineSegment, SegmentOrigin


def reconstruct_path(
    parents: dict[tuple[int, int], tuple[int, int] | None],
    terminal_point: tuple[int, int],
) -> list[tuple[int, int]]:
    path: list[tuple[int, int]] = []
    current_point: tuple[int, int] | None = terminal_point
    while current_point is not None:
        path.append(current_point)
        current_point = parents[current_point]
    path.reverse()
    return path


def find_white_pixel_path_bfs(
    binary_image: np.ndarray,
    search_area: SearchArea,
    start_points: list[tuple[int, int]],
    goal_points: list[tuple[int, int]],
) -> list[tuple[int, int]] | None:
    if not start_points or not goal_points:
        return None

    goal_set = set(goal_points)
    queue: deque[tuple[int, int]] = deque()
    parents: dict[tuple[int, int], tuple[int, int] | None] = {}

    for point in start_points:
        if point in parents:
            continue
        parents[point] = None
        queue.append(point)

    neighbors = ((1, 0), (-1, 0), (0, 1), (0, -1))
    max_width = binary_image.shape[1]
    max_height = binary_image.shape[0]

    while queue:
        current_point = queue.popleft()
        if current_point in goal_set:
            return reconstruct_path(parents, current_point)

        current_x, current_y = current_point
        for delta_x, delta_y in neighbors:
            next_point = (current_x + delta_x, current_y + delta_y)
            next_x, next_y = next_point
            if next_x < 0 or next_x >= max_width or next_y < 0 or next_y >= max_height:
                continue
            if next_point in parents:
                continue
            if not is_point_in_search_area(next_point, search_area):
                continue
            if binary_image[next_y, next_x] != 255:
                continue
            parents[next_point] = current_point
            queue.append(next_point)

    return None


def try_find_path(
    binary_image: np.ndarray,
    search_area: SearchArea,
    start_points: list[tuple[int, int]],
    goal_sets: list[list[tuple[int, int]]],
) -> list[tuple[int, int]] | None:
    for goal_points in goal_sets:
        path_points = find_white_pixel_path_bfs(
            binary_image,
            search_area,
            start_points,
            goal_points,
        )
        if path_points is not None:
            return path_points
    return None


def is_path_white_and_in_search_area(
    binary_image: np.ndarray,
    search_area: SearchArea,
    path_points: list[tuple[int, int]],
) -> bool:
    for point in path_points:
        x_coord, y_coord = point
        if not is_point_in_search_area(point, search_area):
            return False
        if binary_image[y_coord, x_coord] != 255:
            return False
    return True


def try_find_straight_path(
    binary_image: np.ndarray,
    search_area: SearchArea,
    start_points: list[tuple[int, int]],
    goal_points: list[tuple[int, int]],
) -> list[tuple[int, int]] | None:
    candidate_pairs: list[
        tuple[int, float, int, tuple[int, int], tuple[int, int]]
    ] = []
    for start_rank, start_point in enumerate(start_points):
        for goal_point in goal_points:
            delta_x = goal_point[0] - start_point[0]
            delta_y = goal_point[1] - start_point[1]
            candidate_pairs.append(
                (
                    start_rank,
                    float(np.hypot(delta_x, delta_y)),
                    abs(delta_x) + abs(delta_y),
                    start_point,
                    goal_point,
                )
            )

    candidate_pairs.sort(key=lambda item: (item[0], item[1], item[2]))
    for _, _, _, start_point, goal_point in candidate_pairs:
        path_points = rasterize_line_points(start_point, goal_point)
        if is_path_white_and_in_search_area(
            binary_image,
            search_area,
            path_points,
        ):
            return path_points
    return None


def path_to_segments(
    path_points: list[tuple[int, int]],
    family_name: LineFamilyName,
    origin: SegmentOrigin,
) -> list[LineSegment]:
    if len(path_points) < 2:
        return []

    segments: list[LineSegment] = []
    run_start = path_points[0]
    previous_point = path_points[0]
    previous_direction = (
        path_points[1][0] - path_points[0][0],
        path_points[1][1] - path_points[0][1],
    )

    for current_point in path_points[1:]:
        current_direction = (
            current_point[0] - previous_point[0],
            current_point[1] - previous_point[1],
        )
        if current_direction != previous_direction:
            if run_start != previous_point:
                segments.append(
                    build_line_segment_from_points(
                        run_start,
                        previous_point,
                        family_name=family_name,
                        origin=origin,
                    )
                )
            run_start = previous_point
            previous_direction = current_direction
        previous_point = current_point

    if run_start != previous_point:
        segments.append(
            build_line_segment_from_points(
                run_start,
                previous_point,
                family_name=family_name,
                origin=origin,
            )
        )

    return segments


def add_path_segments(
    logical_line: LogicalLine,
    path_points: list[tuple[int, int]],
    origin: SegmentOrigin,
) -> int:
    added_segment_count = 0
    for line_segment in path_to_segments(
        path_points,
        family_name=logical_line.family_name,
        origin=origin,
    ):
        if logical_line.add_segment(line_segment):
            added_segment_count += 1
    return added_segment_count


__all__ = [
    "add_path_segments",
    "try_find_path",
    "try_find_straight_path",
]
