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
from sudoku_board_threshold_models import (
    ExperimentConfig,
    LineBridge,
    LineBridgeDiagnostic,
    MergedLine,
)


def candidate_interval_bridge_positions(
    first_line: MergedLine,
    second_line: MergedLine,
) -> tuple[tuple[float, float, float], ...]:
    candidates: dict[tuple[float, float, float], tuple[float, float, float]] = {}

    for first_start, first_end in first_line.support_intervals:
        for second_start, second_end in second_line.support_intervals:
            first_interval = (float(first_start), float(first_end))
            second_interval = (float(second_start), float(second_end))
            endpoint_candidates = (
                (first_interval[0], second_interval, True),
                (first_interval[1], second_interval, True),
                (second_interval[0], first_interval, False),
                (second_interval[1], first_interval, False),
            )
            for endpoint_position, opposite_interval, endpoint_on_first in (
                endpoint_candidates
            ):
                opposite_position = float(
                    np.clip(
                        endpoint_position,
                        opposite_interval[0],
                        opposite_interval[1],
                    )
                )
                gap = abs(endpoint_position - opposite_position)

                if endpoint_on_first:
                    candidate_positions = (
                        float(endpoint_position),
                        opposite_position,
                    )
                else:
                    candidate_positions = (
                        opposite_position,
                        float(endpoint_position),
                    )
                candidate = (
                    float(candidate_positions[0]),
                    float(candidate_positions[1]),
                    float(gap),
                )
                candidate_key = (
                    round(candidate[0], 4),
                    round(candidate[1], 4),
                    round(candidate[2], 4),
                )
                candidates[candidate_key] = candidate

    ordered_candidates = tuple(
        sorted(
            candidates.values(),
            key=lambda candidate: (candidate[2], candidate[0], candidate[1]),
        )
    )
    return ordered_candidates


def closest_interval_bridge_positions(
    first_line: MergedLine,
    second_line: MergedLine,
) -> tuple[float, float, float] | None:
    bridge_candidates = candidate_interval_bridge_positions(first_line, second_line)
    if not bridge_candidates:
        return None
    return bridge_candidates[0]


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
    is_continuous = max_projection_step <= allowed_projection_hole_px + 1
    return (
        is_continuous,
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
    family_name: str,
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


def build_bridge_diagnostic(
    family_name: str,
    first_line_index: int,
    second_line_index: int,
    accepted: bool,
    reject_reason: str,
    projection_distance_px: float,
    projection_tolerance_px: float,
    candidate_count: int,
    selected_candidate_rank: int | None,
    gap_px: float | None,
    max_gap_px: float,
    ideal_start_point: tuple[int, int] | None = None,
    ideal_end_point: tuple[int, int] | None = None,
    corridor_polygon: tuple[tuple[int, int], ...] = (),
    start_box: tuple[tuple[int, int], tuple[int, int]] | None = None,
    end_box: tuple[tuple[int, int], tuple[int, int]] | None = None,
    projection_coverage_start_px: float | None = None,
    projection_coverage_end_px: float | None = None,
    projection_max_hole_px: int | None = None,
) -> LineBridgeDiagnostic:
    return LineBridgeDiagnostic(
        family_name=family_name,
        first_line_index=first_line_index,
        second_line_index=second_line_index,
        accepted=accepted,
        reject_reason=reject_reason,
        projection_distance_px=float(projection_distance_px),
        projection_tolerance_px=float(projection_tolerance_px),
        candidate_count=int(candidate_count),
        selected_candidate_rank=selected_candidate_rank,
        gap_px=None if gap_px is None else float(gap_px),
        max_gap_px=float(max_gap_px),
        ideal_start_point=ideal_start_point,
        ideal_end_point=ideal_end_point,
        corridor_polygon=corridor_polygon,
        start_box=start_box,
        end_box=end_box,
        projection_coverage_start_px=projection_coverage_start_px,
        projection_coverage_end_px=projection_coverage_end_px,
        projection_max_hole_px=projection_max_hole_px,
    )


def bridge_diagnostic_priority(line_bridge_diagnostic: LineBridgeDiagnostic) -> tuple[int, float]:
    priority_by_reason = {
        "accepted": 9,
        "degenerate_segment": 8,
        "discontinuous_projection": 7,
        "no_common_component": 6,
        "no_components": 5,
        "no_candidate_pixels": 4,
        "empty_roi": 3,
        "gap_too_large": 2,
        "no_bridge_positions": 1,
        "projection_too_far": 0,
    }
    gap_score = (
        float("inf")
        if line_bridge_diagnostic.gap_px is None
        else line_bridge_diagnostic.gap_px
    )
    return priority_by_reason.get(line_bridge_diagnostic.reject_reason, 0), -gap_score


def evaluate_bridge_attempt(
    binary_image: np.ndarray,
    first_line: MergedLine,
    second_line: MergedLine,
    family_angle_degrees: float,
    family_name: str,
    first_line_index: int,
    second_line_index: int,
    projection_distance_px: float,
    projection_tolerance_px: float,
    candidate_count: int,
    candidate_rank: int,
    first_position: float,
    second_position: float,
    gap_px: float,
    max_gap_px: float,
    endpoint_tolerance_px: float,
) -> tuple[LineBridge | None, LineBridgeDiagnostic]:
    (
        ideal_start_point,
        ideal_end_point,
        start_box,
        end_box,
        corridor_polygon,
    ) = build_bridge_geometry(
        binary_image=binary_image,
        family_angle_degrees=family_angle_degrees,
        family_name=family_name,
        first_line=first_line,
        second_line=second_line,
        first_position=first_position,
        second_position=second_position,
        endpoint_tolerance_px=endpoint_tolerance_px,
    )
    if gap_px > max_gap_px:
        return None, build_bridge_diagnostic(
            family_name=family_name,
            first_line_index=first_line_index,
            second_line_index=second_line_index,
            accepted=False,
            reject_reason="gap_too_large",
            projection_distance_px=projection_distance_px,
            projection_tolerance_px=projection_tolerance_px,
            candidate_count=candidate_count,
            selected_candidate_rank=candidate_rank,
            gap_px=gap_px,
            max_gap_px=max_gap_px,
            ideal_start_point=ideal_start_point,
            ideal_end_point=ideal_end_point,
            corridor_polygon=corridor_polygon,
            start_box=start_box,
            end_box=end_box,
        )

    if gap_px <= 1e-6:
        overlap_end_point = build_overlap_bridge_segment(
            ideal_start_point,
            ideal_end_point,
            family_name,
            binary_image.shape,
            second_line.projection - first_line.projection,
        )
        bridge_segment = build_detected_line_segment(
            ideal_start_point,
            overlap_end_point,
        )
        line_bridge = LineBridge(
            family_name=family_name,
            first_line_index=first_line_index,
            second_line_index=second_line_index,
            segment=bridge_segment,
            ideal_start_point=ideal_start_point,
            ideal_end_point=overlap_end_point,
            corridor_polygon=build_corridor_polygon(
                ideal_start_point,
                overlap_end_point,
                max(1.0, endpoint_tolerance_px),
            ),
            start_box=start_box,
            end_box=build_axis_aligned_box(
                overlap_end_point,
                max(2, int(round(endpoint_tolerance_px))),
                binary_image.shape,
            ),
            gap_px=gap_px,
        )
        return line_bridge, build_bridge_diagnostic(
            family_name=family_name,
            first_line_index=first_line_index,
            second_line_index=second_line_index,
            accepted=True,
            reject_reason="accepted",
            projection_distance_px=projection_distance_px,
            projection_tolerance_px=projection_tolerance_px,
            candidate_count=candidate_count,
            selected_candidate_rank=candidate_rank,
            gap_px=gap_px,
            max_gap_px=max_gap_px,
            ideal_start_point=ideal_start_point,
            ideal_end_point=overlap_end_point,
            corridor_polygon=line_bridge.corridor_polygon,
            start_box=line_bridge.start_box,
            end_box=line_bridge.end_box,
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
        return None, build_bridge_diagnostic(
            family_name=family_name,
            first_line_index=first_line_index,
            second_line_index=second_line_index,
            accepted=False,
            reject_reason="empty_roi",
            projection_distance_px=projection_distance_px,
            projection_tolerance_px=projection_tolerance_px,
            candidate_count=candidate_count,
            selected_candidate_rank=candidate_rank,
            gap_px=gap_px,
            max_gap_px=max_gap_px,
            ideal_start_point=ideal_start_point,
            ideal_end_point=ideal_end_point,
            corridor_polygon=corridor_polygon,
            start_box=start_box,
            end_box=end_box,
        )

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
        return None, build_bridge_diagnostic(
            family_name=family_name,
            first_line_index=first_line_index,
            second_line_index=second_line_index,
            accepted=False,
            reject_reason="no_candidate_pixels",
            projection_distance_px=projection_distance_px,
            projection_tolerance_px=projection_tolerance_px,
            candidate_count=candidate_count,
            selected_candidate_rank=candidate_rank,
            gap_px=gap_px,
            max_gap_px=max_gap_px,
            ideal_start_point=ideal_start_point,
            ideal_end_point=ideal_end_point,
            corridor_polygon=corridor_polygon,
            start_box=start_box,
            end_box=end_box,
        )

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
        return None, build_bridge_diagnostic(
            family_name=family_name,
            first_line_index=first_line_index,
            second_line_index=second_line_index,
            accepted=False,
            reject_reason="no_components",
            projection_distance_px=projection_distance_px,
            projection_tolerance_px=projection_tolerance_px,
            candidate_count=candidate_count,
            selected_candidate_rank=candidate_rank,
            gap_px=gap_px,
            max_gap_px=max_gap_px,
            ideal_start_point=ideal_start_point,
            ideal_end_point=ideal_end_point,
            corridor_polygon=corridor_polygon,
            start_box=start_box,
            end_box=end_box,
        )

    start_labels = {
        int(label) for label in np.unique(labels[start_mask > 0]) if int(label) > 0
    }
    end_labels = {int(label) for label in np.unique(labels[end_mask > 0]) if int(label) > 0}
    common_labels = start_labels & end_labels
    if not common_labels:
        return None, build_bridge_diagnostic(
            family_name=family_name,
            first_line_index=first_line_index,
            second_line_index=second_line_index,
            accepted=False,
            reject_reason="no_common_component",
            projection_distance_px=projection_distance_px,
            projection_tolerance_px=projection_tolerance_px,
            candidate_count=candidate_count,
            selected_candidate_rank=candidate_rank,
            gap_px=gap_px,
            max_gap_px=max_gap_px,
            ideal_start_point=ideal_start_point,
            ideal_end_point=ideal_end_point,
            corridor_polygon=corridor_polygon,
            start_box=start_box,
            end_box=end_box,
        )

    best_label = max(
        common_labels,
        key=lambda label: int(np.count_nonzero(labels == label)),
    )
    component_points = np.column_stack(np.where(labels == best_label))
    if component_points.size == 0:
        return None, build_bridge_diagnostic(
            family_name=family_name,
            first_line_index=first_line_index,
            second_line_index=second_line_index,
            accepted=False,
            reject_reason="no_common_component",
            projection_distance_px=projection_distance_px,
            projection_tolerance_px=projection_tolerance_px,
            candidate_count=candidate_count,
            selected_candidate_rank=candidate_rank,
            gap_px=gap_px,
            max_gap_px=max_gap_px,
            ideal_start_point=ideal_start_point,
            ideal_end_point=ideal_end_point,
            corridor_polygon=corridor_polygon,
            start_box=start_box,
            end_box=end_box,
        )

    (
        has_continuous_projection,
        projection_coverage_start_px,
        projection_coverage_end_px,
        projection_max_hole_px,
    ) = component_has_continuous_bridge_projection(
        component_points,
        ideal_start_point,
        ideal_end_point,
        component_origin=(min_x, min_y),
    )
    if not has_continuous_projection:
        return None, build_bridge_diagnostic(
            family_name=family_name,
            first_line_index=first_line_index,
            second_line_index=second_line_index,
            accepted=False,
            reject_reason="discontinuous_projection",
            projection_distance_px=projection_distance_px,
            projection_tolerance_px=projection_tolerance_px,
            candidate_count=candidate_count,
            selected_candidate_rank=candidate_rank,
            gap_px=gap_px,
            max_gap_px=max_gap_px,
            ideal_start_point=ideal_start_point,
            ideal_end_point=ideal_end_point,
            corridor_polygon=corridor_polygon,
            start_box=start_box,
            end_box=end_box,
            projection_coverage_start_px=projection_coverage_start_px,
            projection_coverage_end_px=projection_coverage_end_px,
            projection_max_hole_px=projection_max_hole_px,
        )

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
        return None, build_bridge_diagnostic(
            family_name=family_name,
            first_line_index=first_line_index,
            second_line_index=second_line_index,
            accepted=False,
            reject_reason="degenerate_segment",
            projection_distance_px=projection_distance_px,
            projection_tolerance_px=projection_tolerance_px,
            candidate_count=candidate_count,
            selected_candidate_rank=candidate_rank,
            gap_px=gap_px,
            max_gap_px=max_gap_px,
            ideal_start_point=ideal_start_point,
            ideal_end_point=ideal_end_point,
            corridor_polygon=corridor_polygon,
            start_box=start_box,
            end_box=end_box,
        )

    line_bridge = LineBridge(
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
    return line_bridge, build_bridge_diagnostic(
        family_name=family_name,
        first_line_index=first_line_index,
        second_line_index=second_line_index,
        accepted=True,
        reject_reason="accepted",
        projection_distance_px=projection_distance_px,
        projection_tolerance_px=projection_tolerance_px,
        candidate_count=candidate_count,
        selected_candidate_rank=candidate_rank,
        gap_px=gap_px,
        max_gap_px=max_gap_px,
        ideal_start_point=ideal_start_point,
        ideal_end_point=ideal_end_point,
        corridor_polygon=corridor_polygon,
        start_box=start_box,
        end_box=end_box,
    )


def inspect_line_bridge_candidate(
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
) -> tuple[LineBridge | None, LineBridgeDiagnostic]:
    projection_distance_px = abs(first_line.projection - second_line.projection)
    if projection_distance_px > projection_tolerance_px:
        return None, build_bridge_diagnostic(
            family_name=family_name,
            first_line_index=first_line_index,
            second_line_index=second_line_index,
            accepted=False,
            reject_reason="projection_too_far",
            projection_distance_px=projection_distance_px,
            projection_tolerance_px=projection_tolerance_px,
            candidate_count=0,
            selected_candidate_rank=None,
            gap_px=None,
            max_gap_px=max_gap_px,
        )

    bridge_candidates = candidate_interval_bridge_positions(first_line, second_line)
    if not bridge_candidates:
        return None, build_bridge_diagnostic(
            family_name=family_name,
            first_line_index=first_line_index,
            second_line_index=second_line_index,
            accepted=False,
            reject_reason="no_bridge_positions",
            projection_distance_px=projection_distance_px,
            projection_tolerance_px=projection_tolerance_px,
            candidate_count=0,
            selected_candidate_rank=None,
            gap_px=None,
            max_gap_px=max_gap_px,
        )

    best_diagnostic: LineBridgeDiagnostic | None = None
    candidate_count = len(bridge_candidates)
    for candidate_rank, (first_position, second_position, gap_px) in enumerate(
        bridge_candidates,
        start=1,
    ):
        line_bridge, line_bridge_diagnostic = evaluate_bridge_attempt(
            binary_image=binary_image,
            first_line=first_line,
            second_line=second_line,
            family_angle_degrees=family_angle_degrees,
            family_name=family_name,
            first_line_index=first_line_index,
            second_line_index=second_line_index,
            projection_distance_px=projection_distance_px,
            projection_tolerance_px=projection_tolerance_px,
            candidate_count=candidate_count,
            candidate_rank=candidate_rank,
            first_position=first_position,
            second_position=second_position,
            gap_px=gap_px,
            max_gap_px=max_gap_px,
            endpoint_tolerance_px=endpoint_tolerance_px,
        )
        if line_bridge is not None:
            return line_bridge, line_bridge_diagnostic
        if best_diagnostic is None or bridge_diagnostic_priority(
            line_bridge_diagnostic
        ) > bridge_diagnostic_priority(best_diagnostic):
            best_diagnostic = line_bridge_diagnostic

    if best_diagnostic is None:
        best_diagnostic = build_bridge_diagnostic(
            family_name=family_name,
            first_line_index=first_line_index,
            second_line_index=second_line_index,
            accepted=False,
            reject_reason="no_bridge_positions",
            projection_distance_px=projection_distance_px,
            projection_tolerance_px=projection_tolerance_px,
            candidate_count=candidate_count,
            selected_candidate_rank=None,
            gap_px=None,
            max_gap_px=max_gap_px,
        )
    return None, best_diagnostic


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
    line_bridge, _ = inspect_line_bridge_candidate(
        binary_image=binary_image,
        first_line=first_line,
        second_line=second_line,
        family_angle_degrees=family_angle_degrees,
        family_name=family_name,
        first_line_index=first_line_index,
        second_line_index=second_line_index,
        projection_tolerance_px=projection_tolerance_px,
        max_gap_px=max_gap_px,
        endpoint_tolerance_px=endpoint_tolerance_px,
    )
    return line_bridge


def inspect_line_family_bridge_candidates(
    binary_image: np.ndarray,
    merged_lines: list[MergedLine],
    family_angle_degrees: float | None,
    family_name: str,
    config: ExperimentConfig,
    minimum_dimension: int,
) -> list[LineBridgeDiagnostic]:
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
        return []

    bridge_diagnostics: list[LineBridgeDiagnostic] = []
    for first_index in range(len(merged_lines)):
        for second_index in range(first_index + 1, len(merged_lines)):
            _, line_bridge_diagnostic = inspect_line_bridge_candidate(
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
            bridge_diagnostics.append(line_bridge_diagnostic)
    return bridge_diagnostics


def merge_lines_with_bridges(
    merged_lines: list[MergedLine],
    bridges: list[LineBridge],
    family_name: str,
    family_angle_degrees: float,
) -> list[MergedLine]:
    adjacency: list[list[int]] = [[] for _ in merged_lines]
    for line_bridge in bridges:
        adjacency[line_bridge.first_line_index].append(line_bridge.second_line_index)
        adjacency[line_bridge.second_line_index].append(line_bridge.first_line_index)

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

    return sorted(bridged_lines, key=lambda merged_line: merged_line.projection)


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

    current_lines = list(merged_lines)
    all_bridges: list[LineBridge] = []
    while len(current_lines) > 1:
        iteration_bridges: list[LineBridge] = []
        for first_index in range(len(current_lines)):
            for second_index in range(first_index + 1, len(current_lines)):
                line_bridge = line_bridge_candidate(
                    binary_image=binary_image,
                    first_line=current_lines[first_index],
                    second_line=current_lines[second_index],
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
                iteration_bridges.append(line_bridge)

        if not iteration_bridges:
            break

        current_lines = merge_lines_with_bridges(
            current_lines,
            iteration_bridges,
            family_name,
            family_angle_degrees,
        )
        all_bridges.extend(iteration_bridges)

    return (
        current_lines,
        all_bridges,
        bridge_projection_tolerance_px,
        bridge_max_gap_px,
        bridge_endpoint_tolerance_px,
    )


__all__ = [
    "candidate_interval_bridge_positions",
    "bridge_line_family_gaps",
    "closest_interval_bridge_positions",
    "inspect_line_bridge_candidate",
    "inspect_line_family_bridge_candidates",
    "line_bridge_candidate",
]
