from __future__ import annotations

import cv2
import numpy as np

from raw_line_family_only_detection import RawLineFamilyResult
from raw_line_family_only_models import (
    ExperimentConfig,
    SegmentOrigin,
    ToleranceRectangle,
)


def build_line_family_overlays(
    source_bgr: np.ndarray,
    binary_image: np.ndarray,
    line_family_result: RawLineFamilyResult,
    config: ExperimentConfig,
) -> tuple[np.ndarray, np.ndarray]:
    binary_overlay = cv2.cvtColor(binary_image, cv2.COLOR_GRAY2BGR)
    source_overlay = source_bgr.copy()

    for overlay in (binary_overlay, source_overlay):
        for line_segment in line_family_result.horizontal_segments:
            cv2.line(
                overlay,
                line_segment.start,
                line_segment.end,
                config.horizontal_family_color_bgr,
                config.line_overlay_thickness,
                cv2.LINE_AA,
            )
        for line_segment in line_family_result.vertical_segments:
            cv2.line(
                overlay,
                line_segment.start,
                line_segment.end,
                config.vertical_family_color_bgr,
                config.line_overlay_thickness,
                cv2.LINE_AA,
            )

    return binary_overlay, source_overlay


def _build_logical_line_color(
    line_index: int,
    line_count: int,
) -> tuple[int, int, int]:
    if line_count <= 0:
        return (0, 255, 0)

    hue = int(round((180 * line_index) / line_count)) % 180
    hsv_color = np.uint8([[[hue, 255, 255]]])
    bgr_color = cv2.cvtColor(hsv_color, cv2.COLOR_HSV2BGR)[0, 0]
    return int(bgr_color[0]), int(bgr_color[1]), int(bgr_color[2])


def build_logical_line_overlays(
    source_bgr: np.ndarray,
    binary_image: np.ndarray,
    line_family_result: RawLineFamilyResult,
    config: ExperimentConfig,
) -> tuple[np.ndarray, np.ndarray]:
    binary_overlay = cv2.cvtColor(binary_image, cv2.COLOR_GRAY2BGR)
    source_overlay = source_bgr.copy()
    logical_lines = [
        *line_family_result.horizontal_logical_lines,
        *line_family_result.vertical_logical_lines,
    ]

    for overlay in (binary_overlay, source_overlay):
        for line_index, logical_line in enumerate(logical_lines):
            line_color = _build_logical_line_color(line_index, len(logical_lines))
            for line_segment in logical_line.line_segments:
                segment_color = line_color
                if line_segment.origin == SegmentOrigin.SAME_AXIS_CONNECTION:
                    segment_color = config.same_axis_connection_segment_color_bgr
                elif line_segment.origin == SegmentOrigin.CROSS_AXIS_CONNECTION:
                    segment_color = config.cross_axis_connection_segment_color_bgr
                cv2.line(
                    overlay,
                    line_segment.start,
                    line_segment.end,
                    segment_color,
                    config.line_overlay_thickness,
                    cv2.LINE_AA,
                )
            cv2.circle(
                overlay,
                logical_line.start_vertex,
                config.logical_line_vertex_radius,
                line_color,
                thickness=-1,
                lineType=cv2.LINE_AA,
            )
            cv2.circle(
                overlay,
                logical_line.end_vertex,
                config.logical_line_vertex_radius,
                line_color,
                thickness=-1,
                lineType=cv2.LINE_AA,
            )

    return binary_overlay, source_overlay


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


__all__ = [
    "build_line_family_overlays",
    "build_logical_line_overlays",
    "build_tolerance_rectangle_overlays",
]
