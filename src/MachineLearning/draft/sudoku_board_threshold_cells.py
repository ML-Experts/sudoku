from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class CellExtractionArtifacts:
    board_gray: np.ndarray
    board_contrast: np.ndarray
    board_binary: np.ndarray
    raw_cells: tuple[tuple[np.ndarray, ...], ...]
    cleaned_cells: tuple[tuple[np.ndarray, ...], ...]
    raw_contact_sheet: np.ndarray
    cleaned_contact_sheet: np.ndarray


def _ensure_odd(value: int) -> int:
    if value < 3:
        raise ValueError("Adaptive threshold block size must be at least 3.")
    return value if value % 2 == 1 else value + 1


def _normalize_tile_grid_size(tile_grid_size: int) -> tuple[int, int]:
    if tile_grid_size <= 0:
        raise ValueError("CLAHE tile grid size must be positive.")
    return tile_grid_size, tile_grid_size


def to_grayscale(image: np.ndarray) -> np.ndarray:
    if image.size == 0:
        raise ValueError("Board image cannot be empty.")
    if image.ndim == 2:
        return image
    if image.ndim == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    raise ValueError("Board image must be grayscale or BGR.")


def enhance_board_contrast(
    gray_image: np.ndarray,
    clip_limit: float,
    tile_grid_size: int,
) -> np.ndarray:
    if clip_limit <= 0.0:
        raise ValueError("CLAHE clip limit must be positive.")

    clahe = cv2.createCLAHE(
        clipLimit=float(clip_limit),
        tileGridSize=_normalize_tile_grid_size(tile_grid_size),
    )
    return clahe.apply(gray_image)


def binarize_board_for_cells(
    gray_image: np.ndarray,
    adaptive_block_size: int,
    adaptive_c: int,
) -> np.ndarray:
    block_size = _ensure_odd(int(adaptive_block_size))
    return cv2.adaptiveThreshold(
        gray_image,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        block_size,
        int(adaptive_c),
    )


def sharpen_image(gray_image: np.ndarray) -> np.ndarray:
    sharpen_kernel = np.array(
        [[0, -1, 0], [-1, 5, -1], [0, -1, 0]],
        dtype=np.float32,
    )
    return cv2.filter2D(gray_image, -1, sharpen_kernel)


def build_cell_foreground_mask(
    cell_image: np.ndarray,
    adaptive_block_size: int,
    adaptive_c: int,
) -> np.ndarray:
    gray_cell = to_grayscale(cell_image)
    sharpened_cell = sharpen_image(gray_cell)
    return binarize_board_for_cells(
        sharpened_cell,
        adaptive_block_size,
        adaptive_c,
    )


def _resolve_bounds(
    index: int,
    total_segments: int,
    total_size: int,
) -> tuple[int, int]:
    start = int(round(index * total_size / total_segments))
    end = int(round((index + 1) * total_size / total_segments))
    if end <= start:
        raise ValueError("Could not resolve valid grid bounds.")
    return start, end


def _crop_inner_margin(cell_image: np.ndarray, inner_margin_ratio: float) -> np.ndarray:
    if not 0.0 <= inner_margin_ratio < 0.5:
        raise ValueError("Cell inner margin ratio must be in range [0, 0.5).")
    if inner_margin_ratio == 0.0:
        return cell_image.copy()

    cell_height, cell_width = cell_image.shape[:2]
    margin_y = int(round(cell_height * inner_margin_ratio))
    margin_x = int(round(cell_width * inner_margin_ratio))

    max_margin_y = max((cell_height - 2) // 2, 0)
    max_margin_x = max((cell_width - 2) // 2, 0)
    margin_y = min(margin_y, max_margin_y)
    margin_x = min(margin_x, max_margin_x)

    cropped_cell = cell_image[
        margin_y : cell_height - margin_y,
        margin_x : cell_width - margin_x,
    ]
    if cropped_cell.size == 0:
        raise ValueError("Cell crop produced an empty image.")
    return cropped_cell


def split_image_into_grid(
    image: np.ndarray,
    grid_size: int,
    inner_margin_ratio: float,
) -> tuple[tuple[np.ndarray, ...], ...]:
    if grid_size <= 0:
        raise ValueError("Grid size must be positive.")
    if image.size == 0:
        raise ValueError("Grid source image cannot be empty.")

    image_height, image_width = image.shape[:2]
    rows: list[tuple[np.ndarray, ...]] = []
    for row_index in range(grid_size):
        y_start, y_end = _resolve_bounds(row_index, grid_size, image_height)
        row_cells: list[np.ndarray] = []
        for col_index in range(grid_size):
            x_start, x_end = _resolve_bounds(col_index, grid_size, image_width)
            cell_image = image[y_start:y_end, x_start:x_end]
            row_cells.append(_crop_inner_margin(cell_image, inner_margin_ratio))
        rows.append(tuple(row_cells))
    return tuple(rows)


def resize_cell_to_square(cell_image: np.ndarray, output_size: int) -> np.ndarray:
    if output_size <= 0:
        raise ValueError("Output cell size must be positive.")
    return cv2.resize(
        cell_image,
        (output_size, output_size),
        interpolation=cv2.INTER_AREA,
    )


def remove_components_touching_border(
    binary_image: np.ndarray,
    border_clearance_px: int,
) -> np.ndarray:
    if border_clearance_px < 0:
        raise ValueError("Border clearance cannot be negative.")
    if border_clearance_px == 0:
        return binary_image.copy()

    component_count, component_labels, component_stats, _ = (
        cv2.connectedComponentsWithStats(binary_image, connectivity=8)
    )
    cleaned_image = np.zeros_like(binary_image)
    image_height, image_width = binary_image.shape[:2]

    for component_index in range(1, component_count):
        x, y, width, height, _ = component_stats[component_index]
        touches_border = (
            x <= border_clearance_px
            or y <= border_clearance_px
            or x + width >= image_width - border_clearance_px
            or y + height >= image_height - border_clearance_px
        )
        if touches_border:
            continue
        cleaned_image[component_labels == component_index] = 255

    return cleaned_image


def remove_small_components(
    binary_image: np.ndarray,
    min_component_area_ratio: float,
) -> np.ndarray:
    if not 0.0 <= min_component_area_ratio <= 1.0:
        raise ValueError("Minimum component area ratio must be in range [0, 1].")
    if min_component_area_ratio == 0.0:
        return binary_image.copy()

    minimum_area = max(
        1,
        int(round(binary_image.shape[0] * binary_image.shape[1] * min_component_area_ratio)),
    )
    component_count, component_labels, component_stats, _ = (
        cv2.connectedComponentsWithStats(binary_image, connectivity=8)
    )
    cleaned_image = np.zeros_like(binary_image)

    for component_index in range(1, component_count):
        area = int(component_stats[component_index, cv2.CC_STAT_AREA])
        if area < minimum_area:
            continue
        cleaned_image[component_labels == component_index] = 255

    return cleaned_image


def center_foreground(binary_image: np.ndarray, output_size: int) -> np.ndarray:
    if output_size <= 0:
        raise ValueError("Output cell size must be positive.")

    foreground_points = cv2.findNonZero(binary_image)
    canvas = np.zeros((output_size, output_size), dtype=np.uint8)
    if foreground_points is None:
        return canvas

    x, y, width, height = cv2.boundingRect(foreground_points)
    cropped_foreground = binary_image[y : y + height, x : x + width]
    target_inner_size = max(output_size - 8, 1)
    resize_scale = min(
        target_inner_size / max(width, 1),
        target_inner_size / max(height, 1),
    )
    resized_width = max(1, int(round(width * resize_scale)))
    resized_height = max(1, int(round(height * resize_scale)))
    interpolation = cv2.INTER_NEAREST if resize_scale >= 1.0 else cv2.INTER_AREA
    resized_foreground = cv2.resize(
        cropped_foreground,
        (resized_width, resized_height),
        interpolation=interpolation,
    )

    offset_x = (output_size - resized_width) // 2
    offset_y = (output_size - resized_height) // 2
    canvas[
        offset_y : offset_y + resized_height,
        offset_x : offset_x + resized_width,
    ] = resized_foreground
    return canvas


def clean_cell_binary(
    cell_binary: np.ndarray,
    *,
    border_clearance_px: int,
    min_component_area_ratio: float,
    output_size: int,
) -> np.ndarray:
    filtered_binary = cell_binary.copy()
    if border_clearance_px > 0:
        border_cleaned = remove_components_touching_border(
            filtered_binary,
            border_clearance_px,
        )
        if np.any(border_cleaned):
            filtered_binary = border_cleaned

    if min_component_area_ratio > 0.0:
        component_filtered = remove_small_components(
            filtered_binary,
            min_component_area_ratio,
        )
        if np.any(component_filtered):
            filtered_binary = component_filtered

    return center_foreground(filtered_binary, output_size)


def build_cell_contact_sheet(
    cells: tuple[tuple[np.ndarray, ...], ...],
    gap_px: int,
) -> np.ndarray:
    if gap_px < 0:
        raise ValueError("Cell gap cannot be negative.")
    if not cells or not cells[0]:
        raise ValueError("Cannot build a contact sheet from an empty cells grid.")

    row_count = len(cells)
    col_count = len(cells[0])
    cell_height, cell_width = cells[0][0].shape[:2]
    sheet_height = row_count * cell_height + (row_count - 1) * gap_px
    sheet_width = col_count * cell_width + (col_count - 1) * gap_px
    contact_sheet = np.zeros((sheet_height, sheet_width), dtype=np.uint8)

    for row_index, row in enumerate(cells):
        for col_index, cell_image in enumerate(row):
            y_start = row_index * (cell_height + gap_px)
            x_start = col_index * (cell_width + gap_px)
            contact_sheet[
                y_start : y_start + cell_height,
                x_start : x_start + cell_width,
            ] = cell_image

    return contact_sheet


def extract_cells_from_warped_board(
    board_image: np.ndarray,
    *,
    grid_size: int,
    inner_margin_ratio: float,
    output_size: int,
    contrast_clip_limit: float,
    contrast_tile_grid_size: int,
    adaptive_block_size: int,
    adaptive_c: int,
    border_clearance_px: int,
    min_component_area_ratio: float,
    contact_sheet_gap_px: int,
) -> CellExtractionArtifacts:
    board_gray = to_grayscale(board_image)
    board_contrast = enhance_board_contrast(
        board_gray,
        contrast_clip_limit,
        contrast_tile_grid_size,
    )
    board_binary = binarize_board_for_cells(
        board_contrast,
        adaptive_block_size,
        adaptive_c,
    )

    raw_grid = split_image_into_grid(board_gray, grid_size, inner_margin_ratio)
    raw_cells = tuple(
        tuple(resize_cell_to_square(cell_image, output_size) for cell_image in row)
        for row in raw_grid
    )
    cleaned_cells = tuple(
        tuple(
            clean_cell_binary(
                build_cell_foreground_mask(
                    cell_image,
                    adaptive_block_size,
                    adaptive_c,
                ),
                border_clearance_px=border_clearance_px,
                min_component_area_ratio=min_component_area_ratio,
                output_size=output_size,
            )
            for cell_image in row
        )
        for row in raw_grid
    )

    return CellExtractionArtifacts(
        board_gray=board_gray,
        board_contrast=board_contrast,
        board_binary=board_binary,
        raw_cells=raw_cells,
        cleaned_cells=cleaned_cells,
        raw_contact_sheet=build_cell_contact_sheet(raw_cells, contact_sheet_gap_px),
        cleaned_contact_sheet=build_cell_contact_sheet(
            cleaned_cells,
            contact_sheet_gap_px,
        ),
    )


__all__ = [
    "CellExtractionArtifacts",
    "binarize_board_for_cells",
    "build_cell_foreground_mask",
    "build_cell_contact_sheet",
    "center_foreground",
    "clean_cell_binary",
    "enhance_board_contrast",
    "extract_cells_from_warped_board",
    "remove_components_touching_border",
    "remove_small_components",
    "resize_cell_to_square",
    "sharpen_image",
    "split_image_into_grid",
    "to_grayscale",
]
