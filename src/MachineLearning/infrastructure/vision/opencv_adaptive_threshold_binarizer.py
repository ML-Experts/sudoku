import cv2
import numpy as np
from numpy.typing import NDArray

from infrastructure.vision.sudoku_threshold_binary import build_threshold_variants
from infrastructure.vision.sudoku_threshold_models import SudokuThresholdConfig


class OpenCvAdaptiveThresholdBinarizer:
    def __init__(self, block_size: int, c_value: int) -> None:
        if block_size <= 1:
            raise ValueError("Adaptive threshold block size must be > 1.")
        if block_size % 2 == 0:
            raise ValueError("Adaptive threshold block size must be odd.")

        self._block_size = block_size
        self._c_value = c_value

    def binarize(self, image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        if image.size == 0:
            raise ValueError("Input image is empty.")
        if image.ndim != 2:
            raise ValueError("Adaptive threshold expects a grayscale image.")

        config = SudokuThresholdConfig(
            raw_hough_threshold=1,
            raw_min_line_length_ratio=0.01,
            raw_max_line_gap_ratio=0.01,
            line_family_angle_tolerance_degrees=1.0,
            line_merge_projection_distance_ratio=0.01,
            frame_min_area_ratio=0.01,
            minimum_family_segments=2,
            minimum_distinct_lines_per_family=2,
            adaptive_method_name="gaussian",
            adaptive_block_sizes=(self._block_size,),
            adaptive_c_values=(self._c_value,),
            selected_threshold_name=(
                f"gaussian_block{self._block_size}_c{self._c_value}"
            ),
        )
        threshold_variants = build_threshold_variants(image, config)
        return threshold_variants[config.selected_threshold_name]
