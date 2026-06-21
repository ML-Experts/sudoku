from __future__ import annotations

import logging

import numpy as np
from numpy.typing import NDArray

from infrastructure.vision.engine_vision_pipeline import EngineVisionPipeline
from models.cells_grid import CellsGrid

LOGGER = logging.getLogger(__name__)


class EngineBoardDatasetCellExtractor:
    def __init__(
        self,
        pipeline: EngineVisionPipeline,
    ) -> None:
        self._pipeline = pipeline

    def extract(
        self, board_image: NDArray[np.uint8]
    ) -> tuple[NDArray[np.uint8], CellsGrid]:
        LOGGER.info(
            "EngineBoardDatasetCellExtractor using preprocess-and-extract dataset flow."
        )
        pipeline_result = self._pipeline.preprocess_and_extract_cells(board_image)
        cells_result = pipeline_result.cells_result
        if cells_result is None:
            raise ValueError("Board cells result is not available after preprocessing.")

        corrected_board = pipeline_result.warped_board_image
        cells_grid = CellsGrid.from_rows(cells_result.raw_cells_grid)
        return corrected_board, cells_grid
