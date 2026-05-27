from __future__ import annotations

import cv2
import numpy as np

from sudoku_board_threshold_models import ExperimentConfig


def _apply_clahe(gray_image: np.ndarray, config: ExperimentConfig) -> np.ndarray:
    tile_grid_size = max(1, int(config.denoise_clahe_tile_grid_size))
    clahe = cv2.createCLAHE(
        clipLimit=float(config.denoise_clahe_clip_limit),
        tileGridSize=(tile_grid_size, tile_grid_size),
    )
    return clahe.apply(gray_image)


def _apply_unsharp_mask(
    gray_image: np.ndarray,
    config: ExperimentConfig,
) -> np.ndarray:
    blurred_image = cv2.GaussianBlur(
        gray_image,
        config.unsharp_gaussian_kernel_size,
        config.unsharp_gaussian_sigma,
    )
    sharpened_image = cv2.addWeighted(
        gray_image,
        1.0 + float(config.unsharp_amount),
        blurred_image,
        -float(config.unsharp_amount),
        0,
    )
    return np.clip(sharpened_image, 0, 255).astype(np.uint8)


def build_denoise_variants(
    gray_image: np.ndarray,
    config: ExperimentConfig,
) -> dict[str, np.ndarray]:
    gaussian_image = cv2.GaussianBlur(
        gray_image,
        config.gaussian_kernel_size,
        0,
    )
    median_image = cv2.medianBlur(
        gray_image,
        config.median_kernel_size,
    )
    bilateral_image = cv2.bilateralFilter(
        gray_image,
        config.bilateral_diameter,
        config.bilateral_sigma_color,
        config.bilateral_sigma_space,
    )
    nl_means_image = cv2.fastNlMeansDenoising(
        gray_image,
        None,
        h=config.nl_means_strength,
        templateWindowSize=config.nl_means_template_window_size,
        searchWindowSize=config.nl_means_search_window_size,
    )
    clahe_image = _apply_clahe(gray_image, config)
    clahe_nl_means_image = cv2.fastNlMeansDenoising(
        clahe_image,
        None,
        h=config.nl_means_strength,
        templateWindowSize=config.nl_means_template_window_size,
        searchWindowSize=config.nl_means_search_window_size,
    )

    variants = {
        "raw_gray": gray_image,
        f"gaussian_{config.gaussian_kernel_size[0]}": gaussian_image,
        f"median_{config.median_kernel_size}": median_image,
        "bilateral": bilateral_image,
        "nl_means": nl_means_image,
        "clahe": clahe_image,
        "clahe_nl_means": clahe_nl_means_image,
    }

    base_variants_for_sharpening = {
        f"gaussian_{config.gaussian_kernel_size[0]}": gaussian_image,
        f"median_{config.median_kernel_size}": median_image,
        "bilateral": bilateral_image,
        "nl_means": nl_means_image,
        "clahe_nl_means": clahe_nl_means_image,
    }
    for variant_name, variant_image in base_variants_for_sharpening.items():
        variants[f"{variant_name}_unsharp"] = _apply_unsharp_mask(
            variant_image,
            config,
        )

    return variants


def adaptive_method_code(method_name: str) -> int:
    normalized_method_name = method_name.strip().lower()
    if normalized_method_name == "mean":
        return cv2.ADAPTIVE_THRESH_MEAN_C
    if normalized_method_name == "gaussian":
        return cv2.ADAPTIVE_THRESH_GAUSSIAN_C
    raise ValueError(f"Unsupported adaptive method: {method_name}")


def build_threshold_variants(
    denoised_image: np.ndarray,
    config: ExperimentConfig,
) -> dict[str, np.ndarray]:
    threshold_variants: dict[str, np.ndarray] = {}
    method_code = adaptive_method_code(config.adaptive_method_name)
    threshold_type = (
        cv2.THRESH_BINARY_INV if config.threshold_invert else cv2.THRESH_BINARY
    )

    for block_size in config.adaptive_block_sizes:
        if block_size % 2 == 0:
            raise ValueError(f"Adaptive block size must be odd: {block_size}")

        for c_value in config.adaptive_c_values:
            variant_name = f"{config.adaptive_method_name}_block{block_size}_c{c_value}"
            threshold_variants[variant_name] = cv2.adaptiveThreshold(
                denoised_image,
                255,
                method_code,
                threshold_type,
                block_size,
                c_value,
            )

    return threshold_variants


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


def build_cleanup_variants(
    binary_image: np.ndarray,
    config: ExperimentConfig,
) -> tuple[int, dict[str, np.ndarray]]:
    min_component_area_px = resolve_min_component_area_px(binary_image, config)
    soft_min_component_area_px = max(
        1,
        int(round(min_component_area_px * config.soft_cleanup_area_multiplier)),
    )
    cleanup_variants = {
        "adaptive_only": binary_image,
        "adaptive_plus_components_soft": remove_small_connected_components(
            binary_image,
            soft_min_component_area_px,
        ),
        "adaptive_plus_components": remove_small_connected_components(
            binary_image,
            min_component_area_px,
        ),
    }
    return min_component_area_px, cleanup_variants


def close_binary_image(
    binary_image: np.ndarray,
    kernel_size: tuple[int, int],
) -> np.ndarray:
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)
    return cv2.morphologyEx(binary_image, cv2.MORPH_CLOSE, kernel)


def build_repair_variants(
    binary_image: np.ndarray,
    config: ExperimentConfig,
) -> dict[str, np.ndarray]:
    minimum_dimension = min(binary_image.shape[:2])
    directional_kernel_length = max(
        3,
        int(round(minimum_dimension * config.repair_directional_kernel_ratio)),
    )
    if directional_kernel_length % 2 == 0:
        directional_kernel_length += 1

    repair_variants = {"cleanup_only": binary_image}
    for kernel_size in config.repair_kernel_sizes:
        repair_variants[f"close_square_{kernel_size}"] = close_binary_image(
            binary_image,
            (kernel_size, kernel_size),
        )

    horizontal_closed = close_binary_image(binary_image, (directional_kernel_length, 1))
    vertical_closed = close_binary_image(binary_image, (1, directional_kernel_length))
    repair_variants["directional_close"] = cv2.bitwise_or(
        horizontal_closed,
        vertical_closed,
    )
    return repair_variants


__all__ = [
    "_apply_clahe",
    "_apply_unsharp_mask",
    "adaptive_method_code",
    "build_cleanup_variants",
    "build_denoise_variants",
    "build_repair_variants",
    "build_threshold_variants",
    "close_binary_image",
    "remove_small_connected_components",
    "resolve_min_component_area_px",
]
