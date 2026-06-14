from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import cv2
import numpy as np

from geometry import build_line_segment_from_points
from logical_line_core import (
    LogicalLine,
    LogicalLineVertexKind,
)
from models import (
    LineFamilyName,
    LineSegment,
    SegmentOrigin,
    ToleranceRectangle,
)


@dataclass(frozen=True, slots=True)
class SearchArea:
    mask: np.ndarray
    min_x: int
    max_x: int
    min_y: int
    max_y: int


def build_search_area(
    image_shape: tuple[int, int],
    tolerance_rectangle: ToleranceRectangle,
) -> SearchArea:
    mask = np.zeros(image_shape[:2], dtype=np.uint8)
    corners = np.array(tolerance_rectangle.corners, dtype=np.int32)
    cv2.fillConvexPoly(mask, corners, 1)
    x_coordinates = corners[:, 0]
    y_coordinates = corners[:, 1]
    max_width = image_shape[1] - 1
    max_height = image_shape[0] - 1
    return SearchArea(
        mask=mask.astype(bool),
        min_x=max(0, int(x_coordinates.min())),
        max_x=min(max_width, int(x_coordinates.max())),
        min_y=max(0, int(y_coordinates.min())),
        max_y=min(max_height, int(y_coordinates.max())),
    )


def is_point_in_search_area(
    point: tuple[int, int],
    search_area: SearchArea,
) -> bool:
    x_coord, y_coord = point
    if (
        x_coord < search_area.min_x
        or x_coord > search_area.max_x
        or y_coord < search_area.min_y
        or y_coord > search_area.max_y
    ):
        return False
    return bool(search_area.mask[y_coord, x_coord])


def rasterize_line_points(
    start: tuple[int, int],
    end: tuple[int, int],
) -> list[tuple[int, int]]:
    delta_x = end[0] - start[0]
    delta_y = end[1] - start[1]
    step_count = max(abs(delta_x), abs(delta_y))
    if step_count == 0:
        return [start]

    points: list[tuple[int, int]] = []
    for step_index in range(step_count + 1):
        ratio = step_index / float(step_count)
        point = (
            int(round(start[0] + delta_x * ratio)),
            int(round(start[1] + delta_y * ratio)),
        )
        if not points or points[-1] != point:
            points.append(point)
    return points


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
            max(abs(point[0] - source_vertex[0]), abs(point[1] - source_vertex[1])),
            abs(point[0] - source_vertex[0]) + abs(point[1] - source_vertex[1]),
        )
    )
    return start_points


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
        is_point_in_search_area(target_vertex, search_area)
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


from logical_line_core import LogicalLine
from models import LineFamilyName, ToleranceRectangle

def try_find_white_path_from_point_to_logical_line(
    binary_image: np.ndarray,
    perspective_vertex: tuple[int, int],
    target_line: LogicalLine,
) -> list[tuple[int, int]] | None:
    perspective_x, perspective_y = perspective_vertex

    vector_length: int = 20
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
            direction = (0.0, 1.0)  # down
        elif perspective_y > target_cross_max:
            direction = (0.0, -1.0)  # up
        elif perspective_x < target_axis_start:
            direction = (1.0, 0.0)  # right
        elif perspective_x > target_axis_end:
            direction = (-1.0, 0.0)  # left
        else:
            # Punkt już wpada w bbox target_line, więc szukamy najkrótszej drogi
            # do najbliższej krawędzi bboxa.
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
            direction = (1.0, 0.0)  # right
        elif perspective_x > target_cross_max:
            direction = (-1.0, 0.0)  # left
        elif perspective_y < target_axis_start:
            direction = (0.0, 1.0)  # down
        elif perspective_y > target_axis_end:
            direction = (0.0, -1.0)  # up
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
    "SearchArea",
    "add_path_segments",
    "build_cross_axis_goal_sets",
    "build_cross_axis_span_goal_points",
    "build_logical_line_window_points",
    "build_same_axis_goal_sets",
    "build_search_area",
    "build_start_points",
    "is_point_in_search_area",
    "try_find_straight_path",
    "try_find_path",
    "try_find_white_path_from_point_to_logical_line"
]
