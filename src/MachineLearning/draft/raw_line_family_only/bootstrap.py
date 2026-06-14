from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass
from pathlib import Path


MODULE_RELOAD_ORDER = (
    "models",
    "paths",
    "display",
    "binary",
    "geometry",
    "line_families",
    "logical_line_types",
    "logical_line_segment_geometry",
    "intersection_models",
    "raw_segment_grouping",
    "logical_line_core",
    "logical_line_cross_axis_continuity",
    "logical_line_full_containment",
    "logical_line_vertex_containment_merge",
    "logical_line_search",
    "logical_line_merging",
    "logical_line_connection_types",
    "logical_line_connection_candidates",
    "logical_line_connection_execution",
    "logical_line_connections",
    "logical_line_intersections",
    "logical_lines",
    "detection",
    "visualization",
)


MODULE_RELOAD_PREFIXES = (
    "logical_line_connection_",
    "logical_line_search_",
    "visualization_",
)


@dataclass(frozen=True)
class Api:
    ExperimentConfig: object
    REPO_ROOT: Path
    resolve_active_image_path: object
    path_for_display: object
    load_image_bgr: object
    resize_for_display: object
    plot_named_images: object
    apply_median_denoise: object
    apply_gaussian_threshold: object
    apply_soft_component_cleanup: object
    apply_directional_close_repair: object
    detect_line_families: object
    build_line_family_overlays: object
    build_logical_line_intersection_overlays: object
    build_containment_prune_board: object
    build_containment_prune_overlays: object
    build_vertex_containment_merge_board: object
    build_vertex_containment_merge_overlays: object
    build_long_segment_candidate_board: object
    build_long_segment_candidate_overlays: object
    build_logical_line_overlays: object
    build_post_merge_logical_line_overlays: object
    build_post_connection_logical_line_overlays: object
    build_raw_segment_group_board: object
    build_raw_segment_group_overlays: object
    build_tolerance_rectangle_overlays: object


def _ensure_variant_dir_on_sys_path() -> Path:
    variant_dir = Path(__file__).resolve().parent
    search_paths = [
        variant_dir / "visualization",
        variant_dir / "pipeline",
        variant_dir,
    ]

    for search_path in reversed(search_paths):
        search_path_str = str(search_path)
        if search_path_str in sys.path:
            sys.path.remove(search_path_str)
        sys.path.insert(0, search_path_str)

    return variant_dir


_ensure_variant_dir_on_sys_path()


def load_api() -> Api:
    _ensure_variant_dir_on_sys_path()
    importlib.invalidate_caches()
    for module_name in list(sys.modules):
        if any(
            module_name.startswith(module_prefix)
            for module_prefix in MODULE_RELOAD_PREFIXES
        ):
            sys.modules.pop(module_name, None)
    for module_name in reversed(MODULE_RELOAD_ORDER):
        sys.modules.pop(module_name, None)

    modules = {
        module_name: importlib.import_module(module_name)
        for module_name in MODULE_RELOAD_ORDER
    }

    models_module = modules["models"]
    paths_module = modules["paths"]
    display_module = modules["display"]
    binary_module = modules["binary"]
    detection = modules["detection"]
    visualization = modules["visualization"]

    return Api(
        ExperimentConfig=models_module.ExperimentConfig,
        REPO_ROOT=paths_module.REPO_ROOT,
        resolve_active_image_path=paths_module.resolve_active_image_path,
        path_for_display=paths_module.path_for_display,
        load_image_bgr=display_module.load_image_bgr,
        resize_for_display=display_module.resize_for_display,
        plot_named_images=display_module.plot_named_images,
        apply_median_denoise=binary_module.apply_median_denoise,
        apply_gaussian_threshold=binary_module.apply_gaussian_threshold,
        apply_soft_component_cleanup=binary_module.apply_soft_component_cleanup,
        apply_directional_close_repair=binary_module.apply_directional_close_repair,
        detect_line_families=detection.detect_line_families,
        build_line_family_overlays=visualization.build_line_family_overlays,
        build_logical_line_intersection_overlays=(
            visualization.build_logical_line_intersection_overlays
        ),
        build_containment_prune_board=visualization.build_containment_prune_board,
        build_containment_prune_overlays=(
            visualization.build_containment_prune_overlays
        ),
        build_vertex_containment_merge_board=(
            visualization.build_vertex_containment_merge_board
        ),
        build_vertex_containment_merge_overlays=(
            visualization.build_vertex_containment_merge_overlays
        ),
        build_long_segment_candidate_board=(
            visualization.build_long_segment_candidate_board
        ),
        build_long_segment_candidate_overlays=(
            visualization.build_long_segment_candidate_overlays
        ),
        build_logical_line_overlays=visualization.build_logical_line_overlays,
        build_post_merge_logical_line_overlays=(
            visualization.build_post_merge_logical_line_overlays
        ),
        build_post_connection_logical_line_overlays=(
            visualization.build_post_connection_logical_line_overlays
        ),
        build_raw_segment_group_board=visualization.build_raw_segment_group_board,
        build_raw_segment_group_overlays=(
            visualization.build_raw_segment_group_overlays
        ),
        build_tolerance_rectangle_overlays=(
            visualization.build_tolerance_rectangle_overlays
        ),
    )


__all__ = [
    "MODULE_RELOAD_ORDER",
    "Api",
    "load_api",
]
