from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import subprocess

import cv2
import numpy as np


@dataclass(frozen=True)
class BoardDebugSettings:
    board_output_size: int = 600
    board_output_padding_pixels: int = 8
    grayscale_color_conversion_code: int = cv2.COLOR_BGR2GRAY
    gaussian_kernel_size: tuple[int, int] = (5, 5)
    gaussian_sigma_x: float = 0.0
    adaptive_threshold_block_size: int = 11
    adaptive_threshold_c: int = 2
    board_edge_canny_threshold_1: int = 50
    board_edge_canny_threshold_2: int = 150
    board_edge_hough_threshold: int = 80
    board_edge_min_line_length_ratio: float = 0.2
    board_edge_max_line_gap_ratio: float = 0.04
    board_edge_angle_tolerance_degrees: float = 12.0
    board_edge_outer_line_window_ratio: float = 0.1
    board_edge_minimum_board_area_ratio: float = 0.1
    board_edge_minimum_family_segments: int = 4
    board_edge_line_position_merge_distance_ratio: float = 0.03
    board_edge_minimum_distinct_lines_per_family: int = 5
    max_distinct_lines_per_family: int = 8
    min_interior_lines_per_side: int = 4
    min_boundary_segment_coverage: float = 0.55
    area_score_weight: float = 3.0
    rectangularity_score_weight: float = 2.0
    grid_support_score_weight: float = 3.0
    line_length_score_weight: float = 1.0
    boundary_coverage_score_weight: float = 4.0


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


def read_exif_orientation_label(image_path: Path) -> str | None:
    completed_process = subprocess.run(
        ["file", str(image_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    metadata_text = completed_process.stdout.strip()
    orientation_marker = "orientation="
    orientation_start = metadata_text.find(orientation_marker)
    if orientation_start < 0:
        return None

    orientation_start += len(orientation_marker)
    orientation_end = metadata_text.find(",", orientation_start)
    if orientation_end < 0:
        orientation_end = len(metadata_text)

    return metadata_text[orientation_start:orientation_end].strip().lower() or None


def apply_exif_orientation(
    image: np.ndarray,
    orientation_label: str | None,
) -> np.ndarray:
    if orientation_label in (None, "", "upper-left"):
        return image
    if orientation_label == "upper-right":
        return cv2.flip(image, 1)
    if orientation_label == "lower-right":
        return cv2.rotate(image, cv2.ROTATE_180)
    if orientation_label == "lower-left":
        return cv2.flip(image, 0)
    if orientation_label == "left-top":
        return cv2.transpose(image)
    if orientation_label == "right-top":
        return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    if orientation_label == "right-bottom":
        return cv2.flip(cv2.transpose(image), -1)
    if orientation_label == "left-bottom":
        return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return image


def load_image(image_path: Path) -> np.ndarray:
    image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")

    orientation_label = read_exif_orientation_label(image_path)
    return apply_exif_orientation(image, orientation_label)


def preprocess_image(
    image: np.ndarray,
    settings: BoardDebugSettings,
) -> np.ndarray:
    grayscale = cv2.cvtColor(image, settings.grayscale_color_conversion_code)
    return cv2.GaussianBlur(
        grayscale,
        settings.gaussian_kernel_size,
        settings.gaussian_sigma_x,
    )


def binarize_image(
    image: np.ndarray,
    settings: BoardDebugSettings,
) -> np.ndarray:
    return cv2.adaptiveThreshold(
        image,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        settings.adaptive_threshold_block_size,
        settings.adaptive_threshold_c,
    )


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


def transform_board(
    image: np.ndarray,
    board_quad: BoardQuad,
    settings: BoardDebugSettings,
) -> np.ndarray:
    source_points = np.array(board_quad.as_clockwise_points(), dtype=np.float32)
    min_index = float(settings.board_output_padding_pixels)
    max_index = float(
        settings.board_output_size - settings.board_output_padding_pixels - 1
    )
    destination_points = np.array(
        [
            [min_index, min_index],
            [max_index, min_index],
            [max_index, max_index],
            [min_index, max_index],
        ],
        dtype=np.float32,
    )
    perspective_matrix = cv2.getPerspectiveTransform(source_points, destination_points)
    transformed = cv2.warpPerspective(
        image,
        perspective_matrix,
        (settings.board_output_size, settings.board_output_size),
    )
    if transformed.size == 0:
        raise ValueError("Perspective transform produced empty image.")
    return transformed


def detect_board_quad_legacy(
    binary_image: np.ndarray,
    settings: BoardDebugSettings,
) -> BoardQuad:
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

    line_segments = [build_line_segment(raw_segment[0]) for raw_segment in raw_segments]
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

    merge_distance = (
        minimum_dimension * settings.board_edge_line_position_merge_distance_ratio
    )
    if (
        count_distinct_line_positions(
            primary_family,
            primary_angle_degrees,
            merge_distance,
        )
        < settings.board_edge_minimum_distinct_lines_per_family
    ):
        raise ValueError("Primary board edge family lacks Sudoku-like grid lines.")
    if (
        count_distinct_line_positions(
            secondary_family,
            secondary_angle_degrees,
            merge_distance,
        )
        < settings.board_edge_minimum_distinct_lines_per_family
    ):
        raise ValueError("Secondary board edge family lacks Sudoku-like grid lines.")

    primary_outer_lines = fit_outer_lines(
        primary_family,
        primary_angle_degrees,
        settings.board_edge_outer_line_window_ratio,
    )
    secondary_outer_lines = fit_outer_lines(
        secondary_family,
        secondary_angle_degrees,
        settings.board_edge_outer_line_window_ratio,
    )
    board_points = np.array(
        [
            intersect_lines(primary_outer_lines[0], secondary_outer_lines[0]),
            intersect_lines(primary_outer_lines[0], secondary_outer_lines[1]),
            intersect_lines(primary_outer_lines[1], secondary_outer_lines[1]),
            intersect_lines(primary_outer_lines[1], secondary_outer_lines[0]),
        ],
        dtype=np.float32,
    )
    if not np.isfinite(board_points).all():
        raise ValueError("Board corner intersections are invalid.")

    ordered_points = order_points_clockwise(board_points)
    if not has_sufficient_area(
        ordered_points,
        image_width * image_height,
        settings.board_edge_minimum_board_area_ratio,
    ):
        raise ValueError("Detected board area is too small.")

    return BoardQuad(
        top_left=ordered_points[0],
        top_right=ordered_points[1],
        bottom_right=ordered_points[2],
        bottom_left=ordered_points[3],
    )


def refine_board_image(
    board_image: np.ndarray,
    passes: int,
    settings: BoardDebugSettings,
    detect_board_quad,
) -> np.ndarray:
    refined_board_image = board_image
    for _ in range(passes):
        refined_preprocessed = preprocess_image(refined_board_image, settings)
        refined_binary = binarize_image(refined_preprocessed, settings)
        refined_quad = detect_board_quad(refined_binary, settings)
        refined_board_image = transform_board(
            refined_board_image,
            refined_quad,
            settings,
        )
    return refined_board_image
