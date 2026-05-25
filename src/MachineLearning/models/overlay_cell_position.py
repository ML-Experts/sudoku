from dataclasses import dataclass


@dataclass(frozen=True)
class OverlayCellPosition:
    row_index: int | None = None
    column_index: int | None = None

    def __post_init__(self) -> None:
        if self.row_index is not None and not 0 <= self.row_index <= 8:
            raise ValueError("Overlay row index must be in range 0..8.")
        if self.column_index is not None and not 0 <= self.column_index <= 8:
            raise ValueError("Overlay column index must be in range 0..8.")
