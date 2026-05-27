from __future__ import annotations

import cv2
import numpy as np

from sudoku_board_threshold_models import (
    ExperimentConfig,
    LineBridge,
    LineFamilyResult,
    MergedLine,
)


def build_line_family_overlays(
    source_bgr: np.ndarray,
    binary_image: np.ndarray,
    line_family_result: LineFamilyResult,
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


def build_group_color(
    family_name: str,
    group_index: int,
    group_count: int,
) -> tuple[int, int, int]:
    if group_count <= 0:
        group_count = 1

    if family_name == "horizontal":
        start_hue, end_hue = 8, 32
    else:
        start_hue, end_hue = 82, 120

    if group_count == 1:
        hue = (start_hue + end_hue) // 2
    else:
        hue = int(round(start_hue + (end_hue - start_hue) * group_index / (group_count - 1)))

    hsv_pixel = np.array([[[hue, 220, 255]]], dtype=np.uint8)
    bgr_pixel = cv2.cvtColor(hsv_pixel, cv2.COLOR_HSV2BGR)[0, 0]
    return int(bgr_pixel[0]), int(bgr_pixel[1]), int(bgr_pixel[2])


def draw_logical_line_group(
    overlay: np.ndarray,
    merged_line: MergedLine,
    label: str,
    color_bgr: tuple[int, int, int],
    thickness: int,
) -> None:
    for segment in merged_line.segments:
        cv2.line(
            overlay,
            segment.start,
            segment.end,
            color_bgr,
            thickness,
            cv2.LINE_AA,
        )

    for touch_point in merged_line.touching_points:
        cv2.circle(
            overlay,
            touch_point,
            radius=max(thickness + 2, 4),
            color=(255, 255, 255),
            thickness=1,
            lineType=cv2.LINE_AA,
        )
        cv2.circle(
            overlay,
            touch_point,
            radius=max(thickness, 2),
            color=color_bgr,
            thickness=-1,
            lineType=cv2.LINE_AA,
        )

    cv2.putText(
        overlay,
        label,
        merged_line.centroid,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        color_bgr,
        1,
        cv2.LINE_AA,
    )


def draw_merged_line_groups(
    binary_overlay: np.ndarray,
    source_overlay: np.ndarray,
    horizontal_lines: list[MergedLine],
    vertical_lines: list[MergedLine],
    config: ExperimentConfig,
) -> tuple[np.ndarray, np.ndarray]:
    horizontal_count = len(horizontal_lines)
    vertical_count = len(vertical_lines)

    for overlay in (binary_overlay, source_overlay):
        for line_index, merged_line in enumerate(horizontal_lines):
            draw_logical_line_group(
                overlay,
                merged_line,
                (
                    f"H{line_index} C={merged_line.covered_length:.0f} "
                    f"P={merged_line.touching_point_count}"
                ),
                build_group_color("horizontal", line_index, horizontal_count),
                max(config.line_overlay_thickness + 1, 2),
            )
        for line_index, merged_line in enumerate(vertical_lines):
            draw_logical_line_group(
                overlay,
                merged_line,
                (
                    f"V{line_index} C={merged_line.covered_length:.0f} "
                    f"P={merged_line.touching_point_count}"
                ),
                build_group_color("vertical", line_index, vertical_count),
                max(config.line_overlay_thickness + 1, 2),
            )

    return binary_overlay, source_overlay


def draw_line_bridges(
    overlay: np.ndarray,
    line_bridges: list[LineBridge],
    group_count: int,
    config: ExperimentConfig,
) -> None:
    for line_bridge in line_bridges:
        color_bgr = build_group_color(
            line_bridge.family_name,
            line_bridge.first_line_index,
            group_count,
        )
        corridor_polygon = np.array(line_bridge.corridor_polygon, dtype=np.int32)
        cv2.polylines(
            overlay,
            [corridor_polygon],
            isClosed=True,
            color=(255, 255, 255),
            thickness=1,
            lineType=cv2.LINE_AA,
        )
        cv2.polylines(
            overlay,
            [corridor_polygon],
            isClosed=True,
            color=color_bgr,
            thickness=1,
            lineType=cv2.LINE_AA,
        )
        cv2.rectangle(
            overlay,
            line_bridge.start_box[0],
            line_bridge.start_box[1],
            color_bgr,
            thickness=1,
            lineType=cv2.LINE_AA,
        )
        cv2.rectangle(
            overlay,
            line_bridge.end_box[0],
            line_bridge.end_box[1],
            color_bgr,
            thickness=1,
            lineType=cv2.LINE_AA,
        )
        cv2.line(
            overlay,
            line_bridge.segment.start,
            line_bridge.segment.end,
            color=(255, 255, 255),
            thickness=max(config.line_overlay_thickness + 2, 3),
            lineType=cv2.LINE_AA,
        )
        cv2.line(
            overlay,
            line_bridge.segment.start,
            line_bridge.segment.end,
            color=color_bgr,
            thickness=max(config.line_overlay_thickness + 1, 2),
            lineType=cv2.LINE_AA,
        )
        cv2.circle(
            overlay,
            line_bridge.ideal_start_point,
            radius=max(config.line_overlay_thickness + 2, 3),
            color=(255, 255, 255),
            thickness=1,
            lineType=cv2.LINE_AA,
        )
        cv2.circle(
            overlay,
            line_bridge.ideal_end_point,
            radius=max(config.line_overlay_thickness + 2, 3),
            color=(255, 255, 255),
            thickness=1,
            lineType=cv2.LINE_AA,
        )


def build_bridged_line_family_overlays(
    source_bgr: np.ndarray,
    binary_image: np.ndarray,
    line_family_result: LineFamilyResult,
    config: ExperimentConfig,
) -> tuple[np.ndarray, np.ndarray]:
    binary_overlay = cv2.cvtColor(binary_image, cv2.COLOR_GRAY2BGR)
    source_overlay = source_bgr.copy()
    binary_overlay, source_overlay = draw_merged_line_groups(
        binary_overlay,
        source_overlay,
        line_family_result.horizontal_pre_filter_merged_lines,
        line_family_result.vertical_pre_filter_merged_lines,
        config,
    )
    for overlay in (binary_overlay, source_overlay):
        draw_line_bridges(
            overlay,
            line_family_result.horizontal_bridges,
            len(line_family_result.horizontal_pre_filter_merged_lines),
            config,
        )
        draw_line_bridges(
            overlay,
            line_family_result.vertical_bridges,
            len(line_family_result.vertical_pre_filter_merged_lines),
            config,
        )
    return binary_overlay, source_overlay


def build_merged_line_overlays(
    source_bgr: np.ndarray,
    binary_image: np.ndarray,
    line_family_result: LineFamilyResult,
    config: ExperimentConfig,
) -> tuple[np.ndarray, np.ndarray]:
    binary_overlay = cv2.cvtColor(binary_image, cv2.COLOR_GRAY2BGR)
    source_overlay = source_bgr.copy()
    return draw_merged_line_groups(
        binary_overlay,
        source_overlay,
        line_family_result.horizontal_merged_lines,
        line_family_result.vertical_merged_lines,
        config,
    )


__all__ = [
    "build_bridged_line_family_overlays",
    "build_line_family_overlays",
    "build_merged_line_overlays",
]
