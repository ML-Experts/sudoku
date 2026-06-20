from __future__ import annotations

import numpy as np

from logical_line_frame_cells import build_cells_grid_preview_image
from models import ExperimentConfig

from .core import analyze_empty_cell_preprocessing, preprocess_raw_cell_bgr
from .models import (
    EmptyCellConfig,
    EmptyCellGridAnalysisResult,
    EmptyCellGridCellResult,
    EmptyCellGridPreprocessingResult,
    EmptyCellPreprocessingArtifacts,
)

RawCellsGrid = tuple[tuple[np.ndarray, ...], ...]


def preprocess_raw_cells_grid(
    raw_cells_grid: RawCellsGrid,
    *,
    empty_cell_config: EmptyCellConfig,
    processing_config: ExperimentConfig,
    preview_gap_px: int = 2,
) -> EmptyCellGridPreprocessingResult:
    _validate_raw_cells_grid(raw_cells_grid)

    preprocessing_rows: list[tuple[EmptyCellPreprocessingArtifacts, ...]] = []
    binary_rows: list[tuple[np.ndarray, ...]] = []
    clean_rows: list[tuple[np.ndarray, ...]] = []
    center_composite_rows: list[tuple[np.ndarray, ...]] = []

    for raw_row in raw_cells_grid:
        preprocessing_row: list[EmptyCellPreprocessingArtifacts] = []
        binary_row: list[np.ndarray] = []
        clean_row: list[np.ndarray] = []
        center_composite_row: list[np.ndarray] = []

        for raw_cell_bgr in raw_row:
            preprocessing = preprocess_raw_cell_bgr(
                raw_cell_bgr,
                empty_cell_config=empty_cell_config,
                processing_config=processing_config,
            )
            preprocessing_row.append(preprocessing)
            binary_row.append(preprocessing.binary_mask)
            clean_row.append(preprocessing.clean_mask)
            center_composite_row.append(preprocessing.center_composite)

        preprocessing_rows.append(tuple(preprocessing_row))
        binary_rows.append(tuple(binary_row))
        clean_rows.append(tuple(clean_row))
        center_composite_rows.append(tuple(center_composite_row))

    binary_grid = tuple(binary_rows)
    clean_grid = tuple(clean_rows)
    center_composite_grid = tuple(center_composite_rows)
    return EmptyCellGridPreprocessingResult(
        preprocessing_grid=tuple(preprocessing_rows),
        binary_preview_image=build_cells_grid_preview_image(
            binary_grid,
            gap_px=preview_gap_px,
        ),
        clean_preview_image=build_cells_grid_preview_image(
            clean_grid,
            gap_px=preview_gap_px,
        ),
        center_composite_preview_image=build_cells_grid_preview_image(
            center_composite_grid,
            gap_px=preview_gap_px,
        ),
    )


def analyze_raw_cells_grid(
    raw_cells_grid: RawCellsGrid,
    *,
    empty_cell_config: EmptyCellConfig,
    processing_config: ExperimentConfig,
    preview_gap_px: int = 2,
) -> EmptyCellGridAnalysisResult:
    preprocessing_result = preprocess_raw_cells_grid(
        raw_cells_grid,
        empty_cell_config=empty_cell_config,
        processing_config=processing_config,
        preview_gap_px=preview_gap_px,
    )
    cell_results: list[EmptyCellGridCellResult] = []

    for row_index, preprocessing_row in enumerate(
        preprocessing_result.preprocessing_grid
    ):
        for col_index, preprocessing in enumerate(preprocessing_row):
            cell_results.append(
                EmptyCellGridCellResult(
                    cell_number=row_index * len(preprocessing_row) + col_index + 1,
                    row_index=row_index,
                    col_index=col_index,
                    analysis=analyze_empty_cell_preprocessing(
                        preprocessing,
                        empty_cell_config=empty_cell_config,
                    ),
                )
            )

    empty_count = sum(1 for cell_result in cell_results if cell_result.analysis.is_empty)
    return EmptyCellGridAnalysisResult(
        cell_results=tuple(cell_results),
        preprocessing_result=preprocessing_result,
        empty_count=empty_count,
        non_empty_count=len(cell_results) - empty_count,
    )


def get_cell_result_by_number(
    cell_results: tuple[EmptyCellGridCellResult, ...] | list[EmptyCellGridCellResult],
    cell_number_1_based: int,
) -> EmptyCellGridCellResult:
    for cell_result in cell_results:
        if cell_result.cell_number == cell_number_1_based:
            return cell_result

    raise ValueError(
        f"Cell result with number {cell_number_1_based} was not found."
    )


def _validate_raw_cells_grid(raw_cells_grid: RawCellsGrid) -> None:
    if not raw_cells_grid or not raw_cells_grid[0]:
        raise ValueError("Raw cells grid cannot be empty.")
    expected_row_length = len(raw_cells_grid[0])
    for raw_row in raw_cells_grid:
        if len(raw_row) != expected_row_length:
            raise ValueError("Each row in raw cells grid must have the same length.")


__all__ = [
    "RawCellsGrid",
    "analyze_raw_cells_grid",
    "get_cell_result_by_number",
    "preprocess_raw_cells_grid",
]
