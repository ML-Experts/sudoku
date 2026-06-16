from __future__ import annotations

import cv2
import numpy as np

from detection import RawLineFamilyResult
from intersection_model import (
    LogicalLineIntersection,
    LogicalLineIntersectionKind,
)
from models import ExperimentConfig


def _build_intersection_label(
    logical_line_intersection: LogicalLineIntersection,
) -> str:
    axis_name = logical_line_intersection.intersected_line_axis_debug_name
    cross_axis_name = logical_line_intersection.intersected_line_cross_axis_debug_name
    kind_label = "C" if logical_line_intersection.is_cross else "T"
    order_label = logical_line_intersection.order.value[:1].upper()
    return f"{axis_name}x{cross_axis_name} {kind_label}/{order_label}"


def _kind_color(
    kind: LogicalLineIntersectionKind,
    config: ExperimentConfig,
) -> tuple[int, int, int]:
    if kind == LogicalLineIntersectionKind.CROSS:
        return config.logical_line_intersection_cross_color_bgr
    return config.logical_line_intersection_touch_color_bgr


def _draw_logical_line_intersection(
    overlay: np.ndarray,
    logical_line_intersection: LogicalLineIntersection,
    config: ExperimentConfig,
) -> None:
    point = logical_line_intersection.point
    color = _kind_color(logical_line_intersection.kind, config)
    marker_type = (
        cv2.MARKER_CROSS
        if logical_line_intersection.is_cross
        else cv2.MARKER_TILTED_CROSS
    )

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
    if logical_line_intersection.is_boundary:
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
) -> np.ndarray:
    del binary_image
    source_overlay = source_bgr.copy()

    for logical_line_intersection in line_family_result.logical_line_intersections:
        _draw_logical_line_intersection(
            source_overlay,
            logical_line_intersection,
            config,
        )

    return source_overlay


__all__ = [
    "build_logical_line_intersection_overlays",
]
