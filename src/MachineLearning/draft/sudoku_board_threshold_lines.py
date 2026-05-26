from __future__ import annotations

import cv2
import numpy as np

from sudoku_board_threshold_models import (
    DetectedLineSegment,
    ExperimentConfig,
    LineFamilyResult,
    MergedLine,
)


def build_line_segment(raw_segment: np.ndarray) -> DetectedLineSegment:
    x1, y1, x2, y2 = (int(value) for value in raw_segment)
    delta_x = float(x2 - x1)
    delta_y = float(y2 - y1)
    return DetectedLineSegment(
        start=(x1, y1),
        end=(x2, y2),
        length=float(np.hypot(delta_x, delta_y)),
        angle_degrees=float(np.degrees(np.arctan2(delta_y, delta_x)) % 180.0),
    )


def angle_difference_degrees(first_angle: float, second_angle: float) -> float:
    raw_difference = abs(first_angle - second_angle) % 180.0
    return min(raw_difference, 180.0 - raw_difference)


def get_dominant_angle_degrees(
    line_segments: list[DetectedLineSegment],
) -> float | None:
    if not line_segments:
        return None

    angle_histogram = np.zeros(180, dtype=np.float32)
    for line_segment in line_segments:
        angle_bucket = int(round(line_segment.angle_degrees)) % 180
        angle_histogram[angle_bucket] += line_segment.length
    return float(np.argmax(angle_histogram))


def collect_line_family(
    line_segments: list[DetectedLineSegment],
    target_angle_degrees: float,
    angle_tolerance_degrees: float,
) -> list[DetectedLineSegment]:
    return [
        line_segment
        for line_segment in line_segments
        if angle_difference_degrees(
            line_segment.angle_degrees,
            target_angle_degrees,
        )
        <= angle_tolerance_degrees
    ]


def direction_vector_from_angle(angle_degrees: float) -> np.ndarray:
    angle_radians = np.deg2rad(angle_degrees)
    return np.array(
        [np.cos(angle_radians), np.sin(angle_radians)],
        dtype=np.float32,
    )


def normal_vector_from_angle(angle_degrees: float) -> np.ndarray:
    direction = direction_vector_from_angle(angle_degrees)
    return np.array([-direction[1], direction[0]], dtype=np.float32)


def point_array(point: tuple[int, int] | tuple[float, float]) -> np.ndarray:
    return np.array(point, dtype=np.float32)


def point_position_on_direction(
    point: tuple[int, int] | tuple[float, float],
    direction: np.ndarray,
) -> float:
    return float(np.dot(point_array(point), direction))


def segment_interval_along_direction(
    line_segment: DetectedLineSegment,
    direction: np.ndarray,
) -> tuple[float, float]:
    start_position = point_position_on_direction(line_segment.start, direction)
    end_position = point_position_on_direction(line_segment.end, direction)
    return min(start_position, end_position), max(start_position, end_position)


def interval_gap(
    first_interval: tuple[float, float],
    second_interval: tuple[float, float],
) -> float:
    first_start, first_end = first_interval
    second_start, second_end = second_interval
    if first_end < second_start:
        return second_start - first_end
    if second_end < first_start:
        return first_start - second_end
    return 0.0


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
    endpoint_positions = []
    for line_segment in line_segments:
        endpoint_positions.append(point_position_on_direction(line_segment.start, direction))
        endpoint_positions.append(point_position_on_direction(line_segment.end, direction))

    projection = float(np.mean(midpoint_projections)) if midpoint_projections else 0.0
    span_start = min(endpoint_positions) if endpoint_positions else 0.0
    span_end = max(endpoint_positions) if endpoint_positions else 0.0
    start_point = normal * projection + direction * span_start
    end_point = normal * projection + direction * span_end
    thickness_px = (
        float(max(midpoint_projections) - min(midpoint_projections))
        if midpoint_projections
        else 0.0
    )
    return MergedLine(
        family_name=family_name,
        start=(int(round(start_point[0])), int(round(start_point[1]))),
        end=(int(round(end_point[0])), int(round(end_point[1]))),
        angle_degrees=family_angle_degrees,
        projection=projection,
        span_start=float(span_start),
        span_end=float(span_end),
        span_length=float(span_end - span_start),
        thickness_px=thickness_px,
        total_segment_length=float(sum(segment.length for segment in line_segments)),
        segment_count=len(line_segments),
        touching_line_count=0,
        touching_line_indices=(),
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


def intersection_point_for_merged_lines(
    first_line: MergedLine,
    second_line: MergedLine,
) -> np.ndarray | None:
    first_direction = direction_vector_from_angle(first_line.angle_degrees)
    first_normal = normal_vector_from_angle(first_line.angle_degrees)
    second_direction = direction_vector_from_angle(second_line.angle_degrees)
    second_normal = normal_vector_from_angle(second_line.angle_degrees)

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


def merged_lines_touch(
    first_line: MergedLine,
    second_line: MergedLine,
    touch_tolerance_px: float,
) -> bool:
    intersection_point = intersection_point_for_merged_lines(first_line, second_line)
    if intersection_point is None:
        return False

    first_direction = direction_vector_from_angle(first_line.angle_degrees)
    second_direction = direction_vector_from_angle(second_line.angle_degrees)
    first_position = float(np.dot(intersection_point, first_direction))
    second_position = float(np.dot(intersection_point, second_direction))

    return (
        first_line.span_start - touch_tolerance_px
        <= first_position
        <= first_line.span_end + touch_tolerance_px
        and second_line.span_start - touch_tolerance_px
        <= second_position
        <= second_line.span_end + touch_tolerance_px
    )


def annotate_cross_family_touches(
    horizontal_lines: list[MergedLine],
    vertical_lines: list[MergedLine],
    touch_tolerance_px: float,
) -> tuple[list[MergedLine], list[MergedLine]]:
    horizontal_touch_indices: list[list[int]] = [[] for _ in horizontal_lines]
    vertical_touch_indices: list[list[int]] = [[] for _ in vertical_lines]

    for horizontal_index, horizontal_line in enumerate(horizontal_lines):
        for vertical_index, vertical_line in enumerate(vertical_lines):
            if not merged_lines_touch(
                horizontal_line,
                vertical_line,
                touch_tolerance_px,
            ):
                continue
            horizontal_touch_indices[horizontal_index].append(vertical_index)
            vertical_touch_indices[vertical_index].append(horizontal_index)

    annotated_horizontal_lines = [
        MergedLine(
            family_name=horizontal_line.family_name,
            start=horizontal_line.start,
            end=horizontal_line.end,
            angle_degrees=horizontal_line.angle_degrees,
            projection=horizontal_line.projection,
            span_start=horizontal_line.span_start,
            span_end=horizontal_line.span_end,
            span_length=horizontal_line.span_length,
            thickness_px=horizontal_line.thickness_px,
            total_segment_length=horizontal_line.total_segment_length,
            segment_count=horizontal_line.segment_count,
            touching_line_count=len(horizontal_touch_indices[index]),
            touching_line_indices=tuple(horizontal_touch_indices[index]),
        )
        for index, horizontal_line in enumerate(horizontal_lines)
    ]
    annotated_vertical_lines = [
        MergedLine(
            family_name=vertical_line.family_name,
            start=vertical_line.start,
            end=vertical_line.end,
            angle_degrees=vertical_line.angle_degrees,
            projection=vertical_line.projection,
            span_start=vertical_line.span_start,
            span_end=vertical_line.span_end,
            span_length=vertical_line.span_length,
            thickness_px=vertical_line.thickness_px,
            total_segment_length=vertical_line.total_segment_length,
            segment_count=vertical_line.segment_count,
            touching_line_count=len(vertical_touch_indices[index]),
            touching_line_indices=tuple(vertical_touch_indices[index]),
        )
        for index, vertical_line in enumerate(vertical_lines)
    ]
    return annotated_horizontal_lines, annotated_vertical_lines


def is_horizontal_like(angle_degrees: float) -> bool:
    return angle_difference_degrees(angle_degrees, 0.0) <= angle_difference_degrees(
        angle_degrees,
        90.0,
    )


def detect_line_families(
    binary_image: np.ndarray,
    config: ExperimentConfig,
) -> LineFamilyResult:
    minimum_dimension = min(binary_image.shape[:2])
    raw_min_line_length_px = max(
        8,
        int(round(minimum_dimension * config.raw_min_line_length_ratio)),
    )
    raw_max_line_gap_px = max(
        2,
        int(round(minimum_dimension * config.raw_max_line_gap_ratio)),
    )
    merge_projection_distance_px = max(
        4.0,
        minimum_dimension * config.line_merge_projection_distance_ratio,
    )
    merge_endpoint_gap_px = max(
        6.0,
        minimum_dimension * config.line_merge_endpoint_gap_ratio,
    )
    cross_family_touch_tolerance_px = max(
        8.0,
        minimum_dimension * config.cross_family_touch_tolerance_ratio,
    )

    raw_segments = cv2.HoughLinesP(
        binary_image,
        rho=1,
        theta=np.pi / 180.0,
        threshold=config.raw_hough_threshold,
        minLineLength=raw_min_line_length_px,
        maxLineGap=raw_max_line_gap_px,
    )
    if raw_segments is None:
        return LineFamilyResult(
            raw_segment_count=0,
            raw_min_line_length_px=raw_min_line_length_px,
            raw_max_line_gap_px=raw_max_line_gap_px,
            horizontal_angle_degrees=None,
            vertical_angle_degrees=None,
            merge_projection_distance_px=merge_projection_distance_px,
            merge_endpoint_gap_px=merge_endpoint_gap_px,
            cross_family_touch_tolerance_px=cross_family_touch_tolerance_px,
            horizontal_segments=[],
            vertical_segments=[],
            horizontal_merged_lines=[],
            vertical_merged_lines=[],
        )

    line_segments = [build_line_segment(raw_segment[0]) for raw_segment in raw_segments]
    primary_angle = get_dominant_angle_degrees(line_segments)
    if primary_angle is None:
        return LineFamilyResult(
            raw_segment_count=0,
            raw_min_line_length_px=raw_min_line_length_px,
            raw_max_line_gap_px=raw_max_line_gap_px,
            horizontal_angle_degrees=None,
            vertical_angle_degrees=None,
            merge_projection_distance_px=merge_projection_distance_px,
            merge_endpoint_gap_px=merge_endpoint_gap_px,
            cross_family_touch_tolerance_px=cross_family_touch_tolerance_px,
            horizontal_segments=[],
            vertical_segments=[],
            horizontal_merged_lines=[],
            vertical_merged_lines=[],
        )

    primary_segments = collect_line_family(
        line_segments,
        primary_angle,
        config.line_family_angle_tolerance_degrees,
    )
    remaining_segments = [
        line_segment
        for line_segment in line_segments
        if angle_difference_degrees(
            line_segment.angle_degrees,
            primary_angle,
        )
        > config.line_family_angle_tolerance_degrees
    ]

    secondary_angle = get_dominant_angle_degrees(remaining_segments)
    if secondary_angle is None:
        secondary_angle = (primary_angle + 90.0) % 180.0
    secondary_segments = collect_line_family(
        line_segments,
        secondary_angle,
        config.line_family_angle_tolerance_degrees,
    )

    if is_horizontal_like(primary_angle):
        horizontal_angle_degrees = primary_angle
        horizontal_segments = primary_segments
        vertical_angle_degrees = secondary_angle
        vertical_segments = secondary_segments
    else:
        horizontal_angle_degrees = secondary_angle
        horizontal_segments = secondary_segments
        vertical_angle_degrees = primary_angle
        vertical_segments = primary_segments

    horizontal_merged_lines = merge_line_family_segments(
        horizontal_segments,
        horizontal_angle_degrees,
        "horizontal",
        config,
        minimum_dimension,
    )
    vertical_merged_lines = merge_line_family_segments(
        vertical_segments,
        vertical_angle_degrees,
        "vertical",
        config,
        minimum_dimension,
    )
    horizontal_merged_lines, vertical_merged_lines = annotate_cross_family_touches(
        horizontal_merged_lines,
        vertical_merged_lines,
        cross_family_touch_tolerance_px,
    )

    return LineFamilyResult(
        raw_segment_count=len(line_segments),
        raw_min_line_length_px=raw_min_line_length_px,
        raw_max_line_gap_px=raw_max_line_gap_px,
        horizontal_angle_degrees=horizontal_angle_degrees,
        vertical_angle_degrees=vertical_angle_degrees,
        merge_projection_distance_px=merge_projection_distance_px,
        merge_endpoint_gap_px=merge_endpoint_gap_px,
        cross_family_touch_tolerance_px=cross_family_touch_tolerance_px,
        horizontal_segments=horizontal_segments,
        vertical_segments=vertical_segments,
        horizontal_merged_lines=horizontal_merged_lines,
        vertical_merged_lines=vertical_merged_lines,
    )


__all__ = [
    "angle_difference_degrees",
    "annotate_cross_family_touches",
    "build_line_segment",
    "build_merged_line",
    "collect_line_family",
    "connected_components",
    "detect_line_families",
    "direction_vector_from_angle",
    "get_dominant_angle_degrees",
    "intersection_point_for_merged_lines",
    "interval_gap",
    "is_horizontal_like",
    "merge_line_family_segments",
    "merged_lines_touch",
    "normal_vector_from_angle",
    "point_position_on_direction",
    "segment_interval_along_direction",
    "should_merge_line_segments",
]
