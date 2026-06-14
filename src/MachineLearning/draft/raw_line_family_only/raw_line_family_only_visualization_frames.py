from __future__ import annotations

import cv2
import numpy as np

from raw_line_family_only_detection import RawLineFamilyResult
from raw_line_family_only_logical_line_core import FrameSide
from raw_line_family_only_models import ExperimentConfig
from raw_line_family_only_visualization_logical_lines import draw_logical_line_label


def _frame_side_color(
    frame_side: FrameSide,
    config: ExperimentConfig,
) -> tuple[int, int, int] | None:
    if frame_side == FrameSide.TOP:
        return config.frame_top_color_bgr
    if frame_side == FrameSide.BOTTOM:
        return config.frame_bottom_color_bgr
    if frame_side == FrameSide.LEFT:
        return config.frame_left_color_bgr
    if frame_side == FrameSide.RIGHT:
        return config.frame_right_color_bgr
    return None


def build_frame_overlays(
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
        for logical_line in logical_lines:
            line_color = _frame_side_color(logical_line.frame_side, config)
            if line_color is None:
                continue

            for line_segment in logical_line.line_segments:
                cv2.line(
                    overlay,
                    line_segment.start,
                    line_segment.end,
                    line_color,
                    config.line_overlay_thickness + 1,
                    cv2.LINE_AA,
                )
            cv2.circle(
                overlay,
                logical_line.start_vertex,
                config.logical_line_vertex_radius + 1,
                line_color,
                thickness=-1,
                lineType=cv2.LINE_AA,
            )
            cv2.circle(
                overlay,
                logical_line.end_vertex,
                config.logical_line_vertex_radius + 1,
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

    return binary_overlay, source_overlay


__all__ = ["build_frame_overlays"]
