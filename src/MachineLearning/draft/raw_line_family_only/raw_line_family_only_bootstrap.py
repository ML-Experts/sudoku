from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass
from pathlib import Path


MODULE_RELOAD_ORDER = (
    "raw_line_family_only_models",
    "raw_line_family_only_paths",
    "raw_line_family_only_display",
    "raw_line_family_only_binary",
    "raw_line_family_only_geometry",
    "raw_line_family_only_line_families",
    "raw_line_family_only_logical_lines",
    "raw_line_family_only_detection",
    "raw_line_family_only_visualization",
)


@dataclass(frozen=True)
class RawLineFamilyOnlyApi:
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
    build_logical_line_overlays: object


def _ensure_variant_dir_on_sys_path() -> Path:
    variant_dir = Path(__file__).resolve().parent

    variant_dir_str = str(variant_dir)
    if variant_dir_str not in sys.path:
        sys.path.insert(0, variant_dir_str)

    return variant_dir


def load_raw_line_family_only_api() -> RawLineFamilyOnlyApi:
    _ensure_variant_dir_on_sys_path()
    importlib.invalidate_caches()
    for module_name in reversed(MODULE_RELOAD_ORDER):
        sys.modules.pop(module_name, None)

    modules = {
        module_name: importlib.import_module(module_name)
        for module_name in MODULE_RELOAD_ORDER
    }

    models_module = modules["raw_line_family_only_models"]
    paths_module = modules["raw_line_family_only_paths"]
    display_module = modules["raw_line_family_only_display"]
    binary_module = modules["raw_line_family_only_binary"]
    detection = modules["raw_line_family_only_detection"]
    visualization = modules["raw_line_family_only_visualization"]

    return RawLineFamilyOnlyApi(
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
        build_logical_line_overlays=visualization.build_logical_line_overlays,
    )


__all__ = [
    "MODULE_RELOAD_ORDER",
    "RawLineFamilyOnlyApi",
    "load_raw_line_family_only_api",
]
