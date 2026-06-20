from __future__ import annotations

import cv2
import numpy as np

from logical_line_frame_cells import build_cells_grid_preview_image

from .models import EmptyCellGridCellResult, HoughSegment


def resolve_cell_position(
    cell_number_1_based: int,
    *,
    grid_size: int = 9,
) -> tuple[int, int]:
    if not 1 <= cell_number_1_based <= grid_size * grid_size:
        raise ValueError(
            f"cell_number_1_based must be in range 1..{grid_size * grid_size}."
        )

    zero_based_index = cell_number_1_based - 1
    return zero_based_index // grid_size, zero_based_index % grid_size


def draw_numbered_board_overlay(
    board_bgr: np.ndarray,
    selected_cell_number_1_based: int,
    *,
    grid_size: int = 9,
) -> np.ndarray:
    overlay = board_bgr.copy()
    board_height, board_width = overlay.shape[:2]
    cell_height = board_height / float(grid_size)
    cell_width = board_width / float(grid_size)

    for row_index in range(grid_size):
        for col_index in range(grid_size):
            cell_number = row_index * grid_size + col_index + 1
            y_start = int(round(row_index * cell_height))
            y_end = int(round((row_index + 1) * cell_height))
            x_start = int(round(col_index * cell_width))
            x_end = int(round((col_index + 1) * cell_width))

            is_selected = cell_number == selected_cell_number_1_based
            rectangle_color = (0, 255, 0) if is_selected else (255, 255, 0)
            rectangle_thickness = 3 if is_selected else 1
            cv2.rectangle(
                overlay,
                (x_start, y_start),
                (x_end - 1, y_end - 1),
                rectangle_color,
                rectangle_thickness,
            )

            label = str(cell_number)
            text_scale = 0.45 if cell_number < 10 else 0.38
            text_x = x_start + 6
            text_y = min(y_end - 8, y_start + 20)
            cv2.putText(
                overlay,
                label,
                (text_x, text_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                text_scale,
                rectangle_color,
                1,
                cv2.LINE_AA,
            )

    return overlay


def draw_status_board_overlay(
    board_bgr: np.ndarray,
    cell_results: tuple[EmptyCellGridCellResult, ...] | list[EmptyCellGridCellResult],
    *,
    grid_size: int = 9,
) -> np.ndarray:
    overlay = board_bgr.copy()
    board_height, board_width = overlay.shape[:2]
    cell_height = board_height / float(grid_size)
    cell_width = board_width / float(grid_size)

    for cell_result in cell_results:
        y_start = int(round(cell_result.row_index * cell_height))
        y_end = int(round((cell_result.row_index + 1) * cell_height))
        x_start = int(round(cell_result.col_index * cell_width))
        x_end = int(round((cell_result.col_index + 1) * cell_width))

        rectangle_color = (0, 0, 255) if cell_result.analysis.is_empty else (0, 255, 0)
        status_label = "P" if cell_result.analysis.is_empty else "N"
        cv2.rectangle(
            overlay,
            (x_start, y_start),
            (x_end - 1, y_end - 1),
            rectangle_color,
            2,
        )
        cv2.putText(
            overlay,
            f"{cell_result.cell_number}:{status_label}",
            (x_start + 3, min(y_end - 6, y_start + 18)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.32,
            rectangle_color,
            1,
            cv2.LINE_AA,
        )

    return overlay


def render_segments_overlay(
    binary_mask: np.ndarray,
    segments: tuple[HoughSegment, ...] | list[HoughSegment],
) -> np.ndarray:
    overlay = cv2.cvtColor(binary_mask, cv2.COLOR_GRAY2BGR)
    for segment in segments:
        cv2.line(overlay, segment.start, segment.end, (0, 0, 255), 1)
    return overlay


def render_segments_preview_image(
    cell_results: tuple[EmptyCellGridCellResult, ...] | list[EmptyCellGridCellResult],
    *,
    preview_gap_px: int = 2,
    filtered_only: bool = True,
) -> np.ndarray:
    if not cell_results:
        raise ValueError("cell_results cannot be empty.")

    grid_rows = max(cell_result.row_index for cell_result in cell_results) + 1
    grid_cols = max(cell_result.col_index for cell_result in cell_results) + 1
    overlay_rows: list[list[np.ndarray | None]] = [
        [None for _ in range(grid_cols)] for _ in range(grid_rows)
    ]

    for cell_result in cell_results:
        analysis = cell_result.analysis
        segments = (
            analysis.filtered_segments
            if filtered_only
            else analysis.hough_segments
        )
        overlay_rows[cell_result.row_index][cell_result.col_index] = (
            render_segments_overlay(
                analysis.preprocessing.center_composite,
                segments,
            )
        )

    overlay_grid = tuple(
        tuple(_require_overlay(cell_overlay) for cell_overlay in row)
        for row in overlay_rows
    )
    return build_cells_grid_preview_image(
        overlay_grid,
        gap_px=preview_gap_px,
    )


def _require_overlay(cell_overlay: np.ndarray | None) -> np.ndarray:
    if cell_overlay is None:
        raise ValueError("Missing cell overlay while building segments preview.")
    return cell_overlay


__all__ = [
    "draw_numbered_board_overlay",
    "draw_status_board_overlay",
    "render_segments_overlay",
    "render_segments_preview_image",
    "resolve_cell_position",
]
