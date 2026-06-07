from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np

from raw_line_family_only_geometry import (
    LineSegmentIntersectionResult,
    line_segments_intersect,
)
from raw_line_family_only_logical_line_types import (
    FrameSide,
    LogicalLineVertexKind,
    RawSegmentGroupResult,
    RawSegmentGroupStatus,
    segment_sort_key,
)
from raw_line_family_only_raw_segment_grouping import group_raw_segments_in_line
from raw_line_family_only_models import (
    LineFamilyName,
    LineSegment,
    ToleranceRectangle,
)

if TYPE_CHECKING:
    from raw_line_family_only_intersections import LogicalLineIntersection


@dataclass(slots=True)
class LogicalLine:
    family_name: LineFamilyName
    frame_side: FrameSide = FrameSide.NONE
    line_segments: list[LineSegment] = field(
        init=False,
        default_factory=list,
    )
    intersections: list["LogicalLineIntersection"] = field(
        init=False,
        default_factory=list,
    )
    raw_segment_group_results: list[RawSegmentGroupResult] = field(
        init=False,
        default_factory=list,
    )
    start_segment: LineSegment | None = field(init=False, default=None)
    end_segment: LineSegment | None = field(init=False, default=None)

    @property
    def start_vertex(self) -> tuple[int, int]:
        if self.start_segment is None:
            raise ValueError("LogicalLine does not have a start segment yet.")
        return self.start_segment.start

    @property
    def end_vertex(self) -> tuple[int, int]:
        if self.end_segment is None:
            raise ValueError("LogicalLine does not have an end segment yet.")
        return self.end_segment.end

    @property
    def axis_start(self) -> int:
        if self.start_segment is None:
            raise ValueError("LogicalLine does not have a start segment yet.")
        return self.start_segment.axis_start

    @property
    def axis_end(self) -> int:
        if self.end_segment is None:
            raise ValueError("LogicalLine does not have an end segment yet.")
        return self.end_segment.axis_end

    @property
    def cross_axis_start(self) -> int:
        if self.start_segment is None:
            raise ValueError("LogicalLine does not have a start segment yet.")
        return self.start_segment.cross_axis_start

    @property
    def cross_axis_end(self) -> int:
        if self.end_segment is None:
            raise ValueError("LogicalLine does not have an end segment yet.")
        return self.end_segment.cross_axis_end

    def add_segment(self, line_segment: LineSegment) -> bool:
        self._validate_family(line_segment.family_name)
        if line_segment in self.line_segments:
            return False

        insertion_index = len(self.line_segments)
        for current_index, current_segment in enumerate(self.line_segments):
            if segment_sort_key(line_segment) < segment_sort_key(current_segment):
                insertion_index = current_index
                break

        self.line_segments.insert(insertion_index, line_segment)
        self._refresh_boundary_segments()
        return True

    def replace_segments(self, line_segments: list[LineSegment]) -> None:
        self.line_segments = sorted(line_segments, key=segment_sort_key)
        self._refresh_boundary_segments()

    def clone(self) -> "LogicalLine":
        clone = LogicalLine(
            family_name=self.family_name,
            frame_side=self.frame_side,
        )
        for line_segment in self.line_segments:
            clone.add_segment(line_segment)
        clone.raw_segment_group_results = list(self.raw_segment_group_results)
        return clone

    def merge_logical_line(self, other_line: "LogicalLine") -> None:
        self._validate_family(other_line.family_name)
        for line_segment in other_line.line_segments:
            self.add_segment(line_segment)
        if other_line.raw_segment_group_results:
            self.raw_segment_group_results.extend(other_line.raw_segment_group_results)

    def does_segment_touch(
        self,
        line_segment: LineSegment,
        cross_axis_thickness_px: int,
        axis_gap_tolerance_px: int,
    ) -> LineSegmentIntersectionResult:
        self._validate_family(line_segment.family_name)
        if not self.line_segments:
            return LineSegmentIntersectionResult(intersects=True)

        if (
            line_segment.axis_start >= self.axis_start
            and line_segment.axis_end <= self.axis_end
        ):
            return LineSegmentIntersectionResult(intersects=False)

        for existing_segment in self.line_segments:
            intersection_result = line_segments_intersect(
                existing_segment,
                line_segment,
                cross_axis_thickness_px=cross_axis_thickness_px,
                axis_gap_tolerance_px=axis_gap_tolerance_px,
            )
            if intersection_result.intersects:
                return intersection_result

        return LineSegmentIntersectionResult(intersects=False)

    def does_logical_line_touch(
        self,
        other_line: "LogicalLine",
        cross_axis_thickness_px: int,
        axis_gap_tolerance_px: int,
    ) -> bool:
        self._validate_family(other_line.family_name)
        if self.start_segment is None or self.end_segment is None:
            return False
        if other_line.start_segment is None or other_line.end_segment is None:
            return False

        edge_pairs = (
            (self.start_segment, other_line.start_segment),
            (self.start_segment, other_line.end_segment),
            (self.end_segment, other_line.start_segment),
            (self.end_segment, other_line.end_segment),
        )
        for first_segment, second_segment in edge_pairs:
            intersection_result = line_segments_intersect(
                first_segment,
                second_segment,
                cross_axis_thickness_px=cross_axis_thickness_px,
                axis_gap_tolerance_px=axis_gap_tolerance_px,
            )
            if not intersection_result.intersects:
                continue
            if intersection_result.bridge_segment is not None:
                self.add_segment(intersection_result.bridge_segment)
            self.merge_logical_line(other_line)
            return True

        return False

    def group_raw_segments(
        self,
        binary_image: np.ndarray,
        reference_angle_degrees: float,
        angle_tolerance_degrees: float,
        black_gap_tolerance_px: int,
    ) -> None:
        group_raw_segments_in_line(
            logical_line=self,
            binary_image=binary_image,
            reference_angle_degrees=reference_angle_degrees,
            angle_tolerance_degrees=angle_tolerance_degrees,
            black_gap_tolerance_px=black_gap_tolerance_px,
        )

    def get_vertex(
        self,
        vertex_kind: LogicalLineVertexKind,
    ) -> tuple[int, int]:
        if vertex_kind == LogicalLineVertexKind.START:
            return self.start_vertex
        return self.end_vertex

    def get_vertex_segment(
        self,
        vertex_kind: LogicalLineVertexKind,
    ) -> LineSegment:
        if vertex_kind == LogicalLineVertexKind.START:
            if self.start_segment is None:
                raise ValueError("LogicalLine does not have a start segment yet.")
            return self.start_segment
        if self.end_segment is None:
            raise ValueError("LogicalLine does not have an end segment yet.")
        return self.end_segment

    def build_tolerance_rectangle(
        self,
        reference_vertex: tuple[int, int],
        direction_length: int,
        padding: int,
    ) -> ToleranceRectangle:
        recognition_vector = self._recognition_vector_for_vertex(reference_vertex)
        return ToleranceRectangle(
            reference_point=reference_vertex,
            recognition_vector=recognition_vector,
            vector_length=direction_length,
            padding=padding,
        )

    @property
    def longest_segment(self) -> LineSegment | None:
        if not self.line_segments:
            return None
        return max(self.line_segments, key=lambda current_segment: current_segment.length)

    def collect_long_segments(
        self,
        minimum_length_ratio: float = 0.8,
    ) -> list[LineSegment]:
        if minimum_length_ratio <= 0.0 or minimum_length_ratio > 1.0:
            raise ValueError("minimum_length_ratio must be in the range (0.0, 1.0].")

        longest_segment = self.longest_segment
        if longest_segment is None:
            return []

        minimum_length = longest_segment.length * minimum_length_ratio
        return [
            current_segment
            for current_segment in self.line_segments
            if current_segment.length >= minimum_length
        ]

    def _refresh_boundary_segments(self) -> None:
        if not self.line_segments:
            self.start_segment = None
            self.end_segment = None
            return

        self.start_segment = min(
            self.line_segments,
            key=lambda current_segment: (
                current_segment.axis_start,
                current_segment.axis_end,
            ),
        )
        self.end_segment = max(
            self.line_segments,
            key=lambda current_segment: (
                current_segment.axis_end,
                current_segment.axis_start,
            ),
        )

    def _recognition_vector_for_vertex(
        self,
        reference_vertex: tuple[int, int],
    ) -> tuple[float, float]:
        if self.family_name == LineFamilyName.HORIZONTAL:
            forward_vector = (1.0, 0.0)
        elif self.family_name == LineFamilyName.VERTICAL:
            forward_vector = (0.0, 1.0)
        else:
            raise NotImplementedError(
                "Tolerance rectangles are available only for classified logical lines."
            )

        if reference_vertex == self.end_vertex:
            return forward_vector
        if reference_vertex == self.start_vertex:
            return (-forward_vector[0], -forward_vector[1])

        raise ValueError(
            "reference_vertex must match LogicalLine.start_vertex or "
            "LogicalLine.end_vertex."
        )

    def _validate_family(self, family_name: LineFamilyName) -> None:
        if family_name != self.family_name:
            raise ValueError(
                "LogicalLine and segment/logical line must belong to the same family."
            )


__all__ = [
    "FrameSide",
    "LogicalLine",
    "LogicalLineVertexKind",
    "RawSegmentGroupResult",
    "RawSegmentGroupStatus",
    "segment_sort_key",
]
