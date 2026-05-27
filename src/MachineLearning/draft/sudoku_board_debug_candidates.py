from __future__ import annotations

from dataclasses import dataclass
import math

import cv2
import numpy as np

from sudoku_board_debug_geometry import (
    BoardQuad,
    InfiniteLine,
    LineSegment,
    build_line_segment,
    collect_line_family,
    fit_line,
    get_dominant_angle_degrees,
    get_line_normal,
    has_sufficient_area,
    intersect_lines,
    order_points_clockwise,
)
from sudoku_board_debug_preprocess import BoardDebugSettings


@dataclass(frozen=True)
class DistinctLineCandidate:
    line: InfiniteLine
    projection: float
    total_length: float
    segment_count: int
    segments: tuple[LineSegment, ...]


@dataclass(frozen=True)
class QuadCandidate:
    board_quad: BoardQuad
    score: float
    area: float
    perimeter: float
    rectangularity_score: float
    grid_support_score: float
    line_length_score: float
    boundary_coverage_score: float
    primary_pair: tuple[DistinctLineCandidate, DistinctLineCandidate]
    secondary_pair: tuple[DistinctLineCandidate, DistinctLineCandidate]


def extract_line_segments(
    binary_image: np.ndarray,
    settings: BoardDebugSettings,
) -> list[LineSegment]:
    image_height, image_width = binary_image.shape
    minimum_dimension = min(image_height, image_width)
    raw_segments = cv2.HoughLinesP(
        cv2.Canny(
            binary_image,
            settings.board_edge_canny_threshold_1,
            settings.board_edge_canny_threshold_2,
        ),
        rho=1,
        theta=np.pi / 180.0,
        threshold=settings.board_edge_hough_threshold,
        minLineLength=max(
            1,
            int(round(minimum_dimension * settings.board_edge_min_line_length_ratio)),
        ),
        maxLineGap=max(
            1,
            int(round(minimum_dimension * settings.board_edge_max_line_gap_ratio)),
        ),
    )
    if raw_segments is None or len(raw_segments) == 0:
        raise ValueError("No line segments were found in input image.")
    return [build_line_segment(raw_segment[0]) for raw_segment in raw_segments]


def project_segment_midpoint(line_segment: LineSegment, normal: np.ndarray) -> float:
    return float(np.dot(line_segment.midpoint(), normal))


def build_distinct_line_candidates(
    line_segments: list[LineSegment],
    line_angle_degrees: float,
    merge_distance: float,
    max_candidates: int,
) -> list[DistinctLineCandidate]:
    normal = get_line_normal(line_angle_degrees)
    sorted_segments = sorted(
        (
            (project_segment_midpoint(line_segment, normal), line_segment)
            for line_segment in line_segments
        ),
        key=lambda item: item[0],
    )

    grouped_segments: list[list[tuple[float, LineSegment]]] = []
    for projection, line_segment in sorted_segments:
        if not grouped_segments:
            grouped_segments.append([(projection, line_segment)])
            continue

        previous_group = grouped_segments[-1]
        previous_projection = previous_group[-1][0]
        if abs(projection - previous_projection) <= merge_distance:
            previous_group.append((projection, line_segment))
        else:
            grouped_segments.append([(projection, line_segment)])

    candidates = []
    for group in grouped_segments:
        projections = [projection for projection, _ in group]
        segments = [line_segment for _, line_segment in group]
        candidates.append(
            DistinctLineCandidate(
                line=fit_line(segments),
                projection=float(np.mean(projections)),
                total_length=float(sum(segment.length for segment in segments)),
                segment_count=len(segments),
                segments=tuple(segments),
            )
        )

    if len(candidates) <= max_candidates:
        return sorted(candidates, key=lambda candidate: candidate.projection)

    inner_candidates = sorted(
        candidates[1:-1],
        key=lambda candidate: candidate.total_length,
        reverse=True,
    )
    selected_candidates = [
        candidates[0],
        candidates[-1],
        *inner_candidates[: max_candidates - 2],
    ]
    unique_candidates = []
    seen_projections = set()
    for candidate in selected_candidates:
        key = round(candidate.projection, 4)
        if key not in seen_projections:
            seen_projections.add(key)
            unique_candidates.append(candidate)

    return sorted(unique_candidates, key=lambda candidate: candidate.projection)


def build_quad_from_line_pairs(
    primary_pair: tuple[DistinctLineCandidate, DistinctLineCandidate],
    secondary_pair: tuple[DistinctLineCandidate, DistinctLineCandidate],
) -> BoardQuad:
    board_points = np.array(
        [
            intersect_lines(primary_pair[0].line, secondary_pair[0].line),
            intersect_lines(primary_pair[0].line, secondary_pair[1].line),
            intersect_lines(primary_pair[1].line, secondary_pair[1].line),
            intersect_lines(primary_pair[1].line, secondary_pair[0].line),
        ],
        dtype=np.float32,
    )
    ordered_points = order_points_clockwise(board_points)
    return BoardQuad(
        top_left=ordered_points[0],
        top_right=ordered_points[1],
        bottom_right=ordered_points[2],
        bottom_left=ordered_points[3],
    )


def compute_perimeter(points: tuple[tuple[float, float], ...]) -> float:
    perimeter = 0.0
    for index in range(4):
        x1, y1 = points[index]
        x2, y2 = points[(index + 1) % 4]
        perimeter += math.hypot(x2 - x1, y2 - y1)
    return perimeter


def compute_rectangularity_score(points: tuple[tuple[float, float], ...]) -> float:
    vectors = []
    for index in range(4):
        current_point = np.array(points[index], dtype=np.float32)
        next_point = np.array(points[(index + 1) % 4], dtype=np.float32)
        vector = next_point - current_point
        norm = float(np.linalg.norm(vector))
        if norm <= 1e-6:
            return 0.0
        vectors.append(vector / norm)

    orthogonality_scores = []
    for index in range(4):
        dot_product = float(np.dot(vectors[index], vectors[(index + 1) % 4]))
        orthogonality_scores.append(max(0.0, 1.0 - abs(dot_product)))

    parallelism_scores = []
    for first_index, second_index in ((0, 2), (1, 3)):
        dot_product = float(np.dot(vectors[first_index], vectors[second_index]))
        parallelism_scores.append(max(0.0, abs(dot_product)))

    return float(np.mean(orthogonality_scores) * 0.6 + np.mean(parallelism_scores) * 0.4)


def count_candidates_between(
    candidates: list[DistinctLineCandidate],
    first_projection: float,
    second_projection: float,
) -> int:
    lower_bound = min(first_projection, second_projection)
    upper_bound = max(first_projection, second_projection)
    return sum(
        1
        for candidate in candidates
        if lower_bound <= candidate.projection <= upper_bound
    )


def point_position_along_line(point: tuple[float, float], line: InfiniteLine) -> float:
    point_array = np.array(point, dtype=np.float32)
    return float(np.dot(point_array - line.point, line.direction))


def segment_interval_along_line(
    line_segment: LineSegment,
    line: InfiniteLine,
) -> tuple[float, float]:
    start_position = point_position_along_line(line_segment.start, line)
    end_position = point_position_along_line(line_segment.end, line)
    return min(start_position, end_position), max(start_position, end_position)


def compute_interval_coverage(
    intervals: list[tuple[float, float]],
    target_start: float,
    target_end: float,
) -> float:
    interval_start = min(target_start, target_end)
    interval_end = max(target_start, target_end)
    target_length = interval_end - interval_start
    if target_length <= 1e-6:
        return 0.0

    clipped_intervals = []
    for start, end in intervals:
        clipped_start = max(start, interval_start)
        clipped_end = min(end, interval_end)
        if clipped_end > clipped_start:
            clipped_intervals.append((clipped_start, clipped_end))

    if not clipped_intervals:
        return 0.0

    clipped_intervals.sort(key=lambda item: item[0])
    merged_intervals = [clipped_intervals[0]]
    for start, end in clipped_intervals[1:]:
        previous_start, previous_end = merged_intervals[-1]
        if start <= previous_end:
            merged_intervals[-1] = (previous_start, max(previous_end, end))
        else:
            merged_intervals.append((start, end))

    covered_length = sum(end - start for start, end in merged_intervals)
    return float(min(covered_length / target_length, 1.0))


def compute_candidate_boundary_coverage(
    candidate: DistinctLineCandidate,
    first_corner: tuple[float, float],
    second_corner: tuple[float, float],
) -> float:
    target_start = point_position_along_line(first_corner, candidate.line)
    target_end = point_position_along_line(second_corner, candidate.line)
    intervals = [
        segment_interval_along_line(line_segment, candidate.line)
        for line_segment in candidate.segments
    ]
    return compute_interval_coverage(intervals, target_start, target_end)


def is_quad_convex(points: tuple[tuple[float, float], ...]) -> bool:
    contour = np.array(points, dtype=np.float32)
    return bool(cv2.isContourConvex(contour))


def score_quad_candidate(
    board_quad: BoardQuad,
    image_shape: tuple[int, int],
    primary_pair: tuple[DistinctLineCandidate, DistinctLineCandidate],
    secondary_pair: tuple[DistinctLineCandidate, DistinctLineCandidate],
    primary_candidates: list[DistinctLineCandidate],
    secondary_candidates: list[DistinctLineCandidate],
    settings: BoardDebugSettings,
) -> QuadCandidate | None:
    image_height, image_width = image_shape
    points = board_quad.as_clockwise_points()
    polygon = np.array(points, dtype=np.float32)
    area = float(cv2.contourArea(polygon))
    minimum_area = (
        image_width * image_height * settings.board_edge_minimum_board_area_ratio
    )
    if area <= minimum_area or not is_quad_convex(points):
        return None
    if not has_sufficient_area(
        points,
        image_width * image_height,
        settings.board_edge_minimum_board_area_ratio,
    ):
        return None

    perimeter = compute_perimeter(points)
    rectangularity_score = compute_rectangularity_score(points)
    primary_support = count_candidates_between(
        primary_candidates,
        primary_pair[0].projection,
        primary_pair[1].projection,
    )
    secondary_support = count_candidates_between(
        secondary_candidates,
        secondary_pair[0].projection,
        secondary_pair[1].projection,
    )
    if (
        primary_support < settings.min_interior_lines_per_side
        or secondary_support < settings.min_interior_lines_per_side
    ):
        return None

    top_coverage = compute_candidate_boundary_coverage(
        primary_pair[0],
        points[0],
        points[1],
    )
    bottom_coverage = compute_candidate_boundary_coverage(
        primary_pair[1],
        points[3],
        points[2],
    )
    left_coverage = compute_candidate_boundary_coverage(
        secondary_pair[0],
        points[0],
        points[3],
    )
    right_coverage = compute_candidate_boundary_coverage(
        secondary_pair[1],
        points[1],
        points[2],
    )
    minimum_boundary_coverage = min(
        top_coverage,
        bottom_coverage,
        left_coverage,
        right_coverage,
    )
    if minimum_boundary_coverage < settings.min_boundary_segment_coverage:
        return None

    boundary_coverage_score = (
        top_coverage + bottom_coverage + left_coverage + right_coverage
    ) / 4.0
    grid_support_score = min(primary_support, 10) / 10.0 + min(secondary_support, 10) / 10.0
    line_length_score = (
        primary_pair[0].total_length
        + primary_pair[1].total_length
        + secondary_pair[0].total_length
        + secondary_pair[1].total_length
    ) / float(max(image_width, image_height) * 4)
    area_score = area / float(image_width * image_height)

    score = (
        area_score * settings.area_score_weight
        + rectangularity_score * settings.rectangularity_score_weight
        + grid_support_score * settings.grid_support_score_weight
        + line_length_score * settings.line_length_score_weight
        + boundary_coverage_score * settings.boundary_coverage_score_weight
    )
    return QuadCandidate(
        board_quad=board_quad,
        score=score,
        area=area,
        perimeter=perimeter,
        rectangularity_score=rectangularity_score,
        grid_support_score=grid_support_score,
        line_length_score=line_length_score,
        boundary_coverage_score=boundary_coverage_score,
        primary_pair=primary_pair,
        secondary_pair=secondary_pair,
    )


def detect_board_quad_quad_candidates(
    binary_image: np.ndarray,
    settings: BoardDebugSettings,
) -> tuple[BoardQuad, dict[str, object]]:
    image_height, image_width = binary_image.shape
    minimum_dimension = min(image_height, image_width)
    merge_distance = (
        minimum_dimension * settings.board_edge_line_position_merge_distance_ratio
    )

    line_segments = extract_line_segments(binary_image, settings)
    primary_angle_degrees = get_dominant_angle_degrees(line_segments)
    secondary_angle_degrees = (primary_angle_degrees + 90.0) % 180.0
    primary_family = collect_line_family(
        line_segments,
        primary_angle_degrees,
        settings.board_edge_angle_tolerance_degrees,
    )
    secondary_family = collect_line_family(
        line_segments,
        secondary_angle_degrees,
        settings.board_edge_angle_tolerance_degrees,
    )
    if len(primary_family) < settings.board_edge_minimum_family_segments:
        raise ValueError("Primary board edge family is too small.")
    if len(secondary_family) < settings.board_edge_minimum_family_segments:
        raise ValueError("Secondary board edge family is too small.")

    primary_candidates = build_distinct_line_candidates(
        primary_family,
        primary_angle_degrees,
        merge_distance,
        settings.max_distinct_lines_per_family,
    )
    secondary_candidates = build_distinct_line_candidates(
        secondary_family,
        secondary_angle_degrees,
        merge_distance,
        settings.max_distinct_lines_per_family,
    )
    if len(primary_candidates) < 2 or len(secondary_candidates) < 2:
        raise ValueError("Not enough distinct lines to build quad candidates.")

    quad_candidates = []
    for primary_start in range(len(primary_candidates) - 1):
        for primary_end in range(primary_start + 1, len(primary_candidates)):
            primary_pair = (
                primary_candidates[primary_start],
                primary_candidates[primary_end],
            )
            for secondary_start in range(len(secondary_candidates) - 1):
                for secondary_end in range(secondary_start + 1, len(secondary_candidates)):
                    secondary_pair = (
                        secondary_candidates[secondary_start],
                        secondary_candidates[secondary_end],
                    )
                    try:
                        board_quad = build_quad_from_line_pairs(
                            primary_pair,
                            secondary_pair,
                        )
                    except ValueError:
                        continue

                    candidate = score_quad_candidate(
                        board_quad=board_quad,
                        image_shape=binary_image.shape,
                        primary_pair=primary_pair,
                        secondary_pair=secondary_pair,
                        primary_candidates=primary_candidates,
                        secondary_candidates=secondary_candidates,
                        settings=settings,
                    )
                    if candidate is not None:
                        quad_candidates.append(candidate)

    if not quad_candidates:
        raise ValueError("Could not build a valid board quad candidate from line pairs.")

    best_candidate = max(quad_candidates, key=lambda candidate: candidate.score)
    debug_data = {
        "line_segments": line_segments,
        "primary_family": primary_family,
        "secondary_family": secondary_family,
        "primary_candidates": primary_candidates,
        "secondary_candidates": secondary_candidates,
        "best_candidate": best_candidate,
        "quad_candidates": quad_candidates,
        "primary_angle_degrees": primary_angle_degrees,
        "secondary_angle_degrees": secondary_angle_degrees,
    }
    return best_candidate.board_quad, debug_data


def describe_candidates(candidates: list[DistinctLineCandidate]) -> list[str]:
    return [
        (
            f"{index}: proj={candidate.projection:.1f}, "
            f"len={candidate.total_length:.1f}, n={candidate.segment_count}"
        )
        for index, candidate in enumerate(candidates)
    ]
