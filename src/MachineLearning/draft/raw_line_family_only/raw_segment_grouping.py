from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

import numpy as np

from geometry import (
    angle_difference_degrees,
)
from logical_line_segment_geometry import (
    point_axis_value,
    rasterize_line_points,
    rebuild_segment_axis_range,
    supporting_line_intersection_point,
)
from logical_line_types import (
    RawSegmentGroupResult,
    RawSegmentGroupStatus,
    segment_sort_key,
)
from models import LineFamilyName, LineSegment, SegmentOrigin

if TYPE_CHECKING:
    from logical_line_core import LogicalLine


@dataclass(frozen=True, slots=True)
class ResolvedRawSegment:
    source_segment: LineSegment
    output_segment: LineSegment
    status: RawSegmentGroupStatus


def group_raw_segments_in_line(
    logical_line: "LogicalLine",
    binary_image: np.ndarray,
    reference_angle_degrees: float,
    angle_tolerance_degrees: float,
    black_gap_tolerance_px: int,
) -> None:
    raw_segments = sorted(
        [
            line_segment
            for line_segment in logical_line.line_segments
            if line_segment.origin == SegmentOrigin.RAW
        ],
        key=segment_sort_key,
    )
    if not raw_segments:
        logical_line.raw_segment_group_results = []
        return

    raw_segment_group_results: list[RawSegmentGroupResult] = []
    remaining_segments = raw_segments

    while remaining_segments:
        candidate_window, trailing_segments = collect_raw_candidate_window(
            remaining_segments
        )
        raw_segment_group_results.extend(
            build_raw_segment_group_results(
                candidate_segments=candidate_window,
                family_name=logical_line.family_name,
                binary_image=binary_image,
                reference_angle_degrees=reference_angle_degrees,
                angle_tolerance_degrees=angle_tolerance_degrees,
                black_gap_tolerance_px=black_gap_tolerance_px,
            )
        )
        remaining_segments = sorted(trailing_segments, key=segment_sort_key)

    raw_segment_group_results = repair_adjacent_raw_group_boundaries(
        raw_segment_group_results=raw_segment_group_results,
        family_name=logical_line.family_name,
    )
    logical_line.raw_segment_group_results = raw_segment_group_results
    logical_line.replace_segments(
        [
            group_result.output_segment
            for group_result in raw_segment_group_results
        ]
    )


def collect_raw_candidate_window(
    line_segments: list[LineSegment],
) -> tuple[list[LineSegment], list[LineSegment]]:
    if not line_segments:
        return [], []

    candidate_window = [line_segments[0]]
    current_axis_end = line_segments[0].axis_end
    segment_index = 1
    while segment_index < len(line_segments):
        line_segment = line_segments[segment_index]
        if line_segment.axis_start > current_axis_end + 1:
            break
        candidate_window.append(line_segment)
        current_axis_end = max(current_axis_end, line_segment.axis_end)
        segment_index += 1

    return candidate_window, line_segments[segment_index:]


def build_raw_segment_group_results(
    candidate_segments: list[LineSegment],
    family_name: LineFamilyName,
    binary_image: np.ndarray,
    reference_angle_degrees: float,
    angle_tolerance_degrees: float,
    black_gap_tolerance_px: int,
) -> list[RawSegmentGroupResult]:
    if not candidate_segments:
        raise ValueError("candidate_segments cannot be empty.")

    del binary_image
    del black_gap_tolerance_px

    resolved_segments = resolve_overlapping_raw_segments(
        candidate_segments=candidate_segments,
        family_name=family_name,
        reference_angle_degrees=reference_angle_degrees,
        angle_tolerance_degrees=angle_tolerance_degrees,
    )
    return [
        RawSegmentGroupResult(
            seed_segment=resolved_segment.source_segment,
            consumed_segments=(resolved_segment.source_segment,),
            used_segments=(resolved_segment.source_segment,),
            deferred_segments=(),
            trial_segment=resolved_segment.source_segment,
            output_segment=resolved_segment.output_segment,
            accepted_boundary_segment=resolved_segment.source_segment,
            first_invalid_gap_point=None,
            status=resolved_segment.status,
        )
        for resolved_segment in resolved_segments
    ]


def build_raw_segment_group_result(
    candidate_segments: list[LineSegment],
    family_name: LineFamilyName,
    binary_image: np.ndarray,
    reference_angle_degrees: float,
    angle_tolerance_degrees: float,
    black_gap_tolerance_px: int,
) -> RawSegmentGroupResult:
    group_results = build_raw_segment_group_results(
        candidate_segments=candidate_segments,
        family_name=family_name,
        binary_image=binary_image,
        reference_angle_degrees=reference_angle_degrees,
        angle_tolerance_degrees=angle_tolerance_degrees,
        black_gap_tolerance_px=black_gap_tolerance_px,
    )
    if not group_results:
        raise ValueError("candidate_segments did not produce any group result.")
    return group_results[0]


def resolve_overlapping_raw_segments(
    candidate_segments: list[LineSegment],
    family_name: LineFamilyName,
    reference_angle_degrees: float,
    angle_tolerance_degrees: float,
) -> list[ResolvedRawSegment]:
    if not candidate_segments:
        return []

    seed_segment = candidate_segments[0]
    valid_boundary_segments = [
        line_segment
        for line_segment in candidate_segments
        if angle_difference_degrees(
            line_segment.angle_degrees,
            reference_angle_degrees,
        )
        <= angle_tolerance_degrees
    ]
    if seed_segment not in valid_boundary_segments:
        valid_boundary_segments.insert(0, seed_segment)

    valid_boundary_segments = sorted(valid_boundary_segments, key=segment_sort_key)
    intersection_axis_values = collect_raw_segment_intersection_axis_values(
        valid_boundary_segments,
        family_name,
    )

    min_axis = min(line_segment.axis_start for line_segment in valid_boundary_segments)
    max_axis = max(line_segment.axis_end for line_segment in valid_boundary_segments)
    current_axis = min_axis
    retired_segments: set[LineSegment] = set()
    resolved_segments: list[ResolvedRawSegment] = []

    while current_axis <= max_axis:
        active_segments = [
            line_segment
            for line_segment in valid_boundary_segments
            if (
                line_segment not in retired_segments
                and line_segment.axis_start <= current_axis <= line_segment.axis_end
            )
        ]
        if not active_segments:
            future_segments = [
                line_segment
                for line_segment in valid_boundary_segments
                if (
                    line_segment not in retired_segments
                    and line_segment.axis_start > current_axis
                )
            ]
            if not future_segments:
                break
            current_axis = min(
                future_segments,
                key=lambda line_segment: (
                    line_segment.axis_start,
                    line_segment.axis_end,
                ),
            ).axis_start
            continue

        source_segment = choose_raw_continuation_segment(
            active_segments,
            reference_angle_degrees,
        )
        output_axis_end = choose_raw_continuation_end_axis(
            source_segment=source_segment,
            current_axis=current_axis,
            candidate_segments=valid_boundary_segments,
            retired_segments=retired_segments,
            intersection_axis_values=intersection_axis_values,
        )
        if output_axis_end < current_axis:
            retired_segments.add(source_segment)
            current_axis += 1
            continue

        output_segment = rebuild_segment_axis_range(
            source_segment,
            axis_start=current_axis,
            axis_end=output_axis_end,
        )
        if output_segment is None:
            if output_axis_end < source_segment.axis_end:
                retired_segments.add(source_segment)
            current_axis = output_axis_end + 1
            continue

        was_trimmed = (
            output_segment.axis_start != source_segment.axis_start
            or output_segment.axis_end != source_segment.axis_end
        )
        if was_trimmed:
            status = RawSegmentGroupStatus.TRIMMED_BY_OVERLAP
        elif len(valid_boundary_segments) > 1:
            status = RawSegmentGroupStatus.MERGED
        else:
            status = RawSegmentGroupStatus.SINGLE_SEGMENT

        resolved_segments.append(
            ResolvedRawSegment(
                source_segment=source_segment,
                output_segment=output_segment,
                status=status,
            )
        )
        if output_axis_end < source_segment.axis_end:
            retired_segments.add(source_segment)
        current_axis = output_axis_end + 1

    return resolved_segments


def collect_raw_segment_intersection_axis_values(
    line_segments: list[LineSegment],
    family_name: LineFamilyName,
) -> tuple[int, ...]:
    intersection_axis_values: set[int] = set()
    for first_index, first_segment in enumerate(line_segments):
        for second_segment in line_segments[first_index + 1 :]:
            intersection_axis_value = find_raw_segment_intersection_axis_value(
                first_segment,
                second_segment,
                family_name,
            )
            if intersection_axis_value is None:
                continue
            intersection_axis_values.add(intersection_axis_value)
    return tuple(sorted(intersection_axis_values))


def find_raw_segment_intersection_axis_value(
    first_segment: LineSegment,
    second_segment: LineSegment,
    family_name: LineFamilyName,
) -> int | None:
    overlap_axis_start = max(first_segment.axis_start, second_segment.axis_start)
    overlap_axis_end = min(first_segment.axis_end, second_segment.axis_end)
    if overlap_axis_start > overlap_axis_end:
        return None

    intersection_point = supporting_line_intersection_point(
        first_segment,
        second_segment,
    )
    if intersection_point is None:
        return None

    intersection_axis_value = floating_axis_value(family_name, intersection_point)
    rounded_axis_value = int(round(intersection_axis_value))
    if overlap_axis_start <= rounded_axis_value <= overlap_axis_end:
        return rounded_axis_value
    return None


def floating_axis_value(
    family_name: LineFamilyName,
    point: tuple[float, float],
) -> float:
    if family_name == LineFamilyName.HORIZONTAL:
        return float(point[0])
    if family_name == LineFamilyName.VERTICAL:
        return float(point[1])
    raise NotImplementedError("Axis value is available only for classified lines.")


def choose_raw_continuation_segment(
    active_segments: list[LineSegment],
    reference_angle_degrees: float,
) -> LineSegment:
    return min(
        active_segments,
        key=lambda line_segment: (
            line_segment.axis_end,
            angle_difference_degrees(
                line_segment.angle_degrees,
                reference_angle_degrees,
            ),
            line_segment.axis_start,
            line_segment.cross_axis_start,
            line_segment.cross_axis_end,
        ),
    )


def choose_raw_continuation_end_axis(
    source_segment: LineSegment,
    current_axis: int,
    candidate_segments: list[LineSegment],
    retired_segments: set[LineSegment],
    intersection_axis_values: tuple[int, ...],
) -> int:
    switch_axis_values = [
        intersection_axis_value
        for intersection_axis_value in intersection_axis_values
        if (
            current_axis < intersection_axis_value < source_segment.axis_end
            and has_raw_continuation_after_axis(
                source_segment=source_segment,
                switch_axis=intersection_axis_value,
                candidate_segments=candidate_segments,
                retired_segments=retired_segments,
            )
        )
    ]
    if switch_axis_values:
        return min(switch_axis_values)
    return source_segment.axis_end


def has_raw_continuation_after_axis(
    source_segment: LineSegment,
    switch_axis: int,
    candidate_segments: list[LineSegment],
    retired_segments: set[LineSegment],
) -> bool:
    next_axis = switch_axis + 1
    return any(
        line_segment
        for line_segment in candidate_segments
        if (
            line_segment is not source_segment
            and line_segment not in retired_segments
            and line_segment.axis_start <= next_axis <= line_segment.axis_end
            and line_segment.axis_end > switch_axis
        )
    )


def find_first_invalid_black_gap_point(
    binary_image: np.ndarray,
    line_segment: LineSegment,
    black_gap_tolerance_px: int,
) -> tuple[int, int] | None:
    black_gap_start: tuple[int, int] | None = None
    black_gap_length = 0
    image_height, image_width = binary_image.shape[:2]

    for point in rasterize_line_points(line_segment.start, line_segment.end):
        x_coord, y_coord = point
        is_white = (
            0 <= x_coord < image_width
            and 0 <= y_coord < image_height
            and binary_image[y_coord, x_coord] == 255
        )
        if is_white:
            black_gap_start = None
            black_gap_length = 0
            continue

        if black_gap_start is None:
            black_gap_start = point
        black_gap_length += 1
        if black_gap_length > black_gap_tolerance_px:
            return black_gap_start

    return None


def repair_adjacent_raw_group_boundaries(
    raw_segment_group_results: list[RawSegmentGroupResult],
    family_name: LineFamilyName,
) -> list[RawSegmentGroupResult]:
    if len(raw_segment_group_results) < 2:
        return raw_segment_group_results

    repaired_group_results = list(raw_segment_group_results)
    for group_index in range(len(repaired_group_results) - 1):
        repaired_pair = repair_raw_group_pair(
            first_group_result=repaired_group_results[group_index],
            second_group_result=repaired_group_results[group_index + 1],
            family_name=family_name,
        )
        if repaired_pair is None:
            continue
        repaired_group_results[group_index] = repaired_pair[0]
        repaired_group_results[group_index + 1] = repaired_pair[1]

    return repaired_group_results


def repair_raw_group_pair(
    first_group_result: RawSegmentGroupResult,
    second_group_result: RawSegmentGroupResult,
    family_name: LineFamilyName,
) -> tuple[RawSegmentGroupResult, RawSegmentGroupResult] | None:
    first_segment = first_group_result.output_segment
    second_segment = second_group_result.output_segment
    if first_segment.axis_start > second_segment.axis_start:
        first_group_result, second_group_result = (
            second_group_result,
            first_group_result,
        )
        first_segment, second_segment = second_segment, first_segment

    if first_segment.axis_end < second_segment.axis_start:
        return None

    overlap_axis_start = max(first_segment.axis_start, second_segment.axis_start)
    overlap_axis_end = min(first_segment.axis_end, second_segment.axis_end)
    if overlap_axis_start > overlap_axis_end:
        return None

    preferred_axis_value = float(overlap_axis_start + overlap_axis_end) / 2.0
    intersection_point = supporting_line_intersection_point(
        first_segment,
        second_segment,
    )
    if intersection_point is not None:
        intersection_axis_value = (
            intersection_point[0]
            if family_name == LineFamilyName.HORIZONTAL
            else intersection_point[1]
        )
        if overlap_axis_start - 1.0 <= intersection_axis_value <= overlap_axis_end + 1.0:
            preferred_axis_value = intersection_axis_value

    candidate_pairs: list[
        tuple[LineSegment, LineSegment, tuple[float, float, float], int]
    ] = []
    for boundary_axis in range(overlap_axis_start - 1, overlap_axis_end + 1):
        candidate_pair = build_repaired_group_pair(
            first_segment=first_segment,
            second_segment=second_segment,
            first_end_axis=boundary_axis,
            second_start_axis=boundary_axis + 1,
        )
        if candidate_pair is None:
            continue
        repaired_first_segment, repaired_second_segment = candidate_pair
        score = (
            abs(repaired_first_segment.length - repaired_second_segment.length),
            abs(float(boundary_axis) - preferred_axis_value),
            abs(repaired_first_segment.axis_end - first_segment.axis_end)
            + abs(repaired_second_segment.axis_start - second_segment.axis_start),
        )
        candidate_pairs.append(
            (
                repaired_first_segment,
                repaired_second_segment,
                score,
                boundary_axis,
            )
        )

    if not candidate_pairs:
        return None

    repaired_first_segment, repaired_second_segment, _, _ = min(
        candidate_pairs,
        key=lambda candidate: (
            candidate[2][0],
            candidate[2][1],
        ),
    )
    return (
        replace(first_group_result, output_segment=repaired_first_segment),
        replace(second_group_result, output_segment=repaired_second_segment),
    )


def build_repaired_group_pair(
    first_segment: LineSegment,
    second_segment: LineSegment,
    first_end_axis: int,
    second_start_axis: int,
) -> tuple[LineSegment, LineSegment] | None:
    repaired_first_segment = rebuild_segment_axis_range(
        first_segment,
        axis_end=first_end_axis,
    )
    repaired_second_segment = rebuild_segment_axis_range(
        second_segment,
        axis_start=second_start_axis,
    )
    if repaired_first_segment is None or repaired_second_segment is None:
        return None
    if repaired_first_segment.axis_end + 1 != repaired_second_segment.axis_start:
        return None
    return repaired_first_segment, repaired_second_segment


__all__ = [
    "build_raw_segment_group_result",
    "build_raw_segment_group_results",
    "build_repaired_group_pair",
    "collect_raw_segment_intersection_axis_values",
    "collect_raw_candidate_window",
    "find_first_invalid_black_gap_point",
    "find_raw_segment_intersection_axis_value",
    "group_raw_segments_in_line",
    "repair_adjacent_raw_group_boundaries",
    "repair_raw_group_pair",
    "resolve_overlapping_raw_segments",
]
