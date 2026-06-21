from __future__ import annotations

import logging

import numpy as np
from numpy.typing import NDArray

from infrastructure.vision.engine_vision_pipeline import EngineVisionPipeline
from models.cells_grid import CellsGrid

LOGGER = logging.getLogger(__name__)


class EngineWarpedBoardCellsExtractor:
    def __init__(
        self,
        pipeline: EngineVisionPipeline,
        *,
        grid_rows: int = 9,
        grid_cols: int = 9,
        cell_inner_margin_ratio: float = 0.0,
        minimum_cell_size_px: int = 8,
        output_cell_size_px: int | None = None,
    ) -> None:
        if grid_rows <= 0:
            raise ValueError("Grid rows must be greater than zero.")
        if grid_cols <= 0:
            raise ValueError("Grid cols must be greater than zero.")
        if not 0 <= cell_inner_margin_ratio < 0.5:
            raise ValueError(
                "Cell inner margin ratio must be between 0 and 0.5."
            )
        if minimum_cell_size_px <= 0:
            raise ValueError(
                "Minimum cell size in pixels must be greater than zero."
            )
        if output_cell_size_px is not None and output_cell_size_px <= 0:
            raise ValueError(
                "Output cell size in pixels must be greater than zero."
            )

        self._pipeline = pipeline
        self._grid_rows = grid_rows
        self._grid_cols = grid_cols
        self._cell_inner_margin_ratio = cell_inner_margin_ratio
        self._minimum_cell_size_px = minimum_cell_size_px
        self._output_cell_size_px = output_cell_size_px

    def extract(self, board_image: NDArray[np.uint8]) -> CellsGrid:
        LOGGER.info(
            "EngineWarpedBoardCellsExtractor using explicit warped-board extraction flow."
        )
        cells_result = self._pipeline.extract_cells_from_warped_board(board_image)
        # Notebook/reference flow returns raw warped cells here and keeps
        # ML-ready preprocessing as a separate downstream concern.
        cells_grid = CellsGrid.from_rows(cells_result.raw_cells_grid)
        cells_grid.validate_dimensions(
            expected_rows=self._grid_rows,
            expected_cols=self._grid_cols,
        )
        return cells_grid
