from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sudoku_board_threshold_paths import REPO_ROOT


@dataclass(slots=True)
class ExperimentConfig:
    dataset_root: Path = REPO_ROOT / "data" / "raw" / "boards"
    image_path: Path | None = None
    selected_dataset_index: int = 0
    preview_limit: int = 20
    max_display_size: int = 1600
    gaussian_kernel_size: tuple[int, int] = (5, 5)
    median_kernel_size: int = 5
    bilateral_diameter: int = 9
    bilateral_sigma_color: int = 75
    bilateral_sigma_space: int = 75
    nl_means_strength: int = 13
    nl_means_template_window_size: int = 7
    nl_means_search_window_size: int = 21
    adaptive_method_name: str = "gaussian"
    adaptive_block_sizes: tuple[int, ...] = (11, 15, 21, 31)
    adaptive_c_values: tuple[int, ...] = (2, 4, 6)
    threshold_invert: bool = True
    binary_min_component_area_ratio: float = 0.00008
    binary_min_component_area_floor_px: int = 16
    soft_cleanup_area_multiplier: float = 0.35
    repair_kernel_sizes: tuple[int, ...] = (3, 5)
    repair_directional_kernel_ratio: float = 0.015
    raw_hough_threshold: int = 35
    raw_min_line_length_ratio: float = 0.08
    raw_max_line_gap_ratio: float = 0.02
    line_family_angle_tolerance_degrees: float = 20.0
    line_merge_angle_tolerance_degrees: float = 6.0
    line_merge_projection_distance_ratio: float = 0.012
    line_merge_endpoint_gap_ratio: float = 0.025
    line_bridge_projection_distance_ratio: float = 0.028
    line_bridge_max_gap_ratio: float = 0.065
    line_bridge_endpoint_tolerance_ratio: float = 0.028
    cross_family_touch_tolerance_ratio: float = 0.02
    min_cross_family_touches_to_keep: int = 9
    drop_zero_touch_lines_after_refresh: bool = True
    expected_horizontal_line_count: int = 10
    expected_vertical_line_count: int = 10
    horizontal_family_color_bgr: tuple[int, int, int] = (255, 165, 0)
    vertical_family_color_bgr: tuple[int, int, int] = (0, 255, 255)
    line_overlay_thickness: int = 2
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
    horizontal_merged_lines: list[MergedLine]
    vertical_merged_lines: list[MergedLine]


__all__ = [
    "DetectedLineSegment",
    "ExperimentConfig",
    "LineBridge",
    "LineFamilyResult",
    "MergedLine",
]
