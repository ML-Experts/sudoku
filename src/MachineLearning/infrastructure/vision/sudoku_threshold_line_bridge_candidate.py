from __future__ import annotations

import cv2
import numpy as np

from infrastructure.vision.sudoku_threshold_geometry import (
    build_axis_aligned_box,
    build_corridor_polygon,
    build_detected_line_segment,
)
from infrastructure.vision.sudoku_threshold_line_bridge_diagnostics import (
    build_bridge_diagnostic,
)
from infrastructure.vision.sudoku_threshold_line_bridge_geometry import (
    build_bridge_geometry,
    build_overlap_bridge_segment,
    component_has_continuous_bridge_projection,
)
from infrastructure.vision.sudoku_threshold_models import (
    LineBridge,
    LineBridgeDiagnostic,
    MergedLine,
)


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

    start_labels = {int(label) for label in np.unique(labels[start_mask > 0]) if int(label) > 0}
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

    best_label = max(common_labels, key=lambda label: int(np.count_nonzero(labels == label)))
    component_points = np.column_stack(np.where(labels == best_label))
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
