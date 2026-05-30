from __future__ import annotations

from enum import Enum
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
    logical_line_vertex_radius: int = 5


class LineFamilyName(Enum):
    UNCLASSIFIED = "unclassified"
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


@dataclass(frozen=True)
class DetectedLineSegment:
    family_name: LineFamilyName
    start: tuple[int, int]
    end: tuple[int, int]
    length: float
    angle_degrees: float

    @property
    def axis_start(self) -> int:
        if self.family_name == LineFamilyName.HORIZONTAL:
            return self.start[0]
        if self.family_name == LineFamilyName.VERTICAL:
            return self.start[1]
        raise NotImplementedError(
            "axis_start is available only for classified line segments."
        )

    @property
    def axis_end(self) -> int:
        if self.family_name == LineFamilyName.HORIZONTAL:
            return self.end[0]
        if self.family_name == LineFamilyName.VERTICAL:
            return self.end[1]
        raise NotImplementedError(
            "axis_end is available only for classified line segments."
        )

    @property
    def cross_axis_start(self) -> int:
        if self.family_name == LineFamilyName.HORIZONTAL:
            return self.start[1]
        if self.family_name == LineFamilyName.VERTICAL:
            return self.start[0]
        raise NotImplementedError(
            "cross_axis_start is available only for classified line segments."
        )

    @property
    def cross_axis_end(self) -> int:
        if self.family_name == LineFamilyName.HORIZONTAL:
            return self.end[1]
        if self.family_name == LineFamilyName.VERTICAL:
            return self.end[0]
        raise NotImplementedError(
            "cross_axis_end is available only for classified line segments."
        )


__all__ = ["DetectedLineSegment", "ExperimentConfig", "LineFamilyName"]
