import unittest

import numpy as np

from infrastructure.inference.cell_occupancy_detector import CellOccupancyDetector
from infrastructure.vision.cell_cleaning import (
    build_foreground_mask,
    clean_binary_mask_for_empty_detection,
)


class CellOccupancyDetectorTests(unittest.TestCase):
    def _blank_cell(self, size: int = 64) -> np.ndarray:
        return np.full((size, size, 3), 255, dtype=np.uint8)

    def _detect(
        self,
        image: np.ndarray,
        *,
        dark_pixel_ratio_threshold: float = 0.15,
        empty_cell_min_segment_length_px: int = 15,
        empty_cell_filtered_segment_count_threshold: int = 5,
        inner_margin_ratio: float = 0.0,
    ) -> object:
        detector = CellOccupancyDetector()
        return detector.detect(
            image=image,
            inner_margin_ratio=inner_margin_ratio,
            dark_pixel_ratio_threshold=dark_pixel_ratio_threshold,
            center_area_ratio=0.5,
            min_component_area_ratio=0.00008,
            line_artifact_min_span_ratio=0.5,
            line_artifact_max_thickness_ratio=0.07,
            empty_cell_min_segment_length_px=empty_cell_min_segment_length_px,
            empty_cell_filtered_segment_count_threshold=(
                empty_cell_filtered_segment_count_threshold
            ),
        )

    def test_detect_should_mark_blank_cell_as_empty(self) -> None:
        result = self._detect(self._blank_cell())

        self.assertTrue(result.is_empty)
        self.assertEqual(result.foreground_pixel_count, 0)
        self.assertEqual(result.foreground_pixel_ratio, 0.0)
        self.assertEqual(result.filtered_segment_count, 0)
        self.assertFalse(result.accept_by_pixels)
        self.assertFalse(result.accept_by_segments)

    def test_detect_should_mark_center_digit_as_not_empty(self) -> None:
        image = self._blank_cell()
        image[20:44, 28:36] = 0
        image[20:26, 20:44] = 0

        result = self._detect(image)

        self.assertFalse(result.is_empty)
        self.assertGreater(result.foreground_pixel_ratio, 0.15)
        self.assertTrue(result.accept_by_pixels)

    def test_detect_should_accept_thin_center_stroke_by_segments(self) -> None:
        image = self._blank_cell()
        image[18:46, 31:33] = 0

        result = self._detect(
            image,
            dark_pixel_ratio_threshold=0.15,
            empty_cell_min_segment_length_px=15,
            empty_cell_filtered_segment_count_threshold=1,
        )

        self.assertFalse(result.is_empty)
        self.assertFalse(result.accept_by_pixels)
        self.assertTrue(result.accept_by_segments)
        self.assertGreaterEqual(result.filtered_segment_count, 1)

    def test_detect_should_ignore_border_artifact(self) -> None:
        image = self._blank_cell()
        image[8:56, 0:3] = 0

        result = self._detect(image)

        self.assertTrue(result.is_empty)
        self.assertEqual(result.foreground_pixel_count, 0)

    def test_empty_detection_cleanup_should_keep_original_shape(self) -> None:
        image = self._blank_cell()
        image[24:36, 46:50] = 0
        foreground_mask = build_foreground_mask(
            image,
            median_kernel_size=5,
            adaptive_block_size=11,
            adaptive_c=2,
        )

        cleaned_mask = clean_binary_mask_for_empty_detection(
            foreground_mask,
            border_clearance_px=0,
            min_component_area_ratio=0.0,
        )

        self.assertEqual(cleaned_mask.shape, foreground_mask.shape)
        foreground_points = np.argwhere(cleaned_mask > 0)
        self.assertTrue(np.all(foreground_points[:, 1] >= 46))


if __name__ == "__main__":
    unittest.main()
