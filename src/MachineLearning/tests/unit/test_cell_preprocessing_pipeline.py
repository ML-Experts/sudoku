import unittest

import numpy as np

from infrastructure.vision.cell_cleaning import clean_binary_mask_for_empty_detection
from infrastructure.vision.cell_preprocessing_pipeline import (
    CellPreprocessingPipeline,
)


class CellPreprocessingPipelineTests(unittest.TestCase):
    def test_run_should_normalize_the_same_image_as_run_uint8(self) -> None:
        pipeline = CellPreprocessingPipeline(output_size=28)
        image = np.full((32, 32), 255, dtype=np.uint8)
        image[8:24, 14:18] = 0
        image[8:12, 10:22] = 0

        preview_image = pipeline.run_uint8(image)
        normalized_image = pipeline.run(image)

        np.testing.assert_allclose(
            normalized_image,
            preview_image.astype(np.float32) / 255.0,
        )
        self.assertEqual(preview_image.shape, (28, 28))
        self.assertEqual(normalized_image.shape, (28, 28))

    def test_run_uint8_should_return_empty_canvas_for_blank_image(self) -> None:
        pipeline = CellPreprocessingPipeline(output_size=28)
        image = np.full((28, 28), 255, dtype=np.uint8)

        preview_image = pipeline.run_uint8(image)

        self.assertEqual(int(np.max(preview_image)), 0)

    def test_run_uint8_should_keep_binary_output_after_downscaling(self) -> None:
        pipeline = CellPreprocessingPipeline(output_size=28)
        image = np.full((64, 64), 255, dtype=np.uint8)
        image[10:54, 28:36] = 0
        image[12:20, 20:44] = 0

        preview_image = pipeline.run_uint8(image)

        unique_values = set(np.unique(preview_image).tolist())
        self.assertTrue(unique_values.issubset({0, 255}))
        self.assertIn(255, unique_values)

    def test_run_uint8_should_remove_small_isolated_noise_components(self) -> None:
        pipeline = CellPreprocessingPipeline(output_size=28)
        image = np.full((64, 64), 255, dtype=np.uint8)
        image[14:50, 28:36] = 0
        image[0:2, 0:2] = 0

        preview_image = pipeline.run_uint8(image)

        self.assertEqual(int(preview_image[0:4, 0:4].max()), 0)
        self.assertGreater(int(preview_image.max()), 0)

    def test_empty_detection_cleanup_should_keep_original_resolution(self) -> None:
        binary_mask = np.zeros((64, 64), dtype=np.uint8)
        binary_mask[24:36, 46:50] = 255

        cleaned_mask = clean_binary_mask_for_empty_detection(
            binary_mask,
            border_clearance_px=0,
            min_component_area_ratio=0.0,
        )

        self.assertEqual(cleaned_mask.shape, (64, 64))
        foreground_points = np.argwhere(cleaned_mask > 0)
        self.assertTrue(np.all(foreground_points[:, 1] >= 46))


if __name__ == "__main__":
    unittest.main()
