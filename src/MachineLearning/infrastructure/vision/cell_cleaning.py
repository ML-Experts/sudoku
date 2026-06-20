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


def apply_median_denoise(
    image: NDArray[np.uint8],
    median_kernel_size: int,
) -> NDArray[np.uint8]:
    if median_kernel_size <= 1 or median_kernel_size % 2 == 0:
        raise ValueError("Median kernel size must be an odd value > 1.")
    return cv2.medianBlur(image, median_kernel_size)


def build_foreground_mask(
    cell_image: NDArray[np.uint8],
    median_kernel_size: int,
    adaptive_block_size: int,
    adaptive_c: int,
) -> NDArray[np.uint8]:
    grayscale_image = to_grayscale(cell_image)
    denoised_image = apply_median_denoise(
        grayscale_image,
        median_kernel_size,
    )
    return cv2.adaptiveThreshold(
        denoised_image,
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
    min_area_px: int,
) -> NDArray[np.uint8]:
    if min_area_px < 0:
        raise ValueError("Minimum component area in pixels cannot be negative.")
    if min_area_px == 0:
        return binary_image.copy()
    component_count, component_labels, component_stats, _ = (
        cv2.connectedComponentsWithStats(binary_image, connectivity=8)
    )
    cleaned_image = np.zeros_like(binary_image)
    for component_index in range(1, component_count):
        area = int(component_stats[component_index, cv2.CC_STAT_AREA])
        if area >= min_area_px:
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
    _, resized_foreground = cv2.threshold(
        resized_foreground,
        127,
        255,
        cv2.THRESH_BINARY,
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
    min_component_area_floor_px: int,
    soft_cleanup_area_multiplier: float,
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

    minimum_dimension = min(filtered_binary.shape[:2])
    min_component_area_px = max(
        min_component_area_floor_px,
        int(round(minimum_dimension * minimum_dimension * min_component_area_ratio)),
    )
    soft_min_component_area_px = max(
        0,
        int(round(min_component_area_px * soft_cleanup_area_multiplier)),
    )
    if soft_min_component_area_px > 0:
        component_filtered = remove_small_components(
            filtered_binary,
            soft_min_component_area_px,
        )
        if np.any(component_filtered):
            filtered_binary = component_filtered

    return center_foreground(filtered_binary, output_size)
