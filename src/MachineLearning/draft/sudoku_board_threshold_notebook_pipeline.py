from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np

if TYPE_CHECKING:
    from sudoku_board_threshold_notebook_bootstrap import ThresholdNotebookApi


@dataclass(frozen=True)
class ActiveImageSelection:
    active_image_path: Path
    dataset_images: list[Path]
    preview_lines: tuple[str, ...]


@dataclass(frozen=True)
class ThresholdPreprocessResult:
    source_bgr: np.ndarray
    display_bgr: np.ndarray
    gray_image: np.ndarray
    denoise_variants: dict[str, np.ndarray]
    selected_denoise_name: str
    selected_denoise_image: np.ndarray
    threshold_variants: dict[str, np.ndarray]
    selected_threshold_name: str
    selected_binary: np.ndarray
    min_component_area_px: int
    cleanup_variants: dict[str, np.ndarray]
    selected_cleanup_name: str
    selected_clean_binary: np.ndarray
    repair_variants: dict[str, np.ndarray]
    selected_repair_name: str
    selected_repaired_binary: np.ndarray


def configure_manual_image_path(
    config,
    image_path_input: str,
    repo_root: Path,
) -> str:
    if image_path_input.strip():
        typed_image_path = Path(image_path_input).expanduser()
        if not typed_image_path.is_absolute():
            typed_image_path = (repo_root / typed_image_path).resolve()

        config.image_path = typed_image_path
        return f"Manual image path enabled: {config.image_path}"

    config.image_path = None
    return (
        "Manual image path is empty. Notebook will use dataset_root + "
        "selected_dataset_index."
    )


def resolve_active_image_selection(
    config,
    notebook_api: "ThresholdNotebookApi",
) -> ActiveImageSelection:
    active_image_path, dataset_images = notebook_api.resolve_active_image_path(config)
    preview_lines = [
        f"Found {len(dataset_images)} image(s) under dataset root."
    ]

    preview_paths = dataset_images[: config.preview_limit]
    for index, path in enumerate(preview_paths):
        marker = "<-- selected" if path == active_image_path else ""
        display_path = notebook_api.path_for_display(path, config.dataset_root)
        preview_lines.append(f"[{index:02d}] {display_path} {marker}".rstrip())

    if len(dataset_images) > config.preview_limit:
        preview_lines.append(
            f"... and {len(dataset_images) - config.preview_limit} more"
        )

    preview_lines.extend(("", f"Active image: {active_image_path}"))

    return ActiveImageSelection(
        active_image_path=active_image_path,
        dataset_images=dataset_images,
        preview_lines=tuple(preview_lines),
    )


def _resolve_selected_variant_name(
    requested_name: str | None,
    variants: dict[str, np.ndarray],
    stage_name: str,
) -> str:
    if not variants:
        raise ValueError(f"No variants available for stage: {stage_name}")
    if requested_name is None:
        return next(iter(variants))
    if requested_name not in variants:
        available_names = ", ".join(variants)
        raise KeyError(
            f"Unknown {stage_name} variant '{requested_name}'. "
            f"Available variants: {available_names}"
        )
    return requested_name


def run_threshold_preprocess_pipeline(
    active_image_path: Path,
    config,
    notebook_api: "ThresholdNotebookApi",
) -> ThresholdPreprocessResult:
    source_bgr = notebook_api.load_image_bgr(active_image_path)
    display_bgr = notebook_api.resize_for_display(source_bgr, config.max_display_size)
    gray_image = cv2.cvtColor(display_bgr, cv2.COLOR_BGR2GRAY)

    denoise_variants = notebook_api.build_denoise_variants(gray_image, config)
    selected_denoise_name = _resolve_selected_variant_name(
        config.selected_denoise_variant,
        denoise_variants,
        "denoise",
    )
    selected_denoise_image = denoise_variants[selected_denoise_name]

    threshold_variants = notebook_api.build_threshold_variants(
        selected_denoise_image,
        config,
    )
    selected_threshold_name = _resolve_selected_variant_name(
        config.selected_threshold_name,
        threshold_variants,
        "threshold",
    )
    selected_binary = threshold_variants[selected_threshold_name]

    min_component_area_px, cleanup_variants = notebook_api.build_cleanup_variants(
        selected_binary,
        config,
    )
    selected_cleanup_name = _resolve_selected_variant_name(
        config.selected_cleanup_variant,
        cleanup_variants,
        "cleanup",
    )
    selected_clean_binary = cleanup_variants[selected_cleanup_name]

    repair_variants = notebook_api.build_repair_variants(selected_clean_binary, config)
    selected_repair_name = _resolve_selected_variant_name(
        config.selected_repair_variant,
        repair_variants,
        "repair",
    )
    selected_repaired_binary = repair_variants[selected_repair_name]

    return ThresholdPreprocessResult(
        source_bgr=source_bgr,
        display_bgr=display_bgr,
        gray_image=gray_image,
        denoise_variants=denoise_variants,
        selected_denoise_name=selected_denoise_name,
        selected_denoise_image=selected_denoise_image,
        threshold_variants=threshold_variants,
        selected_threshold_name=selected_threshold_name,
        selected_binary=selected_binary,
        min_component_area_px=min_component_area_px,
        cleanup_variants=cleanup_variants,
        selected_cleanup_name=selected_cleanup_name,
        selected_clean_binary=selected_clean_binary,
        repair_variants=repair_variants,
        selected_repair_name=selected_repair_name,
        selected_repaired_binary=selected_repaired_binary,
    )


def describe_loaded_image(preprocess_result: ThresholdPreprocessResult) -> list[str]:
    return [
        f"Original shape: {preprocess_result.source_bgr.shape}",
        f"Display shape:  {preprocess_result.display_bgr.shape}",
    ]


def describe_denoise_stage(preprocess_result: ThresholdPreprocessResult) -> list[str]:
    lines = ["Available denoise variants:"]
    for variant_name in preprocess_result.denoise_variants:
        marker = (
            "<-- selected"
            if variant_name == preprocess_result.selected_denoise_name
            else ""
        )
        lines.append(f"- {variant_name} {marker}".rstrip())
    return lines


def describe_threshold_stage(preprocess_result: ThresholdPreprocessResult, config) -> list[str]:
    lines = [
        f"Adaptive method: {config.adaptive_method_name}",
        f"Selected denoise variant: {preprocess_result.selected_denoise_name}",
        "",
        "Available threshold variants:",
    ]
    for variant_name in preprocess_result.threshold_variants:
        marker = (
            "<-- selected"
            if variant_name == preprocess_result.selected_threshold_name
            else ""
        )
        lines.append(f"- {variant_name} {marker}".rstrip())
    return lines


def describe_cleanup_stage(preprocess_result: ThresholdPreprocessResult) -> list[str]:
    return [
        "",
        f"Selected cleanup variant: {preprocess_result.selected_cleanup_name}",
        f"Selected repair variant: {preprocess_result.selected_repair_name}",
        (
            "Connected components min area px: "
            f"{preprocess_result.min_component_area_px}"
        ),
        "Available cleanup variants: "
        + ", ".join(preprocess_result.cleanup_variants),
        "Available repair variants: " + ", ".join(preprocess_result.repair_variants),
        "",
        "Notebook continues with line-family visualization below.",
        (
            "Next blocks should start from `selected_repaired_binary` and its "
            "detected line families."
        ),
    ]


__all__ = [
    "ActiveImageSelection",
    "ThresholdPreprocessResult",
    "configure_manual_image_path",
    "describe_cleanup_stage",
    "describe_denoise_stage",
    "describe_loaded_image",
    "describe_threshold_stage",
    "resolve_active_image_selection",
    "run_threshold_preprocess_pipeline",
]
