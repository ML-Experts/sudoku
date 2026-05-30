from __future__ import annotations

import numpy as np

from sudoku_board_threshold_notebook_report_models import (
    FrameDebugArtifacts,
    WarpDebugArtifacts,
)
from sudoku_board_threshold_warp import (
    aligned_frame_corners,
    build_corner_overlay,
    warp_image_from_corners,
)


def run_warp_debug_analysis(
    display_bgr: np.ndarray,
    frame_debug: FrameDebugArtifacts,
    config,
) -> WarpDebugArtifacts:
    if not frame_debug.selected_frames:
        return WarpDebugArtifacts(
            selected_frame=None,
            aligned_corners=None,
            aligned_corner_overlay=None,
            aligned_warp=None,
        )

    selected_frame = frame_debug.selected_frames[0]
    aligned_corners = aligned_frame_corners(selected_frame)
    aligned_corner_overlay = build_corner_overlay(
        display_bgr,
        aligned_corners,
        color_bgr=(0, 200, 0),
        label_prefix="A",
        thickness=max(config.line_overlay_thickness, 2),
    )
    aligned_warp = warp_image_from_corners(
        display_bgr,
        aligned_corners,
        config.warp_output_size,
        config.warp_output_padding_pixels,
    )

    return WarpDebugArtifacts(
        selected_frame=selected_frame,
        aligned_corners=aligned_corners,
        aligned_corner_overlay=aligned_corner_overlay,
        aligned_warp=aligned_warp,
    )


def _format_corner(point: tuple[float, float]) -> str:
    return f"({point[0]:.1f}, {point[1]:.1f})"


def _describe_corner_set(label: str, corners) -> list[str]:
    corner_labels = ("TL", "TR", "BR", "BL")
    lines = [f"{label} corners:"]
    for corner_label, point in zip(corner_labels, corners):
        lines.append(f"  {corner_label}: {_format_corner(point)}")
    return lines


def describe_warp_debug_artifacts(
    warp_debug: WarpDebugArtifacts,
    config,
) -> list[str]:
    lines = [
        "",
        "Warp from the highest-priority selected frame:",
    ]
    if warp_debug.selected_frame is None or warp_debug.aligned_corners is None:
        lines.append("No selected frame, so warp was skipped.")
        return lines

    lines.append(
        "Warp output: "
        f"{config.warp_output_size}x{config.warp_output_size}px, "
        f"padding={config.warp_output_padding_pixels}px"
    )
    lines.extend(
        ("", *_describe_corner_set("Frame corners used for warp", warp_debug.aligned_corners))
    )
    return lines


def build_warp_debug_plot_items(
    frame_debug: FrameDebugArtifacts,
    warp_debug: WarpDebugArtifacts,
) -> list[tuple[str, np.ndarray, bool]]:
    plot_items = [
        (
            "selected frame from mutual endpoint corners on source",
            frame_debug.source_frame_overlay,
            True,
        )
    ]
    if warp_debug.aligned_corner_overlay is not None:
        plot_items.append(
            (
                "frame corners used for warp on source",
                warp_debug.aligned_corner_overlay,
                True,
            )
        )
    if warp_debug.aligned_warp is not None:
        plot_items.append(
            (
                "warp to square from frame corners",
                warp_debug.aligned_warp,
                True,
            )
        )
    return plot_items


__all__ = [
    "build_warp_debug_plot_items",
    "describe_warp_debug_artifacts",
    "run_warp_debug_analysis",
]
