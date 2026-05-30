from __future__ import annotations

import cv2
import numpy as np

from sudoku_board_threshold_models import LineFrame

CORNER_LABELS = ("TL", "TR", "BR", "BL")


def _build_corner_array(
    corners: tuple[tuple[float, float], tuple[float, float], tuple[float, float], tuple[float, float]],
) -> np.ndarray:
    corner_array = np.array(corners, dtype=np.float32)
    if corner_array.shape != (4, 2):
        raise ValueError("Warp corners must contain exactly four 2D points.")
    if not np.isfinite(corner_array).all():
        raise ValueError("Warp corners must contain only finite values.")

    polygon = corner_array.reshape((-1, 1, 2))
    if abs(float(cv2.contourArea(polygon))) <= 1.0:
        raise ValueError("Warp corners do not form a valid quadrilateral.")
    return corner_array


def aligned_frame_corners(
    frame: LineFrame,
) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float], tuple[float, float]]:
    return tuple((float(x), float(y)) for x, y in frame.corners)  # type: ignore[return-value]


def build_destination_corners(output_size: int, padding_pixels: int) -> np.ndarray:
    if output_size <= 0:
        raise ValueError("Warp output size must be positive.")
    if padding_pixels < 0:
        raise ValueError("Warp padding cannot be negative.")
    if padding_pixels * 2 >= output_size:
        raise ValueError("Warp padding must leave room for image content.")

    min_index = float(padding_pixels)
    max_index = float(output_size - padding_pixels - 1)
    return np.array(
        [
            [min_index, min_index],
            [max_index, min_index],
            [max_index, max_index],
            [min_index, max_index],
        ],
        dtype=np.float32,
    )


def warp_image_from_corners(
    image: np.ndarray,
    corners: tuple[tuple[float, float], tuple[float, float], tuple[float, float], tuple[float, float]],
    output_size: int,
    padding_pixels: int,
) -> np.ndarray:
    source_points = _build_corner_array(corners)
    destination_points = build_destination_corners(output_size, padding_pixels)
    perspective_matrix = cv2.getPerspectiveTransform(source_points, destination_points)
    transformed = cv2.warpPerspective(
        image,
        perspective_matrix,
        (output_size, output_size),
    )
    if transformed.size == 0:
        raise ValueError("Perspective transform produced an empty image.")
    return transformed


def _draw_labeled_corners(
    overlay: np.ndarray,
    corners: tuple[tuple[float, float], tuple[float, float], tuple[float, float], tuple[float, float]],
    color_bgr: tuple[int, int, int],
    label_prefix: str,
    thickness: int,
) -> None:
    image_height, image_width = overlay.shape[:2]
    rounded_corners = []
    for corner in corners:
        x = int(np.clip(round(float(corner[0])), 0, image_width - 1))
        y = int(np.clip(round(float(corner[1])), 0, image_height - 1))
        rounded_corners.append((x, y))

    polygon = np.array(rounded_corners, dtype=np.int32).reshape((-1, 1, 2))
    cv2.polylines(
        overlay,
        [polygon],
        isClosed=True,
        color=(255, 255, 255),
        thickness=max(thickness + 3, 4),
        lineType=cv2.LINE_AA,
    )
    cv2.polylines(
        overlay,
        [polygon],
        isClosed=True,
        color=color_bgr,
        thickness=max(thickness + 1, 2),
        lineType=cv2.LINE_AA,
    )

    for corner_label, point in zip(CORNER_LABELS, rounded_corners):
        cv2.circle(
            overlay,
            point,
            radius=max(thickness + 3, 5),
            color=(255, 255, 255),
            thickness=-1,
            lineType=cv2.LINE_AA,
        )
        cv2.circle(
            overlay,
            point,
            radius=max(thickness + 1, 3),
            color=color_bgr,
            thickness=-1,
            lineType=cv2.LINE_AA,
        )
        label_origin = (
            int(np.clip(point[0] + 8, 0, max(image_width - 1, 0))),
            int(np.clip(point[1] - 8, 0, max(image_height - 1, 0))),
        )
        cv2.putText(
            overlay,
            f"{label_prefix}-{corner_label}",
            label_origin,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (255, 255, 255),
            3,
            cv2.LINE_AA,
        )
        cv2.putText(
            overlay,
            f"{label_prefix}-{corner_label}",
            label_origin,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            color_bgr,
            1,
            cv2.LINE_AA,
        )


def build_corner_overlay(
    source_bgr: np.ndarray,
    corners: tuple[tuple[float, float], tuple[float, float], tuple[float, float], tuple[float, float]],
    color_bgr: tuple[int, int, int],
    label_prefix: str,
    thickness: int,
) -> np.ndarray:
    overlay = source_bgr.copy()
    _draw_labeled_corners(overlay, corners, color_bgr, label_prefix, thickness)
    return overlay


__all__ = [
    "aligned_frame_corners",
    "build_corner_overlay",
    "build_destination_corners",
    "warp_image_from_corners",
]
