from __future__ import annotations

import math
from dataclasses import replace

import cv2
import numpy as np

from binary import (
    apply_gaussian_threshold,
    apply_median_denoise,
    apply_soft_component_cleanup,
)
from models import ExperimentConfig

from .models import (
    EmptyCellAnalysisResult,
    EmptyCellConfig,
    EmptyCellPreprocessingArtifacts,
    HoughSegment,
)


def build_empty_cell_processing_config(
    base_config: ExperimentConfig,
    empty_cell_config: EmptyCellConfig,
) -> ExperimentConfig:
    return replace(
        base_config,
        median_kernel_size=empty_cell_config.median_kernel_size,
        adaptive_threshold_block_size=empty_cell_config.adaptive_block_size,
        adaptive_threshold_c_value=empty_cell_config.adaptive_c,
        binary_min_component_area_ratio=(
            empty_cell_config.binary_min_component_area_ratio
        ),
        binary_min_component_area_floor_px=(
            empty_cell_config.binary_min_component_area_floor_px
        ),
        soft_cleanup_area_multiplier=(
            empty_cell_config.soft_cleanup_area_multiplier
        ),
    )


def build_binary_mask(
    raw_cell_image: np.ndarray,
    processing_config: ExperimentConfig,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    gray_image = _to_grayscale(raw_cell_image)
    denoised_image = apply_median_denoise(gray_image, processing_config)
    binary_mask = apply_gaussian_threshold(denoised_image, processing_config)
    return gray_image, denoised_image, binary_mask


def clean_binary_mask(
    binary_mask: np.ndarray,
    processing_config: ExperimentConfig,
) -> tuple[int, np.ndarray]:
    return apply_soft_component_cleanup(binary_mask, processing_config)


def apply_inner_margin(mask: np.ndarray, inner_margin_ratio: float) -> np.ndarray:
    if not 0.0 <= inner_margin_ratio < 0.5:
        raise ValueError("inner_margin_ratio must be in range [0.0, 0.5).")

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
    mask: np.ndarray,
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
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
    composite = np.vstack([composite_top_row, composite_bottom_row])
    selected_quadrants = {
        "1_q4": top_left_bottom_right,
        "2_q3": top_right_bottom_left,
        "3_q2": bottom_left_top_right,
        "4_q1": bottom_right_top_left,
    }
    return composite, selected_quadrants


def detect_hough_segments(
    binary_mask: np.ndarray,
    empty_cell_config: EmptyCellConfig,
) -> list[HoughSegment]:
    minimum_dimension = min(binary_mask.shape[:2])
    min_line_length = max(
        2,
        int(round(minimum_dimension * empty_cell_config.hough_min_line_length_ratio)),
    )
    max_line_gap = max(
        1,
        int(round(minimum_dimension * empty_cell_config.hough_max_line_gap_ratio)),
    )
    raw_segments = cv2.HoughLinesP(
        binary_mask,
        rho=1,
        theta=np.pi / 180.0,
        threshold=empty_cell_config.hough_threshold,
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
    return [
        segment
        for segment in segments
        if segment.length_px >= min_segment_length_px
    ]


def count_segments(
    segments: list[HoughSegment] | tuple[HoughSegment, ...],
) -> int:
    return len(segments)


def count_filtered_segments(
    segments: list[HoughSegment] | tuple[HoughSegment, ...],
    min_segment_length_px: int,
) -> int:
    return count_segments(
        filter_short_segments(segments, min_segment_length_px)
    )


def count_foreground_pixels(binary_mask: np.ndarray) -> int:
    return int(np.count_nonzero(binary_mask > 0))


def count_foreground_pixel_ratio(binary_mask: np.ndarray) -> float:
    return float(np.mean(binary_mask > 0))


def preprocess_raw_cell_bgr(
    raw_cell_bgr: np.ndarray,
    *,
    empty_cell_config: EmptyCellConfig,
    processing_config: ExperimentConfig,
) -> EmptyCellPreprocessingArtifacts:
    gray_image, denoised_image, binary_mask = build_binary_mask(
        raw_cell_bgr,
        processing_config,
    )
    min_component_area_px, clean_mask = clean_binary_mask(
        binary_mask,
        processing_config,
    )
    clean_mask_inner = apply_inner_margin(
        clean_mask,
        empty_cell_config.inner_margin_ratio,
    )
    center_composite, selected_quadrants = build_center_quadrant_composite(
        clean_mask_inner,
    )
    return EmptyCellPreprocessingArtifacts(
        gray_image=gray_image,
        denoised_image=denoised_image,
        binary_mask=binary_mask,
        min_component_area_px=min_component_area_px,
        clean_mask=clean_mask,
        clean_mask_inner=clean_mask_inner,
        selected_quadrants=selected_quadrants,
        center_composite=center_composite,
    )


def analyze_empty_cell_preprocessing(
    preprocessing: EmptyCellPreprocessingArtifacts,
    *,
    empty_cell_config: EmptyCellConfig,
) -> EmptyCellAnalysisResult:
    hough_segments = detect_hough_segments(
        preprocessing.center_composite,
        empty_cell_config,
    )
    filtered_segments = filter_short_segments(
        hough_segments,
        empty_cell_config.min_segment_length_px,
    )
    foreground_pixel_count = count_foreground_pixels(
        preprocessing.center_composite
    )
    foreground_pixel_ratio = count_foreground_pixel_ratio(
        preprocessing.center_composite
    )
    accept_by_pixels = foreground_pixel_ratio > empty_cell_config.pixel_ratio_threshold
    if empty_cell_config.pixel_count_threshold is not None:
        accept_by_pixels = (
            accept_by_pixels
            and foreground_pixel_count >= empty_cell_config.pixel_count_threshold
        )

    filtered_segment_count = count_segments(filtered_segments)
    accept_by_segments = (
        filtered_segment_count
        >= empty_cell_config.filtered_segment_count_threshold
    )
    accept_as_digit = _resolve_accept_as_digit(
        accept_by_pixels=accept_by_pixels,
        accept_by_segments=accept_by_segments,
        decision_mode=empty_cell_config.decision_mode,
    )
    return EmptyCellAnalysisResult(
        preprocessing=preprocessing,
        hough_segments=tuple(hough_segments),
        filtered_segments=tuple(filtered_segments),
        filtered_segment_count=filtered_segment_count,
        foreground_pixel_count=foreground_pixel_count,
        foreground_pixel_ratio=foreground_pixel_ratio,
        accept_by_pixels=accept_by_pixels,
        accept_by_segments=accept_by_segments,
        accept_as_digit=accept_as_digit,
        is_empty=not accept_as_digit,
    )


def analyze_raw_cell_bgr(
    raw_cell_bgr: np.ndarray,
    *,
    empty_cell_config: EmptyCellConfig,
    processing_config: ExperimentConfig,
) -> EmptyCellAnalysisResult:
    preprocessing = preprocess_raw_cell_bgr(
        raw_cell_bgr,
        empty_cell_config=empty_cell_config,
        processing_config=processing_config,
    )
    return analyze_empty_cell_preprocessing(
        preprocessing,
        empty_cell_config=empty_cell_config,
    )


def _to_grayscale(cell_image: np.ndarray) -> np.ndarray:
    if cell_image.size == 0:
        raise ValueError("Cell image cannot be empty.")
    if cell_image.ndim == 2:
        return cell_image
    if cell_image.ndim == 3:
        return cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY)
    raise ValueError("Unsupported cell image dimensions.")


def _resolve_accept_as_digit(
    *,
    accept_by_pixels: bool,
    accept_by_segments: bool,
    decision_mode: str,
) -> bool:
    if decision_mode == "pixels":
        return accept_by_pixels
    if decision_mode == "segments":
        return accept_by_segments
    if decision_mode == "pixels_or_segments":
        return accept_by_pixels or accept_by_segments
    if decision_mode == "pixels_and_segments":
        return accept_by_pixels and accept_by_segments
    raise ValueError(
        "decision_mode must be one of: pixels, segments, "
        "pixels_or_segments, pixels_and_segments."
    )


__all__ = [
    "analyze_empty_cell_preprocessing",
    "analyze_raw_cell_bgr",
    "apply_inner_margin",
    "build_binary_mask",
    "build_center_quadrant_composite",
    "build_empty_cell_processing_config",
    "clean_binary_mask",
    "count_segments",
    "count_filtered_segments",
    "count_foreground_pixel_ratio",
    "count_foreground_pixels",
    "detect_hough_segments",
    "filter_short_segments",
    "preprocess_raw_cell_bgr",
]
