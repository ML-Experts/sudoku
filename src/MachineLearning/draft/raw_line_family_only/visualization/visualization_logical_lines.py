from __future__ import annotations

import cv2
import numpy as np

from detection import RawLineFamilyResult
from logical_line_debug import get_logical_line_debug_name
from models import ExperimentConfig, SegmentOrigin


def build_logical_line_color(
    logical_line,
    line_index: int = 0,
    line_count: int = 1,
) -> tuple[int, int, int]:
    debug_name = get_logical_line_debug_name(logical_line)
    family_prefix = debug_name[:1]
    suffix = debug_name[1:]
    if suffix.isdigit():
        if family_prefix == "H":
            hue = (10 + (int(suffix) - 1) * 23) % 180
        elif family_prefix == "V":
            hue = (100 + (int(suffix) - 1) * 23) % 180
        else:
            hue = (int(suffix) * 23) % 180
    else:
        if line_count <= 0:
            return (0, 255, 0)

        hue = int(round((180 * line_index) / line_count)) % 180
    hsv_color = np.uint8([[[hue, 255, 255]]])
    bgr_color = cv2.cvtColor(hsv_color, cv2.COLOR_HSV2BGR)[0, 0]
    return int(bgr_color[0]), int(bgr_color[1]), int(bgr_color[2])


def build_logical_line_label_text(logical_line) -> str:
    return get_logical_line_debug_name(logical_line)


def draw_logical_line_label(
    overlay: np.ndarray,
    logical_line,
    label_text: str,
    color: tuple[int, int, int],
) -> None:
    label_anchor = (
        int(round((logical_line.start_vertex[0] + logical_line.end_vertex[0]) / 2.0)),
        int(round((logical_line.start_vertex[1] + logical_line.end_vertex[1]) / 2.0)),
    )
    text_origin = (label_anchor[0] + 6, max(18, label_anchor[1] - 6))
    cv2.putText(
        overlay,
        label_text,
        text_origin,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 0, 0),
        3,
        cv2.LINE_AA,
    )
    cv2.putText(
        overlay,
        label_text,
        text_origin,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        color,
        1,
        cv2.LINE_AA,
    )


def build_logical_line_overlays(
    source_bgr: np.ndarray,
    binary_image: np.ndarray,
    line_family_result: RawLineFamilyResult,
    config: ExperimentConfig,
) -> tuple[np.ndarray, np.ndarray]:
    return build_logical_line_overlays_for_lines(
        source_bgr,
        binary_image,
        line_family_result.horizontal_logical_lines,
        line_family_result.vertical_logical_lines,
        config,
    )


def build_post_connection_logical_line_overlays(
    source_bgr: np.ndarray,
    binary_image: np.ndarray,
    line_family_result: RawLineFamilyResult,
    config: ExperimentConfig,
) -> tuple[np.ndarray, np.ndarray]:
    return build_logical_line_overlays_for_lines(
        source_bgr,
        binary_image,
        line_family_result.horizontal_post_connection_logical_lines,
        line_family_result.vertical_post_connection_logical_lines,
        config,
    )


def build_post_merge_logical_line_overlays(
    source_bgr: np.ndarray,
    binary_image: np.ndarray,
    line_family_result: RawLineFamilyResult,
    config: ExperimentConfig,
) -> tuple[np.ndarray, np.ndarray]:
    return build_logical_line_overlays_for_lines(
        source_bgr,
        binary_image,
        line_family_result.horizontal_post_merge_logical_lines,
        line_family_result.vertical_post_merge_logical_lines,
        config,
    )


def build_logical_line_overlays_for_lines(
    source_bgr: np.ndarray,
    binary_image: np.ndarray,
    horizontal_logical_lines,
    vertical_logical_lines,
    config: ExperimentConfig,
) -> tuple[np.ndarray, np.ndarray]:
    binary_overlay = cv2.cvtColor(binary_image, cv2.COLOR_GRAY2BGR)
    source_overlay = source_bgr.copy()
    logical_lines = [
        *horizontal_logical_lines,
        *vertical_logical_lines,
    ]

    draw_logical_lines_for_lines(binary_overlay, logical_lines, config)
    draw_logical_lines_for_lines(source_overlay, logical_lines, config)

    return binary_overlay, source_overlay


def draw_logical_lines_for_lines(
    overlay: np.ndarray,
    logical_lines,
    config: ExperimentConfig,
) -> None:
    for line_index, logical_line in enumerate(logical_lines):
        line_color = build_logical_line_color(
            logical_line,
            line_index,
            len(logical_lines),
        )
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
        draw_logical_line_label(
            overlay,
            logical_line,
            build_logical_line_label_text(logical_line),
            line_color,
        )


__all__ = [
    "build_logical_line_color",
    "build_logical_line_label_text",
    "build_logical_line_overlays",
    "build_logical_line_overlays_for_lines",
    "build_post_merge_logical_line_overlays",
    "build_post_connection_logical_line_overlays",
    "draw_logical_lines_for_lines",
    "draw_logical_line_label",
]
