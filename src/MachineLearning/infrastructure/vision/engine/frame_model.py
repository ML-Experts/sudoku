from __future__ import annotations

from dataclasses import dataclass

from .logical_line_core import LogicalLine


@dataclass(frozen=False, slots=True)
class LogicalLineBoundaryGroup:
    line_start_axis: LogicalLine
    line_end_axis: LogicalLine
    touching_lines: list[LogicalLine]


@dataclass(frozen=True, slots=True)
class LogicalLineFrameCandidateRanking:
    has_exact_inner_line_counts: bool
    inner_horizontal_count: int
    inner_vertical_count: int
    inner_line_count_deviation: int
    matched_vertex_corner_count: int
    matched_order_corner_count: int
    matched_order_expectation_count: int
    top_left_vertex_matches: bool
    top_right_vertex_matches: bool
    bottom_right_vertex_matches: bool
    bottom_left_vertex_matches: bool
    top_left_order_matches: bool
    top_right_order_matches: bool
    bottom_right_order_matches: bool
    bottom_left_order_matches: bool
    perimeter_px: int


@dataclass(frozen=False, slots=True)
class LogicalLineFrameCandidate:
    top_line: LogicalLine
    bottom_line: LogicalLine
    left_line: LogicalLine
    right_line: LogicalLine
    horizontal_lines: tuple[LogicalLine, ...]
    vertical_lines: tuple[LogicalLine, ...]
    ranking_debug: LogicalLineFrameCandidateRanking | None = None
    ranking_position: int | None = None
    is_selected: bool = False


__all__ = [
    "LogicalLineBoundaryGroup",
    "LogicalLineFrameCandidate",
    "LogicalLineFrameCandidateRanking",
]
