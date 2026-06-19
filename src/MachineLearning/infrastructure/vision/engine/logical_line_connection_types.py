from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math

from .logical_line_core import (
    LogicalLine,
    LogicalLineVertexKind,
)


class ConnectionKind(Enum):
    SAME_AXIS = "same_axis"
    CROSS_AXIS = "cross_axis"
    CROSS_AXIS_SPAN = "cross_axis_span"


@dataclass(frozen=True, slots=True)
class ConnectionCandidate:
    connection_kind: ConnectionKind
    target_line: LogicalLine
    target_vertex_kind: LogicalLineVertexKind | None
    distance_px: float
    goal_points: tuple[tuple[int, int], ...] = ()
    preferred_contact_point: tuple[int, int] | None = None


def distance_between_vertices(
    first_vertex: tuple[int, int],
    second_vertex: tuple[int, int],
) -> float:
    return math.hypot(
        first_vertex[0] - second_vertex[0],
        first_vertex[1] - second_vertex[1],
    )


def build_candidate_sort_key(
    candidate: ConnectionCandidate,
) -> tuple[int, float]:
    connection_kind_priority = {
        ConnectionKind.SAME_AXIS: 0,
        ConnectionKind.CROSS_AXIS: 1,
        ConnectionKind.CROSS_AXIS_SPAN: 2,
    }[candidate.connection_kind]
    return connection_kind_priority, candidate.distance_px


def get_source_cross_axis_anchor(
    source_line: LogicalLine,
    source_vertex_kind: LogicalLineVertexKind,
) -> int:
    if source_vertex_kind == LogicalLineVertexKind.START:
        return source_line.cross_axis_start
    return source_line.cross_axis_end


__all__ = [
    "ConnectionCandidate",
    "ConnectionKind",
    "build_candidate_sort_key",
    "distance_between_vertices",
    "get_source_cross_axis_anchor",
]
