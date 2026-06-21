import cv2
import numpy as np
from numpy.typing import NDArray

from models.cells_grid import CellsGrid


class OpenCvBoardCellsExtractor:
    def __init__(
        self,
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

        self._grid_rows = grid_rows
        self._grid_cols = grid_cols
        self._cell_inner_margin_ratio = cell_inner_margin_ratio
        self._minimum_cell_size_px = minimum_cell_size_px
        self._output_cell_size_px = output_cell_size_px

    def extract(self, board_image: NDArray[np.uint8]) -> CellsGrid:
        if board_image.size == 0:
            raise ValueError("Board image cannot be empty.")
        if board_image.ndim not in (2, 3):
            raise ValueError("Board image must be grayscale or color.")

        board_height, board_width = board_image.shape[:2]
        minimum_height = self._grid_rows * self._minimum_cell_size_px
        minimum_width = self._grid_cols * self._minimum_cell_size_px
        if board_height < minimum_height or board_width < minimum_width:
            raise ValueError("Board image is too small for configured grid.")

        extracted_rows: list[list[NDArray[np.uint8]]] = []
        for row_index in range(self._grid_rows):
            y_start, y_end = self._resolve_bounds(
                row_index, self._grid_rows, board_height
            )
            extracted_row: list[NDArray[np.uint8]] = []

            for col_index in range(self._grid_cols):
                x_start, x_end = self._resolve_bounds(
                    col_index, self._grid_cols, board_width
                )

                cell_image = board_image[y_start:y_end, x_start:x_end]
                if cell_image.size == 0:
                    raise ValueError("Extracted cell image is empty.")

                cell_image = self._crop_inner_margin(cell_image)
                cell_image = self._resize_cell_if_needed(cell_image)
                extracted_row.append(cell_image)

            extracted_rows.append(extracted_row)

        return CellsGrid.from_rows(extracted_rows)

    def _resolve_bounds(
        self, index: int, total_segments: int, total_size: int
    ) -> tuple[int, int]:
        start = int(round(index * total_size / total_segments))
        end = int(round((index + 1) * total_size / total_segments))
        if end <= start:
            raise ValueError("Could not resolve valid cell bounds.")
        return start, end

    def _crop_inner_margin(
        self, cell_image: NDArray[np.uint8]
    ) -> NDArray[np.uint8]:
        if self._cell_inner_margin_ratio == 0:
            return cell_image

        cell_height, cell_width = cell_image.shape[:2]
        margin_y = int(round(cell_height * self._cell_inner_margin_ratio))
        margin_x = int(round(cell_width * self._cell_inner_margin_ratio))

        max_margin_y = max((cell_height - self._minimum_cell_size_px) // 2, 0)
        max_margin_x = max((cell_width - self._minimum_cell_size_px) // 2, 0)
        margin_y = min(margin_y, max_margin_y)
        margin_x = min(margin_x, max_margin_x)

        cropped_cell = cell_image[
            margin_y : cell_height - margin_y, margin_x : cell_width - margin_x
        ]
        if cropped_cell.size == 0:
            raise ValueError("Cell crop with margin produced empty image.")

        cropped_height, cropped_width = cropped_cell.shape[:2]
        if (
            cropped_height < self._minimum_cell_size_px
            or cropped_width < self._minimum_cell_size_px
        ):
            raise ValueError("Cropped cell image is below minimum size.")

        return cropped_cell

    def _resize_cell_if_needed(
        self, cell_image: NDArray[np.uint8]
    ) -> NDArray[np.uint8]:
        if self._output_cell_size_px is None:
            return cell_image

        return cv2.resize(
            cell_image,
            (self._output_cell_size_px, self._output_cell_size_px),
            interpolation=cv2.INTER_AREA,
        )
