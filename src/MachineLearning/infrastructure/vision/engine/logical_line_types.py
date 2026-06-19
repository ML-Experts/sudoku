from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .models import LineSegment


def segment_sort_key(
    line_segment: LineSegment,
) -> tuple[int, int, int, int]:
    return (
        line_segment.axis_start,
        line_segment.axis_end,
        line_segment.cross_axis_start,
        line_segment.cross_axis_end,
    )


class LogicalLineVertexKind(Enum):
    START = "start"
    END = "end"


class FrameSide(Enum):
    NONE = "none"
    TOP = "top"
    BOTTOM = "bottom"
    LEFT = "left"
    RIGHT = "right"


class RawSegmentGroupStatus(Enum):
    SINGLE_SEGMENT = "single_segment"
    MERGED = "merged"
    TRIMMED_BY_BLACK_GAP = "trimmed_by_black_gap"
    TRIMMED_BY_OVERLAP = "trimmed_by_overlap"


@dataclass(frozen=True, slots=True)
class RawSegmentGroupResult:
    seed_segment: LineSegment
    consumed_segments: tuple[LineSegment, ...]
    used_segments: tuple[LineSegment, ...]
    deferred_segments: tuple[LineSegment, ...]
    trial_segment: LineSegment
    output_segment: LineSegment
    accepted_boundary_segment: LineSegment
    first_invalid_gap_point: tuple[int, int] | None
    status: RawSegmentGroupStatus


__all__ = [
    "FrameSide",
    "LogicalLineVertexKind",
    "RawSegmentGroupResult",
    "RawSegmentGroupStatus",
    "segment_sort_key",
]
