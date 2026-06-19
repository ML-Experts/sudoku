from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from models import LineSegment


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
    intersected_line_axis_debug_name: str
    intersected_segment_axis: LineSegment
    intersected_line_cross_axis_debug_name: str
    intersected_segment_cross_axis: LineSegment
    point: tuple[int, int]
    kind: LogicalLineIntersectionKind
    order: IntersectionOrder = IntersectionOrder.NONE

    @property
    def horizontal_axis_value(self) -> int:
        return self.point[0]

    @property
    def vertical_axis_value(self) -> int:
        return self.point[1]

    @property
    def is_cross(self) -> bool:
        return self.kind == LogicalLineIntersectionKind.CROSS

    @property
    def is_boundary(self) -> bool:
        return self.order in {
            IntersectionOrder.START,
            IntersectionOrder.END,
            IntersectionOrder.BOTH,
        }


@dataclass(frozen=True, slots=True)
class LogicalLineIntersectionDebugCandidate:
    intersected_line_axis_debug_name: str
    intersected_segment_axis: LineSegment
    intersected_line_cross_axis_debug_name: str
    intersected_segment_cross_axis: LineSegment
    point: tuple[int, int]
    kind: LogicalLineIntersectionKind
    axis_value: int
    cross_axis_value: int
    duplicate_index: int = 0
    duplicate_count: int = 1

    @property
    def is_cross(self) -> bool:
        return self.kind == LogicalLineIntersectionKind.CROSS

    # @property
    # def is_horizontal_boundary(self) -> bool:
    #     return self.horizontal_order in {
    #         IntersectionOrder.START,
    #         IntersectionOrder.END,
    #         IntersectionOrder.BOTH,
    #     }

    # @property
    # def is_vertical_boundary(self) -> bool:
    #     return self.vertical_order in {
    #         IntersectionOrder.START,
    #         IntersectionOrder.END,
    #         IntersectionOrder.BOTH,
    #     }

    # @property
    # def is_mutual_boundary(self) -> bool:
    #     return self.is_horizontal_boundary and self.is_vertical_boundary

    # @property
    # def requires_boundary_repair(self) -> bool:
    #     if self.kind != LogicalLineIntersectionKind.CROSS:
    #         return False

    #     return self.is_horizontal_boundary or self.is_vertical_boundary


__all__ = [
    "IntersectionOrder",
    "LogicalLineIntersection",
    "LogicalLineIntersectionDebugCandidate",
    "LogicalLineIntersectionKind",
]
