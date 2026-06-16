from __future__ import annotations

from dataclasses import dataclass

from intersection_models import (
    LogicalLineIntersection,
)
from logical_line_core import LogicalLine
from logical_line_types import LogicalLineVertexKind
from models import LineFamilyName, LineSegment, SegmentOrigin


@dataclass(frozen=True, slots=True)
class LogicalLineIntersectionTrimAction:
    family_name: LineFamilyName
    line_debug_name: str
    vertex_kind: LogicalLineVertexKind
    intersection_point: tuple[int, int]
    axis_value: int
    original_segment: LineSegment
    updated_segment: LineSegment


@dataclass(frozen=True, slots=True)
class LogicalLineIntersectionTrimResult:
    actions: tuple[LogicalLineIntersectionTrimAction, ...]

    @property
    def horizontal_trim_count(self) -> int:
        return sum(
            1
            for action in self.actions
            if action.family_name == LineFamilyName.HORIZONTAL
        )

    @property
    def vertical_trim_count(self) -> int:
        return sum(
            1
            for action in self.actions
            if action.family_name == LineFamilyName.VERTICAL
        )


@dataclass(frozen=True, slots=True)
class _TrimCandidate:
    logical_line: LogicalLine
    vertex_kind: LogicalLineVertexKind
    intersection_point: tuple[int, int]
    axis_value: int
    boundary_segment: LineSegment


def _collect_boundary_trim_candidates(
    logical_line_intersections: list[LogicalLineIntersection],
) -> list[_TrimCandidate]:
    trim_candidates: list[_TrimCandidate] = []

    for logical_line_intersection in logical_line_intersections:
        if logical_line_intersection.is_horizontal_cross:
            horizontal_candidate = _build_trim_candidate(
                logical_line=logical_line_intersection.ref_horizontal_line,
                boundary_segment=logical_line_intersection.ref_horizontal_segment,
                intersection_point=logical_line_intersection.point,
                axis_value=logical_line_intersection.horizontal_axis_value,
            )
            if horizontal_candidate is not None:
                trim_candidates.append(horizontal_candidate)

        if logical_line_intersection.is_vertical_cross:
            vertical_candidate = _build_trim_candidate(
                logical_line=logical_line_intersection.ref_vertical_line,
                boundary_segment=logical_line_intersection.ref_vertical_segment,
                intersection_point=logical_line_intersection.point,
                axis_value=logical_line_intersection.vertical_axis_value,
            )
            if vertical_candidate is not None:
                trim_candidates.append(vertical_candidate)

    return trim_candidates


def _build_trim_candidate(
    logical_line: LogicalLine,
    boundary_segment: LineSegment,
    intersection_point: tuple[int, int],
    axis_value: int,
) -> _TrimCandidate | None:
    if boundary_segment.origin != SegmentOrigin.CROSS_AXIS_CONNECTION:
        return None

    is_start_segment = logical_line.start_segment == boundary_segment
    is_end_segment = logical_line.end_segment == boundary_segment
    if not is_start_segment and not is_end_segment:
        return None

    if is_start_segment and axis_value > boundary_segment.axis_start:
        return _TrimCandidate(
            logical_line=logical_line,
            vertex_kind=LogicalLineVertexKind.START,
            intersection_point=intersection_point,
            axis_value=axis_value,
            boundary_segment=boundary_segment,
        )
    if is_end_segment and axis_value < boundary_segment.axis_end:
        return _TrimCandidate(
            logical_line=logical_line,
            vertex_kind=LogicalLineVertexKind.END,
            intersection_point=intersection_point,
            axis_value=axis_value,
            boundary_segment=boundary_segment,
        )

    return None


def _select_best_trim_candidates(
    trim_candidates: list[_TrimCandidate],
) -> list[_TrimCandidate]:
    best_candidates: dict[
        tuple[int, str],
        _TrimCandidate,
    ] = {}

    for trim_candidate in trim_candidates:
        candidate_key = (
            id(trim_candidate.logical_line),
            trim_candidate.vertex_kind.value,
        )
        current_best = best_candidates.get(candidate_key)
        if current_best is None:
            best_candidates[candidate_key] = trim_candidate
            continue

        if trim_candidate.vertex_kind == LogicalLineVertexKind.START:
            if trim_candidate.axis_value > current_best.axis_value:
                best_candidates[candidate_key] = trim_candidate
        elif trim_candidate.axis_value < current_best.axis_value:
            best_candidates[candidate_key] = trim_candidate

    return list(best_candidates.values())


def trim_logical_lines_to_intersections(
    logical_line_intersections: list[LogicalLineIntersection],
) -> LogicalLineIntersectionTrimResult:
    trim_candidates = _collect_boundary_trim_candidates(logical_line_intersections)
    selected_trim_candidates = _select_best_trim_candidates(trim_candidates)
    trim_actions: list[LogicalLineIntersectionTrimAction] = []

    for trim_candidate in selected_trim_candidates:
        updated_segment = trim_candidate.logical_line.align_segment_boundary_to_axis(
            trim_candidate.axis_value,
            trim_candidate.boundary_segment,
        )
        if updated_segment == trim_candidate.boundary_segment:
            continue

        trim_actions.append(
            LogicalLineIntersectionTrimAction(
                family_name=trim_candidate.logical_line.family_name,
                line_debug_name=trim_candidate.logical_line.debug_name,
                vertex_kind=trim_candidate.vertex_kind,
                intersection_point=trim_candidate.intersection_point,
                axis_value=trim_candidate.axis_value,
                original_segment=trim_candidate.boundary_segment,
                updated_segment=updated_segment,
            )
        )

    return LogicalLineIntersectionTrimResult(actions=tuple(trim_actions))


__all__ = [
    "LogicalLineIntersectionTrimAction",
    "LogicalLineIntersectionTrimResult",
    "trim_logical_lines_to_intersections",
]
