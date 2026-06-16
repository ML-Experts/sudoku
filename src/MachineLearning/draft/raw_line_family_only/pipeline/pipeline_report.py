from __future__ import annotations

import numpy as np
from logical_line_debug import (
    get_logical_line_debug_name,
    logical_line_debug_sort_key,
)
from logical_line_core import LogicalLine
from models import SegmentOrigin
from pipeline_artifacts import RawLineFamilyArtifacts
from pipeline_plots import build_raw_line_family_plot_items


def _describe_long_segment_candidates(
    line_prefix: str,
    logical_lines: list[LogicalLine],
    minimum_length_ratio: float = 0.8,
) -> list[str]:
    del line_prefix
    description_lines: list[str] = []
    for logical_line in sorted(logical_lines, key=logical_line_debug_sort_key):
        line_id = get_logical_line_debug_name(logical_line)
        longest_segment = logical_line.longest_segment
        if longest_segment is None:
            description_lines.append(f"{line_id} has no segments.")
            continue

        minimum_length = longest_segment.length * minimum_length_ratio
        candidate_segments = logical_line.collect_long_segments(
            minimum_length_ratio=minimum_length_ratio,
        )
        description_lines.append(
            (
                f"{line_id} "
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


def _format_segment(line_segment) -> str:
    return (
        f"origin={line_segment.origin.value} "
        f"start={line_segment.start} "
        f"end={line_segment.end} "
        f"axis=({line_segment.axis_start}..{line_segment.axis_end}) "
        f"angle={line_segment.angle_degrees:.2f}"
    )


def _has_image(image: np.ndarray | None) -> bool:
    return image is not None and image.size > 0


def _has_visible_pixels(image: np.ndarray | None) -> bool:
    return _has_image(image) and bool(np.any(image != 0))


def _count_segment_origins(logical_lines: list[LogicalLine]) -> dict[str, int]:
    origin_counts = {origin.value: 0 for origin in SegmentOrigin}
    for logical_line in logical_lines:
        for line_segment in logical_line.line_segments:
            origin_counts[line_segment.origin.value] += 1
    return origin_counts


def _describe_logical_line_collection(
    label: str,
    logical_lines: list[LogicalLine],
) -> list[str]:
    origin_counts = _count_segment_origins(logical_lines)
    total_segment_count = sum(origin_counts.values())
    return [
        (
            f"{label}: lines={len(logical_lines)} "
            f"segments={total_segment_count} "
            f"raw={origin_counts[SegmentOrigin.RAW.value]} "
            f"sameAxis={origin_counts[SegmentOrigin.SAME_AXIS_CONNECTION.value]} "
            f"crossAxis={origin_counts[SegmentOrigin.CROSS_AXIS_CONNECTION.value]}"
        )
    ]


def _describe_logical_line_intersections(
    logical_line_intersections,
) -> list[str]:
    cross_count = sum(
        1
        for logical_line_intersection in logical_line_intersections
        if logical_line_intersection.is_cross
    )
    touch_count = sum(
        1
        for logical_line_intersection in logical_line_intersections
        if not logical_line_intersection.is_cross
    )
    boundary_count = sum(
        1
        for logical_line_intersection in logical_line_intersections
        if logical_line_intersection.is_boundary
    )
    start_count = sum(
        1
        for logical_line_intersection in logical_line_intersections
        if logical_line_intersection.order.value == "start"
    )
    middle_count = sum(
        1
        for logical_line_intersection in logical_line_intersections
        if logical_line_intersection.order.value == "middle"
    )
    end_count = sum(
        1
        for logical_line_intersection in logical_line_intersections
        if logical_line_intersection.order.value == "end"
    )
    both_count = sum(
        1
        for logical_line_intersection in logical_line_intersections
        if logical_line_intersection.order.value == "both"
    )
    return [
        (
            "logicalLineIntersections: "
            f"count={len(logical_line_intersections)} "
            f"cross={cross_count} "
            f"touch={touch_count} "
            f"boundary={boundary_count} "
            f"start={start_count} "
            f"middle={middle_count} "
            f"end={end_count} "
            f"both={both_count}"
        )
    ]


def _describe_raw_segment_groups(
    line_prefix: str,
    logical_lines: list[LogicalLine],
) -> list[str]:
    del line_prefix
    description_lines: list[str] = []
    for logical_line in sorted(logical_lines, key=logical_line_debug_sort_key):
        line_id = get_logical_line_debug_name(logical_line)
        consumed_segment_count = sum(
            len(group_result.consumed_segments)
            for group_result in logical_line.raw_segment_group_results
        )
        description_lines.append(
            (
                f"{line_id} rawSegmentsBefore={consumed_segment_count} "
                f"rawGroupsBuilt={len(logical_line.raw_segment_group_results)} "
                f"rawSegmentsAfter={len(logical_line.line_segments)}"
            )
        )
        for group_index, group_result in enumerate(
            logical_line.raw_segment_group_results,
            start=1,
        ):
            description_lines.append(
                (
                    f"  - {line_id} G{group_index} "
                    f"segmentCount={len(group_result.consumed_segments)} "
                    f"used={len(group_result.used_segments)} "
                    f"deferred={len(group_result.deferred_segments)} "
                    f"status={group_result.status.value}"
                )
            )
            description_lines.append(
                f"    seedSegment={_format_segment(group_result.seed_segment)}"
            )
            description_lines.append(
                f"    trialSegment={_format_segment(group_result.trial_segment)}"
            )
            if group_result.first_invalid_gap_point is None:
                description_lines.append("    firstInvalidBlackGapAt=None")
            else:
                description_lines.append(
                    "    firstInvalidBlackGapAt="
                    f"{group_result.first_invalid_gap_point}"
                )
            description_lines.append(
                "    acceptedBoundarySegment="
                f"{_format_segment(group_result.accepted_boundary_segment)}"
            )
            description_lines.append(
                f"    outputSegment={_format_segment(group_result.output_segment)}"
            )
            description_lines.append("    consumedSegments:")
            for segment_index, line_segment in enumerate(group_result.consumed_segments):
                description_lines.append(
                    f"      - [{segment_index:02d}] {_format_segment(line_segment)}"
                )
            description_lines.append("    usedSegments:")
            for segment_index, line_segment in enumerate(group_result.used_segments):
                description_lines.append(
                    f"      - [{segment_index:02d}] {_format_segment(line_segment)}"
                )
            description_lines.append("    deferredSegments:")
            if not group_result.deferred_segments:
                description_lines.append("      - none")
            for segment_index, line_segment in enumerate(group_result.deferred_segments):
                description_lines.append(
                    f"      - [{segment_index:02d}] {_format_segment(line_segment)}"
                )

    return description_lines


def _describe_containment_prune_result(
    line_prefix: str,
    prune_result,
) -> list[str]:
    if prune_result is None:
        return [f"{line_prefix}: containment prune unavailable"]

    description_lines = [
        (
            f"{line_prefix}: input={len(prune_result.input_logical_lines)} "
            f"pruned={len(prune_result.pruned_logical_lines)} "
            f"removed={len(prune_result.removed_logical_lines)} "
            f"crossAxisGroups={len(prune_result.cross_axis_groups)}"
        )
    ]
    for group_index, cross_axis_group in enumerate(
        prune_result.cross_axis_groups,
        start=1,
    ):
        description_lines.append(
            (
                f"  - group[{group_index:02d}] "
                f"crossAxis=({cross_axis_group.cross_axis_start}.."
                f"{cross_axis_group.cross_axis_end}) "
                f"removed={len(cross_axis_group.grouped_logical_lines)}"
            )
        )
        container_line = cross_axis_group.anchor_line
        container_label = get_logical_line_debug_name(container_line)
        description_lines.append(
            (
                f"    container={container_label} "
                f"axis=({container_line.axis_start}..{container_line.axis_end}) "
                f"cross=({container_line.cross_axis_start}.."
                f"{container_line.cross_axis_end}) "
                f"removed={len(cross_axis_group.grouped_logical_lines)}"
            )
        )
        for removed_line in cross_axis_group.grouped_logical_lines:
            removed_label = get_logical_line_debug_name(removed_line)
            description_lines.append(
                (
                    f"      - removed={removed_label} "
                    f"axis=({removed_line.axis_start}..{removed_line.axis_end}) "
                    f"cross=({removed_line.cross_axis_start}.."
                    f"{removed_line.cross_axis_end})"
                )
            )

    return description_lines


def _describe_vertex_containment_merge_result(
    line_prefix: str,
    merge_result,
) -> list[str]:
    if merge_result is None:
        return [f"{line_prefix}: vertex containment merge unavailable"]

    description_lines = [
        (
            f"{line_prefix}: input={len(merge_result.input_logical_lines)} "
            f"merged={len(merge_result.merged_logical_lines)} "
            f"consumed={len(merge_result.consumed_logical_lines)} "
            f"mergeGroups={len(merge_result.merge_groups)}"
        )
    ]
    for group_index, merge_group in enumerate(
        merge_result.merge_groups,
        start=1,
    ):
        description_lines.append(
            (
                f"  - group[{group_index:02d}] "
                f"crossAxis=({merge_group.cross_axis_start}.."
                f"{merge_group.cross_axis_end}) "
                f"consumed={len(merge_group.grouped_logical_lines)}"
            )
        )
        anchor_line = merge_group.anchor_line
        anchor_label = get_logical_line_debug_name(anchor_line)
        description_lines.append(
            (
                f"    anchor={anchor_label} "
                f"axis=({anchor_line.axis_start}..{anchor_line.axis_end}) "
                f"cross=({anchor_line.cross_axis_start}.."
                f"{anchor_line.cross_axis_end}) "
                f"consumed={len(merge_group.grouped_logical_lines)}"
            )
        )
        for consumed_line in merge_group.grouped_logical_lines:
            consumed_label = get_logical_line_debug_name(consumed_line)
            description_lines.append(
                (
                    f"      - consumed={consumed_label} "
                    f"axis=({consumed_line.axis_start}..{consumed_line.axis_end}) "
                    f"cross=({consumed_line.cross_axis_start}.."
                    f"{consumed_line.cross_axis_end})"
                )
            )

    return description_lines


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

    logical_line_intersection_count = len(
        line_family_result.logical_line_intersections
    )
    cross_intersection_count = sum(
        1
        for logical_line_intersection in line_family_result.logical_line_intersections
        if logical_line_intersection.is_cross
    )
    touch_intersection_count = sum(
        1
        for logical_line_intersection in line_family_result.logical_line_intersections
        if not logical_line_intersection.is_cross
    )
    boundary_intersection_count = sum(
        1
        for logical_line_intersection in line_family_result.logical_line_intersections
        if logical_line_intersection.is_boundary
    )
    start_intersection_count = sum(
        1
        for logical_line_intersection in line_family_result.logical_line_intersections
        if logical_line_intersection.order.value == "start"
    )
    middle_intersection_count = sum(
        1
        for logical_line_intersection in line_family_result.logical_line_intersections
        if logical_line_intersection.order.value == "middle"
    )
    end_intersection_count = sum(
        1
        for logical_line_intersection in line_family_result.logical_line_intersections
        if logical_line_intersection.order.value == "end"
    )
    both_intersection_count = sum(
        1
        for logical_line_intersection in line_family_result.logical_line_intersections
        if logical_line_intersection.order.value == "both"
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
    raw_segment_group_description_lines = [
        "",
        "RAW segment grouping before pixel merge:",
        *_describe_raw_segment_groups(
            "H",
            line_family_result.horizontal_pre_connection_logical_lines,
        ),
        *_describe_raw_segment_groups(
            "V",
            line_family_result.vertical_pre_connection_logical_lines,
        ),
    ]
    containment_prune_description_lines = [
        "",
        "Containment prune before pixel merge:",
        *_describe_containment_prune_result(
            "H",
            line_family_result.horizontal_containment_prune_result,
        ),
        *_describe_containment_prune_result(
            "V",
            line_family_result.vertical_containment_prune_result,
        ),
    ]
    vertex_containment_merge_description_lines = [
        "",
        "Vertex containment merge before pixel connection:",
        *_describe_vertex_containment_merge_result(
            "H",
            line_family_result.horizontal_vertex_containment_merge_result,
        ),
        *_describe_vertex_containment_merge_result(
            "V",
            line_family_result.vertical_vertex_containment_merge_result,
        ),
    ]
    post_connection_description_lines = [
        "",
        "Logical lines after vertex containment merge, pixel connection, and trim:",
        *_describe_logical_line_collection(
            "horizontalPostMerge",
            line_family_result.horizontal_post_merge_logical_lines,
        ),
        *_describe_logical_line_collection(
            "verticalPostMerge",
            line_family_result.vertical_post_merge_logical_lines,
        ),
        *_describe_logical_line_collection(
            "horizontalPostConnection",
            line_family_result.horizontal_post_connection_logical_lines,
        ),
        *_describe_logical_line_collection(
            "verticalPostConnection",
            line_family_result.vertical_post_connection_logical_lines,
        ),
        *_describe_logical_line_collection(
            "horizontalFinal",
            line_family_result.horizontal_logical_lines,
        ),
        *_describe_logical_line_collection(
            "verticalFinal",
            line_family_result.vertical_logical_lines,
        ),
        *_describe_logical_line_intersections(
            line_family_result.logical_line_intersections,
        ),
    ]
    raw_segment_group_debug_lines = [
        "",
        "RAW segment group render artifacts:",
        (
            "rawSegmentGroupBoard: "
            f"present={_has_image(artifacts.raw_segment_group_board)} "
            f"visiblePixels={_has_visible_pixels(artifacts.raw_segment_group_board)} "
            f"shape={None if artifacts.raw_segment_group_board is None else artifacts.raw_segment_group_board.shape}"
        ),
        (
            "binaryRawSegmentGroupOverlay: "
            f"present={_has_image(artifacts.binary_raw_segment_group_overlay)} "
            f"visiblePixels={_has_visible_pixels(artifacts.binary_raw_segment_group_overlay)} "
            f"shape={None if artifacts.binary_raw_segment_group_overlay is None else artifacts.binary_raw_segment_group_overlay.shape}"
        ),
        (
            "sourceRawSegmentGroupOverlay: "
            f"present={_has_image(artifacts.source_raw_segment_group_overlay)} "
            f"visiblePixels={_has_visible_pixels(artifacts.source_raw_segment_group_overlay)} "
            f"shape={None if artifacts.source_raw_segment_group_overlay is None else artifacts.source_raw_segment_group_overlay.shape}"
        ),
        (
            "binaryLogicalLineIntersectionOverlay: "
            f"present={_has_image(artifacts.binary_logical_line_intersection_overlay)} "
            "visiblePixels="
            f"{_has_visible_pixels(artifacts.binary_logical_line_intersection_overlay)} "
            "shape="
            f"{None if artifacts.binary_logical_line_intersection_overlay is None else artifacts.binary_logical_line_intersection_overlay.shape}"
        ),
        (
            "sourceLogicalLineIntersectionOverlay: "
            f"present={_has_image(artifacts.source_logical_line_intersection_overlay)} "
            "visiblePixels="
            f"{_has_visible_pixels(artifacts.source_logical_line_intersection_overlay)} "
            "shape="
            f"{None if artifacts.source_logical_line_intersection_overlay is None else artifacts.source_logical_line_intersection_overlay.shape}"
        ),
        (
            "binaryIntersectionKindMapOverlay: "
            f"present={_has_image(artifacts.binary_intersection_kind_map_overlay)} "
            f"visiblePixels={_has_visible_pixels(artifacts.binary_intersection_kind_map_overlay)} "
            "shape="
            f"{None if artifacts.binary_intersection_kind_map_overlay is None else artifacts.binary_intersection_kind_map_overlay.shape}"
        ),
        (
            "sourceIntersectionKindMapOverlay: "
            f"present={_has_image(artifacts.source_intersection_kind_map_overlay)} "
            f"visiblePixels={_has_visible_pixels(artifacts.source_intersection_kind_map_overlay)} "
            "shape="
            f"{None if artifacts.source_intersection_kind_map_overlay is None else artifacts.source_intersection_kind_map_overlay.shape}"
        ),
        (
            "vertexContainmentMergeBoard: "
            f"present={_has_image(artifacts.vertex_containment_merge_board)} "
            f"visiblePixels={_has_visible_pixels(artifacts.vertex_containment_merge_board)} "
            f"shape={None if artifacts.vertex_containment_merge_board is None else artifacts.vertex_containment_merge_board.shape}"
        ),
        (
            "binaryVertexContainmentMergeOverlay: "
            f"present={_has_image(artifacts.binary_vertex_containment_merge_overlay)} "
            f"visiblePixels={_has_visible_pixels(artifacts.binary_vertex_containment_merge_overlay)} "
            f"shape={None if artifacts.binary_vertex_containment_merge_overlay is None else artifacts.binary_vertex_containment_merge_overlay.shape}"
        ),
        (
            "sourceVertexContainmentMergeOverlay: "
            f"present={_has_image(artifacts.source_vertex_containment_merge_overlay)} "
            f"visiblePixels={_has_visible_pixels(artifacts.source_vertex_containment_merge_overlay)} "
            f"shape={None if artifacts.source_vertex_containment_merge_overlay is None else artifacts.source_vertex_containment_merge_overlay.shape}"
        ),
        (
            "binaryPostMergeLogicalLineOverlay: "
            f"present={_has_image(artifacts.binary_post_merge_logical_line_overlay)} "
            f"visiblePixels={_has_visible_pixels(artifacts.binary_post_merge_logical_line_overlay)} "
            "shape="
            f"{None if artifacts.binary_post_merge_logical_line_overlay is None else artifacts.binary_post_merge_logical_line_overlay.shape}"
        ),
        (
            "sourcePostMergeLogicalLineOverlay: "
            f"present={_has_image(artifacts.source_post_merge_logical_line_overlay)} "
            f"visiblePixels={_has_visible_pixels(artifacts.source_post_merge_logical_line_overlay)} "
            "shape="
            f"{None if artifacts.source_post_merge_logical_line_overlay is None else artifacts.source_post_merge_logical_line_overlay.shape}"
        ),
        (
            "binaryPostConnectionLogicalLineOverlay: "
            f"present={_has_image(artifacts.binary_post_connection_logical_line_overlay)} "
            f"visiblePixels={_has_visible_pixels(artifacts.binary_post_connection_logical_line_overlay)} "
            "shape="
            f"{None if artifacts.binary_post_connection_logical_line_overlay is None else artifacts.binary_post_connection_logical_line_overlay.shape}"
        ),
        (
            "sourcePostConnectionLogicalLineOverlay: "
            f"present={_has_image(artifacts.source_post_connection_logical_line_overlay)} "
            f"visiblePixels={_has_visible_pixels(artifacts.source_post_connection_logical_line_overlay)} "
            "shape="
            f"{None if artifacts.source_post_connection_logical_line_overlay is None else artifacts.source_post_connection_logical_line_overlay.shape}"
        ),
        (
            "binaryTrimmedLogicalLineOverlay: "
            f"present={_has_image(artifacts.binary_trimmed_logical_line_overlay)} "
            f"visiblePixels={_has_visible_pixels(artifacts.binary_trimmed_logical_line_overlay)} "
            "shape="
            f"{None if artifacts.binary_trimmed_logical_line_overlay is None else artifacts.binary_trimmed_logical_line_overlay.shape}"
        ),
        (
            "sourceTrimmedLogicalLineOverlay: "
            f"present={_has_image(artifacts.source_trimmed_logical_line_overlay)} "
            f"visiblePixels={_has_visible_pixels(artifacts.source_trimmed_logical_line_overlay)} "
            "shape="
            f"{None if artifacts.source_trimmed_logical_line_overlay is None else artifacts.source_trimmed_logical_line_overlay.shape}"
        ),
    ]
    plot_items = build_raw_line_family_plot_items(artifacts)
    plot_item_description_lines = [
        "",
        f"Notebook plot items generated: {len(plot_items)}",
        *[
            f"  - plot[{plot_index:02d}] {title}"
            for plot_index, (title, _, _) in enumerate(plot_items)
        ],
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
            "Horizontal final logical lines: "
            f"{len(line_family_result.horizontal_logical_lines)}"
        ),
        (
            "Vertical final logical lines: "
            f"{len(line_family_result.vertical_logical_lines)}"
        ),
        f"Horizontal same-axis connection segments: {horizontal_same_axis_segments}",
        f"Vertical same-axis connection segments: {vertical_same_axis_segments}",
        f"Horizontal cross-axis connection segments: {horizontal_cross_axis_segments}",
        f"Vertical cross-axis connection segments: {vertical_cross_axis_segments}",
        f"Logical line intersections: {logical_line_intersection_count}",

        f"Cross intersections: {cross_intersection_count}",
        f"Touch intersections: {touch_intersection_count}",
        f"Boundary intersections: {boundary_intersection_count}",
        f"Start intersections: {start_intersection_count}",
        f"Middle intersections: {middle_intersection_count}",
        f"End intersections: {end_intersection_count}",
        f"Both intersections: {both_intersection_count}",
        (
            "Horizontal family angle: "
            f"{line_family_result.horizontal_angle_degrees}"
        ),
        f"Vertical family angle: {line_family_result.vertical_angle_degrees}",
        "",
        "This pipeline now builds logical lines through pixel-validated connection.",
        *raw_segment_group_description_lines,
        *containment_prune_description_lines,
        *vertex_containment_merge_description_lines,
        *post_connection_description_lines,
        *raw_segment_group_debug_lines,
        *longest_segment_description_lines,
        *plot_item_description_lines,
    ]


__all__ = ["describe_raw_line_family_artifacts"]
