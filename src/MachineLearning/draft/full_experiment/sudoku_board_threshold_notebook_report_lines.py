from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from sudoku_board_threshold_notebook_report_line_descriptions import (
    describe_endpoint_connections,
    describe_line_debug_artifacts,
)
from sudoku_board_threshold_notebook_report_models import LineDebugArtifacts

if TYPE_CHECKING:
    from sudoku_board_threshold_notebook_bootstrap import ThresholdNotebookApi


def run_line_debug_analysis(
    display_bgr: np.ndarray,
    selected_repaired_binary: np.ndarray,
    config,
    notebook_api: "ThresholdNotebookApi",
) -> LineDebugArtifacts:
    line_family_result = notebook_api.detect_line_families(
        selected_repaired_binary,
        config,
    )
    binary_family_overlay, source_family_overlay = (
        notebook_api.build_line_family_overlays(
            display_bgr,
            selected_repaired_binary,
            line_family_result,
            config,
        )
    )
    binary_logical_overlay, source_logical_overlay = (
        notebook_api.build_bridged_line_family_overlays(
            display_bgr,
            selected_repaired_binary,
            line_family_result,
            config,
        )
    )
    binary_merged_overlay, source_merged_overlay = (
        notebook_api.build_merged_line_overlays(
            display_bgr,
            selected_repaired_binary,
            line_family_result,
            config,
        )
    )
    binary_vertex_overlay, source_vertex_overlay = (
        notebook_api.build_merged_line_vertex_overlays(
            display_bgr,
            selected_repaired_binary,
            line_family_result,
            config,
        )
    )
    return LineDebugArtifacts(
        line_family_result=line_family_result,
        selected_repaired_binary=selected_repaired_binary,
        binary_family_overlay=binary_family_overlay,
        source_family_overlay=source_family_overlay,
        binary_logical_overlay=binary_logical_overlay,
        source_logical_overlay=source_logical_overlay,
        binary_merged_overlay=binary_merged_overlay,
        source_merged_overlay=source_merged_overlay,
        binary_vertex_overlay=binary_vertex_overlay,
        source_vertex_overlay=source_vertex_overlay,
    )

def build_line_debug_plot_items(
    line_debug: LineDebugArtifacts,
    selected_repair_name: str,
    *,
    include_vertices: bool,
) -> list[tuple[str, np.ndarray, bool]]:
    plot_items = [
        (
            f"selected_repair: {selected_repair_name}",
            line_debug.selected_repaired_binary,
            False,
        ),
        ("raw line families on repaired binary", line_debug.binary_family_overlay, True),
        (
            "logical lines + bridge repair before touch filter on repaired binary",
            line_debug.binary_logical_overlay,
            True,
        ),
        (
            "kept logical groups after refresh on repaired binary",
            line_debug.binary_merged_overlay,
            True,
        ),
    ]
    if include_vertices:
        plot_items.append(
            (
                "logical lines + aligned vertices on repaired binary",
                line_debug.binary_vertex_overlay,
                True,
            )
        )
    plot_items.extend(
        [
            ("raw line families on source", line_debug.source_family_overlay, True),
            (
                "logical lines + bridge repair before touch filter on source",
                line_debug.source_logical_overlay,
                True,
            ),
            (
                "kept logical groups after refresh on source",
                line_debug.source_merged_overlay,
                True,
            ),
        ]
    )
    if include_vertices:
        plot_items.append(
            (
                "logical lines + aligned vertices on source",
                line_debug.source_vertex_overlay,
                True,
            )
        )
    return plot_items


__all__ = [
    "build_line_debug_plot_items",
    "describe_endpoint_connections",
    "describe_line_debug_artifacts",
    "run_line_debug_analysis",
]
