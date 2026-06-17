from __future__ import annotations

import numpy as np

from pipeline_artifacts import RawLineFamilyArtifacts


def _has_image(image: np.ndarray | None) -> bool:
    return image is not None and image.size > 0


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
    ]
    if _has_image(artifacts.raw_segment_group_board):
        plot_items.append(
            (
                "raw segment groups board",
                artifacts.raw_segment_group_board,
                True,
            )
        )
    if _has_image(artifacts.containment_prune_board):
        plot_items.append(
            (
                "containment prune board",
                artifacts.containment_prune_board,
                True,
            )
        )
    if _has_image(artifacts.vertex_containment_merge_board):
        plot_items.append(
            (
                "logical lines post vertex merge board",
                artifacts.vertex_containment_merge_board,
                True,
            )
        )
    if _has_image(artifacts.binary_connection_input_overlay):
        plot_items.append(
            (
                "pixel connection tolerance rectangles on repair binary",
                artifacts.binary_connection_input_overlay,
                True,
            )
        )
    if _has_image(artifacts.source_connection_input_overlay):
        plot_items.append(
            (
                "pixel connection tolerance rectangles on source",
                artifacts.source_connection_input_overlay,
                True,
            )
        )
    if _has_image(artifacts.binary_post_connection_logical_line_overlay):
        plot_items.append(
            (
                "logical lines post connection on repair binary",
                artifacts.binary_post_connection_logical_line_overlay,
                True,
            )
        )
    if _has_image(artifacts.source_post_connection_logical_line_overlay):
        plot_items.append(
            (
                "logical lines post connection on source",
                artifacts.source_post_connection_logical_line_overlay,
                True,
            )
        )
    plot_items.extend(
        [
            (
                "logical lines final on repair binary",
                artifacts.binary_logical_line_overlay,
                True,
            ),
            (
                "logical lines final on source",
                artifacts.source_logical_line_overlay,
                True,
            ),
        ]
    )
    if _has_image(artifacts.source_logical_line_intersection_overlay):
        plot_items.append(
            (
                "logical line intersections on source",
                artifacts.source_logical_line_intersection_overlay,
                True,
            )
        )
    if _has_image(artifacts.source_trimmed_logical_line_overlay):
        plot_items.append(
            (
                "logical lines trimmed vs post connection on source",
                artifacts.source_trimmed_logical_line_overlay,
                True,
            )
        )
    if _has_image(artifacts.source_logical_line_frame_overlay):
        plot_items.append(
            (
                "logical line frames on source",
                artifacts.source_logical_line_frame_overlay,
                True,
            )
        )
    if _has_image(artifacts.source_selected_logical_line_frame_overlay):
        plot_items.append(
            (
                "selected logical line frame on source",
                artifacts.source_selected_logical_line_frame_overlay,
                True,
            )
        )
    return plot_items


__all__ = ["build_raw_line_family_plot_items"]
