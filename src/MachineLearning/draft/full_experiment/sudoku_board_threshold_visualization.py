from __future__ import annotations

import cv2
import numpy as np

from sudoku_board_threshold_line_geometry import (
    clamp_point_to_image,
    resolve_merged_line_vertices,
)
from sudoku_board_threshold_models import (
    ExperimentConfig,
    LineBridge,
    LineFamilyResult,
    LineFrame,
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


def build_vertex_color(
    vertex_index: int,
    vertex_count: int,
) -> tuple[int, int, int]:
    if vertex_count <= 0:
        vertex_count = 1

    if vertex_count == 1:
        hue = 90
    else:
        hue = int(round(179 * vertex_index / (vertex_count - 1)))

    hsv_pixel = np.array([[[hue, 240, 255]]], dtype=np.uint8)
    bgr_pixel = cv2.cvtColor(hsv_pixel, cv2.COLOR_HSV2BGR)[0, 0]
    return int(bgr_pixel[0]), int(bgr_pixel[1]), int(bgr_pixel[2])


def draw_logical_line_group(
    overlay: np.ndarray,
    merged_line: MergedLine,
    label: str,
    color_bgr: tuple[int, int, int],
    thickness: int,
    label_color_bgr: tuple[int, int, int] | None = None,
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

    if label_color_bgr is None:
        label_color_bgr = color_bgr

    cv2.putText(
        overlay,
        label,
        merged_line.centroid,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (255, 255, 255),
        3,
        cv2.LINE_AA,
    )
    cv2.putText(
        overlay,
        label,
        merged_line.centroid,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        label_color_bgr,
        1,
        cv2.LINE_AA,
    )


def draw_line_vertices(
    overlay: np.ndarray,
    vertices: tuple[tuple[int, int], tuple[int, int]],
    vertex_colors_bgr: tuple[tuple[int, int, int], tuple[int, int, int]],
    thickness: int,
) -> None:
    radius = max(thickness + 3, 5)
    for point, color_bgr in zip(vertices, vertex_colors_bgr):
        cv2.circle(
            overlay,
            point,
            radius=radius,
            color=(255, 255, 255),
            thickness=-1,
            lineType=cv2.LINE_AA,
        )
        cv2.circle(
            overlay,
            point,
            radius=max(radius - 2, 2),
            color=color_bgr,
            thickness=-1,
            lineType=cv2.LINE_AA,
        )
        cv2.circle(
            overlay,
            point,
            radius=radius,
            color=(0, 0, 0),
            thickness=1,
            lineType=cv2.LINE_AA,
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


def build_merged_line_vertex_overlays(
    source_bgr: np.ndarray,
    binary_image: np.ndarray,
    line_family_result: LineFamilyResult,
    config: ExperimentConfig,
) -> tuple[np.ndarray, np.ndarray]:
    binary_overlay = cv2.cvtColor(binary_image, cv2.COLOR_GRAY2BGR)
    source_overlay = source_bgr.copy()
    total_vertex_count = 2 * (
        len(line_family_result.horizontal_merged_lines)
        + len(line_family_result.vertical_merged_lines)
    )
    line_descriptors: list[
        tuple[
            MergedLine,
            str,
            tuple[int, int, int],
            tuple[tuple[int, int], tuple[int, int]],
            tuple[tuple[int, int, int], tuple[int, int, int]],
        ]
    ] = []
    vertex_index = 0

    for line_index, merged_line in enumerate(line_family_result.horizontal_merged_lines):
        if line_index < len(line_family_result.horizontal_aligned_vertices):
            resolved_vertices = line_family_result.horizontal_aligned_vertices[line_index]
        else:
            resolved_vertices = resolve_merged_line_vertices(merged_line)
        vertices = (
            clamp_point_to_image(resolved_vertices[0], source_bgr.shape),
            clamp_point_to_image(resolved_vertices[1], source_bgr.shape),
        )
        line_descriptors.append(
            (
                merged_line,
                f"H{line_index}",
                build_group_color(
                    "horizontal",
                    line_index,
                    len(line_family_result.horizontal_merged_lines),
                ),
                vertices,
                (
                    build_vertex_color(vertex_index, total_vertex_count),
                    build_vertex_color(vertex_index + 1, total_vertex_count),
                ),
            )
        )
        vertex_index += 2

    for line_index, merged_line in enumerate(line_family_result.vertical_merged_lines):
        if line_index < len(line_family_result.vertical_aligned_vertices):
            resolved_vertices = line_family_result.vertical_aligned_vertices[line_index]
        else:
            resolved_vertices = resolve_merged_line_vertices(merged_line)
        vertices = (
            clamp_point_to_image(resolved_vertices[0], source_bgr.shape),
            clamp_point_to_image(resolved_vertices[1], source_bgr.shape),
        )
        line_descriptors.append(
            (
                merged_line,
                f"V{line_index}",
                build_group_color(
                    "vertical",
                    line_index,
                    len(line_family_result.vertical_merged_lines),
                ),
                vertices,
                (
                    build_vertex_color(vertex_index, total_vertex_count),
                    build_vertex_color(vertex_index + 1, total_vertex_count),
                ),
            )
        )
        vertex_index += 2

    for overlay in (binary_overlay, source_overlay):
        for (
            merged_line,
            label,
            line_color_bgr,
            vertices,
            vertex_colors_bgr,
        ) in line_descriptors:
            draw_logical_line_group(
                overlay,
                merged_line,
                label,
                line_color_bgr,
                max(config.line_overlay_thickness + 1, 2),
                label_color_bgr=(0, 0, 0),
            )
            draw_line_vertices(
                overlay,
                vertices,
                vertex_colors_bgr,
                max(config.line_overlay_thickness + 1, 2),
            )

    return binary_overlay, source_overlay


def draw_line_frames(
    overlay: np.ndarray,
    frames: list[LineFrame],
    config: ExperimentConfig,
) -> None:
    frame_count = len(frames)
    for frame_index, frame in enumerate(frames):
        color_bgr = build_vertex_color(frame_index, max(frame_count, 2))
        polygon = np.array(frame.corners, dtype=np.int32).reshape((-1, 1, 2))
        cv2.polylines(
            overlay,
            [polygon],
            isClosed=True,
            color=(255, 255, 255),
            thickness=max(config.line_overlay_thickness + 3, 4),
            lineType=cv2.LINE_AA,
        )
        cv2.polylines(
            overlay,
            [polygon],
            isClosed=True,
            color=color_bgr,
            thickness=max(config.line_overlay_thickness + 1, 2),
            lineType=cv2.LINE_AA,
        )
        for corner in frame.corners:
            cv2.circle(
                overlay,
                corner,
                radius=max(config.line_overlay_thickness + 3, 5),
                color=(255, 255, 255),
                thickness=-1,
                lineType=cv2.LINE_AA,
            )
            cv2.circle(
                overlay,
                corner,
                radius=max(config.line_overlay_thickness + 1, 3),
                color=color_bgr,
                thickness=-1,
                lineType=cv2.LINE_AA,
            )

        label_anchor = (
            int(round(sum(point[0] for point in frame.corners) / 4.0)),
            int(round(sum(point[1] for point in frame.corners) / 4.0)),
        )
        label = (
            f"F{frame_index} "
            f"H{frame.top_line_index}-{frame.bottom_line_index} "
            f"V{frame.left_line_index}-{frame.right_line_index}"
        )
        cv2.putText(
            overlay,
            label,
            label_anchor,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (255, 255, 255),
            3,
            cv2.LINE_AA,
        )
        cv2.putText(
            overlay,
            label,
            label_anchor,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            color_bgr,
            1,
            cv2.LINE_AA,
        )


def build_line_frame_overlays(
    source_bgr: np.ndarray,
    binary_image: np.ndarray,
    frames: list[LineFrame],
    config: ExperimentConfig,
) -> tuple[np.ndarray, np.ndarray]:
    binary_overlay = cv2.cvtColor(binary_image, cv2.COLOR_GRAY2BGR)
    source_overlay = source_bgr.copy()
    for overlay in (binary_overlay, source_overlay):
        draw_line_frames(overlay, frames, config)
    return binary_overlay, source_overlay


__all__ = [
    "build_bridged_line_family_overlays",
    "build_line_family_overlays",
    "build_line_frame_overlays",
    "build_merged_line_overlays",
    "build_merged_line_vertex_overlays",
]
