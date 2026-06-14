from __future__ import annotations

import cv2
import numpy as np

from models import ExperimentConfig


def apply_median_denoise(
    gray_image: np.ndarray,
    config: ExperimentConfig,
) -> np.ndarray:
    return cv2.medianBlur(gray_image, config.median_kernel_size)


def apply_gaussian_threshold(
    denoised_image: np.ndarray,
    config: ExperimentConfig,
) -> np.ndarray:
    block_size = int(config.adaptive_threshold_block_size)
    if block_size % 2 == 0:
        raise ValueError(f"Adaptive block size must be odd: {block_size}")

    threshold_type = (
        cv2.THRESH_BINARY_INV if config.threshold_invert else cv2.THRESH_BINARY
    )
    return cv2.adaptiveThreshold(
        denoised_image,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        threshold_type,
        block_size,
        int(config.adaptive_threshold_c_value),
    )


def resolve_min_component_area_px(
    binary_image: np.ndarray,
    config: ExperimentConfig,
) -> int:
    minimum_dimension = min(binary_image.shape[:2])
    return max(
        config.binary_min_component_area_floor_px,
        int(
            round(
                minimum_dimension
                * minimum_dimension
                * config.binary_min_component_area_ratio
            )
        ),
    )


def remove_small_connected_components(
    binary_image: np.ndarray,
    min_area_px: int,
) -> np.ndarray:
    component_count, component_labels, component_stats, _ = (
        cv2.connectedComponentsWithStats(binary_image, connectivity=8)
    )
    cleaned = np.zeros_like(binary_image)
    for component_index in range(1, component_count):
        component_area = component_stats[component_index, cv2.CC_STAT_AREA]
        if component_area >= min_area_px:
            cleaned[component_labels == component_index] = 255
    return cleaned


def close_binary_image(
    binary_image: np.ndarray,
    kernel_size: tuple[int, int],
) -> np.ndarray:
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)
    return cv2.morphologyEx(binary_image, cv2.MORPH_CLOSE, kernel)


def apply_soft_component_cleanup(
    binary_image: np.ndarray,
    config: ExperimentConfig,
) -> tuple[int, np.ndarray]:
    min_component_area_px = resolve_min_component_area_px(binary_image, config)
    soft_min_component_area_px = max(
        1,
        int(round(min_component_area_px * config.soft_cleanup_area_multiplier)),
    )
    return min_component_area_px, remove_small_connected_components(
        binary_image,
        soft_min_component_area_px,
    )


def apply_directional_close_repair(
    binary_image: np.ndarray,
    config: ExperimentConfig,
) -> np.ndarray:
    minimum_dimension = min(binary_image.shape[:2])
    directional_kernel_length = max(
        3,
        int(round(minimum_dimension * config.repair_directional_kernel_ratio)),
    )
    if directional_kernel_length % 2 == 0:
        directional_kernel_length += 1

    horizontal_closed = close_binary_image(binary_image, (directional_kernel_length, 1))
    vertical_closed = close_binary_image(binary_image, (1, directional_kernel_length))
    return cv2.bitwise_or(
        horizontal_closed,
        vertical_closed,
    )


__all__ = [
    "apply_directional_close_repair",
    "apply_gaussian_threshold",
    "apply_median_denoise",
    "apply_soft_component_cleanup",
]
