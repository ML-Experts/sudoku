from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np

from raw_line_family_only_detection import RawLineFamilyResult
from raw_line_family_only_models import SegmentOrigin

if TYPE_CHECKING:
    from raw_line_family_only_bootstrap import RawLineFamilyOnlyApi


@dataclass(frozen=True)
class ActiveImageSelection:
    active_image_path: Path
    preview_lines: tuple[str, ...]


@dataclass(frozen=True)
class RawLineFamilyArtifacts:
    source_bgr: np.ndarray
    display_bgr: np.ndarray
    gray_image: np.ndarray
    denoise_name: str
    denoised_image: np.ndarray
    threshold_name: str
    binary_image: np.ndarray
    min_component_area_px: int
    cleanup_name: str
    clean_binary: np.ndarray
    repair_name: str
    repaired_binary: np.ndarray
    line_family_result: RawLineFamilyResult
    binary_family_overlay: np.ndarray
    source_family_overlay: np.ndarray
    binary_logical_line_overlay: np.ndarray
    source_logical_line_overlay: np.ndarray
    binary_tolerance_rectangle_overlay: np.ndarray
    source_tolerance_rectangle_overlay: np.ndarray


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
    notebook_api: "RawLineFamilyOnlyApi",
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
        preview_lines=tuple(preview_lines),
    )


def run_raw_line_family_pipeline(
    active_image_path: Path,
    config,
    notebook_api: "RawLineFamilyOnlyApi",
) -> RawLineFamilyArtifacts:
    source_bgr = notebook_api.load_image_bgr(active_image_path)
    display_bgr = notebook_api.resize_for_display(source_bgr, config.max_display_size)
    gray_image = cv2.cvtColor(display_bgr, cv2.COLOR_BGR2GRAY)

    denoise_name = f"median_{config.median_kernel_size}"
    denoised_image = notebook_api.apply_median_denoise(
        gray_image,
        config,
    )

    threshold_name = (
        "gaussian_block"
        f"{config.adaptive_threshold_block_size}_c{config.adaptive_threshold_c_value}"
    )
    binary_image = notebook_api.apply_gaussian_threshold(
        denoised_image,
        config,
    )

    cleanup_name = "adaptive_plus_components_soft"
    min_component_area_px, clean_binary = notebook_api.apply_soft_component_cleanup(
        binary_image,
        config,
    )

    repair_name = "directional_close"
    repaired_binary = notebook_api.apply_directional_close_repair(
        clean_binary,
        config,
    )

    line_family_result = notebook_api.detect_line_families(
        repaired_binary,
        config,
    )
    binary_family_overlay, source_family_overlay = (
        notebook_api.build_line_family_overlays(
            display_bgr,
            repaired_binary,
            line_family_result,
            config,
        )
    )
    binary_logical_line_overlay, source_logical_line_overlay = (
        notebook_api.build_logical_line_overlays(
            display_bgr,
            repaired_binary,
            line_family_result,
            config,
        )
    )
    binary_tolerance_rectangle_overlay, source_tolerance_rectangle_overlay = (
        notebook_api.build_tolerance_rectangle_overlays(
            display_bgr,
            repaired_binary,
            line_family_result,
            config,
        )
    )

    return RawLineFamilyArtifacts(
        source_bgr=source_bgr,
        display_bgr=display_bgr,
        gray_image=gray_image,
        denoise_name=denoise_name,
        denoised_image=denoised_image,
        threshold_name=threshold_name,
        binary_image=binary_image,
        min_component_area_px=min_component_area_px,
        cleanup_name=cleanup_name,
        clean_binary=clean_binary,
        repair_name=repair_name,
        repaired_binary=repaired_binary,
        line_family_result=line_family_result,
        binary_family_overlay=binary_family_overlay,
        source_family_overlay=source_family_overlay,
        binary_logical_line_overlay=binary_logical_line_overlay,
        source_logical_line_overlay=source_logical_line_overlay,
        binary_tolerance_rectangle_overlay=binary_tolerance_rectangle_overlay,
        source_tolerance_rectangle_overlay=source_tolerance_rectangle_overlay,
    )


def describe_raw_line_family_artifacts(
    artifacts: RawLineFamilyArtifacts,
) -> list[str]:
    line_family_result = artifacts.line_family_result
    horizontal_tolerance_segments = sum(
        1
        for logical_line in line_family_result.horizontal_logical_lines
        for line_segment in logical_line.line_segments
        if line_segment.origin == SegmentOrigin.TOLERANCE
    )
    vertical_tolerance_segments = sum(
        1
        for logical_line in line_family_result.vertical_logical_lines
        for line_segment in logical_line.line_segments
        if line_segment.origin == SegmentOrigin.TOLERANCE
    )
    horizontal_tolerance_rectangles = len(
        line_family_result.horizontal_tolerance_rectangles
    )
    vertical_tolerance_rectangles = len(
        line_family_result.vertical_tolerance_rectangles
    )
    sample_tolerance_rectangle = None
    if line_family_result.horizontal_tolerance_rectangles:
        sample_tolerance_rectangle = line_family_result.horizontal_tolerance_rectangles[0]
    elif line_family_result.vertical_tolerance_rectangles:
        sample_tolerance_rectangle = line_family_result.vertical_tolerance_rectangles[0]

    tolerance_rectangle_geometry = "n/a"
    if sample_tolerance_rectangle is not None:
        tolerance_rectangle_geometry = (
            f"length={sample_tolerance_rectangle.vector_length}, "
            f"padding={sample_tolerance_rectangle.padding}"
        )

    return [
        f"Original shape: {artifacts.source_bgr.shape}",
        f"Display shape:  {artifacts.display_bgr.shape}",
        f"Denoise: {artifacts.denoise_name}",
        f"Threshold: {artifacts.threshold_name}",
        f"Cleanup: {artifacts.cleanup_name}",
        f"Repair: {artifacts.repair_name}",
        f"Connected components min area px: {artifacts.min_component_area_px}",
        f"Raw Hough segments: {line_family_result.raw_segment_count}",
        (
            "Orientation offset degrees: "
            f"{line_family_result.orientation_offset_degrees}"
        ),
        f"Horizontal family segments: {len(line_family_result.horizontal_segments)}",
        f"Vertical family segments: {len(line_family_result.vertical_segments)}",
        (
            "Horizontal logical lines: "
            f"{len(line_family_result.horizontal_logical_lines)}"
        ),
        f"Vertical logical lines: {len(line_family_result.vertical_logical_lines)}",
        f"Horizontal tolerance segments: {horizontal_tolerance_segments}",
        f"Vertical tolerance segments: {vertical_tolerance_segments}",
        f"Horizontal tolerance rectangles: {horizontal_tolerance_rectangles}",
        f"Vertical tolerance rectangles: {vertical_tolerance_rectangles}",
        f"Tolerance rectangle geometry: {tolerance_rectangle_geometry}",
        (
            "Horizontal family angle: "
            f"{line_family_result.horizontal_angle_degrees}"
        ),
        f"Vertical family angle: {line_family_result.vertical_angle_degrees}",
        "",
        "This pipeline now builds logical lines from family segments.",
    ]


def build_raw_line_family_plot_items(
    artifacts: RawLineFamilyArtifacts,
) -> list[tuple[str, np.ndarray, bool]]:
    return [
        ("source", artifacts.display_bgr, True),
        ("gray", artifacts.gray_image, False),
        (
            f"denoise: {artifacts.denoise_name}",
            artifacts.denoised_image,
            False,
        ),
        (
            f"binary: {artifacts.threshold_name}",
            artifacts.binary_image,
            False,
        ),
        (
            f"cleanup: {artifacts.cleanup_name}",
            artifacts.clean_binary,
            False,
        ),
        (
            f"repair: {artifacts.repair_name}",
            artifacts.repaired_binary,
            False,
        ),
        (
            "raw line families on repaired binary",
            artifacts.binary_family_overlay,
            True,
        ),
        ("raw line families on source", artifacts.source_family_overlay, True),
        (
            "logical lines on repaired binary",
            artifacts.binary_logical_line_overlay,
            True,
        ),
        ("logical lines on source", artifacts.source_logical_line_overlay, True),
        (
            "tolerance rectangles on repaired binary",
            artifacts.binary_tolerance_rectangle_overlay,
            True,
        ),
        (
            "tolerance rectangles on source",
            artifacts.source_tolerance_rectangle_overlay,
            True,
        ),
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
