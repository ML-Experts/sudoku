from __future__ import annotations

import cv2
import numpy as np

from raw_line_family_only_detection import RawLineFamilyResult
from raw_line_family_only_models import ExperimentConfig
from raw_line_family_only_visualization_logical_lines import _build_logical_line_color


def build_raw_segment_group_overlays(
    source_bgr: np.ndarray,
    binary_image: np.ndarray,
    line_family_result: RawLineFamilyResult,
    config: ExperimentConfig,
) -> tuple[np.ndarray, np.ndarray]:
    binary_overlay = cv2.cvtColor(binary_image, cv2.COLOR_GRAY2BGR)
    source_overlay = source_bgr.copy()
    _draw_raw_segment_groups(
        binary_overlay,
        line_family_result,
        config,
    )
    _draw_raw_segment_groups(
        source_overlay,
        line_family_result,
        config,
    )
    return binary_overlay, source_overlay


def _draw_raw_segment_groups(
    overlay: np.ndarray,
    line_family_result: RawLineFamilyResult,
    config: ExperimentConfig,
) -> None:
    logical_lines = [
        *line_family_result.horizontal_pre_connection_logical_lines,
        *line_family_result.vertical_pre_connection_logical_lines,
    ]

    line_labels: list[str] = [
        *[
            f"H{line_index + 1}"
            for line_index, _ in enumerate(
                line_family_result.horizontal_pre_connection_logical_lines
            )
        ],
        *[
            f"V{line_index + 1}"
            for line_index, _ in enumerate(
                line_family_result.vertical_pre_connection_logical_lines
            )
        ],
    ]

    for line_index, logical_line in enumerate(logical_lines):
        line_color = _build_logical_line_color(line_index, len(logical_lines))
        line_label = line_labels[line_index]
        for group_index, group_result in enumerate(
            logical_line.raw_segment_group_results,
            start=1,
        ):
            for line_segment in group_result.consumed_segments:
                cv2.line(
                    overlay,
                    line_segment.start,
                    line_segment.end,
                    line_color,
                    max(1, config.line_overlay_thickness),
                    cv2.LINE_AA,
                )

            cv2.line(
                overlay,
                group_result.output_segment.start,
                group_result.output_segment.end,
                (255, 255, 255),
                config.line_overlay_thickness + 4,
                cv2.LINE_AA,
            )
            cv2.line(
                overlay,
                group_result.output_segment.start,
                group_result.output_segment.end,
                line_color,
                config.line_overlay_thickness + 2,
                cv2.LINE_AA,
            )
            cv2.circle(
                overlay,
                group_result.output_segment.start,
                config.logical_line_vertex_radius,
                line_color,
                thickness=-1,
                lineType=cv2.LINE_AA,
            )
            cv2.circle(
                overlay,
                group_result.output_segment.end,
                config.logical_line_vertex_radius,
                line_color,
                thickness=-1,
                lineType=cv2.LINE_AA,
            )
            if group_result.first_invalid_gap_point is not None:
                cv2.circle(
                    overlay,
                    group_result.first_invalid_gap_point,
                    config.logical_line_vertex_radius + 2,
                    (0, 0, 255),
                    thickness=2,
                    lineType=cv2.LINE_AA,
                )

            output_segment = group_result.output_segment
            label_anchor = (
                int(round((output_segment.start[0] + output_segment.end[0]) / 2.0)),
                int(round((output_segment.start[1] + output_segment.end[1]) / 2.0)),
            )
            label_text = (
                f"{line_label} (G{group_index}:{len(group_result.consumed_segments)})"
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
                line_color,
                1,
                cv2.LINE_AA,
            )


def build_raw_segment_group_board(
    source_bgr: np.ndarray,
    line_family_result: RawLineFamilyResult,
    config: ExperimentConfig,
) -> np.ndarray:
    group_board = np.full_like(source_bgr, 24)
    _draw_raw_segment_groups(
        group_board,
        line_family_result,
        config,
    )
    return group_board


__all__ = [
    "build_raw_segment_group_board",
    "build_raw_segment_group_overlays",
]
