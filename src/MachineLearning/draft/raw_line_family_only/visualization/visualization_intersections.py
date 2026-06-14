from __future__ import annotations

import cv2
import numpy as np

from detection import RawLineFamilyResult
from intersection_models import LogicalLineIntersection, LogicalLineIntersectionKind
from logical_line_debug import get_logical_line_debug_name
from models import ExperimentConfig


def _build_intersection_label(
    logical_line_intersection: LogicalLineIntersection,
) -> str:
    horizontal_name = get_logical_line_debug_name(
        logical_line_intersection.ref_horizontal_line
    )
    vertical_name = get_logical_line_debug_name(
        logical_line_intersection.ref_vertical_line
    )
    return f"{horizontal_name}x{vertical_name}"


def _draw_logical_line_intersection(
    overlay: np.ndarray,
    logical_line_intersection: LogicalLineIntersection,
    config: ExperimentConfig,
) -> None:
    point = logical_line_intersection.point
    if logical_line_intersection.kind == LogicalLineIntersectionKind.CROSS:
        color = config.logical_line_intersection_cross_color_bgr
        marker_type = cv2.MARKER_CROSS
    else:
        color = config.logical_line_intersection_touch_color_bgr
        marker_type = cv2.MARKER_TILTED_CROSS

    cv2.drawMarker(
        overlay,
        point,
        color,
        markerType=marker_type,
        markerSize=config.logical_line_intersection_radius * 2,
        thickness=2,
        line_type=cv2.LINE_AA,
    )
    cv2.circle(
        overlay,
        point,
        config.logical_line_intersection_radius,
        color,
        thickness=1,
        lineType=cv2.LINE_AA,
    )
    if (
        logical_line_intersection.is_horizontal_boundary
        or logical_line_intersection.is_vertical_boundary
    ):
        cv2.circle(
            overlay,
            point,
            config.logical_line_intersection_radius + 3,
            config.logical_line_intersection_boundary_color_bgr,
            thickness=1,
            lineType=cv2.LINE_AA,
        )

    text_origin = (point[0] + 6, max(18, point[1] - 6))
    label_text = _build_intersection_label(logical_line_intersection)
    cv2.putText(
        overlay,
        label_text,
        text_origin,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (0, 0, 0),
        3,
        cv2.LINE_AA,
    )
    cv2.putText(
        overlay,
        label_text,
        text_origin,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        color,
        1,
        cv2.LINE_AA,
    )


def build_logical_line_intersection_overlays(
    source_bgr: np.ndarray,
    binary_image: np.ndarray,
    line_family_result: RawLineFamilyResult,
    config: ExperimentConfig,
) -> tuple[np.ndarray, np.ndarray]:
    binary_overlay = cv2.cvtColor(binary_image, cv2.COLOR_GRAY2BGR)
    source_overlay = source_bgr.copy()

    for overlay in (binary_overlay, source_overlay):
        for logical_line_intersection in line_family_result.logical_line_intersections:
            _draw_logical_line_intersection(
                overlay,
                logical_line_intersection,
                config,
            )

    return binary_overlay, source_overlay


__all__ = ["build_logical_line_intersection_overlays"]
