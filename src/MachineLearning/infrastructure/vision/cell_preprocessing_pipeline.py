import numpy as np
from numpy.typing import NDArray

from infrastructure.vision.cell_cleaning import (
    build_foreground_mask,
    clean_cell_binary,
)


class CellPreprocessingPipeline:
    def __init__(
        self,
        output_size: int = 28,
        median_kernel_size: int = 5,
        adaptive_block_size: int = 11,
        adaptive_c: int = 2,
        border_clearance_px: int = 0,
        min_component_area_ratio: float = 0.00008,
        min_component_area_floor_px: int = 16,
        soft_cleanup_area_multiplier: float = 0.35,
    ) -> None:
        if output_size <= 0:
            raise ValueError("Output size must be greater than zero.")
        if median_kernel_size <= 1 or median_kernel_size % 2 == 0:
            raise ValueError("Median kernel size must be an odd value > 1.")
        if adaptive_block_size <= 1 or adaptive_block_size % 2 == 0:
            raise ValueError("Adaptive block size must be an odd value > 1.")
        if border_clearance_px < 0:
            raise ValueError("Border clearance cannot be negative.")
        if not 0.0 <= min_component_area_ratio <= 1.0:
            raise ValueError("Minimum component area ratio must be in range [0, 1].")
        if min_component_area_floor_px < 0:
            raise ValueError("Minimum component area floor cannot be negative.")
        if soft_cleanup_area_multiplier < 0.0:
            raise ValueError("Soft cleanup area multiplier cannot be negative.")
        self._output_size = output_size
        self._median_kernel_size = median_kernel_size
        self._adaptive_block_size = adaptive_block_size
        self._adaptive_c = adaptive_c
        self._border_clearance_px = border_clearance_px
        self._min_component_area_ratio = min_component_area_ratio
        self._min_component_area_floor_px = min_component_area_floor_px
        self._soft_cleanup_area_multiplier = soft_cleanup_area_multiplier

    def run(self, cell_image: NDArray[np.uint8]) -> NDArray[np.float32]:
        preview_image = self.run_uint8(cell_image)
        normalized_image = preview_image.astype(np.float32) / 255.0
        return normalized_image

    def run_uint8(self, cell_image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        binary_image = self.build_foreground_mask(cell_image)
        return self._center_foreground(binary_image)

    def build_foreground_mask(
        self,
        cell_image: NDArray[np.uint8],
    ) -> NDArray[np.uint8]:
        return build_foreground_mask(
            cell_image,
            median_kernel_size=self._median_kernel_size,
            adaptive_block_size=self._adaptive_block_size,
            adaptive_c=self._adaptive_c,
        )

    def _center_foreground(self, image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        return clean_cell_binary(
            image,
            border_clearance_px=self._border_clearance_px,
            min_component_area_ratio=self._min_component_area_ratio,
            min_component_area_floor_px=self._min_component_area_floor_px,
            soft_cleanup_area_multiplier=self._soft_cleanup_area_multiplier,
            output_size=self._output_size,
        )
