from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np

from sudoku_board_debug_line_experiment import (
    LineExperimentResult,
    ResolvedLineMergeSettings,
    describe_line_experiment,
)
from sudoku_board_debug_preprocess import (
    BoardDebugSettings,
    apply_exif_orientation,
    binarize_image,
    load_image,
    preprocess_image,
    read_exif_orientation_label,
)
import sudoku_board_debug_visualization as debug_visualization

if TYPE_CHECKING:
    from sudoku_board_debug_visualization import LineExperimentOverlays

debug_visualization = importlib.reload(debug_visualization)


@dataclass(frozen=True)
class PreparedBoardImage:
    source_image: np.ndarray
    preprocessed_image: np.ndarray
    binary_image: np.ndarray
    binary_display_image: np.ndarray
    binary_debug_image: np.ndarray
    image_height: int
    image_width: int
    minimum_dimension: int


def to_binary_display_image(binary_image: np.ndarray) -> np.ndarray:
    # Adaptive threshold already returns the foreground as white on black.
    return binary_image.copy()


def to_binary_debug_image(binary_image: np.ndarray) -> np.ndarray:
    binary_display_image = to_binary_display_image(binary_image)
    return cv2.cvtColor(binary_display_image, cv2.COLOR_GRAY2BGR)


def prepare_board_debug_image(
    image_path: Path,
    settings: BoardDebugSettings,
) -> PreparedBoardImage:
    source_image = load_image(image_path)
    preprocessed_image = preprocess_image(source_image, settings)
    binary_image = binarize_image(preprocessed_image, settings)
    binary_display_image = to_binary_display_image(binary_image)
    binary_debug_image = cv2.cvtColor(binary_display_image, cv2.COLOR_GRAY2BGR)
    image_height, image_width = binary_image.shape
    return PreparedBoardImage(
        source_image=source_image,
        preprocessed_image=preprocessed_image,
        binary_image=binary_image,
        binary_display_image=binary_display_image,
        binary_debug_image=binary_debug_image,
        image_height=image_height,
        image_width=image_width,
        minimum_dimension=min(image_height, image_width),
    )


def orient_image_for_display(
    image: np.ndarray,
    orientation_label: str | None,
) -> np.ndarray:
    return apply_exif_orientation(image, orientation_label)


def print_resolved_line_settings(
    resolved_settings: ResolvedLineMergeSettings,
    prepared_image: PreparedBoardImage,
) -> None:
    print("Binary-only debug starts from adaptive threshold.")
    print(f"Image size: {prepared_image.image_width}x{prepared_image.image_height}")
    print(f"Raw Hough threshold: {resolved_settings.raw_hough_threshold}")
    print(f"Raw min line length px: {resolved_settings.raw_min_line_length_px}")
    print(f"Raw max line gap px: {resolved_settings.raw_max_line_gap_px}")
    print(
        "Post-merge projection distance px:",
        resolved_settings.post_merge_projection_distance_px,
    )
    print(
        "Post-merge endpoint gap px:",
        resolved_settings.post_merge_endpoint_gap_px,
    )
    print(
        "Post-merge min overlap ratio:",
        resolved_settings.post_merge_min_overlap_ratio,
    )
    print(f"Min merged span px: {resolved_settings.min_merged_span_px}")
    print("Source image is now EXIF-normalized inside load_image().")


def print_cleanup_settings(resolved_cleanup_settings) -> None:
    print("Binary cleanup experiment before line search")
    print(
        "Connected components min area px:",
        resolved_cleanup_settings.min_component_area_px,
    )


def print_line_experiment_report(
    result: LineExperimentResult,
    *,
    title: str,
    target_line_count: int = 10,
    include_candidate_details: bool = True,
    indent: str = "",
) -> None:
    for line in describe_line_experiment(
        result,
        title=title,
        target_line_count=target_line_count,
        include_candidate_details=include_candidate_details,
        indent=indent,
    ):
        print(line)


def build_notebook_debug_view(
    source_image: np.ndarray,
    result: LineExperimentResult,
) -> "LineExperimentOverlays":
    return debug_visualization.build_line_experiment_overlays(
        source_image,
        result.binary,
        result,
    )


def show_display_image(
    axis,
    image: np.ndarray,
    title: str,
    orientation_label: str | None = None,
    *,
    is_bgr: bool = False,
) -> None:
    oriented_image = orient_image_for_display(image, orientation_label)
    debug_visualization.show_image(axis, oriented_image, title, is_bgr=is_bgr)
