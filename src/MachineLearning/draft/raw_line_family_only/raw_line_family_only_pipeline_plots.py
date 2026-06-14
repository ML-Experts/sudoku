from __future__ import annotations

import numpy as np

from raw_line_family_only_pipeline_artifacts import RawLineFamilyArtifacts


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
    if _has_image(artifacts.binary_raw_segment_group_overlay):
        plot_items.append(
            (
                "raw segment groups before pixel merge on repair binary",
                artifacts.binary_raw_segment_group_overlay,
                True,
            )
        )
    if _has_image(artifacts.source_raw_segment_group_overlay):
        plot_items.append(
            (
                "raw segment groups before pixel merge on source",
                artifacts.source_raw_segment_group_overlay,
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
    if _has_image(artifacts.binary_containment_prune_overlay):
        plot_items.append(
            (
                "containment prune on repair binary",
                artifacts.binary_containment_prune_overlay,
                True,
            )
        )
    if _has_image(artifacts.source_containment_prune_overlay):
        plot_items.append(
            (
                "containment prune on source",
                artifacts.source_containment_prune_overlay,
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
                "logical lines final after intersections on repair binary",
                artifacts.binary_logical_line_overlay,
                True,
            ),
            (
                "logical lines final after intersections on source",
                artifacts.source_logical_line_overlay,
                True,
            ),
        ]
    )
    if _has_image(artifacts.binary_long_segment_candidate_overlay):
        plot_items.append(
            (
                "long segment candidates on repair binary",
                artifacts.binary_long_segment_candidate_overlay,
                True,
            )
        )
    if _has_image(artifacts.source_long_segment_candidate_overlay):
        plot_items.append(
            (
                "long segment candidates on source",
                artifacts.source_long_segment_candidate_overlay,
                True,
            )
        )
    if _has_image(artifacts.long_segment_candidate_board):
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
    if _has_image(artifacts.binary_frame_overlay):
        plot_items.append(("frames on repair binary", artifacts.binary_frame_overlay, True))
    if _has_image(artifacts.source_frame_overlay):
        plot_items.append(("frames on source", artifacts.source_frame_overlay, True))
    if _has_image(artifacts.binary_tolerance_rectangle_overlay):
        plot_items.append(
            (
                "tolerance rectangles on repair binary",
                artifacts.binary_tolerance_rectangle_overlay,
                True,
            )
        )
    if _has_image(artifacts.source_tolerance_rectangle_overlay):
        plot_items.append(
            (
                "tolerance rectangles on source",
                artifacts.source_tolerance_rectangle_overlay,
                True,
            )
        )
    return plot_items


__all__ = ["build_raw_line_family_plot_items"]
