from __future__ import annotations

import cv2
import numpy as np

from detection import RawLineFamilyResult
from models import ExperimentConfig, SegmentOrigin
from visualization_logical_lines import (
    build_logical_line_color,
    draw_logical_line_label,
)


PRE_TRIM_COLOR_BGR = (90, 90, 90)


def _draw_line_collection(
    overlay: np.ndarray,
    logical_lines,
    config: ExperimentConfig,
    muted: bool,
) -> None:
    for line_index, logical_line in enumerate(logical_lines):
        line_color = (
            PRE_TRIM_COLOR_BGR
            if muted
            else build_logical_line_color(logical_line, line_index, len(logical_lines))
        )
        for line_segment in logical_line.line_segments:
            segment_color = line_color
            if not muted:
                if line_segment.origin == SegmentOrigin.SAME_AXIS_CONNECTION:
                    segment_color = config.same_axis_connection_segment_color_bgr
                elif line_segment.origin == SegmentOrigin.CROSS_AXIS_CONNECTION:
                    segment_color = config.cross_axis_connection_segment_color_bgr
            cv2.line(
                overlay,
                line_segment.start,
                line_segment.end,
                segment_color,
                config.line_overlay_thickness if not muted else 1,
                cv2.LINE_AA,
            )
        if muted:
            continue
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
        draw_logical_line_label(
            overlay,
            logical_line,
            logical_line.debug_name or "?",
            line_color,
        )


def build_trimmed_logical_line_overlays(
    source_bgr: np.ndarray,
    binary_image: np.ndarray,
    line_family_result: RawLineFamilyResult,
    config: ExperimentConfig,
) -> tuple[np.ndarray, np.ndarray]:
    binary_overlay = cv2.cvtColor(binary_image, cv2.COLOR_GRAY2BGR)
    source_overlay = source_bgr.copy()

    for overlay in (binary_overlay, source_overlay):
        _draw_line_collection(
            overlay,
            [
                *line_family_result.horizontal_post_connection_logical_lines,
                *line_family_result.vertical_post_connection_logical_lines,
            ],
            config,
            muted=True,
        )
        _draw_line_collection(
            overlay,
            [
                *line_family_result.horizontal_logical_lines,
                *line_family_result.vertical_logical_lines,
            ],
            config,
            muted=False,
        )

    return binary_overlay, source_overlay


__all__ = [
    "build_trimmed_logical_line_overlays",
]
