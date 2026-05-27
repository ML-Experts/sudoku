from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SudokuThresholdConfig:
    raw_hough_threshold: int
    raw_min_line_length_ratio: float
    raw_max_line_gap_ratio: float
    line_family_angle_tolerance_degrees: float
    line_merge_projection_distance_ratio: float
    frame_min_area_ratio: float
    minimum_family_segments: int
    minimum_distinct_lines_per_family: int
    gaussian_kernel_size: tuple[int, int] = (5, 5)
    median_kernel_size: int = 5
    bilateral_diameter: int = 9
    bilateral_sigma_color: int = 75
    bilateral_sigma_space: int = 75
    nl_means_strength: int = 13
    nl_means_template_window_size: int = 7
    nl_means_search_window_size: int = 21
    denoise_clahe_clip_limit: float = 2.5
    denoise_clahe_tile_grid_size: int = 8
    unsharp_gaussian_kernel_size: tuple[int, int] = (5, 5)
    unsharp_gaussian_sigma: float = 0.0
    unsharp_amount: float = 1.35
    adaptive_method_name: str = "gaussian"
    adaptive_block_sizes: tuple[int, ...] = (11, 15, 21, 31)
    adaptive_c_values: tuple[int, ...] = (2, 4, 6)
    threshold_invert: bool = True
    line_merge_angle_tolerance_degrees: float = 6.0
    line_merge_endpoint_gap_ratio: float = 0.025
    line_bridge_projection_distance_ratio: float = 0.028
    line_bridge_max_gap_ratio: float = 0.065
    line_bridge_endpoint_tolerance_ratio: float = 0.028
    cross_family_touch_tolerance_ratio: float = 0.02
    min_cross_family_touches_to_keep: int = 2
    expected_horizontal_line_count: int = 10
    expected_vertical_line_count: int = 10
    frame_max_selected_count: int = 8
    binary_min_component_area_ratio: float = 0.00008
    binary_min_component_area_floor_px: int = 16
    soft_cleanup_area_multiplier: float = 0.35
    aggressive_cleanup_area_multiplier: float = 1.8
    cleanup_open_kernel_size: int = 3
    repair_kernel_sizes: tuple[int, ...] = (3, 5)
    repair_directional_kernel_ratio: float = 0.015
    selected_denoise_variant: str = "median_5"
    selected_threshold_name: str | None = None
    selected_cleanup_variant: str | None = "adaptive_plus_components_soft"
    selected_repair_variant: str | None = "directional_close"


@dataclass(frozen=True)
class DetectedLineSegment:
    start: tuple[int, int]
    end: tuple[int, int]
    length: float
    angle_degrees: float


@dataclass(frozen=True)
class MergedLine:
    family_name: str
    family_angle_degrees: float
    projection: float
    span_start: float
    span_end: float
    span_length: float
    covered_length: float
    support_intervals: tuple[tuple[float, float], ...]
    thickness_px: float
    total_segment_length: float
    segment_count: int
    centroid: tuple[int, int]
    segments: tuple[DetectedLineSegment, ...]
    touching_line_count: int
    touching_line_indices: tuple[int, ...]
    touching_point_count: int
    touching_points: tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class LineBridge:
    family_name: str
    first_line_index: int
    second_line_index: int
    segment: DetectedLineSegment
    ideal_start_point: tuple[int, int]
    ideal_end_point: tuple[int, int]
    corridor_polygon: tuple[tuple[int, int], ...]
    start_box: tuple[tuple[int, int], tuple[int, int]]
    end_box: tuple[tuple[int, int], tuple[int, int]]
    gap_px: float


@dataclass(frozen=True)
class LineBridgeDiagnostic:
    family_name: str
    first_line_index: int
    second_line_index: int
    accepted: bool
    reject_reason: str
    projection_distance_px: float
    projection_tolerance_px: float
    candidate_count: int
    selected_candidate_rank: int | None
    gap_px: float | None
    max_gap_px: float
    ideal_start_point: tuple[int, int] | None
    ideal_end_point: tuple[int, int] | None
    corridor_polygon: tuple[tuple[int, int], ...]
    start_box: tuple[tuple[int, int], tuple[int, int]] | None
    end_box: tuple[tuple[int, int], tuple[int, int]] | None
    projection_coverage_start_px: float | None = None
    projection_coverage_end_px: float | None = None
    projection_max_hole_px: int | None = None


@dataclass(frozen=True)
class EndpointConnection:
    horizontal_line_index: int
    horizontal_vertex_index: int
    vertical_line_index: int
    vertical_vertex_index: int
    horizontal_vertex: tuple[int, int]
    vertical_vertex: tuple[int, int]
    aligned_point: tuple[int, int]
    touch_point: tuple[int, int]


@dataclass(frozen=True)
class LineFamilyResult:
    raw_segment_count: int
    raw_min_line_length_px: int
    raw_max_line_gap_px: int
    horizontal_angle_degrees: float | None
    vertical_angle_degrees: float | None
    merge_projection_distance_px: float
    merge_endpoint_gap_px: float
    bridge_projection_tolerance_px: float
    bridge_max_gap_px: float
    bridge_endpoint_tolerance_px: float
    cross_family_touch_tolerance_px: float
    horizontal_segments: list[DetectedLineSegment]
    vertical_segments: list[DetectedLineSegment]
    horizontal_pre_filter_merged_lines: list[MergedLine]
    vertical_pre_filter_merged_lines: list[MergedLine]
    horizontal_bridges: list[LineBridge]
    vertical_bridges: list[LineBridge]
    horizontal_bridge_diagnostics: list[LineBridgeDiagnostic]
    vertical_bridge_diagnostics: list[LineBridgeDiagnostic]
    horizontal_merged_lines: list[MergedLine]
    vertical_merged_lines: list[MergedLine]
    horizontal_aligned_vertices: tuple[tuple[tuple[int, int], tuple[int, int]], ...]
    vertical_aligned_vertices: tuple[tuple[tuple[int, int], tuple[int, int]], ...]
    endpoint_connections: tuple[EndpointConnection, ...]


@dataclass(frozen=True)
class LineFrame:
    top_line_index: int
    bottom_line_index: int
    left_line_index: int
    right_line_index: int
    top_line: MergedLine
    bottom_line: MergedLine
    left_line: MergedLine
    right_line: MergedLine
    top_left_connection: EndpointConnection
    top_right_connection: EndpointConnection
    bottom_right_connection: EndpointConnection
    bottom_left_connection: EndpointConnection
    corners: tuple[tuple[int, int], tuple[int, int], tuple[int, int], tuple[int, int]]
    area_px: float
    perimeter_px: float
    horizontal_line_count: int
    vertical_line_count: int
    inner_horizontal_line_count: int
    inner_vertical_line_count: int
    shared_horizontal_line_count: int
    shared_vertical_line_count: int
    outer_margin_line_count: int
    grid_distance_score: int
    priority_score: float


@dataclass(frozen=True)
class FrameDetectionResult:
    all_frames: list[LineFrame]
    selected_frames: list[LineFrame]
