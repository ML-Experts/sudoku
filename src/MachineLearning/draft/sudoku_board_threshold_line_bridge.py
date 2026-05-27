from __future__ import annotations

import cv2
import numpy as np

from sudoku_board_threshold_line_geometry import (
    build_axis_aligned_box,
    build_corridor_polygon,
    build_detected_line_segment,
    clamp_point_to_image,
    interval_gap,
    point_array,
    point_from_line_position,
)
from sudoku_board_threshold_line_merge import build_merged_line, connected_components
from sudoku_board_threshold_models import ExperimentConfig, LineBridge, MergedLine


def closest_interval_bridge_positions(
    first_line: MergedLine,
    second_line: MergedLine,
) -> tuple[float, float, float] | None:
    best_gap: float | None = None
    best_positions: tuple[float, float] | None = None

    for first_start, first_end in first_line.support_intervals:
        for second_start, second_end in second_line.support_intervals:
            gap = interval_gap(
                (float(first_start), float(first_end)),
                (float(second_start), float(second_end)),
            )
            if gap > 0.0 and float(first_end) < float(second_start):
                candidate_positions = (float(first_end), float(second_start))
            elif gap > 0.0:
                candidate_positions = (float(first_start), float(second_end))
            else:
                # Overlapping spans can still be separate logical lines if they drift
                # sideways; use a lateral bridge at the shared position.
                overlap_start = max(float(first_start), float(second_start))
                overlap_end = min(float(first_end), float(second_end))
                overlap_position = (overlap_start + overlap_end) / 2.0
                candidate_positions = (overlap_position, overlap_position)

            if best_gap is not None and gap >= best_gap:
                continue
            best_gap = float(gap)
            best_positions = candidate_positions

    if best_gap is None or best_positions is None:
        return None
    return best_positions[0], best_positions[1], best_gap


def component_has_continuous_bridge_projection(
    component_points: np.ndarray,
    start_point: tuple[int, int],
    end_point: tuple[int, int],
    allowed_projection_hole_px: int = 1,
) -> bool:
    if component_points.size == 0:
        return False

    start_vector = point_array(start_point)
    end_vector = point_array(end_point)
    bridge_vector = end_vector - start_vector
    bridge_length = float(np.linalg.norm(bridge_vector))
    if bridge_length <= 1e-6:
        return False

    bridge_direction = bridge_vector / bridge_length
    component_points_xy = np.column_stack(
        (component_points[:, 1], component_points[:, 0])
    ).astype(np.float32)
    bridge_positions = np.dot(component_points_xy - start_vector, bridge_direction)
    occupied_positions = np.unique(np.rint(bridge_positions).astype(np.int32))
    occupied_positions = occupied_positions[
        (occupied_positions >= 0)
        & (occupied_positions <= int(round(bridge_length)))
    ]
    if occupied_positions.size == 0:
        return False

    if occupied_positions[0] > 0 or occupied_positions[-1] < int(round(bridge_length)):
        return False

    projection_steps = np.diff(occupied_positions)
    if projection_steps.size == 0:
        return bridge_length <= 1.5
    return int(np.max(projection_steps)) <= allowed_projection_hole_px + 1


def line_bridge_candidate(
    binary_image: np.ndarray,
    first_line: MergedLine,
    second_line: MergedLine,
    family_angle_degrees: float,
    family_name: str,
    first_line_index: int,
    second_line_index: int,
    projection_tolerance_px: float,
    max_gap_px: float,
    endpoint_tolerance_px: float,
) -> LineBridge | None:
    if abs(first_line.projection - second_line.projection) > projection_tolerance_px:
        return None

    bridge_positions = closest_interval_bridge_positions(first_line, second_line)
    if bridge_positions is None:
        return None

    first_position, second_position, gap_px = bridge_positions
    if gap_px > max_gap_px:
        return None

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

    polygon_points = np.array(corridor_polygon, dtype=np.int32)
    min_x = min(
        [start_box[0][0], start_box[1][0], end_box[0][0], end_box[1][0]]
        + [int(point[0]) for point in corridor_polygon]
    )
    max_x = max(
        [start_box[0][0], start_box[1][0], end_box[0][0], end_box[1][0]]
        + [int(point[0]) for point in corridor_polygon]
    )
    min_y = min(
        [start_box[0][1], start_box[1][1], end_box[0][1], end_box[1][1]]
        + [int(point[1]) for point in corridor_polygon]
    )
    max_y = max(
        [start_box[0][1], start_box[1][1], end_box[0][1], end_box[1][1]]
        + [int(point[1]) for point in corridor_polygon]
    )

    roi = binary_image[min_y : max_y + 1, min_x : max_x + 1]
    if roi.size == 0:
        return None

    corridor_mask = np.zeros_like(roi, dtype=np.uint8)
    shifted_polygon = polygon_points.copy()
    shifted_polygon[:, 0] -= min_x
    shifted_polygon[:, 1] -= min_y
    cv2.fillConvexPoly(corridor_mask, shifted_polygon, 255)

    candidate_mask = np.where(
        (roi > 0) & (corridor_mask > 0),
        255,
        0,
    ).astype(np.uint8)
    if not np.any(candidate_mask):
        return None

    start_mask = np.zeros_like(roi, dtype=np.uint8)
    cv2.rectangle(
        start_mask,
        (start_box[0][0] - min_x, start_box[0][1] - min_y),
        (start_box[1][0] - min_x, start_box[1][1] - min_y),
        255,
        thickness=-1,
    )
    end_mask = np.zeros_like(roi, dtype=np.uint8)
    cv2.rectangle(
        end_mask,
        (end_box[0][0] - min_x, end_box[0][1] - min_y),
        (end_box[1][0] - min_x, end_box[1][1] - min_y),
        255,
        thickness=-1,
    )

    component_count, labels = cv2.connectedComponents(candidate_mask, connectivity=8)
    if component_count <= 1:
        return None

    start_labels = {
        int(label) for label in np.unique(labels[start_mask > 0]) if int(label) > 0
    }
    end_labels = {int(label) for label in np.unique(labels[end_mask > 0]) if int(label) > 0}
    common_labels = start_labels & end_labels
    if not common_labels:
        return None

    best_label = max(
        common_labels,
        key=lambda label: int(np.count_nonzero(labels == label)),
    )
    component_points = np.column_stack(np.where(labels == best_label))
    if component_points.size == 0:
        return None

    if not component_has_continuous_bridge_projection(
        component_points,
        ideal_start_point,
        ideal_end_point,
    ):
        return None

    start_target = np.array(
        [ideal_start_point[1] - min_y, ideal_start_point[0] - min_x],
        dtype=np.float32,
    )
    end_target = np.array(
        [ideal_end_point[1] - min_y, ideal_end_point[0] - min_x],
        dtype=np.float32,
    )
    distances_to_start = np.linalg.norm(
        component_points.astype(np.float32) - start_target,
        axis=1,
    )
    distances_to_end = np.linalg.norm(
        component_points.astype(np.float32) - end_target,
        axis=1,
    )
    start_anchor_y, start_anchor_x = component_points[int(np.argmin(distances_to_start))]
    end_anchor_y, end_anchor_x = component_points[int(np.argmin(distances_to_end))]
    bridge_segment = build_detected_line_segment(
        (int(start_anchor_x + min_x), int(start_anchor_y + min_y)),
        (int(end_anchor_x + min_x), int(end_anchor_y + min_y)),
    )
    if bridge_segment.length <= 1.0:
        return None

    return LineBridge(
        family_name=family_name,
        first_line_index=first_line_index,
        second_line_index=second_line_index,
        segment=bridge_segment,
        ideal_start_point=ideal_start_point,
        ideal_end_point=ideal_end_point,
        corridor_polygon=corridor_polygon,
        start_box=start_box,
        end_box=end_box,
        gap_px=gap_px,
    )


def bridge_line_family_gaps(
    binary_image: np.ndarray,
    merged_lines: list[MergedLine],
    family_angle_degrees: float | None,
    family_name: str,
    config: ExperimentConfig,
    minimum_dimension: int,
) -> tuple[list[MergedLine], list[LineBridge], float, float, float]:
    bridge_projection_tolerance_px = max(
        4.0,
        minimum_dimension * config.line_bridge_projection_distance_ratio,
    )
    bridge_max_gap_px = max(
        8.0,
        minimum_dimension * config.line_bridge_max_gap_ratio,
    )
    bridge_endpoint_tolerance_px = max(
        6.0,
        minimum_dimension * config.line_bridge_endpoint_tolerance_ratio,
    )
    if family_angle_degrees is None or len(merged_lines) <= 1:
        return (
            merged_lines,
            [],
            bridge_projection_tolerance_px,
            bridge_max_gap_px,
            bridge_endpoint_tolerance_px,
        )

    adjacency: list[list[int]] = [[] for _ in merged_lines]
    bridges: list[LineBridge] = []
    for first_index in range(len(merged_lines)):
        for second_index in range(first_index + 1, len(merged_lines)):
            line_bridge = line_bridge_candidate(
                binary_image=binary_image,
                first_line=merged_lines[first_index],
                second_line=merged_lines[second_index],
                family_angle_degrees=family_angle_degrees,
                family_name=family_name,
                first_line_index=first_index,
                second_line_index=second_index,
                projection_tolerance_px=bridge_projection_tolerance_px,
                max_gap_px=bridge_max_gap_px,
                endpoint_tolerance_px=bridge_endpoint_tolerance_px,
            )
            if line_bridge is None:
                continue
            adjacency[first_index].append(second_index)
            adjacency[second_index].append(first_index)
            bridges.append(line_bridge)

    if not bridges:
        return (
            merged_lines,
            [],
            bridge_projection_tolerance_px,
            bridge_max_gap_px,
            bridge_endpoint_tolerance_px,
        )

    bridged_lines = []
    for component in connected_components(adjacency):
        component_set = set(component)
        merged_segments = []
        for line_index in component:
            merged_segments.extend(merged_lines[line_index].segments)
        for line_bridge in bridges:
            if (
                line_bridge.first_line_index in component_set
                and line_bridge.second_line_index in component_set
            ):
                merged_segments.append(line_bridge.segment)
        bridged_lines.append(
            build_merged_line(
                family_name,
                family_angle_degrees,
                merged_segments,
            )
        )

    return (
        sorted(bridged_lines, key=lambda merged_line: merged_line.projection),
        bridges,
        bridge_projection_tolerance_px,
        bridge_max_gap_px,
        bridge_endpoint_tolerance_px,
    )


__all__ = [
    "bridge_line_family_gaps",
    "closest_interval_bridge_positions",
    "line_bridge_candidate",
]
