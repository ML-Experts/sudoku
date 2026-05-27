from __future__ import annotations

import numpy as np

from infrastructure.vision.sudoku_threshold_geometry import (
    build_axis_aligned_box,
    build_corridor_polygon,
    clamp_point_to_image,
    point_array,
    point_from_line_position,
)
from infrastructure.vision.sudoku_threshold_models import MergedLine


def component_has_continuous_bridge_projection(
    component_points: np.ndarray,
    start_point: tuple[int, int],
    end_point: tuple[int, int],
    component_origin: tuple[int, int] = (0, 0),
    allowed_projection_hole_px: int = 1,
) -> tuple[bool, float | None, float | None, int | None]:
    if component_points.size == 0:
        return False, None, None, None

    start_vector = point_array(start_point)
    end_vector = point_array(end_point)
    bridge_vector = end_vector - start_vector
    bridge_length = float(np.linalg.norm(bridge_vector))
    if bridge_length <= 1e-6:
        return False, None, None, None

    bridge_direction = bridge_vector / bridge_length
    origin_x, origin_y = component_origin
    component_points_xy = np.column_stack(
        (component_points[:, 1] + origin_x, component_points[:, 0] + origin_y)
    ).astype(np.float32)
    bridge_positions = np.dot(component_points_xy - start_vector, bridge_direction)
    occupied_positions = np.unique(np.rint(bridge_positions).astype(np.int32))
    occupied_positions = occupied_positions[
        (occupied_positions >= 0)
        & (occupied_positions <= int(round(bridge_length)))
    ]
    if occupied_positions.size == 0:
        return False, None, None, None

    coverage_start_px = float(occupied_positions[0])
    coverage_end_px = float(occupied_positions[-1])
    if occupied_positions[0] > 0 or occupied_positions[-1] < int(round(bridge_length)):
        return False, coverage_start_px, coverage_end_px, None

    projection_steps = np.diff(occupied_positions)
    if projection_steps.size == 0:
        is_continuous = bridge_length <= 1.5
        return is_continuous, coverage_start_px, coverage_end_px, 0

    max_projection_step = int(np.max(projection_steps))
    return (
        max_projection_step <= allowed_projection_hole_px + 1,
        coverage_start_px,
        coverage_end_px,
        max(0, max_projection_step - 1),
    )


def build_overlap_bridge_segment(
    start_point: tuple[int, int],
    end_point: tuple[int, int],
    family_name: str,
    image_shape: tuple[int, ...],
    projection_delta: float,
) -> tuple[int, int]:
    if start_point != end_point:
        return end_point

    if family_name == "vertical":
        delta_x = 1 if projection_delta >= 0.0 else -1
        return clamp_point_to_image(
            (start_point[0] + delta_x, start_point[1]),
            image_shape,
        )

    delta_y = 1 if projection_delta >= 0.0 else -1
    return clamp_point_to_image(
        (start_point[0], start_point[1] + delta_y),
        image_shape,
    )


def build_bridge_geometry(
    binary_image: np.ndarray,
    family_angle_degrees: float,
    first_line: MergedLine,
    second_line: MergedLine,
    first_position: float,
    second_position: float,
    endpoint_tolerance_px: float,
) -> tuple[
    tuple[int, int],
    tuple[int, int],
    tuple[tuple[int, int], tuple[int, int]],
    tuple[tuple[int, int], tuple[int, int]],
    tuple[tuple[int, int], ...],
]:
    ideal_start_point = clamp_point_to_image(
        point_from_line_position(
            first_line.projection,
            first_position,
            family_angle_degrees,
        ),
        binary_image.shape,
    )
    ideal_end_point = clamp_point_to_image(
        point_from_line_position(
            second_line.projection,
            second_position,
            family_angle_degrees,
        ),
        binary_image.shape,
    )
    radius_px = max(2, int(round(endpoint_tolerance_px)))
    start_box = build_axis_aligned_box(ideal_start_point, radius_px, binary_image.shape)
    end_box = build_axis_aligned_box(ideal_end_point, radius_px, binary_image.shape)
    corridor_polygon = build_corridor_polygon(
        ideal_start_point,
        ideal_end_point,
        max(1.0, endpoint_tolerance_px),
    )
    return (
        ideal_start_point,
        ideal_end_point,
        start_box,
        end_box,
        corridor_polygon,
    )
