from __future__ import annotations

import cv2
import numpy as np

from detection import RawLineFamilyResult
from visualization_logical_lines import (
    build_logical_line_color,
    draw_logical_line_label,
)
from models import ExperimentConfig, SegmentOrigin


PRE_TRIM_COLOR_BGR = (90, 90, 90)
TRIM_POINT_COLOR_BGR = (0, 255, 255)


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


def _draw_trim_actions(
    overlay: np.ndarray,
    trim_actions,
    config: ExperimentConfig,
) -> None:
    for trim_action in trim_actions:
        cv2.drawMarker(
            overlay,
            trim_action.intersection_point,
            TRIM_POINT_COLOR_BGR,
            markerType=cv2.MARKER_TILTED_CROSS,
            markerSize=config.logical_line_intersection_radius * 2,
            thickness=2,
            line_type=cv2.LINE_AA,
        )
        cv2.circle(
            overlay,
            trim_action.intersection_point,
            config.logical_line_intersection_radius + 2,
            TRIM_POINT_COLOR_BGR,
            thickness=1,
            lineType=cv2.LINE_AA,
        )


def build_intersection_trim_overlays(
    source_bgr: np.ndarray,
    binary_image: np.ndarray,
    line_family_result: RawLineFamilyResult,
    config: ExperimentConfig,
) -> tuple[np.ndarray, np.ndarray]:
    binary_overlay = cv2.cvtColor(binary_image, cv2.COLOR_GRAY2BGR)
    source_overlay = source_bgr.copy()
    trim_actions = (
        ()
        if line_family_result.intersection_trim_result is None
        else line_family_result.intersection_trim_result.actions
    )

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
        _draw_trim_actions(overlay, trim_actions, config)

    return binary_overlay, source_overlay


def build_intersection_trim_board(
    source_bgr: np.ndarray,
    line_family_result: RawLineFamilyResult,
    config: ExperimentConfig,
) -> np.ndarray:
    trim_board = np.zeros_like(source_bgr)
    trim_actions = (
        ()
        if line_family_result.intersection_trim_result is None
        else line_family_result.intersection_trim_result.actions
    )

    _draw_line_collection(
        trim_board,
        [
            *line_family_result.horizontal_post_connection_logical_lines,
            *line_family_result.vertical_post_connection_logical_lines,
        ],
        config,
        muted=True,
    )
    _draw_line_collection(
        trim_board,
        [
            *line_family_result.horizontal_logical_lines,
            *line_family_result.vertical_logical_lines,
        ],
        config,
        muted=False,
    )
    _draw_trim_actions(trim_board, trim_actions, config)

    return trim_board


__all__ = [
    "build_intersection_trim_board",
    "build_intersection_trim_overlays",
]
