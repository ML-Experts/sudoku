from dataclasses import dataclass
import math

import cv2
import numpy as np
from numpy.typing import NDArray

from models.board_quad import BoardQuad


@dataclass(frozen=True)
class _LineSegment:
    start: tuple[float, float]
    end: tuple[float, float]
    length: float
    angle_degrees: float

    def midpoint(self) -> NDArray[np.float32]:
        return np.array(
            [
                (self.start[0] + self.end[0]) / 2.0,
                (self.start[1] + self.end[1]) / 2.0,
            ],
            dtype=np.float32,
        )


@dataclass(frozen=True)
class _InfiniteLine:
    direction: NDArray[np.float32]
    point: NDArray[np.float32]


class OpenCvBoardEdgeDetector:
    def __init__(
        self,
        canny_threshold_1: int,
        canny_threshold_2: int,
        hough_threshold: int,
        min_line_length_ratio: float,
        max_line_gap_ratio: float,
        angle_tolerance_degrees: float,
        outer_line_window_ratio: float,
        minimum_board_area_ratio: float,
        minimum_family_segments: int,
        line_position_merge_distance_ratio: float,
        minimum_distinct_lines_per_family: int,
    ) -> None:
        if canny_threshold_1 < 0 or canny_threshold_2 < 0:
            raise ValueError("Canny thresholds must be non-negative.")
        if hough_threshold <= 0:
            raise ValueError("Hough threshold must be greater than zero.")
        if min_line_length_ratio <= 0:
            raise ValueError("Minimum line length ratio must be greater than zero.")
        if max_line_gap_ratio <= 0:
            raise ValueError("Maximum line gap ratio must be greater than zero.")
        if not 0 < angle_tolerance_degrees < 45:
            raise ValueError("Angle tolerance must be between 0 and 45 degrees.")
        if not 0 < outer_line_window_ratio < 1:
            raise ValueError("Outer line window ratio must be between 0 and 1.")
        if not 0 < minimum_board_area_ratio < 1:
            raise ValueError("Minimum board area ratio must be between 0 and 1.")
        if minimum_family_segments < 2:
            raise ValueError("Minimum family segments must be at least 2.")
        if not 0 < line_position_merge_distance_ratio < 1:
            raise ValueError(
                "Line position merge distance ratio must be between 0 and 1."
            )
        if minimum_distinct_lines_per_family < 2:
            raise ValueError(
                "Minimum distinct lines per family must be at least 2."
            )

        self._canny_threshold_1 = canny_threshold_1
        self._canny_threshold_2 = canny_threshold_2
        self._hough_threshold = hough_threshold
        self._min_line_length_ratio = min_line_length_ratio
        self._max_line_gap_ratio = max_line_gap_ratio
        self._angle_tolerance_degrees = angle_tolerance_degrees
        self._outer_line_window_ratio = outer_line_window_ratio
        self._minimum_board_area_ratio = minimum_board_area_ratio
        self._minimum_family_segments = minimum_family_segments
        self._line_position_merge_distance_ratio = (
            line_position_merge_distance_ratio
        )
        self._minimum_distinct_lines_per_family = (
            minimum_distinct_lines_per_family
        )

    def detect(self, image: NDArray[np.uint8]) -> BoardQuad:
        if image.size == 0:
            raise ValueError("Input image is empty.")
        if image.ndim != 2:
            raise ValueError("Board edge detector expects a binary image.")

        image_height, image_width = image.shape
        minimum_dimension = min(image_height, image_width)
        raw_segments = cv2.HoughLinesP(
            cv2.Canny(image, self._canny_threshold_1, self._canny_threshold_2),
            rho=1,
            theta=np.pi / 180.0,
            threshold=self._hough_threshold,
            minLineLength=max(
                1, int(round(minimum_dimension * self._min_line_length_ratio))
            ),
            maxLineGap=max(
                1, int(round(minimum_dimension * self._max_line_gap_ratio))
            ),
        )
        if raw_segments is None or len(raw_segments) == 0:
            raise ValueError("No line segments were found in input image.")

        line_segments = [
            _build_line_segment(raw_segment[0]) for raw_segment in raw_segments
        ]
        primary_angle_degrees = _get_dominant_angle_degrees(line_segments)
        secondary_angle_degrees = (primary_angle_degrees + 90.0) % 180.0

        primary_family = _collect_line_family(
            line_segments,
            primary_angle_degrees,
            self._angle_tolerance_degrees,
        )
        secondary_family = _collect_line_family(
            line_segments,
            secondary_angle_degrees,
            self._angle_tolerance_degrees,
        )
        if len(primary_family) < self._minimum_family_segments:
            raise ValueError("Primary board edge family is too small.")
        if len(secondary_family) < self._minimum_family_segments:
            raise ValueError("Secondary board edge family is too small.")
        if (
            _count_distinct_line_positions(
                primary_family,
                primary_angle_degrees,
                minimum_dimension * self._line_position_merge_distance_ratio,
            )
            < self._minimum_distinct_lines_per_family
        ):
            raise ValueError("Primary board edge family lacks Sudoku-like grid lines.")
        if (
            _count_distinct_line_positions(
                secondary_family,
                secondary_angle_degrees,
                minimum_dimension * self._line_position_merge_distance_ratio,
            )
            < self._minimum_distinct_lines_per_family
        ):
            raise ValueError("Secondary board edge family lacks Sudoku-like grid lines.")

        # Recover the outer borders from the two dominant line families.
        primary_outer_lines = _fit_outer_lines(
            primary_family,
            primary_angle_degrees,
            self._outer_line_window_ratio,
        )
        secondary_outer_lines = _fit_outer_lines(
            secondary_family,
            secondary_angle_degrees,
            self._outer_line_window_ratio,
        )

        board_points = np.array(
            [
                _intersect_lines(primary_outer_lines[0], secondary_outer_lines[0]),
                _intersect_lines(primary_outer_lines[0], secondary_outer_lines[1]),
                _intersect_lines(primary_outer_lines[1], secondary_outer_lines[1]),
                _intersect_lines(primary_outer_lines[1], secondary_outer_lines[0]),
            ],
            dtype=np.float32,
        )
        if not np.isfinite(board_points).all():
            raise ValueError("Board corner intersections are invalid.")

        ordered_points = _order_points_clockwise(board_points)
        if not _has_sufficient_area(
            ordered_points,
            image_width * image_height,
            self._minimum_board_area_ratio,
        ):
            raise ValueError("Detected board area is too small.")

        return BoardQuad(
            top_left=ordered_points[0],
            top_right=ordered_points[1],
            bottom_right=ordered_points[2],
            bottom_left=ordered_points[3],
        )


def _build_line_segment(raw_segment: NDArray[np.integer]) -> _LineSegment:
    x1, y1, x2, y2 = (float(value) for value in raw_segment)
    delta_x = x2 - x1
    delta_y = y2 - y1
    length = math.hypot(delta_x, delta_y)
    angle_degrees = math.degrees(math.atan2(delta_y, delta_x)) % 180.0

    return _LineSegment(
        start=(x1, y1),
        end=(x2, y2),
        length=length,
        angle_degrees=angle_degrees,
    )


def _get_dominant_angle_degrees(line_segments: list[_LineSegment]) -> float:
    angle_histogram = np.zeros(180, dtype=np.float32)
    for line_segment in line_segments:
        angle_bucket = int(round(line_segment.angle_degrees)) % 180
        angle_histogram[angle_bucket] += line_segment.length

    return float(np.argmax(angle_histogram))


def _collect_line_family(
    line_segments: list[_LineSegment],
    target_angle_degrees: float,
    angle_tolerance_degrees: float,
) -> list[_LineSegment]:
    family = []
    for line_segment in line_segments:
        if (
            _angle_difference_degrees(
                line_segment.angle_degrees,
                target_angle_degrees,
            )
            <= angle_tolerance_degrees
        ):
            family.append(line_segment)

    return family


def _fit_outer_lines(
    line_segments: list[_LineSegment],
    line_angle_degrees: float,
    outer_line_window_ratio: float,
) -> tuple[_InfiniteLine, _InfiniteLine]:
    normal = _get_line_normal(line_angle_degrees)
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
        _fit_line(minimum_projection_segments),
        _fit_line(maximum_projection_segments),
    )


def _count_distinct_line_positions(
    line_segments: list[_LineSegment],
    line_angle_degrees: float,
    merge_distance: float,
) -> int:
    normal = _get_line_normal(line_angle_degrees)
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


def _fit_line(line_segments: list[_LineSegment]) -> _InfiniteLine:
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

    return _InfiniteLine(
        direction=np.array([float(vx[0]), float(vy[0])], dtype=np.float32),
        point=np.array([float(x0[0]), float(y0[0])], dtype=np.float32),
    )


def _intersect_lines(
    first_line: _InfiniteLine,
    second_line: _InfiniteLine,
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


def _get_line_normal(line_angle_degrees: float) -> NDArray[np.float32]:
    line_angle_radians = math.radians(line_angle_degrees)
    return np.array(
        [
            -math.sin(line_angle_radians),
            math.cos(line_angle_radians),
        ],
        dtype=np.float32,
    )


def _angle_difference_degrees(first_angle: float, second_angle: float) -> float:
    raw_difference = abs(first_angle - second_angle) % 180.0
    return min(raw_difference, 180.0 - raw_difference)


def _order_points_clockwise(
    points: NDArray[np.floating],
) -> tuple[tuple[float, float], ...]:
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


def _has_sufficient_area(
    ordered_points: tuple[tuple[float, float], ...],
    image_area: int,
    minimum_board_area_ratio: float,
) -> bool:
    polygon = np.array(ordered_points, dtype=np.float32)
    detected_area = cv2.contourArea(polygon)
    return detected_area > image_area * minimum_board_area_ratio
