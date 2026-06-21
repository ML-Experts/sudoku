import numpy as np
from numpy.typing import NDArray

from infrastructure.vision.cell_cleaning import (
    apply_inner_margin,
    build_center_quadrant_composite,
    build_foreground_mask,
    clean_binary_mask_for_empty_detection,
    count_foreground_pixel_ratio,
    count_foreground_pixels,
    detect_hough_segments,
    filter_short_segments,
)
from models.cell_occupancy import CellOccupancy


class CellOccupancyDetector:
    def detect(
        self,
        image: NDArray[np.uint8],
        inner_margin_ratio: float,
        dark_pixel_ratio_threshold: float,
        center_area_ratio: float,
        min_component_area_ratio: float,
        line_artifact_min_span_ratio: float,
        line_artifact_max_thickness_ratio: float,
        empty_cell_min_segment_length_px: int,
        empty_cell_filtered_segment_count_threshold: int,
    ) -> CellOccupancy:
        if image.size == 0:
            raise ValueError("Image cannot be empty.")
        if image.ndim not in (2, 3):
            raise ValueError("Cell occupancy detector expects a 2D or 3D image.")
        if not 0.0 <= inner_margin_ratio < 0.5:
            raise ValueError("Inner margin ratio must be in range [0.0, 0.5).")
        if not 0.0 <= dark_pixel_ratio_threshold <= 1.0:
            raise ValueError(
                "Dark pixel ratio threshold must be in range [0.0, 1.0]."
            )
        if not 0.0 <= center_area_ratio <= 1.0:
            raise ValueError("Center area ratio must be in range [0.0, 1.0].")
        if not 0.0 <= min_component_area_ratio <= 1.0:
            raise ValueError(
                "Minimum component area ratio must be in range [0.0, 1.0]."
            )
        if not 0.0 <= line_artifact_min_span_ratio <= 1.0:
            raise ValueError(
                "Line artifact min span ratio must be in range [0.0, 1.0]."
            )
        if not 0.0 <= line_artifact_max_thickness_ratio <= 1.0:
            raise ValueError(
                "Line artifact max thickness ratio must be in range [0.0, 1.0]."
            )
        if empty_cell_min_segment_length_px <= 0:
            raise ValueError("Minimum segment length must be greater than zero.")
        if empty_cell_filtered_segment_count_threshold <= 0:
            raise ValueError(
                "Filtered segment count threshold must be greater than zero."
            )

        foreground_mask = build_foreground_mask(
            image,
            median_kernel_size=5,
            adaptive_block_size=11,
            adaptive_c=2,
        )
        cleaned_mask = clean_binary_mask_for_empty_detection(
            foreground_mask,
            min_component_area_ratio=min_component_area_ratio,
            border_clearance_px=0,
        )
        # Notebook `FinalApi` crops the inner margin after cleanup instead of
        # removing border-touching components. We keep that behavior here.
        cropped_mask = apply_inner_margin(
            cleaned_mask,
            inner_margin_ratio,
        )
        center_composite = build_center_quadrant_composite(cropped_mask)
        segments = detect_hough_segments(center_composite)
        filtered_segments = filter_short_segments(
            segments,
            empty_cell_min_segment_length_px,
        )

        foreground_pixel_count = count_foreground_pixels(center_composite)
        foreground_pixel_ratio = count_foreground_pixel_ratio(center_composite)
        accept_by_pixels = (
            foreground_pixel_ratio > dark_pixel_ratio_threshold
        )
        accept_by_segments = (
            len(filtered_segments)
            >= empty_cell_filtered_segment_count_threshold
        )

        return CellOccupancy(
            is_empty=not (accept_by_pixels or accept_by_segments),
            foreground_pixel_count=foreground_pixel_count,
            foreground_pixel_ratio=foreground_pixel_ratio,
            filtered_segment_count=len(filtered_segments),
            accept_by_pixels=accept_by_pixels,
            accept_by_segments=accept_by_segments,
        )