from __future__ import annotations

import importlib

import sudoku_board_threshold_notebook_report_frames as _frame_report
import sudoku_board_threshold_notebook_report_line_descriptions as _line_descriptions
import sudoku_board_threshold_notebook_report_lines as _line_report
import sudoku_board_threshold_notebook_report_models as _report_models
import sudoku_board_threshold_notebook_report_warp as _warp_report

_report_models = importlib.reload(_report_models)
_line_descriptions = importlib.reload(_line_descriptions)
_line_report = importlib.reload(_line_report)
_frame_report = importlib.reload(_frame_report)
_warp_report = importlib.reload(_warp_report)

FrameDebugArtifacts = _report_models.FrameDebugArtifacts
LineDebugArtifacts = _report_models.LineDebugArtifacts
WarpDebugArtifacts = _report_models.WarpDebugArtifacts

build_frame_debug_plot_items = _frame_report.build_frame_debug_plot_items
describe_frame_debug_artifacts = _frame_report.describe_frame_debug_artifacts
run_frame_debug_analysis = _frame_report.run_frame_debug_analysis

build_line_debug_plot_items = _line_report.build_line_debug_plot_items
describe_endpoint_connections = _line_report.describe_endpoint_connections
describe_line_debug_artifacts = _line_report.describe_line_debug_artifacts
run_line_debug_analysis = _line_report.run_line_debug_analysis

build_warp_debug_plot_items = _warp_report.build_warp_debug_plot_items
describe_warp_debug_artifacts = _warp_report.describe_warp_debug_artifacts
run_warp_debug_analysis = _warp_report.run_warp_debug_analysis


__all__ = [
    "FrameDebugArtifacts",
    "LineDebugArtifacts",
    "WarpDebugArtifacts",
    "build_frame_debug_plot_items",
    "build_line_debug_plot_items",
    "build_warp_debug_plot_items",
    "describe_endpoint_connections",
    "describe_frame_debug_artifacts",
    "describe_line_debug_artifacts",
    "describe_warp_debug_artifacts",
    "run_frame_debug_analysis",
    "run_line_debug_analysis",
    "run_warp_debug_analysis",
]
