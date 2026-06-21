from __future__ import annotations

import math

import cv2
import numpy as np

from .frame_model import LogicalLineFrameCandidate
from .logical_line_debug import get_logical_line_debug_name
from .logical_line_frame_cells import build_warped_frame_cells_grid_result
from .logical_line_frame_warp_model import (
    LogicalLineFrameCorners,
    LogicalLineFrameWarpResult,
)


def resolve_frame_candidate_corners(
    frame_candidate: LogicalLineFrameCandidate,
) -> LogicalLineFrameCorners | None:
    top_left = _resolve_intersection_point(
        frame_candidate.top_line,
        frame_candidate.left_line,
    )
    top_right = _resolve_intersection_point(
        frame_candidate.top_line,
        frame_candidate.right_line,
    )
    bottom_right = _resolve_intersection_point(
        frame_candidate.bottom_line,
        frame_candidate.right_line,
    )
    bottom_left = _resolve_intersection_point(
        frame_candidate.bottom_line,
        frame_candidate.left_line,
    )
    if any(
        point is None for point in (top_left, top_right, bottom_right, bottom_left)
    ):
        return None

    return LogicalLineFrameCorners(
        top_left=top_left,
        top_right=top_right,
        bottom_right=bottom_right,
        bottom_left=bottom_left,
    )


def estimate_frame_rectangle_size(
    frame_corners: LogicalLineFrameCorners,
) -> tuple[float, float]:
    top_width_px = _distance_px(
        frame_corners.top_left,
        frame_corners.top_right,
    )
    bottom_width_px = _distance_px(
        frame_corners.bottom_left,
        frame_corners.bottom_right,
    )
    left_height_px = _distance_px(
        frame_corners.top_left,
        frame_corners.bottom_left,
    )
    right_height_px = _distance_px(
        frame_corners.top_right,
        frame_corners.bottom_right,
    )
    rectangle_width_px = (top_width_px + bottom_width_px) / 2.0
    rectangle_height_px = (left_height_px + right_height_px) / 2.0
    return rectangle_width_px, rectangle_height_px


def build_destination_square_corners(
    output_size_px: int,
    padding_px: int,
    grid_division_count: int = 9,
) -> np.ndarray:
    if output_size_px <= 0:
        raise ValueError("Warp output size must be positive.")
    if padding_px < 0:
        raise ValueError("Warp padding cannot be negative.")
    if padding_px * 2 >= output_size_px:
        raise ValueError("Warp padding must leave room for image content.")
    if grid_division_count <= 0:
        raise ValueError("grid_division_count must be positive.")
    if output_size_px % grid_division_count != 0:
        raise ValueError(
            "Warp output size must be divisible by the grid division count."
        )

    min_index = float(padding_px)
    max_index = float(output_size_px - padding_px - 1)
    return np.array(
        [
            [min_index, min_index],
            [max_index, min_index],
            [max_index, max_index],
            [min_index, max_index],
        ],
        dtype=np.float32,
    )


def warp_selected_frame_to_square(
    image: np.ndarray,
    frame_candidate: LogicalLineFrameCandidate,
    output_size_px: int,
    padding_px: int,
    grid_division_count: int = 9,
    cells_output_mime_type: str = "image/png",
    cells_preview_gap_px: int = 2,
    ml_ready_cell_size_px: int = 28,
    ml_ready_adaptive_block_size: int = 11,
    ml_ready_adaptive_c: int = 2,
) -> LogicalLineFrameWarpResult | None:
    frame_corners = resolve_frame_candidate_corners(frame_candidate)
    if frame_corners is None:
        return None

    source_points = _build_source_corner_array(frame_corners)
    rectangle_width_px, rectangle_height_px = estimate_frame_rectangle_size(
        frame_corners
    )
    inferred_square_side_px = max(rectangle_width_px, rectangle_height_px)
    if inferred_square_side_px <= 1.0:
        raise ValueError("Frame corners do not span a usable square area.")

    destination_points = build_destination_square_corners(
        output_size_px=output_size_px,
        padding_px=padding_px,
        grid_division_count=grid_division_count,
    )
    perspective_matrix = cv2.getPerspectiveTransform(
        source_points,
        destination_points,
    )
    warped_image = cv2.warpPerspective(
        image,
        perspective_matrix,
        (output_size_px, output_size_px),
    )
    if warped_image.size == 0:
        raise ValueError("Perspective transform produced an empty image.")

    cells_grid_result = build_warped_frame_cells_grid_result(
        board_image=warped_image,
        output_mime_type=cells_output_mime_type,
        grid_rows=grid_division_count,
        grid_cols=grid_division_count,
        preview_gap_px=cells_preview_gap_px,
        ml_ready_cell_size_px=ml_ready_cell_size_px,
        ml_ready_adaptive_block_size=ml_ready_adaptive_block_size,
        ml_ready_adaptive_c=ml_ready_adaptive_c,
    )

    return LogicalLineFrameWarpResult(
        source_corners=frame_corners,
        rectangle_width_px=rectangle_width_px,
        rectangle_height_px=rectangle_height_px,
        inferred_square_side_px=inferred_square_side_px,
        output_size_px=output_size_px,
        padding_px=padding_px,
        destination_corners=tuple(
            (float(point[0]), float(point[1])) for point in destination_points
        ),
        perspective_matrix=perspective_matrix,
        warped_image=warped_image,
        cells_grid_result=cells_grid_result,
    )


def build_corner_overlay(
    source_bgr: np.ndarray,
    frame_corners: LogicalLineFrameCorners,
    color_bgr: tuple[int, int, int],
    label_prefix: str,
    thickness: int,
) -> np.ndarray:
    overlay = source_bgr.copy()
    _draw_labeled_corners(
        overlay=overlay,
        frame_corners=frame_corners,
        color_bgr=color_bgr,
        label_prefix=label_prefix,
        thickness=thickness,
    )
    return overlay


def _build_source_corner_array(frame_corners: LogicalLineFrameCorners) -> np.ndarray:
    source_points = frame_corners.as_array()
    polygon = source_points.reshape((-1, 1, 2))
    if abs(float(cv2.contourArea(polygon))) <= 1.0:
        raise ValueError("Warp corners do not form a valid quadrilateral.")
    return source_points


def _resolve_intersection_point(
    logical_line,
    cross_axis_line,
) -> tuple[float, float] | None:
    cross_axis_line_name = get_logical_line_debug_name(cross_axis_line)
    for intersection in logical_line.intersections:
        if intersection.intersected_line_cross_axis_debug_name == cross_axis_line_name:
            point = intersection.point
            return float(point[0]), float(point[1])
    return None


def _distance_px(
    first_point: tuple[float, float],
    second_point: tuple[float, float],
) -> float:
    return math.hypot(
        second_point[0] - first_point[0],
        second_point[1] - first_point[1],
    )


def _draw_labeled_corners(
    overlay: np.ndarray,
    frame_corners: LogicalLineFrameCorners,
    color_bgr: tuple[int, int, int],
    label_prefix: str,
    thickness: int,
) -> None:
    corner_labels = ("TL", "TR", "BR", "BL")
    image_height, image_width = overlay.shape[:2]
    rounded_corners: list[tuple[int, int]] = []
    for corner in frame_corners.ordered_points:
        x_coord = int(np.clip(round(float(corner[0])), 0, image_width - 1))
        y_coord = int(np.clip(round(float(corner[1])), 0, image_height - 1))
        rounded_corners.append((x_coord, y_coord))

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

    for corner_label, point in zip(corner_labels, rounded_corners):
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


__all__ = [
    "build_corner_overlay",
    "build_destination_square_corners",
    "estimate_frame_rectangle_size",
    "resolve_frame_candidate_corners",
    "warp_selected_frame_to_square",
]
