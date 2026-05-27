from __future__ import annotations

import cv2
import numpy as np

from infrastructure.vision.sudoku_threshold_line_bridge_family import (
    bridge_line_family_gaps,
    inspect_line_family_bridge_candidates,
)
from infrastructure.vision.sudoku_threshold_line_families import (
    collect_line_family,
    get_dominant_angle_degrees,
    is_horizontal_like,
    refine_family_angle_degrees,
)
from infrastructure.vision.sudoku_threshold_geometry import (
    angle_difference_degrees,
    build_line_segment,
)
from infrastructure.vision.sudoku_threshold_line_merge import merge_line_family_segments
from infrastructure.vision.sudoku_threshold_line_touch import (
    annotate_cross_family_touches,
    iteratively_filter_lines_by_touch_points,
    refresh_cross_family_touches,
    resolve_last_touch_endpoint_connections,
)
from infrastructure.vision.sudoku_threshold_models import (
    LineFamilyResult,
    SudokuThresholdConfig,
)


def build_empty_line_family_result(
    raw_min_line_length_px: int,
    raw_max_line_gap_px: int,
    merge_projection_distance_px: float,
    merge_endpoint_gap_px: float,
    cross_family_touch_tolerance_px: float,
) -> LineFamilyResult:
    return LineFamilyResult(
        raw_segment_count=0,
        raw_min_line_length_px=raw_min_line_length_px,
        raw_max_line_gap_px=raw_max_line_gap_px,
        horizontal_angle_degrees=None,
        vertical_angle_degrees=None,
        merge_projection_distance_px=merge_projection_distance_px,
        merge_endpoint_gap_px=merge_endpoint_gap_px,
        bridge_projection_tolerance_px=0.0,
        bridge_max_gap_px=0.0,
        bridge_endpoint_tolerance_px=0.0,
        cross_family_touch_tolerance_px=cross_family_touch_tolerance_px,
        horizontal_segments=[],
        vertical_segments=[],
        horizontal_pre_filter_merged_lines=[],
        vertical_pre_filter_merged_lines=[],
        horizontal_bridges=[],
        vertical_bridges=[],
        horizontal_bridge_diagnostics=[],
        vertical_bridge_diagnostics=[],
        horizontal_merged_lines=[],
        vertical_merged_lines=[],
        horizontal_aligned_vertices=(),
        vertical_aligned_vertices=(),
        endpoint_connections=(),
    )


def detect_line_families(
    binary_image,
    config: SudokuThresholdConfig,
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
        return build_empty_line_family_result(
            raw_min_line_length_px,
            raw_max_line_gap_px,
            merge_projection_distance_px,
            merge_endpoint_gap_px,
            cross_family_touch_tolerance_px,
        )

    line_segments = [build_line_segment(raw_segment[0]) for raw_segment in raw_segments]
    primary_seed_angle = get_dominant_angle_degrees(line_segments)
    if primary_seed_angle is None:
        return build_empty_line_family_result(
            raw_min_line_length_px,
            raw_max_line_gap_px,
            merge_projection_distance_px,
            merge_endpoint_gap_px,
            cross_family_touch_tolerance_px,
        )

    primary_segments = collect_line_family(
        line_segments,
        primary_seed_angle,
        config.line_family_angle_tolerance_degrees,
    )
    primary_angle = refine_family_angle_degrees(primary_segments, primary_seed_angle)
    primary_segments = collect_line_family(
        line_segments,
        primary_angle,
        config.line_family_angle_tolerance_degrees,
    )
    remaining_segments = [
        line_segment
        for line_segment in line_segments
        if angle_difference_degrees(line_segment.angle_degrees, primary_angle)
        > config.line_family_angle_tolerance_degrees
    ]

    secondary_seed_angle = get_dominant_angle_degrees(remaining_segments)
    if secondary_seed_angle is None:
        secondary_seed_angle = (primary_angle + 90.0) % 180.0
    secondary_segments = collect_line_family(
        line_segments,
        secondary_seed_angle,
        config.line_family_angle_tolerance_degrees,
    )
    secondary_angle = refine_family_angle_degrees(
        secondary_segments,
        secondary_seed_angle,
    )
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
    (
        horizontal_merged_lines,
        horizontal_bridges,
        bridge_projection_tolerance_px,
        bridge_max_gap_px,
        bridge_endpoint_tolerance_px,
    ) = bridge_line_family_gaps(
        binary_image,
        horizontal_merged_lines,
        horizontal_angle_degrees,
        "horizontal",
        config,
        minimum_dimension,
    )
    (
        vertical_merged_lines,
        vertical_bridges,
        _,
        _,
        _,
    ) = bridge_line_family_gaps(
        binary_image,
        vertical_merged_lines,
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
    horizontal_pre_filter_merged_lines = list(horizontal_merged_lines)
    vertical_pre_filter_merged_lines = list(vertical_merged_lines)
    horizontal_merged_lines, vertical_merged_lines = (
        iteratively_filter_lines_by_touch_points(
            horizontal_merged_lines,
            vertical_merged_lines,
            config.min_cross_family_touches_to_keep,
            cross_family_touch_tolerance_px,
        )
    )
    horizontal_merged_lines, vertical_merged_lines = refresh_cross_family_touches(
        horizontal_merged_lines,
        vertical_merged_lines,
        cross_family_touch_tolerance_px,
    )
    (
        horizontal_aligned_vertices,
        vertical_aligned_vertices,
        endpoint_connections,
    ) = resolve_last_touch_endpoint_connections(
        horizontal_merged_lines,
        vertical_merged_lines,
        cross_family_touch_tolerance_px,
    )
    horizontal_bridge_diagnostics = inspect_line_family_bridge_candidates(
        binary_image,
        horizontal_merged_lines,
        horizontal_angle_degrees,
        "horizontal",
        config,
        minimum_dimension,
    )
    vertical_bridge_diagnostics = inspect_line_family_bridge_candidates(
        binary_image,
        vertical_merged_lines,
        vertical_angle_degrees,
        "vertical",
        config,
        minimum_dimension,
    )

    return LineFamilyResult(
        raw_segment_count=len(line_segments),
        raw_min_line_length_px=raw_min_line_length_px,
        raw_max_line_gap_px=raw_max_line_gap_px,
        horizontal_angle_degrees=horizontal_angle_degrees,
        vertical_angle_degrees=vertical_angle_degrees,
        merge_projection_distance_px=merge_projection_distance_px,
        merge_endpoint_gap_px=merge_endpoint_gap_px,
        bridge_projection_tolerance_px=bridge_projection_tolerance_px,
        bridge_max_gap_px=bridge_max_gap_px,
        bridge_endpoint_tolerance_px=bridge_endpoint_tolerance_px,
        cross_family_touch_tolerance_px=cross_family_touch_tolerance_px,
        horizontal_segments=horizontal_segments,
        vertical_segments=vertical_segments,
        horizontal_pre_filter_merged_lines=horizontal_pre_filter_merged_lines,
        vertical_pre_filter_merged_lines=vertical_pre_filter_merged_lines,
        horizontal_bridges=horizontal_bridges,
        vertical_bridges=vertical_bridges,
        horizontal_bridge_diagnostics=horizontal_bridge_diagnostics,
        vertical_bridge_diagnostics=vertical_bridge_diagnostics,
        horizontal_merged_lines=horizontal_merged_lines,
        vertical_merged_lines=vertical_merged_lines,
        horizontal_aligned_vertices=horizontal_aligned_vertices,
        vertical_aligned_vertices=vertical_aligned_vertices,
        endpoint_connections=endpoint_connections,
    )
