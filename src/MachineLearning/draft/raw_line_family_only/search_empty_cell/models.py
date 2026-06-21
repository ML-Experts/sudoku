from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

DecisionMode = Literal[
    "pixels",
    "segments",
    "pixels_or_segments",
    "pixels_and_segments",
]


@dataclass(frozen=True, slots=True)
class EmptyCellConfig:
    median_kernel_size: int = 5
    adaptive_block_size: int = 11
    adaptive_c: int = 2
    binary_min_component_area_ratio: float = 0.00008
    binary_min_component_area_floor_px: int = 16
    soft_cleanup_area_multiplier: float = 0.35
    inner_margin_ratio: float = 0.0
    hough_threshold: int = 8
    hough_min_line_length_ratio: float = 0.20
    hough_max_line_gap_ratio: float = 0.10
    min_segment_length_px: int = 8
    filtered_segment_count_threshold: int = 6
    pixel_ratio_threshold: float = 0.02
    pixel_count_threshold: int | None = None
    decision_mode: DecisionMode = "pixels_or_segments"


@dataclass(frozen=True, slots=True)
class HoughSegment:
    start: tuple[int, int]
    end: tuple[int, int]
    length_px: float


@dataclass(frozen=True, slots=True)
class EmptyCellPreprocessingArtifacts:
    gray_image: np.ndarray
    denoised_image: np.ndarray
    binary_mask: np.ndarray
    min_component_area_px: int
    clean_mask: np.ndarray
    clean_mask_inner: np.ndarray
    selected_quadrants: dict[str, np.ndarray]
    center_composite: np.ndarray


@dataclass(frozen=True, slots=True)
class EmptyCellAnalysisResult:
    preprocessing: EmptyCellPreprocessingArtifacts
    hough_segments: tuple[HoughSegment, ...]
    filtered_segments: tuple[HoughSegment, ...]
    filtered_segment_count: int
    foreground_pixel_count: int
    foreground_pixel_ratio: float
    accept_by_pixels: bool
    accept_by_segments: bool
    accept_as_digit: bool
    is_empty: bool


@dataclass(frozen=True, slots=True)
class EmptyCellGridCellResult:
    cell_number: int
    row_index: int
    col_index: int
    analysis: EmptyCellAnalysisResult


@dataclass(frozen=True, slots=True)
class EmptyCellGridPreprocessingResult:
    preprocessing_grid: tuple[tuple[EmptyCellPreprocessingArtifacts, ...], ...]
    binary_preview_image: np.ndarray
    clean_preview_image: np.ndarray
    center_composite_preview_image: np.ndarray


@dataclass(frozen=True, slots=True)
class EmptyCellGridAnalysisResult:
    cell_results: tuple[EmptyCellGridCellResult, ...]
    preprocessing_result: EmptyCellGridPreprocessingResult
    empty_count: int
    non_empty_count: int


__all__ = [
    "DecisionMode",
    "EmptyCellAnalysisResult",
    "EmptyCellConfig",
    "EmptyCellGridAnalysisResult",
    "EmptyCellGridCellResult",
    "EmptyCellGridPreprocessingResult",
    "EmptyCellPreprocessingArtifacts",
    "HoughSegment",
]
