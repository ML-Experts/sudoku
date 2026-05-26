from __future__ import annotations

from dataclasses import dataclass, field

import cv2
import numpy as np

from sudoku_board_debug_core import (
    InfiniteLine,
    LineSegment,
    angle_difference_degrees,
    build_line_segment,
    fit_line,
    get_dominant_angle_degrees,
    get_line_normal,
)

@dataclass(frozen=True)
class LineMergeSettings:
    raw_hough_threshold: int = 35
    raw_min_line_length_ratio: float = 0.08
    raw_max_line_gap_ratio: float = 0.02
    family_angle_tolerance_degrees: float = 20.0
    merge_angle_tolerance_degrees: float = 6.0
    merge_distance_px: float = 10.0
    merge_endpoint_gap_px: float = 20.0
    post_merge_projection_distance_px: float = 8.0
    post_merge_endpoint_gap_px: float = 28.0
    post_merge_min_overlap_ratio: float = 0.45
    min_merged_span_ratio: float = 0.16
    max_merged_thickness_px: float = 18.0

@dataclass(frozen=True)
class ResolvedLineMergeSettings:
    raw_hough_threshold: int
    raw_min_line_length_px: int
    raw_max_line_gap_px: int
    family_angle_tolerance_degrees: float
    merge_angle_tolerance_degrees: float
    merge_distance_px: float
    merge_endpoint_gap_px: float
    post_merge_projection_distance_px: float
    post_merge_endpoint_gap_px: float
    post_merge_min_overlap_ratio: float
    min_merged_span_px: int
    max_merged_thickness_px: float

@dataclass
class MergedLineCandidate:
    family_name: str
    family_angle_degrees: float
    segments: list[LineSegment] = field(default_factory=list)
    line: InfiniteLine | None = None
    projection: float = 0.0
    span_start: float = 0.0
    span_end: float = 0.0
    span_length: float = 0.0
    thickness_px: float = 0.0
    total_length: float = 0.0

@dataclass(frozen=True)
class LineExperimentResult:
    name: str
    binary: np.ndarray
    resolved_settings: ResolvedLineMergeSettings
    raw_segments: list[LineSegment]
    primary_angle_degrees: float | None
    secondary_angle_degrees: float | None
    primary_segments: list[LineSegment]
    secondary_segments: list[LineSegment]
    primary_merged_candidates: list[MergedLineCandidate]
    secondary_merged_candidates: list[MergedLineCandidate]
    primary_filtered_candidates: list[MergedLineCandidate]
    secondary_filtered_candidates: list[MergedLineCandidate]
    primary_final_candidates: list[MergedLineCandidate]
    secondary_final_candidates: list[MergedLineCandidate]

def resolve_line_merge_settings(
    image_shape: tuple[int, int],
    settings: LineMergeSettings,
) -> ResolvedLineMergeSettings:
    minimum_dimension = min(image_shape)
    raw_min_line_length_px = max(
        8,
        int(round(minimum_dimension * settings.raw_min_line_length_ratio)),
    )
    raw_max_line_gap_px = max(
        2,
        int(round(minimum_dimension * settings.raw_max_line_gap_ratio)),
    )
    min_merged_span_px = max(
        raw_min_line_length_px,
        int(round(minimum_dimension * settings.min_merged_span_ratio)),
    )
    return ResolvedLineMergeSettings(
        raw_hough_threshold=settings.raw_hough_threshold,
        raw_min_line_length_px=raw_min_line_length_px,
        raw_max_line_gap_px=raw_max_line_gap_px,
        family_angle_tolerance_degrees=settings.family_angle_tolerance_degrees,
        merge_angle_tolerance_degrees=settings.merge_angle_tolerance_degrees,
        merge_distance_px=settings.merge_distance_px,
        merge_endpoint_gap_px=settings.merge_endpoint_gap_px,
        post_merge_projection_distance_px=settings.post_merge_projection_distance_px,
        post_merge_endpoint_gap_px=settings.post_merge_endpoint_gap_px,
        post_merge_min_overlap_ratio=settings.post_merge_min_overlap_ratio,
        min_merged_span_px=min_merged_span_px,
        max_merged_thickness_px=settings.max_merged_thickness_px,
    )

def point_position_on_line(
    point: tuple[float, float],
    line: InfiniteLine,
) -> float:
    point_array = np.array(point, dtype=np.float32)
    return float(np.dot(point_array - line.point, line.direction))

def interval_gap(
    first_interval: tuple[float, float],
    second_interval: tuple[float, float],
) -> float:
    first_start, first_end = min(first_interval), max(first_interval)
    second_start, second_end = min(second_interval), max(second_interval)
    if first_end < second_start:
        return second_start - first_end
    if second_end < first_start:
        return first_start - second_end
    return 0.0

def interval_overlap(
    first_interval: tuple[float, float],
    second_interval: tuple[float, float],
) -> float:
    first_start, first_end = min(first_interval), max(first_interval)
    second_start, second_end = min(second_interval), max(second_interval)
    return max(0.0, min(first_end, second_end) - max(first_start, second_start))

def interval_length(interval: tuple[float, float]) -> float:
    interval_start, interval_end = min(interval), max(interval)
    return interval_end - interval_start

def interval_overlap_ratio(
    first_interval: tuple[float, float],
    second_interval: tuple[float, float],
) -> float:
    shorter_length = min(
        interval_length(first_interval),
        interval_length(second_interval),
    )
    if shorter_length <= 1e-6:
        return 0.0
    return interval_overlap(first_interval, second_interval) / shorter_length

def extract_raw_line_segments(
    binary_image: np.ndarray,
    resolved_settings: ResolvedLineMergeSettings,
) -> list[LineSegment]:
    raw_segments = cv2.HoughLinesP(
        binary_image,
        rho=1,
        theta=np.pi / 180.0,
        threshold=resolved_settings.raw_hough_threshold,
        minLineLength=resolved_settings.raw_min_line_length_px,
        maxLineGap=resolved_settings.raw_max_line_gap_px,
    )
    if raw_segments is None:
        return []
    return [build_line_segment(raw_segment[0]) for raw_segment in raw_segments]

def collect_family_segments(
    line_segments: list[LineSegment],
    family_angle_degrees: float,
    angle_tolerance_degrees: float,
) -> list[LineSegment]:
    return [
        line_segment
        for line_segment in line_segments
        if angle_difference_degrees(line_segment.angle_degrees, family_angle_degrees)
        <= angle_tolerance_degrees
    ]

def build_merged_candidate(
    family_name: str,
    family_angle_degrees: float,
    segments: list[LineSegment],
) -> MergedLineCandidate:
    fitted_line = fit_line(segments)
    line_normal = get_line_normal(family_angle_degrees)
    midpoint_projections = [
        float(np.dot(line_segment.midpoint(), line_normal))
        for line_segment in segments
    ]
    endpoint_positions = []
    for line_segment in segments:
        endpoint_positions.append(point_position_on_line(line_segment.start, fitted_line))
        endpoint_positions.append(point_position_on_line(line_segment.end, fitted_line))

    span_start = min(endpoint_positions)
    span_end = max(endpoint_positions)
    thickness_px = 0.0
    if midpoint_projections:
        thickness_px = max(midpoint_projections) - min(midpoint_projections)

    return MergedLineCandidate(
        family_name=family_name,
        family_angle_degrees=family_angle_degrees,
        segments=list(segments),
        line=fitted_line,
        projection=float(np.mean(midpoint_projections)) if midpoint_projections else 0.0,
        span_start=float(span_start),
        span_end=float(span_end),
        span_length=float(span_end - span_start),
        thickness_px=float(thickness_px),
        total_length=float(sum(line_segment.length for line_segment in segments)),
    )

def segment_interval_on_candidate_line(
    line_segment: LineSegment,
    candidate: MergedLineCandidate,
) -> tuple[float, float]:
    if candidate.line is None:
        raise ValueError("Merged line candidate is missing fitted line.")
    start_position = point_position_on_line(line_segment.start, candidate.line)
    end_position = point_position_on_line(line_segment.end, candidate.line)
    return start_position, end_position

def can_attach_segment(
    candidate: MergedLineCandidate,
    line_segment: LineSegment,
    resolved_settings: ResolvedLineMergeSettings,
) -> bool:
    if (
        angle_difference_degrees(
            line_segment.angle_degrees,
            candidate.family_angle_degrees,
        )
        > resolved_settings.merge_angle_tolerance_degrees
    ):
        return False

    line_normal = get_line_normal(candidate.family_angle_degrees)
    segment_projection = float(np.dot(line_segment.midpoint(), line_normal))
    projection_distance = abs(segment_projection - candidate.projection)
    if projection_distance > resolved_settings.merge_distance_px:
        return False

    candidate_interval = (candidate.span_start, candidate.span_end)
    segment_interval = segment_interval_on_candidate_line(line_segment, candidate)
    return (
        interval_gap(candidate_interval, segment_interval)
        <= resolved_settings.merge_endpoint_gap_px
    )

def merge_parallel_segments(
    line_segments: list[LineSegment],
    family_angle_degrees: float,
    family_name: str,
    resolved_settings: ResolvedLineMergeSettings,
) -> list[MergedLineCandidate]:
    family_normal = get_line_normal(family_angle_degrees)
    sorted_segments = sorted(
        line_segments,
        key=lambda line_segment: (
            float(np.dot(line_segment.midpoint(), family_normal)),
            min(
                line_segment.start[0],
                line_segment.end[0],
                line_segment.start[1],
                line_segment.end[1],
            ),
        ),
    )

    merged_candidates: list[MergedLineCandidate] = []
    for line_segment in sorted_segments:
        best_match_index = None
        best_match_score = None

        for candidate_index, candidate in enumerate(merged_candidates):
            if not can_attach_segment(candidate, line_segment, resolved_settings):
                continue

            candidate_interval = (candidate.span_start, candidate.span_end)
            segment_interval = segment_interval_on_candidate_line(line_segment, candidate)
            family_normal = get_line_normal(candidate.family_angle_degrees)
            segment_projection = float(np.dot(line_segment.midpoint(), family_normal))
            score = (
                abs(segment_projection - candidate.projection),
                interval_gap(candidate_interval, segment_interval),
            )
            if best_match_score is None or score < best_match_score:
                best_match_score = score
                best_match_index = candidate_index

        if best_match_index is None:
            merged_candidates.append(
                build_merged_candidate(
                    family_name,
                    family_angle_degrees,
                    [line_segment],
                )
            )
            continue

        merged_segments = merged_candidates[best_match_index].segments + [line_segment]
        merged_candidates[best_match_index] = build_merged_candidate(
            family_name,
            family_angle_degrees,
            merged_segments,
        )

    return sorted(merged_candidates, key=lambda candidate: candidate.projection)

def can_merge_candidates(
    first_candidate: MergedLineCandidate,
    second_candidate: MergedLineCandidate,
    resolved_settings: ResolvedLineMergeSettings,
) -> bool:
    projection_distance = abs(
        first_candidate.projection - second_candidate.projection
    )
    if projection_distance > resolved_settings.post_merge_projection_distance_px:
        return False

    first_interval = (first_candidate.span_start, first_candidate.span_end)
    second_interval = (second_candidate.span_start, second_candidate.span_end)
    overlap_ratio = interval_overlap_ratio(first_interval, second_interval)
    if overlap_ratio >= resolved_settings.post_merge_min_overlap_ratio:
        return True

    return (
        interval_gap(first_interval, second_interval)
        <= resolved_settings.post_merge_endpoint_gap_px
    )

def merge_close_candidates(
    candidates: list[MergedLineCandidate],
    resolved_settings: ResolvedLineMergeSettings,
) -> list[MergedLineCandidate]:
    sorted_candidates = sorted(candidates, key=lambda candidate: candidate.projection)
    merged_candidates: list[MergedLineCandidate] = []

    for candidate in sorted_candidates:
        best_match_index = None
        best_match_score = None
        candidate_interval = (candidate.span_start, candidate.span_end)

        for candidate_index, existing_candidate in enumerate(merged_candidates):
            if not can_merge_candidates(
                existing_candidate,
                candidate,
                resolved_settings,
            ):
                continue

            existing_interval = (
                existing_candidate.span_start,
                existing_candidate.span_end,
            )
            overlap_ratio = interval_overlap_ratio(existing_interval, candidate_interval)
            score = (
                abs(existing_candidate.projection - candidate.projection),
                -overlap_ratio,
                interval_gap(existing_interval, candidate_interval),
            )
            if best_match_score is None or score < best_match_score:
                best_match_score = score
                best_match_index = candidate_index

        if best_match_index is None:
            merged_candidates.append(
                build_merged_candidate(
                    candidate.family_name,
                    candidate.family_angle_degrees,
                    candidate.segments,
                )
            )
            continue

        merged_segments = merged_candidates[best_match_index].segments + candidate.segments
        merged_candidates[best_match_index] = build_merged_candidate(
            candidate.family_name,
            candidate.family_angle_degrees,
            merged_segments,
        )

    return sorted(merged_candidates, key=lambda candidate: candidate.projection)

def filter_merged_candidates(
    candidates: list[MergedLineCandidate],
    resolved_settings: ResolvedLineMergeSettings,
) -> list[MergedLineCandidate]:
    return [
        candidate
        for candidate in candidates
        if candidate.span_length >= resolved_settings.min_merged_span_px
        and candidate.thickness_px <= resolved_settings.max_merged_thickness_px
    ]

def describe_merged_candidates(
    candidates: list[MergedLineCandidate],
) -> list[str]:
    return [
        (
            f"proj={candidate.projection:.1f}, span={candidate.span_length:.1f}, "
            f"thickness={candidate.thickness_px:.1f}, "
            f"segments={len(candidate.segments)}, len={candidate.total_length:.1f}"
        )
        for candidate in candidates
    ]

def run_line_detection_experiment(
    variant_name: str,
    binary_image: np.ndarray,
    settings: LineMergeSettings,
) -> LineExperimentResult:
    resolved_settings = resolve_line_merge_settings(binary_image.shape, settings)
    raw_segments = extract_raw_line_segments(binary_image, resolved_settings)
    if not raw_segments:
        return LineExperimentResult(
            name=variant_name,
            binary=binary_image,
            resolved_settings=resolved_settings,
            raw_segments=[],
            primary_angle_degrees=None,
            secondary_angle_degrees=None,
            primary_segments=[],
            secondary_segments=[],
            primary_merged_candidates=[],
            secondary_merged_candidates=[],
            primary_filtered_candidates=[],
            secondary_filtered_candidates=[],
            primary_final_candidates=[],
            secondary_final_candidates=[],
        )

    primary_angle_degrees = get_dominant_angle_degrees(raw_segments)
    secondary_angle_degrees = (primary_angle_degrees + 90.0) % 180.0
    primary_segments = collect_family_segments(
        raw_segments,
        primary_angle_degrees,
        resolved_settings.family_angle_tolerance_degrees,
    )
    secondary_segments = collect_family_segments(
        raw_segments,
        secondary_angle_degrees,
        resolved_settings.family_angle_tolerance_degrees,
    )

    primary_merged_candidates = merge_parallel_segments(
        primary_segments,
        primary_angle_degrees,
        "primary",
        resolved_settings,
    )
    secondary_merged_candidates = merge_parallel_segments(
        secondary_segments,
        secondary_angle_degrees,
        "secondary",
        resolved_settings,
    )

    primary_filtered_candidates = filter_merged_candidates(
        primary_merged_candidates,
        resolved_settings,
    )
    secondary_filtered_candidates = filter_merged_candidates(
        secondary_merged_candidates,
        resolved_settings,
    )

    primary_final_candidates = filter_merged_candidates(
        merge_close_candidates(primary_filtered_candidates, resolved_settings),
        resolved_settings,
    )
    secondary_final_candidates = filter_merged_candidates(
        merge_close_candidates(secondary_filtered_candidates, resolved_settings),
        resolved_settings,
    )

    return LineExperimentResult(
        name=variant_name,
        binary=binary_image,
        resolved_settings=resolved_settings,
        raw_segments=raw_segments,
        primary_angle_degrees=primary_angle_degrees,
        secondary_angle_degrees=secondary_angle_degrees,
        primary_segments=primary_segments,
        secondary_segments=secondary_segments,
        primary_merged_candidates=primary_merged_candidates,
        secondary_merged_candidates=secondary_merged_candidates,
        primary_filtered_candidates=primary_filtered_candidates,
        secondary_filtered_candidates=secondary_filtered_candidates,
        primary_final_candidates=primary_final_candidates,
        secondary_final_candidates=secondary_final_candidates,
    )
