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
class RawLineFamilyArtifacts:
    source_bgr: np.ndarray
    display_bgr: np.ndarray
    gray_image: np.ndarray
    selected_denoise_name: str
    selected_denoise_image: np.ndarray
    selected_threshold_name: str
    selected_binary: np.ndarray
    min_component_area_px: int
    selected_cleanup_name: str
    selected_clean_binary: np.ndarray
    selected_repair_name: str
    selected_repaired_binary: np.ndarray
    line_family_result: object
    binary_family_overlay: np.ndarray
    source_family_overlay: np.ndarray


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


def _select_variant(
    requested_name: str | None,
    variants: dict[str, np.ndarray],
    stage_name: str,
) -> tuple[str, np.ndarray]:
    if not variants:
        raise ValueError(f"No variants available for stage: {stage_name}")

    if requested_name is None:
        selected_name = next(iter(variants))
        return selected_name, variants[selected_name]

    if requested_name not in variants:
        available_names = ", ".join(variants)
        raise KeyError(
            f"Unknown {stage_name} variant '{requested_name}'. "
            f"Available variants: {available_names}"
        )

    return requested_name, variants[requested_name]


def run_raw_line_family_pipeline(
    active_image_path: Path,
    config,
    notebook_api: "ThresholdNotebookApi",
) -> RawLineFamilyArtifacts:
    source_bgr = notebook_api.load_image_bgr(active_image_path)
    display_bgr = notebook_api.resize_for_display(source_bgr, config.max_display_size)
    gray_image = cv2.cvtColor(display_bgr, cv2.COLOR_BGR2GRAY)

    denoise_variants = notebook_api.build_denoise_variants(gray_image, config)
    selected_denoise_name, selected_denoise_image = _select_variant(
        config.selected_denoise_variant,
        denoise_variants,
        "denoise",
    )

    threshold_variants = notebook_api.build_threshold_variants(
        selected_denoise_image,
        config,
    )
    selected_threshold_name, selected_binary = _select_variant(
        config.selected_threshold_name,
        threshold_variants,
        "threshold",
    )

    min_component_area_px, cleanup_variants = notebook_api.build_cleanup_variants(
        selected_binary,
        config,
    )
    selected_cleanup_name, selected_clean_binary = _select_variant(
        config.selected_cleanup_variant,
        cleanup_variants,
        "cleanup",
    )

    repair_variants = notebook_api.build_repair_variants(selected_clean_binary, config)
    selected_repair_name, selected_repaired_binary = _select_variant(
        config.selected_repair_variant,
        repair_variants,
        "repair",
    )

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

    return RawLineFamilyArtifacts(
        source_bgr=source_bgr,
        display_bgr=display_bgr,
        gray_image=gray_image,
        selected_denoise_name=selected_denoise_name,
        selected_denoise_image=selected_denoise_image,
        selected_threshold_name=selected_threshold_name,
        selected_binary=selected_binary,
        min_component_area_px=min_component_area_px,
        selected_cleanup_name=selected_cleanup_name,
        selected_clean_binary=selected_clean_binary,
        selected_repair_name=selected_repair_name,
        selected_repaired_binary=selected_repaired_binary,
        line_family_result=line_family_result,
        binary_family_overlay=binary_family_overlay,
        source_family_overlay=source_family_overlay,
    )


def describe_raw_line_family_artifacts(
    artifacts: RawLineFamilyArtifacts,
) -> list[str]:
    line_family_result = artifacts.line_family_result
    return [
        f"Original shape: {artifacts.source_bgr.shape}",
        f"Display shape:  {artifacts.display_bgr.shape}",
        f"Selected denoise: {artifacts.selected_denoise_name}",
        f"Selected threshold: {artifacts.selected_threshold_name}",
        f"Selected cleanup: {artifacts.selected_cleanup_name}",
        f"Selected repair: {artifacts.selected_repair_name}",
        f"Connected components min area px: {artifacts.min_component_area_px}",
        f"Raw Hough segments: {line_family_result.raw_segment_count}",
        f"Horizontal raw segments: {len(line_family_result.horizontal_segments)}",
        f"Vertical raw segments: {len(line_family_result.vertical_segments)}",
        (
            "Horizontal family angle: "
            f"{line_family_result.horizontal_angle_degrees}"
        ),
        f"Vertical family angle: {line_family_result.vertical_angle_degrees}",
        "",
        "Notebook stops at raw line families on repaired binary.",
    ]


def build_raw_line_family_plot_items(
    artifacts: RawLineFamilyArtifacts,
) -> list[tuple[str, np.ndarray, bool]]:
    return [
        ("source", artifacts.display_bgr, True),
        ("gray", artifacts.gray_image, False),
        (
            f"denoise: {artifacts.selected_denoise_name}",
            artifacts.selected_denoise_image,
            False,
        ),
        (
            f"binary: {artifacts.selected_threshold_name}",
            artifacts.selected_binary,
            False,
        ),
        (
            f"cleanup: {artifacts.selected_cleanup_name}",
            artifacts.selected_clean_binary,
            False,
        ),
        (
            f"repair: {artifacts.selected_repair_name}",
            artifacts.selected_repaired_binary,
            False,
        ),
        (
            "raw line families on repaired binary",
            artifacts.binary_family_overlay,
            True,
        ),
        ("raw line families on source", artifacts.source_family_overlay, True),
    ]


__all__ = [
    "ActiveImageSelection",
    "RawLineFamilyArtifacts",
    "build_raw_line_family_plot_items",
    "configure_manual_image_path",
    "describe_raw_line_family_artifacts",
    "resolve_active_image_selection",
    "run_raw_line_family_pipeline",
]
