from __future__ import annotations

import cv2
import numpy as np

from detection import RawLineFamilyResult
from models import ExperimentConfig
from visualization_logical_lines import (
    build_logical_line_color,
    draw_logical_line_label,
)
from visualization_raw_segment_groups import (
    draw_raw_segment_groups_for_lines,
)


def build_containment_prune_overlays(
    source_bgr: np.ndarray,
    binary_image: np.ndarray,
    line_family_result: RawLineFamilyResult,
    config: ExperimentConfig,
) -> tuple[np.ndarray, np.ndarray]:
    binary_overlay = cv2.cvtColor(binary_image, cv2.COLOR_GRAY2BGR)
    source_overlay = source_bgr.copy()
    _draw_containment_prune(binary_overlay, line_family_result, config)
    _draw_containment_prune(source_overlay, line_family_result, config)
    return binary_overlay, source_overlay


def build_containment_prune_board(
    source_bgr: np.ndarray,
    line_family_result: RawLineFamilyResult,
    config: ExperimentConfig,
) -> np.ndarray:
    prune_board = np.full_like(source_bgr, 24)
    pruned_lines = [
        *(
            []
            if line_family_result.horizontal_containment_prune_result is None
            else line_family_result.horizontal_containment_prune_result.pruned_logical_lines
        ),
        *(
            []
            if line_family_result.vertical_containment_prune_result is None
            else line_family_result.vertical_containment_prune_result.pruned_logical_lines
        ),
    ]
    draw_raw_segment_groups_for_lines(
        prune_board,
        pruned_lines,
        config,
    )
    return prune_board


def _draw_containment_prune(
    overlay: np.ndarray,
    line_family_result: RawLineFamilyResult,
    config: ExperimentConfig,
) -> None:
    horizontal_result = line_family_result.horizontal_containment_prune_result
    vertical_result = line_family_result.vertical_containment_prune_result
    if horizontal_result is None and vertical_result is None:
        return

    containment_groups = [
        *([] if horizontal_result is None else horizontal_result.cross_axis_groups),
        *([] if vertical_result is None else vertical_result.cross_axis_groups),
    ]
    group_count = len(containment_groups)
    if group_count <= 0:
        return

    group_index = 0
    for cross_axis_group in containment_groups:
        line_color = build_logical_line_color(
            cross_axis_group.container_line,
            group_index,
            group_count,
        )
        for removed_line in cross_axis_group.removed_logical_lines:
            _draw_logical_line(
                overlay,
                removed_line,
                color=(255, 255, 255),
                config=config,
                thickness_delta=4,
            )
            _draw_logical_line(
                overlay,
                removed_line,
                color=(0, 0, 255),
                config=config,
                thickness_delta=2,
            )
            draw_logical_line_label(
                overlay,
                removed_line,
                label_text=f"{removed_line.debug_name or '?'} rm",
                color=(0, 0, 255),
            )

        _draw_logical_line(
            overlay,
            cross_axis_group.container_line,
            color=(255, 255, 255),
            config=config,
            thickness_delta=4,
        )
        _draw_logical_line(
            overlay,
            cross_axis_group.container_line,
            color=line_color,
            config=config,
            thickness_delta=2,
        )
        draw_logical_line_label(
            overlay,
            cross_axis_group.container_line,
            label_text=(
                f"{cross_axis_group.container_line.debug_name or '?'} "
                f"rm={len(cross_axis_group.removed_logical_lines)}"
            ),
            color=line_color,
        )
        group_index += 1


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
    "build_containment_prune_board",
    "build_containment_prune_overlays",
]
