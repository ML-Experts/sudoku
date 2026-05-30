from __future__ import annotations

from itertools import combinations

import cv2
import numpy as np

from sudoku_board_threshold_models import (
    EndpointConnection,
    ExperimentConfig,
    FrameDetectionResult,
    LineFamilyResult,
    LineFrame,
    MergedLine,
)


def build_endpoint_connection_lookup(
    endpoint_connections: tuple[EndpointConnection, ...],
) -> dict[tuple[int, int], EndpointConnection]:
    return {
        (
            endpoint_connection.horizontal_line_index,
            endpoint_connection.vertical_line_index,
        ): endpoint_connection
        for endpoint_connection in endpoint_connections
    }


def build_horizontal_connection_map(
    endpoint_connections: tuple[EndpointConnection, ...],
) -> dict[int, set[int]]:
    connection_map: dict[int, set[int]] = {}
    for endpoint_connection in endpoint_connections:
        connection_map.setdefault(
            endpoint_connection.horizontal_line_index,
            set(),
        ).add(endpoint_connection.vertical_line_index)
    return connection_map


def build_vertical_connection_map(
    endpoint_connections: tuple[EndpointConnection, ...],
) -> dict[int, set[int]]:
    connection_map: dict[int, set[int]] = {}
    for endpoint_connection in endpoint_connections:
        connection_map.setdefault(
            endpoint_connection.vertical_line_index,
            set(),
        ).add(endpoint_connection.horizontal_line_index)
    return connection_map


def order_frame_corners(
    corners: tuple[tuple[int, int], tuple[int, int], tuple[int, int], tuple[int, int]],
) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int], tuple[int, int]]:
    points = sorted(corners, key=lambda point: (point[1], point[0]))
    top_points = sorted(points[:2], key=lambda point: point[0])
    bottom_points = sorted(points[2:], key=lambda point: point[0])
    top_left, top_right = top_points
    bottom_left, bottom_right = bottom_points
    return top_left, top_right, bottom_right, bottom_left


def compute_frame_perimeter(
    corners: tuple[tuple[int, int], tuple[int, int], tuple[int, int], tuple[int, int]],
) -> float:
    perimeter = 0.0
    for index in range(len(corners)):
        first_point = np.array(corners[index], dtype=np.float32)
        second_point = np.array(corners[(index + 1) % len(corners)], dtype=np.float32)
        perimeter += float(np.linalg.norm(second_point - first_point))
    return perimeter


def count_lines_between_projections(
    lines: list[MergedLine],
    first_projection: float,
    second_projection: float,
) -> int:
    lower_bound = min(first_projection, second_projection)
    upper_bound = max(first_projection, second_projection)
    return sum(
        1
        for merged_line in lines
        if lower_bound <= merged_line.projection <= upper_bound
    )


def build_polygon_array(
    corners: tuple[tuple[int, int], tuple[int, int], tuple[int, int], tuple[int, int]],
) -> np.ndarray:
    return np.array(corners, dtype=np.int32).reshape((-1, 1, 2))


def resolve_reference_area(
    horizontal_lines: list[MergedLine],
    vertical_lines: list[MergedLine],
) -> float:
    all_points: list[tuple[int, int]] = []
    for merged_line in [*horizontal_lines, *vertical_lines]:
        for segment in merged_line.segments:
            all_points.append(segment.start)
            all_points.append(segment.end)

    if not all_points:
        return 0.0

    points = np.array(all_points, dtype=np.float32)
    x_min = float(np.min(points[:, 0]))
    x_max = float(np.max(points[:, 0]))
    y_min = float(np.min(points[:, 1]))
    y_max = float(np.max(points[:, 1]))
    return max((x_max - x_min) * (y_max - y_min), 0.0)


def compute_priority_score(
    area_px: float,
    reference_area_px: float,
    grid_distance_score: int,
    shared_horizontal_line_count: int,
    shared_vertical_line_count: int,
    inner_horizontal_line_count: int,
    inner_vertical_line_count: int,
    outer_margin_line_count: int,
) -> float:
    normalized_area_score = 0.0
    if reference_area_px > 1e-6:
        normalized_area_score = area_px / reference_area_px

    return (
        + 220.0 * float(inner_horizontal_line_count + inner_vertical_line_count)
        + 140.0 * float(shared_horizontal_line_count + shared_vertical_line_count)
        + 500.0 * normalized_area_score
        - 70.0 * float(grid_distance_score)
        - 40.0 * float(outer_margin_line_count)
    )


def total_inner_line_count(frame: LineFrame) -> int:
    return frame.inner_horizontal_line_count + frame.inner_vertical_line_count


def build_line_frame_candidate(
    horizontal_lines: list[MergedLine],
    vertical_lines: list[MergedLine],
    top_line_index: int,
    bottom_line_index: int,
    left_line_index: int,
    right_line_index: int,
    endpoint_connection_lookup: dict[tuple[int, int], EndpointConnection],
    horizontal_connection_map: dict[int, set[int]],
    vertical_connection_map: dict[int, set[int]],
    minimum_area_px: float,
    reference_area_px: float,
    config: ExperimentConfig,
) -> LineFrame | None:
    top_line = horizontal_lines[top_line_index]
    bottom_line = horizontal_lines[bottom_line_index]
    left_line = vertical_lines[left_line_index]
    right_line = vertical_lines[right_line_index]

    top_left_connection = endpoint_connection_lookup.get((top_line_index, left_line_index))
    top_right_connection = endpoint_connection_lookup.get(
        (top_line_index, right_line_index)
    )
    bottom_right_connection = endpoint_connection_lookup.get(
        (bottom_line_index, right_line_index)
    )
    bottom_left_connection = endpoint_connection_lookup.get(
        (bottom_line_index, left_line_index)
    )
    if (
        top_left_connection is None
        or top_right_connection is None
        or bottom_right_connection is None
        or bottom_left_connection is None
    ):
        return None

    corners = order_frame_corners(
        (
            top_left_connection.aligned_point,
            top_right_connection.aligned_point,
            bottom_right_connection.aligned_point,
            bottom_left_connection.aligned_point,
        )
    )
    if len(set(corners)) != 4:
        return None

    contour = build_polygon_array(corners)
    area_px = float(abs(cv2.contourArea(contour)))
    if area_px < minimum_area_px:
        return None
    if not cv2.isContourConvex(contour):
        return None

    shared_vertical_indices = horizontal_connection_map.get(
        top_line_index, set()
    ).intersection(horizontal_connection_map.get(bottom_line_index, set()))
    shared_horizontal_indices = vertical_connection_map.get(
        left_line_index, set()
    ).intersection(vertical_connection_map.get(right_line_index, set()))
    horizontal_line_count = count_lines_between_projections(
        horizontal_lines,
        top_line.projection,
        bottom_line.projection,
    )
    vertical_line_count = count_lines_between_projections(
        vertical_lines,
        left_line.projection,
        right_line.projection,
    )
    inner_horizontal_line_count = max(horizontal_line_count - 2, 0)
    inner_vertical_line_count = max(vertical_line_count - 2, 0)
    outer_margin_line_count = (
        top_line_index
        + (len(horizontal_lines) - bottom_line_index - 1)
        + left_line_index
        + (len(vertical_lines) - right_line_index - 1)
    )
    grid_distance_score = (
        abs(horizontal_line_count - config.expected_horizontal_line_count)
        + abs(vertical_line_count - config.expected_vertical_line_count)
    )
    priority_score = compute_priority_score(
        area_px=area_px,
        reference_area_px=reference_area_px,
        grid_distance_score=grid_distance_score,
        shared_horizontal_line_count=len(shared_horizontal_indices),
        shared_vertical_line_count=len(shared_vertical_indices),
        inner_horizontal_line_count=inner_horizontal_line_count,
        inner_vertical_line_count=inner_vertical_line_count,
        outer_margin_line_count=outer_margin_line_count,
    )

    return LineFrame(
        top_line_index=top_line_index,
        bottom_line_index=bottom_line_index,
        left_line_index=left_line_index,
        right_line_index=right_line_index,
        top_line=top_line,
        bottom_line=bottom_line,
        left_line=left_line,
        right_line=right_line,
        top_left_connection=top_left_connection,
        top_right_connection=top_right_connection,
        bottom_right_connection=bottom_right_connection,
        bottom_left_connection=bottom_left_connection,
        corners=corners,
        area_px=area_px,
        perimeter_px=compute_frame_perimeter(corners),
        horizontal_line_count=horizontal_line_count,
        vertical_line_count=vertical_line_count,
        inner_horizontal_line_count=inner_horizontal_line_count,
        inner_vertical_line_count=inner_vertical_line_count,
        shared_horizontal_line_count=len(shared_horizontal_indices),
        shared_vertical_line_count=len(shared_vertical_indices),
        outer_margin_line_count=outer_margin_line_count,
        grid_distance_score=grid_distance_score,
        priority_score=priority_score,
    )


def frame_contains_corner(container_frame: LineFrame, corner: tuple[int, int]) -> bool:
    contour = build_polygon_array(container_frame.corners)
    return cv2.pointPolygonTest(contour, corner, False) >= 0


def is_dominated_by_larger_container(
    candidate_frame: LineFrame,
    other_frame: LineFrame,
) -> bool:
    if not all(
        frame_contains_corner(other_frame, corner) for corner in candidate_frame.corners
    ):
        return False

    perimeter_tolerance = 1e-6
    if other_frame.perimeter_px > candidate_frame.perimeter_px + perimeter_tolerance:
        return True
    if other_frame.perimeter_px + perimeter_tolerance < candidate_frame.perimeter_px:
        return False

    if other_frame.area_px > candidate_frame.area_px + perimeter_tolerance:
        return True
    if other_frame.area_px + perimeter_tolerance < candidate_frame.area_px:
        return False

    return other_frame.priority_score >= candidate_frame.priority_score


def filter_out_inner_smaller_frames(frames: list[LineFrame]) -> list[LineFrame]:
    selected_frames: list[LineFrame] = []
    for candidate_frame in frames:
        if any(
            is_dominated_by_larger_container(candidate_frame, other_frame)
            for other_frame in frames
            if other_frame is not candidate_frame
        ):
            continue
        selected_frames.append(candidate_frame)
    return selected_frames


def frame_priority_key(frame: LineFrame) -> tuple[float, float, float, float]:
    return (
        float(total_inner_line_count(frame)),
        -float(frame.grid_distance_score),
        frame.priority_score,
        frame.perimeter_px,
    )


def find_line_frames(
    line_family_result: LineFamilyResult,
    config: ExperimentConfig,
) -> FrameDetectionResult:
    horizontal_lines = list(line_family_result.horizontal_merged_lines)
    vertical_lines = list(line_family_result.vertical_merged_lines)
    if len(horizontal_lines) < 2 or len(vertical_lines) < 2:
        return FrameDetectionResult(all_frames=[], selected_frames=[])

    endpoint_connection_lookup = build_endpoint_connection_lookup(
        line_family_result.endpoint_connections
    )
    horizontal_connection_map = build_horizontal_connection_map(
        line_family_result.endpoint_connections
    )
    vertical_connection_map = build_vertical_connection_map(
        line_family_result.endpoint_connections
    )
    if len(endpoint_connection_lookup) < 4:
        return FrameDetectionResult(all_frames=[], selected_frames=[])

    reference_area_px = resolve_reference_area(horizontal_lines, vertical_lines)
    minimum_area_px = reference_area_px * config.frame_min_area_ratio
    all_frames: list[LineFrame] = []

    for top_line_index, bottom_line_index in combinations(range(len(horizontal_lines)), 2):
        shared_vertical_indices = sorted(
            horizontal_connection_map.get(top_line_index, set()).intersection(
                horizontal_connection_map.get(bottom_line_index, set())
            )
        )
        if len(shared_vertical_indices) < 2:
            continue

        for left_line_index, right_line_index in combinations(shared_vertical_indices, 2):
            candidate_frame = build_line_frame_candidate(
                horizontal_lines=horizontal_lines,
                vertical_lines=vertical_lines,
                top_line_index=top_line_index,
                bottom_line_index=bottom_line_index,
                left_line_index=left_line_index,
                right_line_index=right_line_index,
                endpoint_connection_lookup=endpoint_connection_lookup,
                horizontal_connection_map=horizontal_connection_map,
                vertical_connection_map=vertical_connection_map,
                minimum_area_px=minimum_area_px,
                reference_area_px=reference_area_px,
                config=config,
            )
            if candidate_frame is None:
                continue
            all_frames.append(candidate_frame)

    ordered_frames = sorted(all_frames, key=frame_priority_key, reverse=True)
    selected_frames = filter_out_inner_smaller_frames(ordered_frames)
    if config.frame_max_selected_count > 0:
        selected_frames = selected_frames[: config.frame_max_selected_count]

    return FrameDetectionResult(
        all_frames=ordered_frames,
        selected_frames=selected_frames,
    )


__all__ = [
    "build_endpoint_connection_lookup",
    "build_horizontal_connection_map",
    "build_line_frame_candidate",
    "build_vertical_connection_map",
    "compute_frame_perimeter",
    "count_lines_between_projections",
    "filter_out_inner_smaller_frames",
    "find_line_frames",
    "frame_contains_corner",
    "frame_priority_key",
    "is_dominated_by_larger_container",
    "order_frame_corners",
    "total_inner_line_count",
]
