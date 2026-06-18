import unittest
from unittest.mock import patch

import numpy as np

from infrastructure.vision.engine_vision_pipeline import (
    EngineVisionPipeline,
    EngineVisionPipelineError,
)


class EngineVisionPipelineTests(unittest.TestCase):
    def _create_pipeline(self) -> EngineVisionPipeline:
        return EngineVisionPipeline(
            output_mime_type="image/png",
            minimum_cell_size_px=8,
            max_display_size=1600,
            adaptive_threshold_block_size=11,
            adaptive_threshold_c_value=2,
            hough_threshold=35,
            min_line_length_ratio=0.08,
            max_line_gap_ratio=0.005,
            angle_tolerance_degrees=20.0,
            warp_output_size_px=720,
            warp_output_padding_px=0,
            warp_cell_divisions=9,
            warp_cells_output_mime_type="image/png",
        )

    @patch(
        "infrastructure.vision.engine_vision_pipeline.extract_cells_from_board_image"
    )
    def test_extract_cells_from_warped_board_should_flatten_raw_and_ml_ready_cells(
        self,
        extract_cells_from_board_image_mock,
    ) -> None:
        pipeline = self._create_pipeline()
        raw_cells = tuple(
            tuple(np.full((4, 4), row * 2 + col, dtype=np.uint8) for col in range(2))
            for row in range(2)
        )
        ml_ready_cells = tuple(
            tuple(np.full((28, 28), row * 2 + col, dtype=np.uint8) for col in range(2))
            for row in range(2)
        )
        extract_cells_from_board_image_mock.return_value = type(
            "_Result",
            (),
            {
                "cells_grid_result": type(
                    "_GridResult",
                    (),
                    {
                        "cells": raw_cells,
                        "ml_ready_cells": ml_ready_cells,
                        "preview_image": np.zeros((10, 10), dtype=np.uint8),
                        "ml_ready_preview_image": np.zeros(
                            (20, 20), dtype=np.uint8
                        ),
                    },
                )()
            },
        )()

        result = pipeline.extract_cells_from_warped_board(
            np.zeros((90, 90, 3), dtype=np.uint8)
        )

        self.assertEqual(len(result.raw_cells_flat), 4)
        self.assertEqual(len(result.ml_ready_cells_flat), 4)
        self.assertEqual(result.raw_cells_grid, raw_cells)
        self.assertEqual(result.ml_ready_cells_grid, ml_ready_cells)

    @patch("infrastructure.vision.engine_vision_pipeline.preprocess_board_image")
    def test_preprocess_board_should_map_engine_error_type(self, preprocess_mock) -> None:
        pipeline = self._create_pipeline()
        preprocess_mock.side_effect = type(
            "_Error",
            (Exception,),
            {"error_type": "board_not_found"},
        )("board_not_found")

        with self.assertRaises(EngineVisionPipelineError) as raised_error:
            pipeline.preprocess_board(np.zeros((20, 20, 3), dtype=np.uint8))

        self.assertEqual(raised_error.exception.error_type, "board_not_found")


if __name__ == "__main__":
    unittest.main()
