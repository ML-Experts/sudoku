from __future__ import annotations

import math
from dataclasses import dataclass

import cv2
import numpy as np
from numpy.typing import NDArray

DEFAULT_EMPTY_DETECTION_MIN_COMPONENT_AREA_FLOOR_PX = 16
DEFAULT_EMPTY_DETECTION_SOFT_CLEANUP_AREA_MULTIPLIER = 0.35
DEFAULT_HOUGH_THRESHOLD = 8
DEFAULT_HOUGH_MIN_LINE_LENGTH_RATIO = 0.20
DEFAULT_HOUGH_MAX_LINE_GAP_RATIO = 0.10


@dataclass(frozen=True, slots=True)
class HoughSegment:
    start: tuple[int, int]
    end: tuple[int, int]
    length_px: float


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


def clean_binary_mask_for_empty_detection(
    cell_binary: NDArray[np.uint8],
    *,
    border_clearance_px: int,
    min_component_area_ratio: float,
    min_component_area_floor_px: int = (
        DEFAULT_EMPTY_DETECTION_MIN_COMPONENT_AREA_FLOOR_PX
    ),
    soft_cleanup_area_multiplier: float = (
        DEFAULT_EMPTY_DETECTION_SOFT_CLEANUP_AREA_MULTIPLIER
    ),
) -> NDArray[np.uint8]:
    if not 0.0 <= min_component_area_ratio <= 1.0:
        raise ValueError("Minimum component area ratio must be in range [0.0, 1.0].")
    if min_component_area_floor_px < 0:
        raise ValueError("Minimum component area floor cannot be negative.")
    if soft_cleanup_area_multiplier < 0.0:
        raise ValueError("Soft cleanup area multiplier cannot be negative.")

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
    if soft_min_component_area_px == 0:
        return filtered_binary

    component_filtered = remove_small_components(
        filtered_binary,
        soft_min_component_area_px,
    )
    if np.any(component_filtered):
        return component_filtered
    return filtered_binary


def apply_inner_margin(
    mask: NDArray[np.uint8],
    inner_margin_ratio: float,
) -> NDArray[np.uint8]:
    if not 0.0 <= inner_margin_ratio < 0.5:
        raise ValueError("Inner margin ratio must be in range [0.0, 0.5).")
    if inner_margin_ratio == 0.0:
        return mask.copy()

    height, width = mask.shape[:2]
    margin_y = int(round(height * inner_margin_ratio))
    margin_x = int(round(width * inner_margin_ratio))
    max_margin_y = max((height - 1) // 2, 0)
    max_margin_x = max((width - 1) // 2, 0)
    margin_y = min(margin_y, max_margin_y)
    margin_x = min(margin_x, max_margin_x)

    cropped_mask = mask[
        margin_y : height - margin_y,
        margin_x : width - margin_x,
    ]
    if cropped_mask.size == 0:
        raise ValueError("Inner-margin crop produced an empty image.")
    return cropped_mask


def build_center_quadrant_composite(
    mask: NDArray[np.uint8],
) -> NDArray[np.uint8]:
    height, width = mask.shape[:2]
    if height < 4 or width < 4:
        raise ValueError("Mask is too small to build center quadrant composite.")

    top_left_bottom_right = mask[height // 4 : height // 2, width // 4 : width // 2]
    top_right_bottom_left = mask[
        height // 4 : height // 2,
        width // 2 : (3 * width) // 4,
    ]
    bottom_left_top_right = mask[
        height // 2 : (3 * height) // 4,
        width // 4 : width // 2,
    ]
    bottom_right_top_left = mask[
        height // 2 : (3 * height) // 4,
        width // 2 : (3 * width) // 4,
    ]

    composite_top_row = np.hstack(
        [top_left_bottom_right, top_right_bottom_left]
    )
    composite_bottom_row = np.hstack(
        [bottom_left_top_right, bottom_right_top_left]
    )
    return np.vstack([composite_top_row, composite_bottom_row])


def detect_hough_segments(
    binary_mask: NDArray[np.uint8],
    *,
    hough_threshold: int = DEFAULT_HOUGH_THRESHOLD,
    hough_min_line_length_ratio: float = DEFAULT_HOUGH_MIN_LINE_LENGTH_RATIO,
    hough_max_line_gap_ratio: float = DEFAULT_HOUGH_MAX_LINE_GAP_RATIO,
) -> list[HoughSegment]:
    if hough_threshold <= 0:
        raise ValueError("Hough threshold must be greater than zero.")
    if hough_min_line_length_ratio <= 0.0:
        raise ValueError("Hough min line length ratio must be greater than zero.")
    if hough_max_line_gap_ratio <= 0.0:
        raise ValueError("Hough max line gap ratio must be greater than zero.")

    minimum_dimension = min(binary_mask.shape[:2])
    min_line_length = max(
        2,
        int(round(minimum_dimension * hough_min_line_length_ratio)),
    )
    max_line_gap = max(
        1,
        int(round(minimum_dimension * hough_max_line_gap_ratio)),
    )
    raw_segments = cv2.HoughLinesP(
        binary_mask,
        rho=1,
        theta=np.pi / 180.0,
        threshold=hough_threshold,
        minLineLength=min_line_length,
        maxLineGap=max_line_gap,
    )
    if raw_segments is None:
        return []

    segments: list[HoughSegment] = []
    for raw_segment in raw_segments[:, 0, :]:
        x1, y1, x2, y2 = [int(value) for value in raw_segment]
        segments.append(
            HoughSegment(
                start=(x1, y1),
                end=(x2, y2),
                length_px=float(math.hypot(x2 - x1, y2 - y1)),
            )
        )
    return segments


def filter_short_segments(
    segments: list[HoughSegment] | tuple[HoughSegment, ...],
    min_segment_length_px: int,
) -> list[HoughSegment]:
    if min_segment_length_px <= 0:
        raise ValueError("Minimum segment length must be greater than zero.")
    return [
        segment
        for segment in segments
        if segment.length_px >= min_segment_length_px
    ]


def count_foreground_pixels(binary_mask: NDArray[np.uint8]) -> int:
    return int(np.count_nonzero(binary_mask > 0))


def count_foreground_pixel_ratio(binary_mask: NDArray[np.uint8]) -> float:
    return float(np.mean(binary_mask > 0))


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


__all__ = [
    "DEFAULT_EMPTY_DETECTION_MIN_COMPONENT_AREA_FLOOR_PX",
    "DEFAULT_EMPTY_DETECTION_SOFT_CLEANUP_AREA_MULTIPLIER",
    "DEFAULT_HOUGH_MAX_LINE_GAP_RATIO",
    "DEFAULT_HOUGH_MIN_LINE_LENGTH_RATIO",
    "DEFAULT_HOUGH_THRESHOLD",
    "HoughSegment",
    "apply_inner_margin",
    "apply_median_denoise",
    "build_center_quadrant_composite",
    "build_foreground_mask",
    "clean_binary_mask_for_empty_detection",
    "clean_cell_binary",
    "count_foreground_pixel_ratio",
    "count_foreground_pixels",
    "detect_hough_segments",
    "filter_short_segments",
    "remove_components_touching_border",
    "remove_small_components",
    "to_grayscale",
]
