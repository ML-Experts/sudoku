from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from line_families import (
    collect_line_family,
    get_dominant_angle_degrees,
    is_horizontal_like,
    refine_family_angle_degrees,
)
from geometry import (
    angle_difference_degrees,
    build_line_segment,
    classify_line_segment,
    signed_angle_offset_degrees,
)
from intersection_model import (
    LogicalLineIntersection,
    LogicalLineIntersectionDebugCandidate,
)
from frame_model import (
    LogicalLineBoundaryGroup,
    LogicalLineFrameCandidate,
)
from logical_line_frame_warp import (
    warp_selected_frame_to_square,
)
from logical_line_frame_warp_model import (
    LogicalLineFrameWarpResult,
)
from logical_lines import (
    LogicalLine,
    build_logical_lines,
    connect_logical_lines_by_pixels,
)
from logical_line_debug import (
    assign_logical_line_debug_names,
)
from logical_line_intersections import assign_logical_line_intersections
from logical_line_frames import (
    build_boundary_groups,
    find_logical_line_frame_candidates,
)
from logical_line_frame_ranking import (
    rank_logical_line_frame_candidates,
    select_best_ranked_logical_line_frame_candidate,
)
from logical_line_cross_axis_continuity import LogicalLineCrossAxisGroup
from models import (
    ExperimentConfig,
    LineFamilyName,
    LineSegment,
    ToleranceRectangle,
)
from logical_line_full_containment import (
    PruneContainedLogicalLinesResult,
    prune_logical_lines_by_full_axis_containment,
)
from logical_line_vertex_containment_merge import (
    MergeVertexContainedLogicalLinesResult,
    merge_logical_lines_by_vertex_axis_containment,
)
from logical_line_intersection_trimming import trim_logical_lines_to_intersections


@dataclass(frozen=True)
class RawLineFamilyResult:
    raw_segment_count: int
    orientation_offset_degrees: float | None
    horizontal_angle_degrees: float | None
    vertical_angle_degrees: float | None
    horizontal_segments: list[LineSegment]
    vertical_segments: list[LineSegment]
    horizontal_pre_connection_logical_lines: list[LogicalLine]
    vertical_pre_connection_logical_lines: list[LogicalLine]
    horizontal_containment_prune_result: PruneContainedLogicalLinesResult | None
    vertical_containment_prune_result: PruneContainedLogicalLinesResult | None
    horizontal_vertex_containment_merge_result: (
        MergeVertexContainedLogicalLinesResult | None
    )
    vertical_vertex_containment_merge_result: (
        MergeVertexContainedLogicalLinesResult | None
    )
    horizontal_post_merge_logical_lines: list[LogicalLine]
    vertical_post_merge_logical_lines: list[LogicalLine]
    horizontal_post_connection_logical_lines: list[LogicalLine]
    vertical_post_connection_logical_lines: list[LogicalLine]
    horizontal_logical_lines: list[LogicalLine]
    vertical_logical_lines: list[LogicalLine]
    logical_line_intersections: list[LogicalLineIntersection]
    horizontal_boundary_groups: list[LogicalLineBoundaryGroup]
    vertical_boundary_groups: list[LogicalLineBoundaryGroup]
    logical_line_frame_candidates: list[LogicalLineFrameCandidate]
    selected_logical_line_frame_candidate: LogicalLineFrameCandidate | None
    selected_logical_line_frame_warp_result: LogicalLineFrameWarpResult | None


def _build_empty_line_family_result(
) -> RawLineFamilyResult:
    return RawLineFamilyResult(
        raw_segment_count=0,
        orientation_offset_degrees=None,
        horizontal_angle_degrees=None,
        vertical_angle_degrees=None,
        horizontal_segments=[],
        vertical_segments=[],
        horizontal_pre_connection_logical_lines=[],
        vertical_pre_connection_logical_lines=[],
        horizontal_containment_prune_result=None,
        vertical_containment_prune_result=None,
        horizontal_vertex_containment_merge_result=None,
        vertical_vertex_containment_merge_result=None,
        horizontal_post_merge_logical_lines=[],
        vertical_post_merge_logical_lines=[],
        horizontal_post_connection_logical_lines=[],
        vertical_post_connection_logical_lines=[],
        horizontal_logical_lines=[],
        vertical_logical_lines=[],
        logical_line_intersections=[],
        horizontal_boundary_groups=[],
        vertical_boundary_groups=[],
        logical_line_frame_candidates=[],
        selected_logical_line_frame_candidate=None,
        selected_logical_line_frame_warp_result=None,
    )


def _estimate_orientation_offset_degrees(
    line_segments: list[LineSegment],
    angle_tolerance_degrees: float,
) -> float | None:
    dominant_seed_angle = get_dominant_angle_degrees(line_segments)
    if dominant_seed_angle is None:
        return None

    dominant_segments = collect_line_family(
        line_segments,
        dominant_seed_angle,
        angle_tolerance_degrees,
    )
    dominant_angle = refine_family_angle_degrees(
        dominant_segments,
        dominant_seed_angle,
    )
    if is_horizontal_like(dominant_angle):
        return signed_angle_offset_degrees(dominant_angle, 0.0)

    return signed_angle_offset_degrees(dominant_angle, 90.0)


def _collect_family_by_reference_angle(
    line_segments: list[LineSegment],
    family_reference_angle_degrees: float,
    opposite_reference_angle_degrees: float,
    angle_tolerance_degrees: float,
) -> list[LineSegment]:
    family_segments: list[LineSegment] = []
    for line_segment in line_segments:
        family_angle_difference = angle_difference_degrees(
            line_segment.angle_degrees,
            family_reference_angle_degrees,
        )
        opposite_angle_difference = angle_difference_degrees(
            line_segment.angle_degrees,
            opposite_reference_angle_degrees,
        )
        if (
            family_angle_difference <= angle_tolerance_degrees
            and family_angle_difference <= opposite_angle_difference
        ):
            family_segments.append(line_segment)

    return family_segments


def _group_raw_segments_in_logical_lines(
    logical_lines: list[LogicalLine],
    binary_image: np.ndarray,
    reference_angle_degrees: float | None,
    config: ExperimentConfig,
) -> None:
    if reference_angle_degrees is None:
        return

    for logical_line in logical_lines:
        logical_line.group_raw_segments(
            binary_image=binary_image,
            reference_angle_degrees=reference_angle_degrees,
            angle_tolerance_degrees=config.line_family_angle_tolerance_degrees,
            black_gap_tolerance_px=config.raw_segment_group_black_gap_tolerance_px,
        )


def _clone_logical_lines(
    logical_lines: list[LogicalLine],
) -> list[LogicalLine]:
    return [logical_line.clone() for logical_line in logical_lines]


def _clone_cross_axis_groups(
    groups: list[LogicalLineCrossAxisGroup],
) -> list[LogicalLineCrossAxisGroup]:
    return [
        LogicalLineCrossAxisGroup(
            cross_axis_start=group.cross_axis_start,
            cross_axis_end=group.cross_axis_end,
            anchor_line=group.anchor_line.clone(),
            grouped_logical_lines=[
                logical_line.clone() for logical_line in group.grouped_logical_lines
            ],
            grouped_logical_line_ids=set(group.grouped_logical_line_ids),
        )
        for group in groups
    ]


def _clone_containment_prune_result(
    prune_result: PruneContainedLogicalLinesResult,
) -> PruneContainedLogicalLinesResult:
    return PruneContainedLogicalLinesResult(
        input_logical_lines=_clone_logical_lines(prune_result.input_logical_lines),
        pruned_logical_lines=_clone_logical_lines(prune_result.pruned_logical_lines),
        removed_logical_lines=_clone_logical_lines(prune_result.removed_logical_lines),
        cross_axis_groups=_clone_cross_axis_groups(prune_result.cross_axis_groups),
    )


def _clone_vertex_containment_merge_result(
    merge_result: MergeVertexContainedLogicalLinesResult,
) -> MergeVertexContainedLogicalLinesResult:
    return MergeVertexContainedLogicalLinesResult(
        input_logical_lines=_clone_logical_lines(merge_result.input_logical_lines),
        merged_logical_lines=_clone_logical_lines(merge_result.merged_logical_lines),
        consumed_logical_lines=_clone_logical_lines(merge_result.consumed_logical_lines),
        merge_groups=_clone_cross_axis_groups(merge_result.merge_groups),
    )


def _logical_line_has_intersection_duplicates(
    logical_line: LogicalLine,
) -> bool:
    return any(
        logical_line_intersection_candidate.duplicate_count > 1
        for logical_line_intersection_candidate in (
            logical_line.intersection_debug_candidates
        )
    )


def _detect_raw_segments(
    binary_image: np.ndarray,
    config: ExperimentConfig,
) -> list[LineSegment]:
    minimum_dimension = min(binary_image.shape[:2])
    min_line_length_px = max(
        8,
        int(round(minimum_dimension * config.raw_min_line_length_ratio)),
    )
    max_line_gap_px = max(
        2,
        int(round(minimum_dimension * config.raw_max_line_gap_ratio)),
    )
    raw_segments = cv2.HoughLinesP(
        binary_image,
        rho=1,
        theta=np.pi / 180.0,
        threshold=config.raw_hough_threshold,
        minLineLength=min_line_length_px,
        maxLineGap=max_line_gap_px,
    )
    if raw_segments is None:
        return []

    return [build_line_segment(raw_segment[0]) for raw_segment in raw_segments]


def _collect_classified_family_segments(
    line_segments: list[LineSegment],
    horizontal_reference_angle: float,
    vertical_reference_angle: float,
    angle_tolerance_degrees: float,
) -> tuple[list[LineSegment], list[LineSegment]]:
    horizontal_segments = _collect_family_by_reference_angle(
        line_segments,
        horizontal_reference_angle,
        vertical_reference_angle,
        angle_tolerance_degrees,
    )
    vertical_segments = _collect_family_by_reference_angle(
        line_segments,
        vertical_reference_angle,
        horizontal_reference_angle,
        angle_tolerance_degrees,
    )
    return (
        [
            classify_line_segment(line_segment, LineFamilyName.HORIZONTAL)
            for line_segment in horizontal_segments
        ],
        [
            classify_line_segment(line_segment, LineFamilyName.VERTICAL)
            for line_segment in vertical_segments
        ],
    )


def detect_line_families(
    family_detection_binary_image: np.ndarray,
    config: ExperimentConfig,
    pixel_connection_binary_image: np.ndarray | None = None,
    warp_source_image: np.ndarray | None = None,
    include_logical_lines: bool = True,
) -> RawLineFamilyResult:
    image_height, image_width = family_detection_binary_image.shape[:2]
    pixel_connection_binary = pixel_connection_binary_image
    if pixel_connection_binary is None:
        pixel_connection_binary = family_detection_binary_image

    family_detection_segments = _detect_raw_segments(
        family_detection_binary_image,
        config,
    )
    if not family_detection_segments:
        return _build_empty_line_family_result()

    orientation_offset_degrees = _estimate_orientation_offset_degrees(
        family_detection_segments,
        config.line_family_angle_tolerance_degrees,
    )
    if orientation_offset_degrees is None:
        return _build_empty_line_family_result()

    horizontal_reference_angle = orientation_offset_degrees % 180.0
    vertical_reference_angle = (horizontal_reference_angle + 90.0) % 180.0

    family_horizontal_segments, family_vertical_segments = (
        _collect_classified_family_segments(
            family_detection_segments,
            horizontal_reference_angle,
            vertical_reference_angle,
            config.line_family_angle_tolerance_degrees,
        )
    )
    horizontal_angle_degrees = refine_family_angle_degrees(
        family_horizontal_segments,
        horizontal_reference_angle,
    )
    vertical_angle_degrees = refine_family_angle_degrees(
        family_vertical_segments,
        vertical_reference_angle,
    )

    if not include_logical_lines:
        return RawLineFamilyResult(
            raw_segment_count=len(family_detection_segments),
            orientation_offset_degrees=orientation_offset_degrees,
            horizontal_angle_degrees=horizontal_angle_degrees,
            vertical_angle_degrees=vertical_angle_degrees,
            horizontal_segments=family_horizontal_segments,
            vertical_segments=family_vertical_segments,
            horizontal_pre_connection_logical_lines=[],
            vertical_pre_connection_logical_lines=[],
            horizontal_containment_prune_result=None,
            vertical_containment_prune_result=None,
            horizontal_vertex_containment_merge_result=None,
            vertical_vertex_containment_merge_result=None,
            horizontal_post_merge_logical_lines=[],
            vertical_post_merge_logical_lines=[],
            horizontal_post_connection_logical_lines=[],
            vertical_post_connection_logical_lines=[],
            horizontal_logical_lines=[],
            vertical_logical_lines=[],
            logical_line_intersections=[],
            horizontal_boundary_groups=[],
            vertical_boundary_groups=[],
            logical_line_frame_candidates=[],
            selected_logical_line_frame_candidate=None,
            selected_logical_line_frame_warp_result=None,
        )

    horizontal_segments = family_horizontal_segments
    vertical_segments = family_vertical_segments
    horizontal_logical_lines = build_logical_lines(
        horizontal_segments,
        cross_axis_thickness_px=config.logical_line_cross_axis_thickness_px,
        axis_gap_tolerance_px=config.logical_line_axis_gap_tolerance_px,
    )
    vertical_logical_lines = build_logical_lines(
        vertical_segments,
        cross_axis_thickness_px=config.logical_line_cross_axis_thickness_px,
        axis_gap_tolerance_px=config.logical_line_axis_gap_tolerance_px,
    )
    assign_logical_line_debug_names(horizontal_logical_lines, "H")
    assign_logical_line_debug_names(vertical_logical_lines, "V")
    _group_raw_segments_in_logical_lines(
        horizontal_logical_lines,
        binary_image=family_detection_binary_image,
        reference_angle_degrees=horizontal_angle_degrees,
        config=config,
    )
    _group_raw_segments_in_logical_lines(
        vertical_logical_lines,
        binary_image=family_detection_binary_image,
        reference_angle_degrees=vertical_angle_degrees,
        config=config,
    )
    horizontal_pre_connection_logical_lines = [
        logical_line.clone() for logical_line in horizontal_logical_lines
    ]
    vertical_pre_connection_logical_lines = [
        logical_line.clone() for logical_line in vertical_logical_lines
    ]


    prune_contained_horizontal_logical_lines_result: PruneContainedLogicalLinesResult = prune_logical_lines_by_full_axis_containment(family_detection_binary_image, horizontal_logical_lines)
    prune_contained_vertical_logical_lines_result: PruneContainedLogicalLinesResult = prune_logical_lines_by_full_axis_containment(family_detection_binary_image, vertical_logical_lines)
    horizontal_logical_lines = prune_contained_horizontal_logical_lines_result.pruned_logical_lines
    vertical_logical_lines = prune_contained_vertical_logical_lines_result.pruned_logical_lines
    prune_contained_horizontal_logical_lines_result = _clone_containment_prune_result(
        prune_contained_horizontal_logical_lines_result
    )
    prune_contained_vertical_logical_lines_result = _clone_containment_prune_result(
        prune_contained_vertical_logical_lines_result
    )

    merge_vertex_contained_horizontal_logical_lines_result: MergeVertexContainedLogicalLinesResult = merge_logical_lines_by_vertex_axis_containment(family_detection_binary_image, horizontal_logical_lines, horizontal_angle_degrees, config)
    merge_vertex_contained_vertical_logical_lines_result: MergeVertexContainedLogicalLinesResult = merge_logical_lines_by_vertex_axis_containment(family_detection_binary_image, vertical_logical_lines, vertical_angle_degrees, config)
    horizontal_logical_lines = merge_vertex_contained_horizontal_logical_lines_result.merged_logical_lines
    vertical_logical_lines = merge_vertex_contained_vertical_logical_lines_result.merged_logical_lines
    # assign_logical_line_debug_names(horizontal_logical_lines, "H")
    # assign_logical_line_debug_names(vertical_logical_lines, "V")
    horizontal_post_merge_logical_lines = _clone_logical_lines(horizontal_logical_lines)
    vertical_post_merge_logical_lines = _clone_logical_lines(vertical_logical_lines)
    merge_vertex_contained_horizontal_logical_lines_result = (
        _clone_vertex_containment_merge_result(
            merge_vertex_contained_horizontal_logical_lines_result
        )
    )
    merge_vertex_contained_vertical_logical_lines_result = (
        _clone_vertex_containment_merge_result(
            merge_vertex_contained_vertical_logical_lines_result
        )
    )

    horizontal_logical_lines, vertical_logical_lines = connect_logical_lines_by_pixels(
        pixel_connection_binary,
        horizontal_logical_lines,
        vertical_logical_lines,
        axis_gap_tolerance_px=config.logical_line_axis_gap_tolerance_px,
        cross_axis_thickness_px=config.logical_line_cross_axis_thickness_px,
        rectangle_vector_length_px=config.tolerance_rectangle_vector_length_px,
        rectangle_padding_px=config.tolerance_rectangle_padding_px
    )
    horizontal_post_connection_logical_lines = _clone_logical_lines(
        horizontal_logical_lines
    )
    vertical_post_connection_logical_lines = _clone_logical_lines(
        vertical_logical_lines
    )

    assign_logical_line_intersections(
        horizontal_logical_lines,
        vertical_logical_lines,
    )

    trim_logical_lines_to_intersections(
        horizontal_logical_lines,
        vertical_logical_lines,
    )

    logical_line_intersections = [
        logical_line_intersection
        for logical_line in horizontal_logical_lines
        for logical_line_intersection in logical_line.intersections
    ]
    horizontal_boundary_groups = build_boundary_groups(
        horizontal_logical_lines,
        vertical_logical_lines,
    )
    vertical_boundary_groups = build_boundary_groups(
        vertical_logical_lines,
        horizontal_logical_lines,
    )
    logical_line_frame_candidates = find_logical_line_frame_candidates(
        horizontal_boundary_groups,
        vertical_boundary_groups,
    )
    logical_line_frame_candidates = rank_logical_line_frame_candidates(
        logical_line_frame_candidates
    )
    selected_logical_line_frame_candidate = (
        select_best_ranked_logical_line_frame_candidate(
            logical_line_frame_candidates,
            image_height=image_height,
            image_width=image_width,
        )
    )
    selected_logical_line_frame_warp_result = None
    if (
        selected_logical_line_frame_candidate is not None
        and warp_source_image is not None
    ):
        selected_logical_line_frame_warp_result = warp_selected_frame_to_square(
            image=warp_source_image,
            frame_candidate=selected_logical_line_frame_candidate,
            output_size_px=config.warp_output_size_px,
            padding_px=config.warp_output_padding_px,
            grid_division_count=config.warp_cell_divisions,
            cells_output_mime_type=config.warp_cells_output_mime_type,
            cells_preview_gap_px=config.warp_cells_preview_gap_px,
            ml_ready_adaptive_block_size=config.adaptive_threshold_block_size,
            ml_ready_adaptive_c=config.adaptive_threshold_c_value,
        )

    return RawLineFamilyResult(
        raw_segment_count=len(family_detection_segments),
        orientation_offset_degrees=orientation_offset_degrees,
        horizontal_angle_degrees=horizontal_angle_degrees,
        vertical_angle_degrees=vertical_angle_degrees,
        horizontal_segments=horizontal_segments,
        vertical_segments=vertical_segments,
        horizontal_pre_connection_logical_lines=horizontal_pre_connection_logical_lines,
        vertical_pre_connection_logical_lines=vertical_pre_connection_logical_lines,
        horizontal_containment_prune_result=(
            prune_contained_horizontal_logical_lines_result
        ),
        vertical_containment_prune_result=(
            prune_contained_vertical_logical_lines_result
        ),
        horizontal_vertex_containment_merge_result=(
            merge_vertex_contained_horizontal_logical_lines_result
        ),
        vertical_vertex_containment_merge_result=(
            merge_vertex_contained_vertical_logical_lines_result
        ),
        horizontal_post_merge_logical_lines=horizontal_post_merge_logical_lines,
        vertical_post_merge_logical_lines=vertical_post_merge_logical_lines,
        horizontal_post_connection_logical_lines=(
            horizontal_post_connection_logical_lines
        ),
        vertical_post_connection_logical_lines=(
            vertical_post_connection_logical_lines
        ),
        horizontal_logical_lines=horizontal_logical_lines,
        vertical_logical_lines=vertical_logical_lines,
        logical_line_intersections=logical_line_intersections,
        horizontal_boundary_groups=horizontal_boundary_groups,
        vertical_boundary_groups=vertical_boundary_groups,
        logical_line_frame_candidates=logical_line_frame_candidates,
        selected_logical_line_frame_candidate=selected_logical_line_frame_candidate,
        selected_logical_line_frame_warp_result=(
            selected_logical_line_frame_warp_result
        ),
    )


__all__ = [
    "RawLineFamilyResult",
    "detect_line_families",
]
