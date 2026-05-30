from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from raw_line_family_only_paths import REPO_ROOT


@dataclass(slots=True)
class ExperimentConfig:
    dataset_root: Path = REPO_ROOT / "data" / "raw" / "boards"
    image_path: Path | None = None
    selected_dataset_index: int = 0
    preview_limit: int = 20
    max_display_size: int = 1600
    median_kernel_size: int = 5
    adaptive_threshold_block_size: int = 11
    adaptive_threshold_c_value: int = 2
    threshold_invert: bool = True
    binary_min_component_area_ratio: float = 0.00008
    binary_min_component_area_floor_px: int = 16
    soft_cleanup_area_multiplier: float = 0.35
    repair_directional_kernel_ratio: float = 0.015
    raw_hough_threshold: int = 35
    raw_min_line_length_ratio: float = 0.08
    raw_max_line_gap_ratio: float = 0.02
    line_family_angle_tolerance_degrees: float = 20.0
    horizontal_family_color_bgr: tuple[int, int, int] = (255, 165, 0)
    vertical_family_color_bgr: tuple[int, int, int] = (0, 255, 255)
    line_overlay_thickness: int = 2


@dataclass(frozen=True)
class DetectedLineSegment:
    start: tuple[int, int]
    end: tuple[int, int]
    length: float
    angle_degrees: float


__all__ = ["DetectedLineSegment", "ExperimentConfig"]
