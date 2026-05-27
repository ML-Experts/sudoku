import cv2
import numpy as np
from numpy.typing import NDArray

from infrastructure.vision.sudoku_threshold_binary import build_denoise_variants
from infrastructure.vision.sudoku_threshold_models import SudokuThresholdConfig


class OpenCvGrayscaleBlurPreprocessor:
    def __init__(
        self,
        grayscale_color_conversion_code: int,
        gaussian_kernel_size: tuple[int, int],
        gaussian_sigma_x: float,
    ) -> None:
        kernel_width, kernel_height = gaussian_kernel_size
        if kernel_width <= 0 or kernel_height <= 0:
            raise ValueError("Gaussian kernel size must be greater than zero.")
        if kernel_width % 2 == 0 or kernel_height % 2 == 0:
            raise ValueError("Gaussian kernel size must have odd values.")

        self._grayscale_color_conversion_code = grayscale_color_conversion_code
        self._gaussian_kernel_size = gaussian_kernel_size
        self._gaussian_sigma_x = gaussian_sigma_x

    def preprocess(self, image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        if image.size == 0:
            raise ValueError("Input image is empty.")

        if image.ndim == 2:
            grayscale = image
        elif image.ndim == 3:
            grayscale = cv2.cvtColor(image, self._grayscale_color_conversion_code)
        else:
            raise ValueError("Unsupported image dimensions.")

        config = SudokuThresholdConfig(
            raw_hough_threshold=1,
            raw_min_line_length_ratio=0.01,
            raw_max_line_gap_ratio=0.01,
            line_family_angle_tolerance_degrees=1.0,
            line_merge_projection_distance_ratio=0.01,
            frame_min_area_ratio=0.01,
            minimum_family_segments=2,
            minimum_distinct_lines_per_family=2,
            gaussian_kernel_size=self._gaussian_kernel_size,
            median_kernel_size=self._gaussian_kernel_size[0],
            unsharp_gaussian_kernel_size=self._gaussian_kernel_size,
            unsharp_gaussian_sigma=self._gaussian_sigma_x,
            selected_denoise_variant=f"median_{self._gaussian_kernel_size[0]}",
        )
        denoise_variants = build_denoise_variants(grayscale, config)
        return denoise_variants[config.selected_denoise_variant]
