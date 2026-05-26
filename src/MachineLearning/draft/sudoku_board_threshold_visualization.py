from __future__ import annotations

import cv2
import numpy as np

from sudoku_board_threshold_models import ExperimentConfig, LineFamilyResult


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


def build_merged_line_overlays(
    source_bgr: np.ndarray,
    binary_image: np.ndarray,
    line_family_result: LineFamilyResult,
    config: ExperimentConfig,
) -> tuple[np.ndarray, np.ndarray]:
    binary_overlay = cv2.cvtColor(binary_image, cv2.COLOR_GRAY2BGR)
    source_overlay = source_bgr.copy()

    for overlay in (binary_overlay, source_overlay):
        for line_index, merged_line in enumerate(line_family_result.horizontal_merged_lines):
            cv2.line(
                overlay,
                merged_line.start,
                merged_line.end,
                config.horizontal_family_color_bgr,
                max(config.line_overlay_thickness + 1, 2),
                cv2.LINE_AA,
            )
            cv2.putText(
                overlay,
                (
                    f"H{line_index} L={merged_line.span_length:.0f} "
                    f"T={merged_line.touching_line_count}"
                ),
                merged_line.start,
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                config.horizontal_family_color_bgr,
                1,
                cv2.LINE_AA,
            )
        for line_index, merged_line in enumerate(line_family_result.vertical_merged_lines):
            cv2.line(
                overlay,
                merged_line.start,
                merged_line.end,
                config.vertical_family_color_bgr,
                max(config.line_overlay_thickness + 1, 2),
                cv2.LINE_AA,
            )
            cv2.putText(
                overlay,
                (
                    f"V{line_index} L={merged_line.span_length:.0f} "
                    f"T={merged_line.touching_line_count}"
                ),
                merged_line.start,
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                config.vertical_family_color_bgr,
                1,
                cv2.LINE_AA,
            )

    return binary_overlay, source_overlay


__all__ = [
    "build_line_family_overlays",
    "build_merged_line_overlays",
]
