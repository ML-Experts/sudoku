import unittest

import numpy as np

from infrastructure.inference.cell_occupancy_detector import (
    CellOccupancyDetector,
)


class CellOccupancyDetectorTests(unittest.TestCase):
    def _detect(self, image: np.ndarray) -> object:
        detector = CellOccupancyDetector()
        return detector.detect(
            image=image,
            inner_margin_ratio=0.12,
            dark_pixel_ratio_threshold=0.02,
            center_area_ratio=0.5,
            min_component_area_ratio=0.02,
            line_artifact_min_span_ratio=0.5,
            line_artifact_max_thickness_ratio=0.07,
        )

    def _detect_with_configuration(
        self,
        image: np.ndarray,
        *,
        inner_margin_ratio: float,
        center_area_ratio: float,
        line_artifact_min_span_ratio: float,
        line_artifact_max_thickness_ratio: float,
    ) -> object:
        detector = CellOccupancyDetector()
        return detector.detect(
            image=image,
            inner_margin_ratio=inner_margin_ratio,
            dark_pixel_ratio_threshold=0.02,
            center_area_ratio=center_area_ratio,
            min_component_area_ratio=0.02,
            line_artifact_min_span_ratio=line_artifact_min_span_ratio,
            line_artifact_max_thickness_ratio=line_artifact_max_thickness_ratio,
        )

    def test_detect_should_mark_blank_cell_as_empty(self) -> None:
        image = np.zeros((28, 28), dtype=np.float32)

        result = self._detect(image)

        self.assertTrue(result.is_empty)
        self.assertEqual(result.dark_pixel_ratio, 0.0)

    def test_detect_should_mark_center_digit_as_not_empty(self) -> None:
        image = np.zeros((28, 28), dtype=np.float32)
        image[10:18, 12:16] = 1.0

        result = self._detect(image)

        self.assertFalse(result.is_empty)
        self.assertGreater(result.dark_pixel_ratio, 0.02)

    def test_detect_should_ignore_foreground_near_border(self) -> None:
        image = np.zeros((28, 28), dtype=np.float32)
        image[:, 0:2] = 1.0

        result = self._detect(image)

        self.assertTrue(result.is_empty)

    def test_detect_should_ignore_component_touching_inner_window_border(
        self,
    ) -> None:
        image = np.zeros((28, 28), dtype=np.float32)
        image[4:24, 4:7] = 1.0

        result = self._detect(image)

        self.assertTrue(result.is_empty)

    def test_detect_should_keep_center_component_after_border_filtering(
        self,
    ) -> None:
        image = np.zeros((28, 28), dtype=np.float32)
        image[4:24, 4:7] = 1.0
        image[10:18, 12:16] = 1.0

        result = self._detect(image)

        self.assertFalse(result.is_empty)
        self.assertGreater(result.dark_pixel_ratio, 0.02)

    def test_detect_should_ignore_detached_near_edge_line_artifact(
        self,
    ) -> None:
        image = np.zeros((57, 57), dtype=np.float32)
        image[10:47, 8:10] = 1.0

        result = self._detect(image)

        self.assertTrue(result.is_empty)
        self.assertEqual(result.dark_pixel_ratio, 0.0)

    def test_detect_should_keep_centered_slender_digit_like_component(
        self,
    ) -> None:
        image = np.zeros((57, 57), dtype=np.float32)
        image[14:43, 27:30] = 1.0

        result = self._detect(image)

        self.assertFalse(result.is_empty)
        self.assertGreater(result.dark_pixel_ratio, 0.02)

    def test_detect_should_ignore_internal_horizontal_line_artifact(
        self,
    ) -> None:
        image = np.zeros((57, 57), dtype=np.float32)
        image[24:26, 10:40] = 1.0

        result = self._detect(image)

        self.assertTrue(result.is_empty)
        self.assertEqual(result.dark_pixel_ratio, 0.0)

    def test_detect_should_ignore_side_vertical_line_artifact_from_bad_crop(
        self,
    ) -> None:
        image = np.zeros((57, 57), dtype=np.float32)
        image[10:36, 36:38] = 1.0

        result = self._detect(image)

        self.assertTrue(result.is_empty)
        self.assertEqual(result.dark_pixel_ratio, 0.0)

    def test_detect_should_keep_right_shifted_slender_digit_component(
        self,
    ) -> None:
        image = np.zeros((57, 57), dtype=np.float32)
        image[14:43, 34:37] = 1.0

        result = self._detect(image)

        self.assertFalse(result.is_empty)
        self.assertGreater(result.dark_pixel_ratio, 0.02)

    def test_detect_should_apply_inner_margin_ratio_before_center_analysis(
        self,
    ) -> None:
        image = np.zeros((28, 28), dtype=np.float32)
        image[4:24, 4:7] = 1.0

        result_without_margin = self._detect_with_configuration(
            image,
            inner_margin_ratio=0.0,
            center_area_ratio=0.8,
            line_artifact_min_span_ratio=1.0,
            line_artifact_max_thickness_ratio=0.01,
        )
        result_with_margin = self._detect_with_configuration(
            image,
            inner_margin_ratio=0.12,
            center_area_ratio=0.8,
            line_artifact_min_span_ratio=1.0,
            line_artifact_max_thickness_ratio=0.01,
        )

        self.assertFalse(result_without_margin.is_empty)
        self.assertTrue(result_with_margin.is_empty)


if __name__ == "__main__":
    unittest.main()
