from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from pathlib import Path

from .paths import PROJECT_ROOT


@dataclass(slots=True)
class ExperimentConfig:
    dataset_root: Path | None = PROJECT_ROOT / "data" / "raw" / "boards"
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
    raw_max_line_gap_ratio: float = 0.005
    line_family_angle_tolerance_degrees: float = 20.0
    horizontal_family_color_bgr: tuple[int, int, int] = (255, 165, 0)
    vertical_family_color_bgr: tuple[int, int, int] = (0, 255, 255)
    line_overlay_thickness: int = 2
    logical_line_vertex_radius: int = 5
    logical_line_cross_axis_thickness_px: int = 1
    logical_line_axis_gap_tolerance_px: int = 1
    raw_segment_group_black_gap_tolerance_px: int = 2
    same_axis_connection_segment_color_bgr: tuple[int, int, int] = (255, 0, 255)
    cross_axis_connection_segment_color_bgr: tuple[int, int, int] = (0, 0, 255)
    tolerance_rectangle_vector_length_px: int = 350
    tolerance_rectangle_padding_px: int = 18
    pixel_connection_cross_axis_step_limit_px: int = 4
    tolerance_rectangle_thickness: int = 2
    tolerance_rectangle_reference_radius: int = 4
    logical_line_intersection_radius: int = 7
    logical_line_intersection_cross_color_bgr: tuple[int, int, int] = (0, 255, 0)
    logical_line_intersection_touch_color_bgr: tuple[int, int, int] = (255, 0, 0)
    logical_line_intersection_boundary_color_bgr: tuple[int, int, int] = (
        0,
        165,
        255,
    )
    frame_top_color_bgr: tuple[int, int, int] = (255, 128, 0)
    frame_bottom_color_bgr: tuple[int, int, int] = (0, 128, 255)
    frame_left_color_bgr: tuple[int, int, int] = (255, 0, 255)
    frame_right_color_bgr: tuple[int, int, int] = (0, 255, 128)
    warp_output_size_px: int = 720
    warp_output_padding_px: int = 0
    warp_cell_divisions: int = 9
    warp_cells_output_mime_type: str = "image/png"
    warp_cells_preview_gap_px: int = 2
    axis_grid_step_px: int = 25
    axis_grid_dot_radius: int = 2
    axis_grid_label_font_scale: float = 0.4
    axis_grid_label_thickness: int = 1
    axis_grid_margin_left_px: int = 44
    axis_grid_margin_top_px: int = 24
    axis_grid_margin_right_px: int = 8
    axis_grid_margin_bottom_px: int = 8


class LineFamilyName(Enum):
    UNCLASSIFIED = "unclassified"
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class SegmentOrigin(Enum):
    RAW = "raw"
    SAME_AXIS_CONNECTION = "same_axis_connection"
    CROSS_AXIS_CONNECTION = "cross_axis_connection"


@dataclass(frozen=True)
class LineSegment:
    family_name: LineFamilyName
    start: tuple[int, int]
    end: tuple[int, int]
    length: float
    angle_degrees: float
    origin: SegmentOrigin = SegmentOrigin.RAW

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


@dataclass(frozen=True)
class ToleranceRectangle:
    reference_point: tuple[int, int]
    recognition_vector: tuple[float, float]
    vector_length: int
    padding: int

    @property
    def recognition_end_point(self) -> tuple[int, int]:
        unit_x, unit_y = self._unit_vector
        return (
            int(round(self.reference_point[0] + unit_x * self.vector_length)),
            int(round(self.reference_point[1] + unit_y * self.vector_length)),
        )

    @property
    def corners(self) -> tuple[tuple[int, int], ...]:
        unit_x, unit_y = self._unit_vector
        normal_x = -unit_y
        normal_y = unit_x
        reference_x, reference_y = self.reference_point
        far_x = reference_x + unit_x * self.vector_length
        far_y = reference_y + unit_y * self.vector_length

        near_left = (
            int(round(reference_x - normal_x * self.padding)),
            int(round(reference_y - normal_y * self.padding)),
        )
        near_right = (
            int(round(reference_x + normal_x * self.padding)),
            int(round(reference_y + normal_y * self.padding)),
        )
        far_right = (
            int(round(far_x + normal_x * self.padding)),
            int(round(far_y + normal_y * self.padding)),
        )
        far_left = (
            int(round(far_x - normal_x * self.padding)),
            int(round(far_y - normal_y * self.padding)),
        )
        return (near_left, near_right, far_right, far_left)

    @property
    def _unit_vector(self) -> tuple[float, float]:
        vector_x, vector_y = self.recognition_vector
        vector_norm = math.hypot(vector_x, vector_y)
        if vector_norm == 0.0:
            raise ValueError("ToleranceRectangle recognition_vector cannot be zero.")
        return vector_x / vector_norm, vector_y / vector_norm


__all__ = [
    "ExperimentConfig",
    "LineFamilyName",
    "LineSegment",
    "SegmentOrigin",
    "ToleranceRectangle",
]
