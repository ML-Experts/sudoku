from __future__ import annotations

import numpy as np

from raw_line_family_only_intersections import LogicalLineIntersectionKind
from raw_line_family_only_logical_line_core import LogicalLine
from raw_line_family_only_models import SegmentOrigin
from raw_line_family_only_pipeline_artifacts import RawLineFamilyArtifacts
from raw_line_family_only_pipeline_plots import build_raw_line_family_plot_items


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


def _describe_raw_segment_groups(
    line_prefix: str,
    logical_lines: list[LogicalLine],
) -> list[str]:
    description_lines: list[str] = []
    for line_index, logical_line in enumerate(logical_lines, start=1):
        line_id = f"{line_prefix}{line_index}"
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
        sample_tolerance_rectangle = line_family_result.horizontal_tolerance_rectangles[
            0
        ]
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
    post_connection_description_lines = [
        "",
        "Logical lines after pixel connection and before intersection pruning:",
        *_describe_logical_line_collection(
            "horizontalPostConnection",
            line_family_result.horizontal_post_connection_logical_lines,
        ),
        *_describe_logical_line_collection(
            "verticalPostConnection",
            line_family_result.vertical_post_connection_logical_lines,
        ),
        *_describe_logical_line_collection(
            "horizontalFinalAfterIntersections",
            line_family_result.horizontal_logical_lines,
        ),
        *_describe_logical_line_collection(
            "verticalFinalAfterIntersections",
            line_family_result.vertical_logical_lines,
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
            "Horizontal final logical lines after intersections/frame: "
            f"{len(line_family_result.horizontal_logical_lines)}"
        ),
        (
            "Vertical final logical lines after intersections/frame: "
            f"{len(line_family_result.vertical_logical_lines)}"
        ),
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
        *raw_segment_group_description_lines,
        *post_connection_description_lines,
        *raw_segment_group_debug_lines,
        *longest_segment_description_lines,
        *plot_item_description_lines,
    ]


__all__ = ["describe_raw_line_family_artifacts"]
