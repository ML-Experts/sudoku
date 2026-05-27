from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess

import cv2
import numpy as np


@dataclass(frozen=True)
class BoardDebugSettings:
    board_output_size: int = 600
    board_output_padding_pixels: int = 8
    grayscale_color_conversion_code: int = cv2.COLOR_BGR2GRAY
    gaussian_kernel_size: tuple[int, int] = (5, 5)
    gaussian_sigma_x: float = 0.0
    adaptive_threshold_block_size: int = 11
    adaptive_threshold_c: int = 2
    board_edge_canny_threshold_1: int = 50
    board_edge_canny_threshold_2: int = 150
    board_edge_hough_threshold: int = 80
    board_edge_min_line_length_ratio: float = 0.2
    board_edge_max_line_gap_ratio: float = 0.04
    board_edge_angle_tolerance_degrees: float = 12.0
    board_edge_outer_line_window_ratio: float = 0.1
    board_edge_minimum_board_area_ratio: float = 0.1
    board_edge_minimum_family_segments: int = 4
    board_edge_line_position_merge_distance_ratio: float = 0.03
    board_edge_minimum_distinct_lines_per_family: int = 5
    max_distinct_lines_per_family: int = 8
    min_interior_lines_per_side: int = 4
    min_boundary_segment_coverage: float = 0.55
    area_score_weight: float = 3.0
    rectangularity_score_weight: float = 2.0
    grid_support_score_weight: float = 3.0
    line_length_score_weight: float = 1.0
    boundary_coverage_score_weight: float = 4.0


def read_exif_orientation_label(image_path: Path) -> str | None:
    completed_process = subprocess.run(
        ["file", str(image_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    metadata_text = completed_process.stdout.strip()
    orientation_marker = "orientation="
    orientation_start = metadata_text.find(orientation_marker)
    if orientation_start < 0:
        return None

    orientation_start += len(orientation_marker)
    orientation_end = metadata_text.find(",", orientation_start)
    if orientation_end < 0:
        orientation_end = len(metadata_text)

    return metadata_text[orientation_start:orientation_end].strip().lower() or None


def apply_exif_orientation(
    image: np.ndarray,
    orientation_label: str | None,
) -> np.ndarray:
    if orientation_label in (None, "", "upper-left"):
        return image
    if orientation_label == "upper-right":
        return cv2.flip(image, 1)
    if orientation_label == "lower-right":
        return cv2.rotate(image, cv2.ROTATE_180)
    if orientation_label == "lower-left":
        return cv2.flip(image, 0)
    if orientation_label == "left-top":
        return cv2.transpose(image)
    if orientation_label == "right-top":
        return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    if orientation_label == "right-bottom":
        return cv2.flip(cv2.transpose(image), -1)
    if orientation_label == "left-bottom":
        return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return image


def load_image(image_path: Path) -> np.ndarray:
    image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")

    orientation_label = read_exif_orientation_label(image_path)
    return apply_exif_orientation(image, orientation_label)


def preprocess_image(
    image: np.ndarray,
    settings: BoardDebugSettings,
) -> np.ndarray:
    grayscale = cv2.cvtColor(image, settings.grayscale_color_conversion_code)
    return cv2.GaussianBlur(
        grayscale,
        settings.gaussian_kernel_size,
        settings.gaussian_sigma_x,
    )


def binarize_image(
    image: np.ndarray,
    settings: BoardDebugSettings,
) -> np.ndarray:
    return cv2.adaptiveThreshold(
        image,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        settings.adaptive_threshold_block_size,
        settings.adaptive_threshold_c,
    )
