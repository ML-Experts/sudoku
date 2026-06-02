from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from raw_line_family_only_line_families import (
    collect_line_family,
    get_dominant_angle_degrees,
    is_horizontal_like,
    refine_family_angle_degrees,
)
from raw_line_family_only_geometry import (
    angle_difference_degrees,
    build_line_segment,
    classify_line_segment,
    signed_angle_offset_degrees,
)
from raw_line_family_only_intersections import (
    LogicalLineIntersectionAnalysis,
    LogicalLineBorderPair,
    LogicalLineFrame,
    LogicalLineIntersection,
    analyze_logical_line_intersections,
    find_logical_line_border_pairs,
)
from raw_line_family_only_logical_lines import (
    LogicalLine,
    build_logical_lines,
    connect_logical_lines_by_pixels,
)
from raw_line_family_only_models import (
    ExperimentConfig,
    LineFamilyName,
    LineSegment,
    ToleranceRectangle,
)


@dataclass(frozen=True)
class RawLineFamilyResult:
    raw_segment_count: int
    orientation_offset_degrees: float | None
    horizontal_angle_degrees: float | None
    vertical_angle_degrees: float | None
    horizontal_segments: list[LineSegment]
    vertical_segments: list[LineSegment]
    horizontal_logical_lines: list[LogicalLine]
    vertical_logical_lines: list[LogicalLine]
    horizontal_tolerance_rectangles: list[ToleranceRectangle]
    vertical_tolerance_rectangles: list[ToleranceRectangle]
    logical_line_intersection_analysis: LogicalLineIntersectionAnalysis | None
    logical_line_intersections: list[LogicalLineIntersection]
    logical_line_border_pairs: list[LogicalLineBorderPair]
    logical_line_frames: list[LogicalLineFrame]


def _build_empty_line_family_result(
) -> RawLineFamilyResult:
    return RawLineFamilyResult(
        raw_segment_count=0,
        orientation_offset_degrees=None,
        horizontal_angle_degrees=None,
        vertical_angle_degrees=None,
        horizontal_segments=[],
        vertical_segments=[],
        horizontal_logical_lines=[],
        vertical_logical_lines=[],
        horizontal_tolerance_rectangles=[],
        vertical_tolerance_rectangles=[],
        logical_line_intersection_analysis=None,
        logical_line_intersections=[],
        logical_line_border_pairs=[],
        logical_line_frames=[],
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


def _build_tolerance_rectangles(
    logical_lines: list[LogicalLine],
    config: ExperimentConfig,
) -> list[ToleranceRectangle]:
    return [
        tolerance_rectangle
        for logical_line in logical_lines
        for tolerance_rectangle in (
            logical_line.build_tolerance_rectangle(
                reference_vertex=logical_line.start_vertex,
                direction_length=config.tolerance_rectangle_vector_length_px,
                padding=config.tolerance_rectangle_padding_px,
            ),
            logical_line.build_tolerance_rectangle(
                reference_vertex=logical_line.end_vertex,
                direction_length=config.tolerance_rectangle_vector_length_px,
                padding=config.tolerance_rectangle_padding_px,
            ),
        )
    ]


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
    include_logical_lines: bool = True,
) -> RawLineFamilyResult:
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
            horizontal_logical_lines=[],
            vertical_logical_lines=[],
            horizontal_tolerance_rectangles=[],
            vertical_tolerance_rectangles=[],
            logical_line_intersection_analysis=None,
            logical_line_intersections=[],
            logical_line_border_pairs=[],
            logical_line_frames=[],
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
    horizontal_logical_lines, vertical_logical_lines = connect_logical_lines_by_pixels(
        pixel_connection_binary,
        horizontal_logical_lines,
        vertical_logical_lines,
        axis_gap_tolerance_px=config.logical_line_axis_gap_tolerance_px,
        cross_axis_thickness_px=config.logical_line_cross_axis_thickness_px,
        rectangle_vector_length_px=config.tolerance_rectangle_vector_length_px,
        rectangle_padding_px=config.tolerance_rectangle_padding_px,
    )
    logical_line_intersection_analysis = analyze_logical_line_intersections(
        horizontal_logical_lines,
        vertical_logical_lines,
    )
    horizontal_logical_lines = logical_line_intersection_analysis.horizontal_lines
    vertical_logical_lines = logical_line_intersection_analysis.vertical_lines
    horizontal_tolerance_rectangles = _build_tolerance_rectangles(
        horizontal_logical_lines,
        config,
    )
    vertical_tolerance_rectangles = _build_tolerance_rectangles(
        vertical_logical_lines,
        config,
    )
    logical_line_intersections = logical_line_intersection_analysis.intersections
    logical_line_border_pairs = find_logical_line_border_pairs(
        logical_line_intersections
    )
    logical_line_frames = []
    if logical_line_intersection_analysis.frame is not None:
        logical_line_frames.append(logical_line_intersection_analysis.frame)

    return RawLineFamilyResult(
        raw_segment_count=len(family_detection_segments),
        orientation_offset_degrees=orientation_offset_degrees,
        horizontal_angle_degrees=horizontal_angle_degrees,
        vertical_angle_degrees=vertical_angle_degrees,
        horizontal_segments=horizontal_segments,
        vertical_segments=vertical_segments,
        horizontal_logical_lines=horizontal_logical_lines,
        vertical_logical_lines=vertical_logical_lines,
        horizontal_tolerance_rectangles=horizontal_tolerance_rectangles,
        vertical_tolerance_rectangles=vertical_tolerance_rectangles,
        logical_line_intersection_analysis=logical_line_intersection_analysis,
        logical_line_intersections=logical_line_intersections,
        logical_line_border_pairs=logical_line_border_pairs,
        logical_line_frames=logical_line_frames,
    )


__all__ = [
    "RawLineFamilyResult",
    "detect_line_families",
]
