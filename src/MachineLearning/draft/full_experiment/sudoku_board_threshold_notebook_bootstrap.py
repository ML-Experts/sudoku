from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass
from pathlib import Path


MODULE_RELOAD_ORDER = (
    "sudoku_board_threshold_models",
    "sudoku_board_threshold_paths",
    "sudoku_board_threshold_display",
    "sudoku_board_threshold_binary",
    "sudoku_board_threshold_line_geometry",
    "sudoku_board_threshold_line_merge",
    "sudoku_board_threshold_line_touch",
    "sudoku_board_threshold_line_families",
    "sudoku_board_threshold_line_bridge",
    "sudoku_board_threshold_line_detection",
    "sudoku_board_threshold_frame",
    "sudoku_board_threshold_warp",
    "sudoku_board_threshold_lines",
    "sudoku_board_threshold_visualization",
    "sudoku_board_threshold_helpers",
)


@dataclass(frozen=True)
class ThresholdNotebookApi:
    ExperimentConfig: object
    REPO_ROOT: Path
    DRAFT_DIR: Path
    resolve_active_image_path: object
    path_for_display: object
    load_image_bgr: object
    resize_for_display: object
    plot_named_images: object
    build_denoise_variants: object
    build_threshold_variants: object
    build_cleanup_variants: object
    build_repair_variants: object
    detect_line_families: object
    build_line_family_overlays: object
    build_bridged_line_family_overlays: object
    build_merged_line_overlays: object
    build_merged_line_vertex_overlays: object
    resolve_merged_line_vertices: object
    line_vertex_name: object
    find_line_frames: object
    build_line_frame_overlays: object


def ensure_draft_dir_on_sys_path() -> Path:
    draft_dir = Path(__file__).resolve().parent
    draft_dir_str = str(draft_dir)
    if draft_dir_str not in sys.path:
        sys.path.insert(0, draft_dir_str)
    return draft_dir


def load_threshold_notebook_api() -> ThresholdNotebookApi:
    ensure_draft_dir_on_sys_path()
    modules = {
        module_name: importlib.import_module(module_name)
        for module_name in MODULE_RELOAD_ORDER
    }
    for module_name in MODULE_RELOAD_ORDER:
        modules[module_name] = importlib.reload(modules[module_name])

    threshold_helpers = modules["sudoku_board_threshold_helpers"]

    return ThresholdNotebookApi(
        ExperimentConfig=threshold_helpers.ExperimentConfig,
        REPO_ROOT=threshold_helpers.REPO_ROOT,
        DRAFT_DIR=threshold_helpers.DRAFT_DIR,
        resolve_active_image_path=threshold_helpers.resolve_active_image_path,
        path_for_display=threshold_helpers.path_for_display,
        load_image_bgr=threshold_helpers.load_image_bgr,
        resize_for_display=threshold_helpers.resize_for_display,
        plot_named_images=threshold_helpers.plot_named_images,
        build_denoise_variants=threshold_helpers.build_denoise_variants,
        build_threshold_variants=threshold_helpers.build_threshold_variants,
        build_cleanup_variants=threshold_helpers.build_cleanup_variants,
        build_repair_variants=threshold_helpers.build_repair_variants,
        detect_line_families=threshold_helpers.detect_line_families,
        build_line_family_overlays=threshold_helpers.build_line_family_overlays,
        build_bridged_line_family_overlays=(
            threshold_helpers.build_bridged_line_family_overlays
        ),
        build_merged_line_overlays=threshold_helpers.build_merged_line_overlays,
        build_merged_line_vertex_overlays=(
            threshold_helpers.build_merged_line_vertex_overlays
        ),
        resolve_merged_line_vertices=threshold_helpers.resolve_merged_line_vertices,
        line_vertex_name=threshold_helpers.line_vertex_name,
        find_line_frames=threshold_helpers.find_line_frames,
        build_line_frame_overlays=threshold_helpers.build_line_frame_overlays,
    )


__all__ = [
    "MODULE_RELOAD_ORDER",
    "ThresholdNotebookApi",
    "ensure_draft_dir_on_sys_path",
    "load_threshold_notebook_api",
]
