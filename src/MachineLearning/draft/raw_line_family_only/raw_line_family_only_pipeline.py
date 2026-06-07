from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np

from raw_line_family_only_detection import RawLineFamilyResult
from raw_line_family_only_logical_line_core import LogicalLine
from raw_line_family_only_intersections import LogicalLineIntersectionKind
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
    binary_logical_line_intersection_overlay: np.ndarray
    source_logical_line_intersection_overlay: np.ndarray
    binary_long_segment_candidate_overlay: np.ndarray | None = None
    source_long_segment_candidate_overlay: np.ndarray | None = None
    long_segment_candidate_board: np.ndarray | None = None
    binary_frame_overlay: np.ndarray | None = None
    source_frame_overlay: np.ndarray | None = None
    binary_tolerance_rectangle_overlay: np.ndarray | None = None
    source_tolerance_rectangle_overlay: np.ndarray | None = None


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


def _describe_long_segment_candidates(
    line_prefix: str,
    logical_lines: list[LogicalLine],
    minimum_length_ratio: float = 0.8,
) -> list[str]:
    description_lines: list[str] = []
    for line_index, logical_line in enumerate(logical_lines):
        longest_segment = logical_line.longest_segment
        if longest_segment is None:
            description_lines.append(f"{line_prefix}[{line_index:02d}] has no segments.")
            continue

        minimum_length = longest_segment.length * minimum_length_ratio
        candidate_segments = logical_line.collect_long_segments(
            minimum_length_ratio=minimum_length_ratio,
        )
        description_lines.append(
            (
                f"{line_prefix}[{line_index:02d}] "
                f"frameSide={logical_line.frame_side.value} "
                f"segmentCount={len(logical_line.line_segments)} "
                f"maxLength={longest_segment.length:.2f} "
                f"threshold={minimum_length:.2f} "
                f"selected={len(candidate_segments)}"
            )
        )
        for segment_index, line_segment in enumerate(candidate_segments):
            description_lines.append(
                (
                    f"  - candidate[{segment_index:02d}] "
                    f"length={line_segment.length:.2f} "
                    f"origin={line_segment.origin.value} "
                    f"start={line_segment.start} "
                    f"end={line_segment.end}"
                )
            )

    return description_lines


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

    family_detection_result = notebook_api.detect_line_families(
        clean_binary,
        config,
        include_logical_lines=False,
    )
    line_family_result = notebook_api.detect_line_families(
        clean_binary,
        config,
        pixel_connection_binary_image=repaired_binary,
    )
    binary_family_overlay, source_family_overlay = (
        notebook_api.build_line_family_overlays(
            display_bgr,
            clean_binary,
            family_detection_result,
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
    (
        binary_long_segment_candidate_overlay,
        source_long_segment_candidate_overlay,
    ) = notebook_api.build_long_segment_candidate_overlays(
        display_bgr,
        repaired_binary,
        line_family_result,
        config,
    )
    long_segment_candidate_board = notebook_api.build_long_segment_candidate_board(
        display_bgr,
        line_family_result,
        config,
    )
    (
        binary_logical_line_intersection_overlay,
        source_logical_line_intersection_overlay,
    ) = notebook_api.build_logical_line_intersection_overlays(
        display_bgr,
        repaired_binary,
        line_family_result,
        config,
    )
    binary_frame_overlay, source_frame_overlay = notebook_api.build_frame_overlays(
        display_bgr,
        repaired_binary,
        line_family_result,
        config,
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
        binary_long_segment_candidate_overlay=binary_long_segment_candidate_overlay,
        source_long_segment_candidate_overlay=source_long_segment_candidate_overlay,
        long_segment_candidate_board=long_segment_candidate_board,
        binary_logical_line_intersection_overlay=(
            binary_logical_line_intersection_overlay
        ),
        source_logical_line_intersection_overlay=(
            source_logical_line_intersection_overlay
        ),
        binary_frame_overlay=binary_frame_overlay,
        source_frame_overlay=source_frame_overlay,
        binary_tolerance_rectangle_overlay=binary_tolerance_rectangle_overlay,
        source_tolerance_rectangle_overlay=source_tolerance_rectangle_overlay,
    )


def describe_raw_line_family_artifacts(
    artifacts: RawLineFamilyArtifacts,
) -> list[str]:
    line_family_result = artifacts.line_family_result
    horizontal_same_axis_segments = sum(
        1
        for logical_line in line_family_result.horizontal_logical_lines
        for line_segment in logical_line.line_segments
        if line_segment.origin == SegmentOrigin.SAME_AXIS_CONNECTION
    )
    vertical_same_axis_segments = sum(
        1
        for logical_line in line_family_result.vertical_logical_lines
        for line_segment in logical_line.line_segments
        if line_segment.origin == SegmentOrigin.SAME_AXIS_CONNECTION
    )
    horizontal_cross_axis_segments = sum(
        1
        for logical_line in line_family_result.horizontal_logical_lines
        for line_segment in logical_line.line_segments
        if line_segment.origin == SegmentOrigin.CROSS_AXIS_CONNECTION
    )
    vertical_cross_axis_segments = sum(
        1
        for logical_line in line_family_result.vertical_logical_lines
        for line_segment in logical_line.line_segments
        if line_segment.origin == SegmentOrigin.CROSS_AXIS_CONNECTION
    )
    horizontal_tolerance_rectangles = len(
        line_family_result.horizontal_tolerance_rectangles
    )
    vertical_tolerance_rectangles = len(
        line_family_result.vertical_tolerance_rectangles
    )
    logical_line_intersection_count = len(line_family_result.logical_line_intersections)
    logical_line_cross_intersection_count = sum(
        1
        for logical_line_intersection in line_family_result.logical_line_intersections
        if logical_line_intersection.kind == LogicalLineIntersectionKind.CROSS
    )
    logical_line_touch_intersection_count = sum(
        1
        for logical_line_intersection in line_family_result.logical_line_intersections
        if logical_line_intersection.kind == LogicalLineIntersectionKind.TOUCH
    )
    logical_line_mutual_boundary_intersection_count = sum(
        1
        for logical_line_intersection in line_family_result.logical_line_intersections
        if logical_line_intersection.is_mutual_boundary
    )
    logical_line_border_pair_count = len(line_family_result.logical_line_border_pairs)
    logical_line_frame_count = len(line_family_result.logical_line_frames)
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

    longest_segment_description_lines = [
        "",
        "Longest segment candidates per logical line (>= 80% of max length):",
        *_describe_long_segment_candidates(
            "H",
            line_family_result.horizontal_logical_lines,
        ),
        *_describe_long_segment_candidates(
            "V",
            line_family_result.vertical_logical_lines,
        ),
    ]

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
        f"Horizontal same-axis connection segments: {horizontal_same_axis_segments}",
        f"Vertical same-axis connection segments: {vertical_same_axis_segments}",
        f"Horizontal cross-axis connection segments: {horizontal_cross_axis_segments}",
        f"Vertical cross-axis connection segments: {vertical_cross_axis_segments}",
        f"Horizontal tolerance rectangles: {horizontal_tolerance_rectangles}",
        f"Vertical tolerance rectangles: {vertical_tolerance_rectangles}",
        f"Logical line intersections: {logical_line_intersection_count}",
        (
            "Logical line crosses / touches: "
            f"{logical_line_cross_intersection_count} / "
            f"{logical_line_touch_intersection_count}"
        ),
        (
            "Mutual boundary intersections / border pairs / frames: "
            f"{logical_line_mutual_boundary_intersection_count} / "
            f"{logical_line_border_pair_count} / "
            f"{logical_line_frame_count}"
        ),
        f"Tolerance rectangle geometry: {tolerance_rectangle_geometry}",
        (
            "Horizontal family angle: "
            f"{line_family_result.horizontal_angle_degrees}"
        ),
        f"Vertical family angle: {line_family_result.vertical_angle_degrees}",
        "",
        "This pipeline now builds logical lines and pixel-validated connections.",
        *longest_segment_description_lines,
    ]


def build_raw_line_family_plot_items(
    artifacts: RawLineFamilyArtifacts,
) -> list[tuple[str, np.ndarray, bool]]:
    plot_items: list[tuple[str, np.ndarray, bool]] = [
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
            "raw line families on cleanup binary",
            artifacts.binary_family_overlay,
            True,
        ),
        ("raw line families on source", artifacts.source_family_overlay, True),
        (
            "logical lines on repair binary",
            artifacts.binary_logical_line_overlay,
            True,
        ),
        ("logical lines on source", artifacts.source_logical_line_overlay, True),
    ]
    if artifacts.binary_long_segment_candidate_overlay is not None:
        plot_items.append(
            (
                "long segment candidates on repair binary",
                artifacts.binary_long_segment_candidate_overlay,
                True,
            )
        )
    if artifacts.source_long_segment_candidate_overlay is not None:
        plot_items.append(
            (
                "long segment candidates on source",
                artifacts.source_long_segment_candidate_overlay,
                True,
            )
        )
    if artifacts.long_segment_candidate_board is not None:
        plot_items.append(
            (
                "logical lines board: blue=all, red=longest",
                artifacts.long_segment_candidate_board,
                True,
            )
        )
    plot_items.extend(
        [
        (
            "logical line intersections on repair binary",
            artifacts.binary_logical_line_intersection_overlay,
            True,
        ),
        (
            "logical line intersections on source",
            artifacts.source_logical_line_intersection_overlay,
            True,
        ),
        ]
    )
    if artifacts.binary_frame_overlay is not None:
        plot_items.append(("frames on repair binary", artifacts.binary_frame_overlay, True))
    if artifacts.source_frame_overlay is not None:
        plot_items.append(("frames on source", artifacts.source_frame_overlay, True))
    if artifacts.binary_tolerance_rectangle_overlay is not None:
        plot_items.append(
            (
                "tolerance rectangles on repair binary",
                artifacts.binary_tolerance_rectangle_overlay,
                True,
            )
        )
    if artifacts.source_tolerance_rectangle_overlay is not None:
        plot_items.append(
            (
                "tolerance rectangles on source",
                artifacts.source_tolerance_rectangle_overlay,
                True,
            )
        )
    return plot_items


__all__ = [
    "ActiveImageSelection",
    "RawLineFamilyArtifacts",
    "build_raw_line_family_plot_items",
    "configure_manual_image_path",
    "describe_raw_line_family_artifacts",
    "resolve_active_image_selection",
    "run_raw_line_family_pipeline",
]
