from __future__ import annotations

import cv2
import numpy as np

from sudoku_board_debug_geometry import (
    BoardQuad,
    build_line_segment,
    collect_line_family,
    count_distinct_line_positions,
    fit_outer_lines,
    get_dominant_angle_degrees,
    has_sufficient_area,
    intersect_lines,
    order_points_clockwise,
)
from sudoku_board_debug_preprocess import (
    BoardDebugSettings,
    binarize_image,
    preprocess_image,
)


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
