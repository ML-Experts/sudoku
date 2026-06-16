from __future__ import annotations

import importlib
from pathlib import Path
from typing import TYPE_CHECKING

import cv2

import pipeline_artifacts as pipeline_artifacts
import pipeline_plots as pipeline_plots
import pipeline_report as pipeline_report
import pipeline_selection as pipeline_selection

if TYPE_CHECKING:
    from bootstrap import RawLineFamilyOnlyApi


pipeline_artifacts = importlib.reload(pipeline_artifacts)
pipeline_selection = importlib.reload(pipeline_selection)
pipeline_plots = importlib.reload(pipeline_plots)
pipeline_report = importlib.reload(pipeline_report)

ActiveImageSelection = pipeline_artifacts.ActiveImageSelection
RawLineFamilyArtifacts = pipeline_artifacts.RawLineFamilyArtifacts
build_raw_line_family_plot_items = pipeline_plots.build_raw_line_family_plot_items
describe_raw_line_family_artifacts = (
    pipeline_report.describe_raw_line_family_artifacts
)
configure_manual_image_path = pipeline_selection.configure_manual_image_path
resolve_active_image_selection = pipeline_selection.resolve_active_image_selection


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
    (
        binary_raw_segment_group_overlay,
        source_raw_segment_group_overlay,
    ) = notebook_api.build_raw_segment_group_overlays(
        display_bgr,
        repaired_binary,
        line_family_result,
        config,
    )
    raw_segment_group_board = notebook_api.build_raw_segment_group_board(
        display_bgr,
        line_family_result,
        config,
    )
    (
        binary_containment_prune_overlay,
        source_containment_prune_overlay,
    ) = notebook_api.build_containment_prune_overlays(
        display_bgr,
        repaired_binary,
        line_family_result,
        config,
    )
    containment_prune_board = notebook_api.build_containment_prune_board(
        display_bgr,
        line_family_result,
        config,
    )
    (
        binary_vertex_containment_merge_overlay,
        source_vertex_containment_merge_overlay,
    ) = notebook_api.build_vertex_containment_merge_overlays(
        display_bgr,
        repaired_binary,
        line_family_result,
        config,
    )
    vertex_containment_merge_board = notebook_api.build_vertex_containment_merge_board(
        display_bgr,
        line_family_result,
        config,
    )
    (
        binary_post_merge_logical_line_overlay,
        source_post_merge_logical_line_overlay,
    ) = notebook_api.build_post_merge_logical_line_overlays(
        display_bgr,
        repaired_binary,
        line_family_result,
        config,
    )
    (
        binary_post_connection_logical_line_overlay,
        source_post_connection_logical_line_overlay,
    ) = notebook_api.build_post_connection_logical_line_overlays(
        display_bgr,
        repaired_binary,
        line_family_result,
        config,
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
        binary_trimmed_logical_line_overlay,
        source_trimmed_logical_line_overlay,
    ) = notebook_api.build_trimmed_logical_line_overlays(
        display_bgr,
        repaired_binary,
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
    (
        binary_intersection_kind_map_overlay,
        source_intersection_kind_map_overlay,
    ) = notebook_api.build_logical_line_intersection_kind_map_overlays(
        display_bgr,
        repaired_binary,
        line_family_result,
        config,
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
        raw_segment_group_board=raw_segment_group_board,
        binary_raw_segment_group_overlay=binary_raw_segment_group_overlay,
        source_raw_segment_group_overlay=source_raw_segment_group_overlay,
        containment_prune_board=containment_prune_board,
        binary_containment_prune_overlay=binary_containment_prune_overlay,
        source_containment_prune_overlay=source_containment_prune_overlay,
        vertex_containment_merge_board=vertex_containment_merge_board,
        binary_vertex_containment_merge_overlay=(
            binary_vertex_containment_merge_overlay
        ),
        source_vertex_containment_merge_overlay=(
            source_vertex_containment_merge_overlay
        ),
        binary_post_merge_logical_line_overlay=(
            binary_post_merge_logical_line_overlay
        ),
        source_post_merge_logical_line_overlay=(
            source_post_merge_logical_line_overlay
        ),
        binary_post_connection_logical_line_overlay=(
            binary_post_connection_logical_line_overlay
        ),
        source_post_connection_logical_line_overlay=(
            source_post_connection_logical_line_overlay
        ),
        binary_logical_line_overlay=binary_logical_line_overlay,
        source_logical_line_overlay=source_logical_line_overlay,
        binary_trimmed_logical_line_overlay=binary_trimmed_logical_line_overlay,
        source_trimmed_logical_line_overlay=source_trimmed_logical_line_overlay,
        binary_logical_line_intersection_overlay=(
            binary_logical_line_intersection_overlay
        ),
        source_logical_line_intersection_overlay=(
            source_logical_line_intersection_overlay
        ),
        binary_intersection_kind_map_overlay=binary_intersection_kind_map_overlay,
        source_intersection_kind_map_overlay=source_intersection_kind_map_overlay,
        binary_long_segment_candidate_overlay=binary_long_segment_candidate_overlay,
        source_long_segment_candidate_overlay=source_long_segment_candidate_overlay,
        long_segment_candidate_board=long_segment_candidate_board,
        binary_tolerance_rectangle_overlay=binary_tolerance_rectangle_overlay,
        source_tolerance_rectangle_overlay=source_tolerance_rectangle_overlay,
    )


__all__ = [
    "ActiveImageSelection",
    "RawLineFamilyArtifacts",
    "build_raw_line_family_plot_items",
    "configure_manual_image_path",
    "describe_raw_line_family_artifacts",
    "resolve_active_image_selection",
    "run_raw_line_family_pipeline",
]
