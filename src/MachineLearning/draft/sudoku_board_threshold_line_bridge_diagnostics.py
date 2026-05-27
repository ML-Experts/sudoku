from __future__ import annotations

from sudoku_board_threshold_models import LineBridgeDiagnostic


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


def bridge_diagnostic_priority(
    line_bridge_diagnostic: LineBridgeDiagnostic,
) -> tuple[int, float]:
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


__all__ = [
    "bridge_diagnostic_priority",
    "build_bridge_diagnostic",
]
