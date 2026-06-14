from __future__ import annotations

import cv2
import numpy as np

from detection import RawLineFamilyResult
from intersections import LogicalLineIntersectionKind
from models import ExperimentConfig


def _draw_logical_line_intersection(
    overlay: np.ndarray,
    logical_line_intersection,
    config: ExperimentConfig,
) -> None:
    point_color = config.logical_line_intersection_cross_color_bgr
    if logical_line_intersection.kind == LogicalLineIntersectionKind.TOUCH:
        point_color = config.logical_line_intersection_touch_color_bgr

    cv2.circle(
        overlay,
        logical_line_intersection.point,
        config.logical_line_intersection_radius,
        point_color,
        thickness=-1,
        lineType=cv2.LINE_AA,
    )
    if logical_line_intersection.is_mutual_boundary:
        cv2.circle(
            overlay,
            logical_line_intersection.point,
            config.logical_line_intersection_radius + 3,
            config.logical_line_intersection_boundary_color_bgr,
            thickness=2,
            lineType=cv2.LINE_AA,
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
