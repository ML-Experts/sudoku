from __future__ import annotations

import numpy as np

from sudoku_board_threshold_line_geometry import (
    angle_difference_degrees,
    direction_vector_from_angle,
    merge_overlapping_intervals,
    merged_interval_length,
    normal_vector_from_angle,
    point_position_on_direction,
    segment_interval_along_direction,
    interval_gap,
)
from sudoku_board_threshold_models import (
    DetectedLineSegment,
    ExperimentConfig,
    MergedLine,
)


def build_merged_line(
    family_name: str,
    family_angle_degrees: float,
    line_segments: list[DetectedLineSegment],
) -> MergedLine:
    direction = direction_vector_from_angle(family_angle_degrees)
    normal = normal_vector_from_angle(family_angle_degrees)
    midpoint_projections = [
        point_position_on_direction(
            (
                (line_segment.start[0] + line_segment.end[0]) / 2.0,
                (line_segment.start[1] + line_segment.end[1]) / 2.0,
            ),
            normal,
        )
        for line_segment in line_segments
    ]
    endpoint_positions: list[float] = []
    for line_segment in line_segments:
        endpoint_positions.append(point_position_on_direction(line_segment.start, direction))
        endpoint_positions.append(point_position_on_direction(line_segment.end, direction))
    support_intervals = merge_overlapping_intervals(
        [
            segment_interval_along_direction(line_segment, direction)
            for line_segment in line_segments
        ]
    )

    projection = float(np.mean(midpoint_projections)) if midpoint_projections else 0.0
    span_start = min(endpoint_positions) if endpoint_positions else 0.0
    span_end = max(endpoint_positions) if endpoint_positions else 0.0
    thickness_px = (
        float(max(midpoint_projections) - min(midpoint_projections))
        if midpoint_projections
        else 0.0
    )
    segment_midpoints = [
        (
            (line_segment.start[0] + line_segment.end[0]) / 2.0,
            (line_segment.start[1] + line_segment.end[1]) / 2.0,
        )
        for line_segment in line_segments
    ]
    centroid = (
        int(round(np.mean([midpoint[0] for midpoint in segment_midpoints]))),
        int(round(np.mean([midpoint[1] for midpoint in segment_midpoints]))),
    )
    return MergedLine(
        family_name=family_name,
        family_angle_degrees=family_angle_degrees,
        projection=projection,
        span_start=float(span_start),
        span_end=float(span_end),
        span_length=float(span_end - span_start),
        covered_length=merged_interval_length(support_intervals),
        support_intervals=support_intervals,
        thickness_px=thickness_px,
        total_segment_length=float(sum(segment.length for segment in line_segments)),
        segment_count=len(line_segments),
        centroid=centroid,
        segments=tuple(line_segments),
        touching_line_count=0,
        touching_line_indices=(),
        touching_point_count=0,
        touching_points=(),
    )


def should_merge_line_segments(
    first_segment: DetectedLineSegment,
    second_segment: DetectedLineSegment,
    family_angle_degrees: float,
    merge_angle_tolerance_degrees: float,
    merge_projection_distance_px: float,
    merge_endpoint_gap_px: float,
) -> bool:
    if (
        angle_difference_degrees(first_segment.angle_degrees, family_angle_degrees)
        > merge_angle_tolerance_degrees
    ):
        return False
    if (
        angle_difference_degrees(second_segment.angle_degrees, family_angle_degrees)
        > merge_angle_tolerance_degrees
    ):
        return False

    direction = direction_vector_from_angle(family_angle_degrees)
    normal = normal_vector_from_angle(family_angle_degrees)

    first_midpoint = (
        (first_segment.start[0] + first_segment.end[0]) / 2.0,
        (first_segment.start[1] + first_segment.end[1]) / 2.0,
    )
    second_midpoint = (
        (second_segment.start[0] + second_segment.end[0]) / 2.0,
        (second_segment.start[1] + second_segment.end[1]) / 2.0,
    )
    first_projection = point_position_on_direction(first_midpoint, normal)
    second_projection = point_position_on_direction(second_midpoint, normal)
    if abs(first_projection - second_projection) > merge_projection_distance_px:
        return False

    first_interval = segment_interval_along_direction(first_segment, direction)
    second_interval = segment_interval_along_direction(second_segment, direction)
    return interval_gap(first_interval, second_interval) <= merge_endpoint_gap_px


def connected_components(adjacency: list[list[int]]) -> list[list[int]]:
    visited = [False] * len(adjacency)
    components: list[list[int]] = []
    for start_index in range(len(adjacency)):
        if visited[start_index]:
            continue

        stack = [start_index]
        visited[start_index] = True
        component: list[int] = []
        while stack:
            node_index = stack.pop()
            component.append(node_index)
            for neighbor_index in adjacency[node_index]:
                if visited[neighbor_index]:
                    continue
                visited[neighbor_index] = True
                stack.append(neighbor_index)
        components.append(sorted(component))
    return components


def merge_line_family_segments(
    family_segments: list[DetectedLineSegment],
    family_angle_degrees: float | None,
    family_name: str,
    config: ExperimentConfig,
    minimum_dimension: int,
) -> list[MergedLine]:
    if family_angle_degrees is None or not family_segments:
        return []

    merge_projection_distance_px = max(
        4.0,
        minimum_dimension * config.line_merge_projection_distance_ratio,
    )
    merge_endpoint_gap_px = max(
        6.0,
        minimum_dimension * config.line_merge_endpoint_gap_ratio,
    )
    adjacency: list[list[int]] = [[] for _ in family_segments]
    for first_index in range(len(family_segments)):
        for second_index in range(first_index + 1, len(family_segments)):
            if should_merge_line_segments(
                family_segments[first_index],
                family_segments[second_index],
                family_angle_degrees,
                config.line_merge_angle_tolerance_degrees,
                merge_projection_distance_px,
                merge_endpoint_gap_px,
            ):
                adjacency[first_index].append(second_index)
                adjacency[second_index].append(first_index)

    merged_lines = [
        build_merged_line(
            family_name,
            family_angle_degrees,
            [family_segments[index] for index in component],
        )
        for component in connected_components(adjacency)
    ]
    return sorted(merged_lines, key=lambda merged_line: merged_line.projection)


__all__ = [
    "build_merged_line",
    "connected_components",
    "merge_line_family_segments",
    "should_merge_line_segments",
]
