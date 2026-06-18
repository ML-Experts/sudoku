from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .logical_line_frame_cell_preprocessing import (
    DEFAULT_OUTPUT_SIZE_PX,
    preprocess_cells_grid_for_ml,
)
from .preprocessing_api_codec import encode_image_api_response
from .preprocessing_api_models import CellsGridApiResponse, ImageApiResponse


@dataclass(frozen=True, slots=True)
class LogicalLineFrameCellsGridResult:
    grid_rows: int
    grid_cols: int
    min_cell_height_px: int
    min_cell_width_px: int
    cells: tuple[tuple[np.ndarray, ...], ...]
    ml_ready_cell_size_px: int
    ml_ready_cells: tuple[tuple[np.ndarray, ...], ...]
    api_response: CellsGridApiResponse
    preview_image: np.ndarray
    ml_ready_preview_image: np.ndarray


def build_warped_frame_cells_grid_result(
    board_image: np.ndarray,
    output_mime_type: str = "image/png",
    grid_rows: int = 9,
    grid_cols: int = 9,
    preview_gap_px: int = 2,
    ml_ready_cell_size_px: int = DEFAULT_OUTPUT_SIZE_PX,
    ml_ready_adaptive_block_size: int = 11,
    ml_ready_adaptive_c: int = 2,
) -> LogicalLineFrameCellsGridResult:
    if board_image.size == 0:
        raise ValueError("Board image cannot be empty.")
    if board_image.ndim not in (2, 3):
        raise ValueError("Board image must be grayscale or color.")
    if grid_rows <= 0 or grid_cols <= 0:
        raise ValueError("Grid dimensions must be positive.")
    if preview_gap_px < 0:
        raise ValueError("Preview gap cannot be negative.")

    board_height, board_width = board_image.shape[:2]
    if board_height < grid_rows or board_width < grid_cols:
        raise ValueError("Board image is too small for requested grid size.")

    extracted_rows: list[tuple[np.ndarray, ...]] = []
    cell_heights: list[int] = []
    cell_widths: list[int] = []
    for row_index in range(grid_rows):
        y_start, y_end = _resolve_bounds(row_index, grid_rows, board_height)
        extracted_row: list[np.ndarray] = []
        for col_index in range(grid_cols):
            x_start, x_end = _resolve_bounds(col_index, grid_cols, board_width)
            cell_image = board_image[y_start:y_end, x_start:x_end].copy()
            if cell_image.size == 0:
                raise ValueError("Extracted cell image cannot be empty.")

            cell_height, cell_width = cell_image.shape[:2]
            cell_heights.append(cell_height)
            cell_widths.append(cell_width)
            extracted_row.append(cell_image)
        extracted_rows.append(tuple(extracted_row))

    if not cell_heights or not cell_widths:
        raise ValueError("Could not extract any grid cells from warped board.")

    preview_image = build_cells_grid_preview_image(
        cells=tuple(extracted_rows),
        gap_px=preview_gap_px,
    )
    ml_ready_cells = preprocess_cells_grid_for_ml(
        cells=tuple(extracted_rows),
        adaptive_block_size=ml_ready_adaptive_block_size,
        adaptive_c=ml_ready_adaptive_c,
        output_size_px=ml_ready_cell_size_px,
    )
    ml_ready_preview_image = build_cells_grid_preview_image(
        cells=ml_ready_cells,
        gap_px=preview_gap_px,
    )
    return LogicalLineFrameCellsGridResult(
        grid_rows=grid_rows,
        grid_cols=grid_cols,
        min_cell_height_px=min(cell_heights),
        min_cell_width_px=min(cell_widths),
        cells=tuple(extracted_rows),
        ml_ready_cell_size_px=ml_ready_cell_size_px,
        ml_ready_cells=ml_ready_cells,
        api_response=CellsGridApiResponse(
            cells=_build_encoded_rows(
                cells=ml_ready_cells,
                output_mime_type=output_mime_type,
            )
        ),
        preview_image=preview_image,
        ml_ready_preview_image=ml_ready_preview_image,
    )


def build_cells_grid_preview_image(
    cells: tuple[tuple[np.ndarray, ...], ...],
    gap_px: int,
) -> np.ndarray:
    if not cells or not cells[0]:
        raise ValueError("Cells grid cannot be empty.")
    if gap_px < 0:
        raise ValueError("Preview gap cannot be negative.")

    flat_cells = [cell for row in cells for cell in row]
    first_cell = flat_cells[0]
    first_shape_suffix = first_cell.shape[2:] if first_cell.ndim == 3 else ()
    for cell in flat_cells:
        if cell.ndim != first_cell.ndim:
            raise ValueError("All cells must have the same number of dimensions.")
        if cell.shape[2:] != first_shape_suffix:
            raise ValueError("All cells must have compatible channel layout.")

    max_cell_height = max(cell.shape[0] for cell in flat_cells)
    max_cell_width = max(cell.shape[1] for cell in flat_cells)
    grid_rows = len(cells)
    grid_cols = len(cells[0])
    preview_height = grid_rows * max_cell_height + (grid_rows - 1) * gap_px
    preview_width = grid_cols * max_cell_width + (grid_cols - 1) * gap_px

    if first_cell.ndim == 2:
        preview_image = np.full(
            (preview_height, preview_width),
            255,
            dtype=first_cell.dtype,
        )
    else:
        preview_image = np.full(
            (preview_height, preview_width, first_cell.shape[2]),
            255,
            dtype=first_cell.dtype,
        )

    for row_index, row in enumerate(cells):
        for col_index, cell in enumerate(row):
            slot_y = row_index * (max_cell_height + gap_px)
            slot_x = col_index * (max_cell_width + gap_px)
            cell_height, cell_width = cell.shape[:2]
            offset_y = slot_y + (max_cell_height - cell_height) // 2
            offset_x = slot_x + (max_cell_width - cell_width) // 2
            preview_image[
                offset_y : offset_y + cell_height,
                offset_x : offset_x + cell_width,
            ] = cell

    return preview_image


def _resolve_bounds(
    index: int,
    total_segments: int,
    total_size: int,
) -> tuple[int, int]:
    start = int(round(index * total_size / total_segments))
    end = int(round((index + 1) * total_size / total_segments))
    if end <= start:
        raise ValueError("Could not resolve valid cell bounds.")
    return start, end


def _build_encoded_rows(
    cells: tuple[tuple[np.ndarray, ...], ...],
    output_mime_type: str,
) -> list[list[ImageApiResponse]]:
    encoded_rows: list[list[ImageApiResponse]] = []
    for row in cells:
        encoded_row = [
            encode_image_api_response(
                image=cell_image,
                mime_type=output_mime_type,
            )
            for cell_image in row
        ]
        encoded_rows.append(encoded_row)
    return encoded_rows


__all__ = [
    "CellsGridApiResponse",
    "ImageApiResponse",
    "LogicalLineFrameCellsGridResult",
    "build_cells_grid_preview_image",
    "build_warped_frame_cells_grid_result",
]
