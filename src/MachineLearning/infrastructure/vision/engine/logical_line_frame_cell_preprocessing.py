from __future__ import annotations

import cv2
import numpy as np

DEFAULT_OUTPUT_SIZE_PX = 28
DEFAULT_BORDER_CLEARANCE_PX = 0
DEFAULT_MIN_COMPONENT_AREA_RATIO = 0.0


def build_foreground_mask(
    cell_image: np.ndarray,
    adaptive_block_size: int,
    adaptive_c: int,
) -> np.ndarray:
    grayscale_image = _to_grayscale(cell_image)
    sharpened_image = _sharpen_image(grayscale_image)
    return cv2.adaptiveThreshold(
        sharpened_image,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        adaptive_block_size,
        adaptive_c,
    )


def preprocess_cell_for_ml(
    cell_image: np.ndarray,
    adaptive_block_size: int,
    adaptive_c: int,
    output_size_px: int = DEFAULT_OUTPUT_SIZE_PX,
    border_clearance_px: int = DEFAULT_BORDER_CLEARANCE_PX,
    min_component_area_ratio: float = DEFAULT_MIN_COMPONENT_AREA_RATIO,
) -> np.ndarray:
    foreground_mask = build_foreground_mask(
        cell_image=cell_image,
        adaptive_block_size=adaptive_block_size,
        adaptive_c=adaptive_c,
    )
    return clean_cell_binary(
        foreground_mask,
        border_clearance_px=border_clearance_px,
        min_component_area_ratio=min_component_area_ratio,
        output_size_px=output_size_px,
    )


def preprocess_cells_grid_for_ml(
    cells: tuple[tuple[np.ndarray, ...], ...],
    adaptive_block_size: int,
    adaptive_c: int,
    output_size_px: int = DEFAULT_OUTPUT_SIZE_PX,
    border_clearance_px: int = DEFAULT_BORDER_CLEARANCE_PX,
    min_component_area_ratio: float = DEFAULT_MIN_COMPONENT_AREA_RATIO,
) -> tuple[tuple[np.ndarray, ...], ...]:
    if not cells or not cells[0]:
        raise ValueError("Cells grid cannot be empty.")

    processed_rows: list[tuple[np.ndarray, ...]] = []
    for row in cells:
        processed_row = tuple(
            preprocess_cell_for_ml(
                cell_image=cell_image,
                adaptive_block_size=adaptive_block_size,
                adaptive_c=adaptive_c,
                output_size_px=output_size_px,
                border_clearance_px=border_clearance_px,
                min_component_area_ratio=min_component_area_ratio,
            )
            for cell_image in row
        )
        processed_rows.append(processed_row)

    return tuple(processed_rows)


def clean_cell_binary(
    cell_binary: np.ndarray,
    *,
    border_clearance_px: int,
    min_component_area_ratio: float,
    output_size_px: int,
) -> np.ndarray:
    filtered_binary = cell_binary.copy()
    if border_clearance_px > 0:
        border_cleaned = _remove_components_touching_border(
            filtered_binary,
            border_clearance_px,
        )
        if np.any(border_cleaned):
            filtered_binary = border_cleaned

    if min_component_area_ratio > 0.0:
        component_filtered = _remove_small_components(
            filtered_binary,
            min_component_area_ratio,
        )
        if np.any(component_filtered):
            filtered_binary = component_filtered

    return _center_foreground(filtered_binary, output_size_px)


def _to_grayscale(cell_image: np.ndarray) -> np.ndarray:
    if cell_image.size == 0:
        raise ValueError("Cell image cannot be empty.")
    if cell_image.ndim == 2:
        return cell_image
    if cell_image.ndim == 3:
        return cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY)
    raise ValueError("Unsupported cell image dimensions.")


def _sharpen_image(image: np.ndarray) -> np.ndarray:
    sharpen_kernel = np.array(
        [[0, -1, 0], [-1, 5, -1], [0, -1, 0]],
        dtype=np.float32,
    )
    return cv2.filter2D(image, -1, sharpen_kernel)


def _remove_components_touching_border(
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
        x_coord, y_coord, width, height, _ = component_stats[component_index]
        touches_border = (
            x_coord <= border_clearance_px
            or y_coord <= border_clearance_px
            or x_coord + width >= image_width - border_clearance_px
            or y_coord + height >= image_height - border_clearance_px
        )
        if not touches_border:
            cleaned_image[component_labels == component_index] = 255
    return cleaned_image


def _remove_small_components(
    binary_image: np.ndarray,
    min_component_area_ratio: float,
) -> np.ndarray:
    if not 0.0 <= min_component_area_ratio <= 1.0:
        raise ValueError("Minimum component area ratio must be in range [0, 1].")
    if min_component_area_ratio == 0.0:
        return binary_image.copy()

    minimum_area = max(
        1,
        int(
            round(
                binary_image.shape[0]
                * binary_image.shape[1]
                * min_component_area_ratio
            )
        ),
    )
    component_count, component_labels, component_stats, _ = (
        cv2.connectedComponentsWithStats(binary_image, connectivity=8)
    )
    cleaned_image = np.zeros_like(binary_image)
    for component_index in range(1, component_count):
        area = int(component_stats[component_index, cv2.CC_STAT_AREA])
        if area >= minimum_area:
            cleaned_image[component_labels == component_index] = 255
    return cleaned_image


def _center_foreground(
    binary_image: np.ndarray,
    output_size_px: int,
) -> np.ndarray:
    if output_size_px <= 0:
        raise ValueError("Output size must be greater than zero.")

    foreground_points = cv2.findNonZero(binary_image)
    canvas = np.zeros((output_size_px, output_size_px), dtype=np.uint8)
    if foreground_points is None:
        return canvas

    x_coord, y_coord, width, height = cv2.boundingRect(foreground_points)
    cropped_foreground = binary_image[
        y_coord : y_coord + height,
        x_coord : x_coord + width,
    ]
    target_inner_size = max(output_size_px - 8, 1)
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
    offset_x = (output_size_px - resized_width) // 2
    offset_y = (output_size_px - resized_height) // 2
    canvas[
        offset_y : offset_y + resized_height,
        offset_x : offset_x + resized_width,
    ] = resized_foreground
    return canvas


__all__ = [
    "DEFAULT_OUTPUT_SIZE_PX",
    "build_foreground_mask",
    "clean_cell_binary",
    "preprocess_cell_for_ml",
    "preprocess_cells_grid_for_ml",
]
