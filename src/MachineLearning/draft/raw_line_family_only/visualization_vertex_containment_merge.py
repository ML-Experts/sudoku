from __future__ import annotations

import cv2
import numpy as np

from detection import RawLineFamilyResult
from models import ExperimentConfig
from visualization_logical_lines import (
    build_logical_line_color,
    draw_logical_lines_for_lines,
    draw_logical_line_label,
)


def build_vertex_containment_merge_overlays(
    source_bgr: np.ndarray,
    binary_image: np.ndarray,
    line_family_result: RawLineFamilyResult,
    config: ExperimentConfig,
) -> tuple[np.ndarray, np.ndarray]:
    binary_overlay = cv2.cvtColor(binary_image, cv2.COLOR_GRAY2BGR)
    source_overlay = source_bgr.copy()
    _draw_vertex_containment_merge(binary_overlay, line_family_result, config)
    _draw_vertex_containment_merge(source_overlay, line_family_result, config)
    return binary_overlay, source_overlay


def build_vertex_containment_merge_board(
    source_bgr: np.ndarray,
    line_family_result: RawLineFamilyResult,
    config: ExperimentConfig,
) -> np.ndarray:
    merge_board = np.full_like(source_bgr, 24)
    merged_lines = [
        *line_family_result.horizontal_post_merge_logical_lines,
        *line_family_result.vertical_post_merge_logical_lines,
    ]
    draw_logical_lines_for_lines(
        merge_board,
        merged_lines,
        config,
    )
    return merge_board


def _draw_vertex_containment_merge(
    overlay: np.ndarray,
    line_family_result: RawLineFamilyResult,
    config: ExperimentConfig,
) -> None:
    horizontal_result = line_family_result.horizontal_vertex_containment_merge_result
    vertical_result = line_family_result.vertical_vertex_containment_merge_result
    if horizontal_result is None and vertical_result is None:
        return

    merge_groups = [
        *([] if horizontal_result is None else horizontal_result.merge_groups),
        *([] if vertical_result is None else vertical_result.merge_groups),
    ]
    group_count = len(merge_groups)
    if group_count <= 0:
        return

    for group_index, cross_axis_group in enumerate(merge_groups):
        line_color = build_logical_line_color(
            cross_axis_group.anchor_line,
            group_index,
            group_count,
        )
        for consumed_line in cross_axis_group.grouped_logical_lines:
            _draw_logical_line(
                overlay,
                consumed_line,
                color=(255, 255, 255),
                config=config,
                thickness_delta=4,
            )
            _draw_logical_line(
                overlay,
                consumed_line,
                color=(0, 0, 255),
                config=config,
                thickness_delta=2,
            )
            draw_logical_line_label(
                overlay,
                consumed_line,
                label_text=f"{consumed_line.debug_name or '?'} mg",
                color=(0, 0, 255),
            )

        _draw_logical_line(
            overlay,
            cross_axis_group.anchor_line,
            color=(255, 255, 255),
            config=config,
            thickness_delta=4,
        )
        _draw_logical_line(
            overlay,
            cross_axis_group.anchor_line,
            color=line_color,
            config=config,
            thickness_delta=2,
        )
        draw_logical_line_label(
            overlay,
            cross_axis_group.anchor_line,
            label_text=(
                f"{cross_axis_group.anchor_line.debug_name or '?'} "
                f"mg={len(cross_axis_group.grouped_logical_lines)}"
            ),
            color=line_color,
        )


def _draw_logical_line(
    overlay: np.ndarray,
    logical_line,
    color: tuple[int, int, int],
    config: ExperimentConfig,
    thickness_delta: int = 0,
) -> None:
    line_thickness = max(1, config.line_overlay_thickness + thickness_delta)
    for line_segment in logical_line.line_segments:
        cv2.line(
            overlay,
            line_segment.start,
            line_segment.end,
            color,
            line_thickness,
            cv2.LINE_AA,
        )
    cv2.circle(
        overlay,
        logical_line.start_vertex,
        config.logical_line_vertex_radius,
        color,
        thickness=-1,
        lineType=cv2.LINE_AA,
    )
    cv2.circle(
        overlay,
        logical_line.end_vertex,
        config.logical_line_vertex_radius,
        color,
        thickness=-1,
        lineType=cv2.LINE_AA,
    )


__all__ = [
    "build_vertex_containment_merge_board",
    "build_vertex_containment_merge_overlays",
]
