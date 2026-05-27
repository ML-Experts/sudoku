from __future__ import annotations

import numpy as np

from infrastructure.vision.sudoku_threshold_line_bridge_candidate import (
    evaluate_bridge_attempt,
)
from infrastructure.vision.sudoku_threshold_line_bridge_diagnostics import (
    bridge_diagnostic_priority,
    build_bridge_diagnostic,
)
from infrastructure.vision.sudoku_threshold_line_bridge_positions import (
    candidate_interval_bridge_positions,
)
from infrastructure.vision.sudoku_threshold_models import (
    LineBridge,
    LineBridgeDiagnostic,
    MergedLine,
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
