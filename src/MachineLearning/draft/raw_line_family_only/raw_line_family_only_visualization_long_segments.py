from __future__ import annotations

import cv2
import numpy as np

from raw_line_family_only_detection import RawLineFamilyResult
from raw_line_family_only_models import ExperimentConfig, LineFamilyName


def build_long_segment_candidate_overlays(
    source_bgr: np.ndarray,
    binary_image: np.ndarray,
    line_family_result: RawLineFamilyResult,
    config: ExperimentConfig,
    minimum_length_ratio: float = 0.8,
) -> tuple[np.ndarray, np.ndarray]:
    binary_overlay = cv2.cvtColor(binary_image, cv2.COLOR_GRAY2BGR)
    source_overlay = source_bgr.copy()
    logical_lines = [
        *line_family_result.horizontal_logical_lines,
        *line_family_result.vertical_logical_lines,
    ]

    for overlay in (binary_overlay, source_overlay):
        for logical_line in logical_lines:
            if logical_line.family_name == LineFamilyName.HORIZONTAL:
                segment_color = config.horizontal_family_color_bgr
            else:
                segment_color = config.vertical_family_color_bgr

            for line_segment in logical_line.collect_long_segments(
                minimum_length_ratio=minimum_length_ratio
            ):
                cv2.line(
                    overlay,
                    line_segment.start,
                    line_segment.end,
                    segment_color,
                    config.line_overlay_thickness + 2,
                    cv2.LINE_AA,
                )

    return binary_overlay, source_overlay


def build_long_segment_candidate_board(
    source_bgr: np.ndarray,
    line_family_result: RawLineFamilyResult,
    config: ExperimentConfig,
    minimum_length_ratio: float = 0.8,
) -> np.ndarray:
    del config
    logical_line_board = np.zeros_like(source_bgr)
    logical_lines = [
        *line_family_result.horizontal_logical_lines,
        *line_family_result.vertical_logical_lines,
    ]
    all_line_color_bgr = (255, 0, 0)
    longest_line_color_bgr = (0, 0, 255)

    for logical_line in logical_lines:
        for line_segment in logical_line.line_segments:
            cv2.line(
                logical_line_board,
                line_segment.start,
                line_segment.end,
                all_line_color_bgr,
                2,
                cv2.LINE_AA,
            )

        for line_segment in logical_line.collect_long_segments(
            minimum_length_ratio=minimum_length_ratio
        ):
            cv2.line(
                logical_line_board,
                line_segment.start,
                line_segment.end,
                longest_line_color_bgr,
                4,
                cv2.LINE_AA,
            )

    return logical_line_board


__all__ = [
    "build_long_segment_candidate_board",
    "build_long_segment_candidate_overlays",
]
