from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class BinaryCleanupSettings:
    min_component_area_ratio: float = 0.00008
    min_component_area_floor_px: int = 16


@dataclass(frozen=True)
class ResolvedBinaryCleanupSettings:
    min_component_area_px: int


def resolve_binary_cleanup_settings(
    minimum_dimension: int,
    settings: BinaryCleanupSettings,
) -> ResolvedBinaryCleanupSettings:
    return ResolvedBinaryCleanupSettings(
        min_component_area_px=max(
            settings.min_component_area_floor_px,
            int(round(minimum_dimension * minimum_dimension * settings.min_component_area_ratio)),
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
    variants = [
        ("adaptive + components", components_clean_binary),
    ]
    return resolved_settings, variants
