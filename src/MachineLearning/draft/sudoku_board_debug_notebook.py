from __future__ import annotations

from pathlib import Path
import subprocess

import cv2
import numpy as np

from sudoku_board_debug_visualization import show_image


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


def orient_image_for_display(
    image: np.ndarray,
    orientation_label: str | None,
) -> np.ndarray:
    return apply_exif_orientation(image, orientation_label)


def show_display_image(
    axis,
    image: np.ndarray,
    title: str,
    orientation_label: str | None,
    *,
    is_bgr: bool = False,
) -> None:
    oriented_image = orient_image_for_display(image, orientation_label)
    show_image(axis, oriented_image, title, is_bgr=is_bgr)
