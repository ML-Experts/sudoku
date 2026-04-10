from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class CellsGrid:
    cells: tuple[tuple[NDArray[np.uint8], ...], ...]

    @classmethod
    def from_rows(
        cls, rows: Sequence[Sequence[NDArray[np.uint8]]]
    ) -> "CellsGrid":
        normalized_rows: list[tuple[NDArray[np.uint8], ...]] = []
        for row in rows:
            normalized_row: list[NDArray[np.uint8]] = []
            for cell in row:
                if cell.size == 0:
                    raise ValueError("Cells grid cannot contain empty images.")
                normalized_row.append(cell)
            if not normalized_row:
                raise ValueError("Cells grid row cannot be empty.")
            normalized_rows.append(tuple(normalized_row))

        if not normalized_rows:
            raise ValueError("Cells grid cannot be empty.")

        expected_columns = len(normalized_rows[0])
        for normalized_row in normalized_rows[1:]:
            if len(normalized_row) != expected_columns:
                raise ValueError(
                    "Every cells grid row must have the same length."
                )

        return cls(cells=tuple(normalized_rows))

    @property
    def rows(self) -> int:
        return len(self.cells)

    @property
    def cols(self) -> int:
        if not self.cells:
            return 0
        return len(self.cells[0])

    def validate_dimensions(
        self, expected_rows: int, expected_cols: int
    ) -> None:
        if self.rows != expected_rows:
            raise ValueError(
                f"Expected {expected_rows} rows, got {self.rows}."
            )

        for row_index, row in enumerate(self.cells):
            if len(row) != expected_cols:
                raise ValueError(
                    f"Expected {expected_cols} columns in row "
                    f"{row_index}, got {len(row)}."
                )
