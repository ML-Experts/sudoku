from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from raw_line_family_only_logical_line_core import LogicalLine
from raw_line_family_only_models import LineSegment


class LogicalLineIntersectionKind(Enum):
    CROSS = "cross"
    TOUCH = "touch"


class IntersectionOrder(Enum):
    NONE = "none"
    START = "start"
    MIDDLE = "middle"
    END = "end"
    BOTH = "both"


@dataclass(slots=True)
class LogicalLineIntersection:
    ref_horizontal_line: LogicalLine
    ref_vertical_line: LogicalLine
    ref_horizontal_segment: LineSegment
    ref_vertical_segment: LineSegment
    point: tuple[int, int]
    kind: LogicalLineIntersectionKind
    horizontal_order: IntersectionOrder = IntersectionOrder.NONE
    vertical_order: IntersectionOrder = IntersectionOrder.NONE

    @property
    def horizontal_axis_value(self) -> int:
        return self.point[0]

    @property
    def vertical_axis_value(self) -> int:
        return self.point[1]

    @property
    def is_horizontal_boundary(self) -> bool:
        return self.horizontal_order in {
            IntersectionOrder.START,
            IntersectionOrder.END,
            IntersectionOrder.BOTH,
        }

    @property
    def is_vertical_boundary(self) -> bool:
        return self.vertical_order in {
            IntersectionOrder.START,
            IntersectionOrder.END,
            IntersectionOrder.BOTH,
        }

    @property
    def is_mutual_boundary(self) -> bool:
        return self.is_horizontal_boundary and self.is_vertical_boundary

    def correct_intersection(self) -> None:
        raise NotImplementedError(
            "LogicalLineIntersection.correct_intersection() is not implemented yet."
        )


@dataclass(frozen=True, slots=True)
class LogicalLineBorderPair:
    ref_line: LogicalLine
    border_lines: tuple[LogicalLine, ...]


@dataclass(frozen=True, slots=True)
class LogicalLineFrame:
    top_line: LogicalLine
    bottom_line: LogicalLine
    left_line: LogicalLine
    right_line: LogicalLine

    @property
    def lines(self) -> tuple[LogicalLine, LogicalLine, LogicalLine, LogicalLine]:
        return (
            self.top_line,
            self.bottom_line,
            self.left_line,
            self.right_line,
        )


@dataclass(frozen=True, slots=True)
class LogicalLineIntersectionAnalysis:
    frame: LogicalLineFrame | None
    horizontal_lines: list[LogicalLine]
    vertical_lines: list[LogicalLine]
    intersections: list[LogicalLineIntersection]

    @property
    def logical_lines(self) -> list[LogicalLine]:
        return [*self.horizontal_lines, *self.vertical_lines]


@dataclass(slots=True)
class _LogicalLineIntersectionCandidate:
    ref_horizontal_line: LogicalLine
    ref_vertical_line: LogicalLine
    ref_horizontal_segment: LineSegment
    ref_vertical_segment: LineSegment
    point: tuple[int, int]
    kind: LogicalLineIntersectionKind
    horizontal_order: IntersectionOrder = IntersectionOrder.NONE
    vertical_order: IntersectionOrder = IntersectionOrder.NONE

    @property
    def horizontal_axis_value(self) -> int:
        return self.point[0]

    @property
    def vertical_axis_value(self) -> int:
        return self.point[1]

    @property
    def is_horizontal_boundary(self) -> bool:
        return self.horizontal_order in {
            IntersectionOrder.START,
            IntersectionOrder.END,
            IntersectionOrder.BOTH,
        }

    @property
    def is_vertical_boundary(self) -> bool:
        return self.vertical_order in {
            IntersectionOrder.START,
            IntersectionOrder.END,
            IntersectionOrder.BOTH,
        }

    @property
    def is_mutual_boundary(self) -> bool:
        return self.is_horizontal_boundary and self.is_vertical_boundary


__all__ = [
    "IntersectionOrder",
    "LogicalLineBorderPair",
    "LogicalLineFrame",
    "LogicalLineIntersection",
    "LogicalLineIntersectionAnalysis",
    "LogicalLineIntersectionKind",
    "_LogicalLineIntersectionCandidate",
]
