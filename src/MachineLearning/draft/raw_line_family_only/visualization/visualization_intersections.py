from __future__ import annotations

import cv2
import numpy as np

from detection import RawLineFamilyResult
from intersection_model import (
    LogicalLineIntersection,
    LogicalLineIntersectionDebugCandidate,
    LogicalLineIntersectionKind,
)
from models import ExperimentConfig

DEBUG_DUPLICATE_OFFSETS = (
    (0, 0),
    (-8, -8),
    (8, -8),
    (-8, 8),
    (8, 8),
    (0, -12),
    (0, 12),
    (-12, 0),
    (12, 0),
)


def _build_intersection_label(
    logical_line_intersection: LogicalLineIntersection,
) -> str:
    axis_name = logical_line_intersection.intersected_line_axis_debug_name
    cross_axis_name = logical_line_intersection.intersected_line_cross_axis_debug_name
    kind_label = "C" if logical_line_intersection.is_cross else "T"
    order_label = logical_line_intersection.order.value[:1].upper()
    return f"{axis_name}x{cross_axis_name} {kind_label}/{order_label}"


def _build_debug_candidate_label(
    logical_line_intersection_candidate: LogicalLineIntersectionDebugCandidate,
) -> str:
    axis_name = logical_line_intersection_candidate.intersected_line_axis_debug_name
    cross_axis_name = (
        logical_line_intersection_candidate.intersected_line_cross_axis_debug_name
    )
    kind_label = "C" if logical_line_intersection_candidate.is_cross else "T"
    duplicate_label = ""
    if logical_line_intersection_candidate.duplicate_count > 1:
        duplicate_label = (
            f" {logical_line_intersection_candidate.duplicate_index + 1}"
            f"/{logical_line_intersection_candidate.duplicate_count}"
        )
    return f"{axis_name}x{cross_axis_name} {kind_label}{duplicate_label}"


def _kind_color(
    kind: LogicalLineIntersectionKind,
    config: ExperimentConfig,
) -> tuple[int, int, int]:
    if kind == LogicalLineIntersectionKind.CROSS:
        return config.logical_line_intersection_cross_color_bgr
    return config.logical_line_intersection_touch_color_bgr


def _debug_candidate_draw_point(
    logical_line_intersection_candidate: LogicalLineIntersectionDebugCandidate,
) -> tuple[int, int]:
    base_point = logical_line_intersection_candidate.point
    offset_x, offset_y = DEBUG_DUPLICATE_OFFSETS[
        logical_line_intersection_candidate.duplicate_index
        % len(DEBUG_DUPLICATE_OFFSETS)
    ]
    return base_point[0] + offset_x, base_point[1] + offset_y


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


def _draw_logical_line_intersection_candidate(
    overlay: np.ndarray,
    logical_line_intersection_candidate: LogicalLineIntersectionDebugCandidate,
    config: ExperimentConfig,
) -> None:
    point = _debug_candidate_draw_point(logical_line_intersection_candidate)
    color = _kind_color(logical_line_intersection_candidate.kind, config)
    radius = config.logical_line_intersection_radius + 1

    cv2.circle(
        overlay,
        point,
        radius + 1,
        (255, 255, 255),
        thickness=-1,
        lineType=cv2.LINE_AA,
    )
    cv2.circle(
        overlay,
        point,
        radius + 2,
        (0, 0, 0),
        thickness=1,
        lineType=cv2.LINE_AA,
    )
    cv2.drawMarker(
        overlay,
        point,
        color,
        markerType=cv2.MARKER_DIAMOND,
        markerSize=radius * 2,
        thickness=2,
        line_type=cv2.LINE_AA,
    )

    if logical_line_intersection_candidate.duplicate_count > 1:
        cv2.circle(
            overlay,
            logical_line_intersection_candidate.point,
            config.logical_line_intersection_radius + 6,
            config.logical_line_intersection_boundary_color_bgr,
            thickness=1,
            lineType=cv2.LINE_AA,
        )

    label_text = _build_debug_candidate_label(logical_line_intersection_candidate)
    text_origin = (point[0] + 8, min(overlay.shape[0] - 8, point[1] + 16))
    cv2.putText(
        overlay,
        label_text,
        text_origin,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.42,
        (0, 0, 0),
        3,
        cv2.LINE_AA,
    )
    cv2.putText(
        overlay,
        label_text,
        text_origin,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.42,
        (255, 255, 255),
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


def build_logical_line_intersection_kind_map_overlays(
    source_bgr: np.ndarray,
    binary_image: np.ndarray,
    line_family_result: RawLineFamilyResult,
    config: ExperimentConfig,
) -> tuple[np.ndarray, np.ndarray]:
    binary_overlay = cv2.cvtColor(binary_image, cv2.COLOR_GRAY2BGR)
    source_overlay = source_bgr.copy()

    for overlay in (binary_overlay, source_overlay):
        for logical_line_intersection_candidate in (
            line_family_result.logical_line_intersection_debug_candidates
        ):
            _draw_logical_line_intersection_candidate(
                overlay,
                logical_line_intersection_candidate,
                config,
            )

    return binary_overlay, source_overlay


__all__ = [
    "build_logical_line_intersection_kind_map_overlays",
    "build_logical_line_intersection_overlays",
]
