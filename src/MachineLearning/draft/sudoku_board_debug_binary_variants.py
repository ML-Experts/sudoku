from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class BinaryCleanupSettings:
    min_component_area_ratio: float = 0.00008
    min_component_area_floor_px: int = 16
    open_kernel_ratio: float = 0.02
    open_kernel_floor_px: int = 9
    close_kernel_ratio: float = 0.035
    close_kernel_floor_px: int = 15


@dataclass(frozen=True)
class ResolvedBinaryCleanupSettings:
    min_component_area_px: int
    open_kernel_length: int
    close_kernel_length: int


def resolve_binary_cleanup_settings(
    minimum_dimension: int,
    settings: BinaryCleanupSettings,
) -> ResolvedBinaryCleanupSettings:
    return ResolvedBinaryCleanupSettings(
        min_component_area_px=max(
            settings.min_component_area_floor_px,
            int(round(minimum_dimension * minimum_dimension * settings.min_component_area_ratio)),
        ),
        open_kernel_length=max(
            settings.open_kernel_floor_px,
            int(round(minimum_dimension * settings.open_kernel_ratio)),
        ),
        close_kernel_length=max(
            settings.close_kernel_floor_px,
            int(round(minimum_dimension * settings.close_kernel_ratio)),
        ),
    )


def remove_small_connected_components(
    binary_image: np.ndarray,
    min_area_px: int,
) -> np.ndarray:
    component_count, component_labels, component_stats, _ = (
        cv2.connectedComponentsWithStats(
            binary_image,
            connectivity=8,
        )
    )
    cleaned = np.zeros_like(binary_image)
    for component_index in range(1, component_count):
        component_area = component_stats[component_index, cv2.CC_STAT_AREA]
        if component_area >= min_area_px:
            cleaned[component_labels == component_index] = 255
    return cleaned


def build_directional_line_mask(
    binary_image: np.ndarray,
    open_kernel_length: int,
    close_kernel_length: int,
) -> np.ndarray:
    horizontal_open_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (open_kernel_length, 1),
    )
    vertical_open_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (1, open_kernel_length),
    )
    horizontal_close_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (close_kernel_length, 1),
    )
    vertical_close_kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (1, close_kernel_length),
    )

    horizontal = cv2.morphologyEx(
        binary_image,
        cv2.MORPH_OPEN,
        horizontal_open_kernel,
    )
    vertical = cv2.morphologyEx(
        binary_image,
        cv2.MORPH_OPEN,
        vertical_open_kernel,
    )

    horizontal = cv2.morphologyEx(
        horizontal,
        cv2.MORPH_CLOSE,
        horizontal_close_kernel,
    )
    vertical = cv2.morphologyEx(
        vertical,
        cv2.MORPH_CLOSE,
        vertical_close_kernel,
    )
    return cv2.bitwise_or(horizontal, vertical)


def build_binary_variants(
    binary_image: np.ndarray,
    minimum_dimension: int,
    settings: BinaryCleanupSettings,
) -> tuple[ResolvedBinaryCleanupSettings, list[tuple[str, np.ndarray]]]:
    resolved_settings = resolve_binary_cleanup_settings(minimum_dimension, settings)
    components_clean_binary = remove_small_connected_components(
        binary_image,
        resolved_settings.min_component_area_px,
    )
    directional_binary = build_directional_line_mask(
        binary_image,
        resolved_settings.open_kernel_length,
        resolved_settings.close_kernel_length,
    )
    components_plus_directional_binary = build_directional_line_mask(
        components_clean_binary,
        resolved_settings.open_kernel_length,
        resolved_settings.close_kernel_length,
    )
    variants = [
        ("adaptive only", binary_image),
        ("adaptive + components", components_clean_binary),
        ("adaptive + directional", directional_binary),
        ("adaptive + components + directional", components_plus_directional_binary),
    ]
    return resolved_settings, variants
