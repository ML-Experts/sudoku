from __future__ import annotations

import cv2
import numpy as np
from numpy.typing import NDArray


def to_grayscale(image: NDArray[np.uint8]) -> NDArray[np.uint8]:
    if image.size == 0:
        raise ValueError("Cell image cannot be empty.")
    if image.ndim == 2:
        return image
    if image.ndim == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    raise ValueError("Unsupported image dimensions.")


def sharpen_image(image: NDArray[np.uint8]) -> NDArray[np.uint8]:
    sharpen_kernel = np.array(
        [[0, -1, 0], [-1, 5, -1], [0, -1, 0]],
        dtype=np.float32,
    )
    return cv2.filter2D(image, -1, sharpen_kernel)


def build_foreground_mask(
    cell_image: NDArray[np.uint8],
    adaptive_block_size: int,
    adaptive_c: int,
) -> NDArray[np.uint8]:
    grayscale_image = to_grayscale(cell_image)
    sharpened_image = sharpen_image(grayscale_image)
    return cv2.adaptiveThreshold(
        sharpened_image,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        adaptive_block_size,
        adaptive_c,
    )


def remove_components_touching_border(
    binary_image: NDArray[np.uint8],
    border_clearance_px: int,
) -> NDArray[np.uint8]:
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
        if not touches_border:
            cleaned_image[component_labels == component_index] = 255
    return cleaned_image


def remove_small_components(
    binary_image: NDArray[np.uint8],
    min_component_area_ratio: float,
) -> NDArray[np.uint8]:
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


def center_foreground(
    binary_image: NDArray[np.uint8],
    output_size: int,
) -> NDArray[np.uint8]:
    if output_size <= 0:
        raise ValueError("Output size must be greater than zero.")

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
    cell_binary: NDArray[np.uint8],
    *,
    border_clearance_px: int,
    min_component_area_ratio: float,
    output_size: int,
) -> NDArray[np.uint8]:
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
