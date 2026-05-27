from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from sudoku_board_threshold_notebook_report_models import (
    FrameDebugArtifacts,
    LineDebugArtifacts,
)

if TYPE_CHECKING:
    from sudoku_board_threshold_notebook_bootstrap import ThresholdNotebookApi


def run_frame_debug_analysis(
    display_bgr: np.ndarray,
    selected_repaired_binary: np.ndarray,
    line_debug: LineDebugArtifacts,
    config,
    notebook_api: "ThresholdNotebookApi",
) -> FrameDebugArtifacts:
    frame_detection_result = notebook_api.find_line_frames(
        line_debug.line_family_result,
        config,
    )
    selected_frames = frame_detection_result.selected_frames
    binary_frame_overlay, source_frame_overlay = notebook_api.build_line_frame_overlays(
        display_bgr,
        selected_repaired_binary,
        selected_frames,
        config,
    )
    return FrameDebugArtifacts(
        frame_detection_result=frame_detection_result,
        selected_frames=selected_frames,
        binary_frame_overlay=binary_frame_overlay,
        source_frame_overlay=source_frame_overlay,
    )


def describe_frame_debug_artifacts(frame_debug: FrameDebugArtifacts) -> list[str]:
    lines = [
        "",
        (
            "Detected frame candidates: "
            f"all={len(frame_debug.frame_detection_result.all_frames)}, "
            f"selected={len(frame_debug.selected_frames)}"
        ),
        "",
        "Selected frames built from mutual endpoint corners:",
    ]
    for frame_index, frame in enumerate(frame_debug.selected_frames):
        lines.append(
            f"  F{frame_index}: H{frame.top_line_index}-H{frame.bottom_line_index} x "
            f"V{frame.left_line_index}-V{frame.right_line_index}, "
            f"area={frame.area_px:.1f}px, perimeter={frame.perimeter_px:.1f}px, "
            f"H_count={frame.horizontal_line_count}, V_count={frame.vertical_line_count}, "
            f"inner_H={frame.inner_horizontal_line_count}, "
            f"inner_V={frame.inner_vertical_line_count}, "
            f"priority={frame.priority_score:.1f}"
        )
        lines.append(
            "    TL: "
            f"H{frame.top_line_index} <-> V{frame.left_line_index} = "
            f"{frame.top_left_connection.aligned_point}"
        )
        lines.append(
            "    TR: "
            f"H{frame.top_line_index} <-> V{frame.right_line_index} = "
            f"{frame.top_right_connection.aligned_point}"
        )
        lines.append(
            "    BR: "
            f"H{frame.bottom_line_index} <-> V{frame.right_line_index} = "
            f"{frame.bottom_right_connection.aligned_point}"
        )
        lines.append(
            "    BL: "
            f"H{frame.bottom_line_index} <-> V{frame.left_line_index} = "
            f"{frame.bottom_left_connection.aligned_point}"
        )
    if not frame_debug.selected_frames:
        lines.append("  -")
    return lines


def build_frame_debug_plot_items(
    frame_debug: FrameDebugArtifacts,
    line_debug: LineDebugArtifacts,
) -> list[tuple[str, np.ndarray, bool]]:
    return [
        (
            "kept logical groups after refresh on repaired binary",
            line_debug.binary_merged_overlay,
            True,
        ),
        (
            "selected frames from mutual endpoint corners on repaired binary",
            frame_debug.binary_frame_overlay,
            True,
        ),
        (
            "kept logical groups after refresh on source",
            line_debug.source_merged_overlay,
            True,
        ),
        (
            "selected frames from mutual endpoint corners on source",
            frame_debug.source_frame_overlay,
            True,
        ),
    ]


__all__ = [
    "build_frame_debug_plot_items",
    "describe_frame_debug_artifacts",
    "run_frame_debug_analysis",
]
