from __future__ import annotations

from dataclasses import dataclass
import math

import cv2
import numpy as np


@dataclass(frozen=True)
class BoardQuad:
    top_left: tuple[float, float]
    top_right: tuple[float, float]
    bottom_right: tuple[float, float]
    bottom_left: tuple[float, float]

    def as_clockwise_points(self) -> tuple[tuple[float, float], ...]:
        return (
            self.top_left,
            self.top_right,
            self.bottom_right,
            self.bottom_left,
        )


@dataclass(frozen=True)
class LineSegment:
    start: tuple[float, float]
    end: tuple[float, float]
    length: float
    angle_degrees: float

    def midpoint(self) -> np.ndarray:
        return np.array(
            [
                (self.start[0] + self.end[0]) / 2.0,
                (self.start[1] + self.end[1]) / 2.0,
            ],
            dtype=np.float32,
        )


@dataclass(frozen=True)
class InfiniteLine:
    direction: np.ndarray
    point: np.ndarray


def build_line_segment(raw_segment: np.ndarray) -> LineSegment:
    x1, y1, x2, y2 = (float(value) for value in raw_segment)
    delta_x = x2 - x1
    delta_y = y2 - y1
    length = math.hypot(delta_x, delta_y)
    angle_degrees = math.degrees(math.atan2(delta_y, delta_x)) % 180.0
    return LineSegment(
        start=(x1, y1),
        end=(x2, y2),
        length=length,
        angle_degrees=angle_degrees,
    )


def get_dominant_angle_degrees(line_segments: list[LineSegment]) -> float:
    angle_histogram = np.zeros(180, dtype=np.float32)
    for line_segment in line_segments:
        angle_bucket = int(round(line_segment.angle_degrees)) % 180
        angle_histogram[angle_bucket] += line_segment.length
    return float(np.argmax(angle_histogram))


def angle_difference_degrees(first_angle: float, second_angle: float) -> float:
    raw_difference = abs(first_angle - second_angle) % 180.0
    return min(raw_difference, 180.0 - raw_difference)


def collect_line_family(
    line_segments: list[LineSegment],
    target_angle_degrees: float,
    angle_tolerance_degrees: float,
) -> list[LineSegment]:
    return [
        line_segment
        for line_segment in line_segments
        if angle_difference_degrees(
            line_segment.angle_degrees,
            target_angle_degrees,
        )
        <= angle_tolerance_degrees
    ]


def get_line_normal(line_angle_degrees: float) -> np.ndarray:
    line_angle_radians = math.radians(line_angle_degrees)
    return np.array(
        [
            -math.sin(line_angle_radians),
            math.cos(line_angle_radians),
        ],
        dtype=np.float32,
    )


def count_distinct_line_positions(
    line_segments: list[LineSegment],
    line_angle_degrees: float,
    merge_distance: float,
) -> int:
    normal = get_line_normal(line_angle_degrees)
    projections = sorted(
        float(np.dot(line_segment.midpoint(), normal)) for line_segment in line_segments
    )
    if not projections:
        return 0

    distinct_positions = [projections[0]]
    for projection in projections[1:]:
        if abs(projection - distinct_positions[-1]) > merge_distance:
            distinct_positions.append(projection)

    return len(distinct_positions)


def fit_line(line_segments: list[LineSegment]) -> InfiniteLine:
    points = []
    for line_segment in line_segments:
        points.append(line_segment.start)
        points.append(line_segment.end)

    fit_input = np.array(points, dtype=np.float32)
    vx, vy, x0, y0 = cv2.fitLine(
        fit_input,
        distType=cv2.DIST_L2,
        param=0,
        reps=0.01,
        aeps=0.01,
    )

    return InfiniteLine(
        direction=np.array([float(vx[0]), float(vy[0])], dtype=np.float32),
        point=np.array([float(x0[0]), float(y0[0])], dtype=np.float32),
    )


def fit_outer_lines(
    line_segments: list[LineSegment],
    line_angle_degrees: float,
    outer_line_window_ratio: float,
) -> tuple[InfiniteLine, InfiniteLine]:
    normal = get_line_normal(line_angle_degrees)
    projections = [
        float(np.dot(line_segment.midpoint(), normal)) for line_segment in line_segments
    ]
    minimum_projection = min(projections)
    maximum_projection = max(projections)
    projection_span = maximum_projection - minimum_projection
    if projection_span <= 0:
        raise ValueError("Detected line family has no measurable span.")

    selection_margin = max(projection_span * outer_line_window_ratio, 1.0)
    minimum_projection_segments = [
        line_segment
        for line_segment, projection in zip(line_segments, projections)
        if projection <= minimum_projection + selection_margin
    ]
    maximum_projection_segments = [
        line_segment
        for line_segment, projection in zip(line_segments, projections)
        if projection >= maximum_projection - selection_margin
    ]
    if not minimum_projection_segments or not maximum_projection_segments:
        raise ValueError("Could not isolate outer board edges.")

    return (
        fit_line(minimum_projection_segments),
        fit_line(maximum_projection_segments),
    )


def intersect_lines(
    first_line: InfiniteLine,
    second_line: InfiniteLine,
) -> tuple[float, float]:
    coefficient_matrix = np.array(
        [
            [first_line.direction[0], -second_line.direction[0]],
            [first_line.direction[1], -second_line.direction[1]],
        ],
        dtype=np.float32,
    )
    determinant = float(np.linalg.det(coefficient_matrix))
    if abs(determinant) < 1e-6:
        raise ValueError("Detected board edge families are nearly parallel.")

    offset = second_line.point - first_line.point
    distance_along_first_line, _ = np.linalg.solve(coefficient_matrix, offset)
    intersection = first_line.point + distance_along_first_line * first_line.direction
    return float(intersection[0]), float(intersection[1])


def order_points_clockwise(points: np.ndarray) -> tuple[tuple[float, float], ...]:
    if points.shape[0] != 4:
        raise ValueError("Expected exactly four board corner points.")

    unique_points = np.unique(points, axis=0)
    if unique_points.shape[0] != 4:
        raise ValueError("Board corner points must be unique.")

    points_as_float32 = points.astype(np.float32)
    centroid = np.mean(points_as_float32, axis=0)
    angles = np.arctan2(
        points_as_float32[:, 1] - centroid[1],
        points_as_float32[:, 0] - centroid[0],
    )
    clockwise_points = points_as_float32[np.argsort(angles)]
    start_index = int(np.argmin(np.sum(clockwise_points, axis=1)))
    ordered_points = np.roll(clockwise_points, -start_index, axis=0)
    return (
        (float(ordered_points[0][0]), float(ordered_points[0][1])),
        (float(ordered_points[1][0]), float(ordered_points[1][1])),
        (float(ordered_points[2][0]), float(ordered_points[2][1])),
        (float(ordered_points[3][0]), float(ordered_points[3][1])),
    )


def has_sufficient_area(
    ordered_points: tuple[tuple[float, float], ...],
    image_area: int,
    minimum_board_area_ratio: float,
) -> bool:
    polygon = np.array(ordered_points, dtype=np.float32)
    detected_area = cv2.contourArea(polygon)
    return detected_area > image_area * minimum_board_area_ratio
