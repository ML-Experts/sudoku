from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from logical_line_frame_cells import LogicalLineFrameCellsGridResult


@dataclass(frozen=True, slots=True)
class LogicalLineFrameCorners:
    top_left: tuple[float, float]
    top_right: tuple[float, float]
    bottom_right: tuple[float, float]
    bottom_left: tuple[float, float]

    @property
    def ordered_points(
        self,
    ) -> tuple[
        tuple[float, float],
        tuple[float, float],
        tuple[float, float],
        tuple[float, float],
    ]:
        return (
            self.top_left,
            self.top_right,
            self.bottom_right,
            self.bottom_left,
        )

    def as_array(self) -> np.ndarray:
        corner_array = np.array(self.ordered_points, dtype=np.float32)
        if corner_array.shape != (4, 2):
            raise ValueError("Frame corners must contain exactly four 2D points.")
        if not np.isfinite(corner_array).all():
            raise ValueError("Frame corners must contain only finite values.")
        return corner_array


@dataclass(frozen=True, slots=True)
class LogicalLineFrameWarpResult:
    source_corners: LogicalLineFrameCorners
    rectangle_width_px: float
    rectangle_height_px: float
    inferred_square_side_px: float
    output_size_px: int
    padding_px: int
    destination_corners: tuple[
        tuple[float, float],
        tuple[float, float],
        tuple[float, float],
        tuple[float, float],
    ]
    perspective_matrix: np.ndarray
    warped_image: np.ndarray
    cells_grid_result: LogicalLineFrameCellsGridResult | None = None


__all__ = [
    "LogicalLineFrameCorners",
    "LogicalLineFrameWarpResult",
]
