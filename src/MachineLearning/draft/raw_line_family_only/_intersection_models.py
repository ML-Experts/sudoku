from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from logical_line_core import LogicalLine
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
    ref_horizontal_line: LogicalLine
    ref_vertical_line: LogicalLine
    ref_horizontal_segment: LineSegment
    ref_vertical_segment: LineSegment
    point: tuple[int, int]
    horizontal_kind: LogicalLineIntersectionKind
    vertical_kind: LogicalLineIntersectionKind
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
    def is_horizontal_cross(self) -> bool:
        return self.horizontal_kind == LogicalLineIntersectionKind.CROSS

    @property
    def is_vertical_cross(self) -> bool:
        return self.vertical_kind == LogicalLineIntersectionKind.CROSS

    @property
    def is_mutual_boundary(self) -> bool:
        return self.is_horizontal_boundary and self.is_vertical_boundary

    @property
    def is_mutual_cross(self) -> bool:
        return self.is_horizontal_cross and self.is_vertical_cross

    @property
    def is_asymmetric_kind(self) -> bool:
        return self.horizontal_kind != self.vertical_kind

    @property
    def kind_pair_label(self) -> str:
        return f"{self.horizontal_kind.value}_{self.vertical_kind.value}"

    @property
    def requires_horizontal_boundary_repair(self) -> bool:
        return self.is_horizontal_cross and self.is_horizontal_boundary

    @property
    def requires_vertical_boundary_repair(self) -> bool:
        return self.is_vertical_cross and self.is_vertical_boundary

    @property
    def requires_boundary_repair(self) -> bool:
        return (
            self.requires_horizontal_boundary_repair
            or self.requires_vertical_boundary_repair
        )


__all__ = [
    "IntersectionOrder",
    "LogicalLineIntersection",
    "LogicalLineIntersectionKind",
]
