from __future__ import annotations

import cv2
import numpy as np

from detection import RawLineFamilyResult
from models import ExperimentConfig, ToleranceRectangle


def _draw_tolerance_rectangle(
    overlay: np.ndarray,
    tolerance_rectangle: ToleranceRectangle,
    color_bgr: tuple[int, int, int],
    config: ExperimentConfig,
) -> None:
    corners = np.array(
        tolerance_rectangle.corners,
        dtype=np.int32,
    ).reshape((-1, 1, 2))
    cv2.polylines(
        overlay,
        [corners],
        isClosed=True,
        color=color_bgr,
        thickness=config.tolerance_rectangle_thickness,
        lineType=cv2.LINE_AA,
    )
    cv2.arrowedLine(
        overlay,
        tolerance_rectangle.reference_point,
        tolerance_rectangle.recognition_end_point,
        color_bgr,
        thickness=1,
        line_type=cv2.LINE_AA,
        tipLength=0.2,
    )
    cv2.circle(
        overlay,
        tolerance_rectangle.reference_point,
        config.tolerance_rectangle_reference_radius,
        color_bgr,
        thickness=-1,
        lineType=cv2.LINE_AA,
    )


def build_tolerance_rectangle_overlays(
    source_bgr: np.ndarray,
    binary_image: np.ndarray,
    line_family_result: RawLineFamilyResult,
    config: ExperimentConfig,
) -> tuple[np.ndarray, np.ndarray]:
    binary_overlay = cv2.cvtColor(binary_image, cv2.COLOR_GRAY2BGR)
    source_overlay = source_bgr.copy()

    for overlay in (binary_overlay, source_overlay):
        for tolerance_rectangle in line_family_result.horizontal_tolerance_rectangles:
            _draw_tolerance_rectangle(
                overlay,
                tolerance_rectangle,
                config.horizontal_family_color_bgr,
                config,
            )
        for tolerance_rectangle in line_family_result.vertical_tolerance_rectangles:
            _draw_tolerance_rectangle(
                overlay,
                tolerance_rectangle,
                config.vertical_family_color_bgr,
                config,
            )

    return binary_overlay, source_overlay


__all__ = ["build_tolerance_rectangle_overlays"]
