from __future__ import annotations

from dataclasses import dataclass

from intersection_model import LogicalLineIntersection
from logical_line_core import LogicalLine


@dataclass(frozen=False, slots=True)
class LogicalLineBoundaryGroup:
    line_start_axis: LogicalLine
    line_end_axis: LogicalLine
    touching_lines: list[LogicalLine]


@dataclass(frozen=True, slots=True)
class LogicalLineFrameCandidate:
    top_line: LogicalLine
    bottom_line: LogicalLine
    left_line: LogicalLine
    right_line: LogicalLine
    horizontal_lines: tuple[LogicalLine, ...]
    vertical_lines: tuple[LogicalLine, ...]


__all__ = [
    "LogicalLineBoundaryGroup",
    "LogicalLineFrameCandidate",
]
