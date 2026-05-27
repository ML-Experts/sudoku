import unittest

import numpy as np

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


if __name__ == "__main__":
    unittest.main()
