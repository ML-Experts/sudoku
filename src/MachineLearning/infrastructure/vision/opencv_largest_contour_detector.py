import numpy as np
from numpy.typing import NDArray

from infrastructure.vision.sudoku_threshold_binary import (
    build_cleanup_variants,
    build_repair_variants,
)
from infrastructure.vision.sudoku_threshold_frame import find_line_frames
from infrastructure.vision.sudoku_threshold_line_detection import detect_line_families
from infrastructure.vision.sudoku_threshold_models import SudokuThresholdConfig
from models.board_quad import BoardQuad


class OpenCvBoardEdgeDetector:
    def __init__(
        self,
        canny_threshold_1: int,
        canny_threshold_2: int,
        hough_threshold: int,
        min_line_length_ratio: float,
        max_line_gap_ratio: float,
        angle_tolerance_degrees: float,
        outer_line_window_ratio: float,
        minimum_board_area_ratio: float,
        minimum_family_segments: int,
        line_position_merge_distance_ratio: float,
        minimum_distinct_lines_per_family: int,
    ) -> None:
        if canny_threshold_1 < 0 or canny_threshold_2 < 0:
            raise ValueError("Canny thresholds must be non-negative.")
        if hough_threshold <= 0:
            raise ValueError("Hough threshold must be greater than zero.")
        if min_line_length_ratio <= 0:
            raise ValueError("Minimum line length ratio must be greater than zero.")
        if max_line_gap_ratio <= 0:
            raise ValueError("Maximum line gap ratio must be greater than zero.")
        if not 0 < angle_tolerance_degrees < 45:
            raise ValueError("Angle tolerance must be between 0 and 45 degrees.")
        if not 0 < outer_line_window_ratio < 1:
            raise ValueError("Outer line window ratio must be between 0 and 1.")
        if not 0 < minimum_board_area_ratio < 1:
            raise ValueError("Minimum board area ratio must be between 0 and 1.")
        if minimum_family_segments < 2:
            raise ValueError("Minimum family segments must be at least 2.")
        if not 0 < line_position_merge_distance_ratio < 1:
            raise ValueError(
                "Line position merge distance ratio must be between 0 and 1."
            )
        if minimum_distinct_lines_per_family < 2:
            raise ValueError(
                "Minimum distinct lines per family must be at least 2."
            )

        self._minimum_family_segments = minimum_family_segments
        self._minimum_distinct_lines_per_family = (
            minimum_distinct_lines_per_family
        )
        self._config = SudokuThresholdConfig(
            raw_hough_threshold=hough_threshold,
            raw_min_line_length_ratio=min_line_length_ratio,
            raw_max_line_gap_ratio=max_line_gap_ratio,
            line_family_angle_tolerance_degrees=angle_tolerance_degrees,
            line_merge_projection_distance_ratio=line_position_merge_distance_ratio,
            frame_min_area_ratio=minimum_board_area_ratio,
            minimum_family_segments=minimum_family_segments,
            minimum_distinct_lines_per_family=minimum_distinct_lines_per_family,
        )

    def detect(self, image: NDArray[np.uint8]) -> BoardQuad:
        if image.size == 0:
            raise ValueError("Input image is empty.")
        if image.ndim != 2:
            raise ValueError("Board edge detector expects a binary image.")

        _, cleanup_variants = build_cleanup_variants(
            image,
            self._config,
        )
        cleanup_variant_name = self._config.selected_cleanup_variant or "adaptive_only"
        cleaned_binary = cleanup_variants.get(cleanup_variant_name, image)
        if not np.any(cleaned_binary):
            cleaned_binary = image.copy()

        repair_variants = build_repair_variants(cleaned_binary, self._config)
        repair_variant_name = self._config.selected_repair_variant or "cleanup_only"
        repaired_binary = repair_variants.get(repair_variant_name, cleaned_binary)
        if not np.any(repaired_binary):
            repaired_binary = cleaned_binary

        line_family_result = detect_line_families(repaired_binary, self._config)
        if (
            len(line_family_result.horizontal_segments)
            < self._minimum_family_segments
        ):
            raise ValueError("Primary board edge family is too small.")
        if len(line_family_result.vertical_segments) < self._minimum_family_segments:
            raise ValueError("Secondary board edge family is too small.")
        if (
            len(line_family_result.horizontal_merged_lines)
            < self._minimum_distinct_lines_per_family
        ):
            raise ValueError(
                "Primary board edge family lacks Sudoku-like grid lines."
            )
        if (
            len(line_family_result.vertical_merged_lines)
            < self._minimum_distinct_lines_per_family
        ):
            raise ValueError(
                "Secondary board edge family lacks Sudoku-like grid lines."
            )

        frame_detection_result = find_line_frames(line_family_result, self._config)
        if not frame_detection_result.selected_frames:
            raise ValueError("Could not build a valid Sudoku board frame.")

        selected_frame = frame_detection_result.selected_frames[0]
        corners = selected_frame.corners
        horizontal_line_count = selected_frame.horizontal_line_count
        vertical_line_count = selected_frame.vertical_line_count

        if (
            horizontal_line_count < self._minimum_distinct_lines_per_family
            or vertical_line_count < self._minimum_distinct_lines_per_family
        ):
            raise ValueError("Detected board frame does not contain enough grid lines.")

        return BoardQuad(
            top_left=tuple(map(float, corners[0])),
            top_right=tuple(map(float, corners[1])),
            bottom_right=tuple(map(float, corners[2])),
            bottom_left=tuple(map(float, corners[3])),
        )
