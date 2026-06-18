import unittest

import numpy as np

from infrastructure.vision.engine_board_dataset_cell_extractor import (
    EngineBoardDatasetCellExtractor,
)
from infrastructure.vision.engine_board_preprocessor import EngineBoardPreprocessor
from infrastructure.vision.engine_warped_board_cells_extractor import (
    EngineWarpedBoardCellsExtractor,
)
from models.cells_grid import CellsGrid


class _Pipeline:
    def __init__(self) -> None:
        self.preprocess_inputs: list[np.ndarray] = []
        self.extract_inputs: list[np.ndarray] = []

    def preprocess_board(self, image: np.ndarray) -> object:
        self.preprocess_inputs.append(np.copy(image))
        return type(
            "_BoardResult",
            (),
            {"warped_board_image": np.full((18, 18), 7, dtype=np.uint8)},
        )()

    def extract_cells_from_warped_board(self, board_image: np.ndarray) -> object:
        self.extract_inputs.append(np.copy(board_image))
        cells = (
            (np.full((10, 10), 1, dtype=np.uint8),),
            (np.full((10, 10), 2, dtype=np.uint8),),
        )
        return type(
            "_CellsResult",
            (),
            {"raw_cells_grid": cells},
        )()


class _BoardPreprocessor:
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        return np.full((20, 20), 3, dtype=np.uint8)


class _WarpedBoardCellsExtractor:
    def extract(self, board_image: np.ndarray) -> CellsGrid:
        return CellsGrid.from_rows([[np.full((8, 8), 5, dtype=np.uint8)]])


class _DatasetPipeline:
    def preprocess_and_extract_cells(self, image: np.ndarray) -> object:
        return type(
            "_BoardPipelineResult",
            (),
            {
                "warped_board_image": np.full((20, 20), 3, dtype=np.uint8),
                "cells_result": type(
                    "_CellsResult",
                    (),
                    {
                        "raw_cells_grid": (
                            (np.full((8, 8), 5, dtype=np.uint8),),
                        )
                    },
                )(),
            },
        )()


class EngineBoardAdaptersTests(unittest.TestCase):
    def test_engine_board_preprocessor_should_return_warped_board_image(self) -> None:
        pipeline = _Pipeline()
        adapter = EngineBoardPreprocessor(pipeline)

        result = adapter.preprocess(np.zeros((12, 12, 3), dtype=np.uint8))

        self.assertEqual(result.shape, (18, 18))
        self.assertEqual(len(pipeline.preprocess_inputs), 1)

    def test_engine_warped_board_cells_extractor_should_return_raw_cells_grid(self) -> None:
        pipeline = _Pipeline()
        extractor = EngineWarpedBoardCellsExtractor(
            pipeline=pipeline,
            grid_rows=2,
            grid_cols=1,
            cell_inner_margin_ratio=0.2,
            minimum_cell_size_px=4,
            output_cell_size_px=None,
        )

        result = extractor.extract(np.zeros((20, 20), dtype=np.uint8))

        self.assertEqual(result.rows, 2)
        self.assertEqual(result.cols, 1)
        self.assertEqual(result.cells[0][0].shape, (10, 10))
        self.assertEqual(int(result.cells[0][0][0, 0]), 1)
        self.assertEqual(int(result.cells[1][0][0, 0]), 2)
        self.assertEqual(len(pipeline.extract_inputs), 1)

    def test_engine_board_dataset_cell_extractor_should_use_same_cells_adapter(self) -> None:
        extractor = EngineBoardDatasetCellExtractor(
            pipeline=_DatasetPipeline(),
        )

        corrected_board, cells_grid = extractor.extract(
            np.zeros((30, 30, 3), dtype=np.uint8)
        )

        self.assertEqual(corrected_board.shape, (20, 20))
        self.assertEqual(cells_grid.rows, 1)
        self.assertEqual(cells_grid.cols, 1)
        self.assertEqual(cells_grid.cells[0][0].shape, (8, 8))


if __name__ == "__main__":
    unittest.main()
