from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np

from .geometry import (
    LineSegmentIntersectionResult,
    line_segments_intersect,
)
from .logical_line_segment_geometry import rebuild_segment_axis_range
from .logical_line_types import (
    FrameSide,
    LogicalLineVertexKind,
    RawSegmentGroupResult,
    RawSegmentGroupStatus,
    segment_sort_key,
)
from .raw_segment_grouping import group_raw_segments_in_line
from .models import (
    LineFamilyName,
    LineSegment,
    ToleranceRectangle,
)

from .intersection_model import (
    LogicalLineIntersection,
    LogicalLineIntersectionDebugCandidate,
    IntersectionOrder,
    LogicalLineIntersectionKind,
)

@dataclass(slots=True)
class LogicalLine:
    family_name: LineFamilyName
    debug_name: str = ""
    frame_side: FrameSide = FrameSide.NONE
    line_segments: list[LineSegment] = field(
        init=False,
        default_factory=list,
    )
    raw_segment_group_results: list[RawSegmentGroupResult] = field(
        init=False,
        default_factory=list,
    )
    start_segment: LineSegment | None = field(init=False, default=None)
    end_segment: LineSegment | None = field(init=False, default=None)
    intersections: list[LogicalLineIntersection] = field(
        init=False,
        default_factory=list,
    )
    intersection_debug_candidates: list[LogicalLineIntersectionDebugCandidate] = field(
        init=False,
        default_factory=list,
    )

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
    def axis_length(self) -> int:
        return self.axis_end - self.axis_start + 1

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
            debug_name=self.debug_name,
            frame_side=self.frame_side,
        )
        for line_segment in self.line_segments:
            clone.add_segment(line_segment)
        clone.raw_segment_group_results = list(self.raw_segment_group_results)
        clone.intersections = []
        clone.intersection_debug_candidates = []
        return clone

    def merge_logical_line(self, other_line: "LogicalLine") -> None:
        self._validate_family(other_line.family_name)
        if not self.debug_name and other_line.debug_name:
            self.debug_name = other_line.debug_name
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

    # def align_segment_boundary_to_axis(
    #     self,
    #     axis_value: int,
    #     line_segment: LineSegment,
    # ) -> LineSegment:
    #     if line_segment not in self.line_segments:
    #         raise ValueError("The provided segment does not belong to this LogicalLine.")

    #     vertex_kind = self._resolve_segment_boundary_vertex_kind(
    #         line_segment,
    #         axis_value,
    #     )
    #     if vertex_kind == LogicalLineVertexKind.START:
    #         if axis_value <= line_segment.axis_start:
    #             return line_segment
    #         updated_segment = rebuild_segment_axis_range(
    #             line_segment,
    #             axis_start=axis_value,
    #         )
    #     else:
    #         if axis_value >= line_segment.axis_end:
    #             return line_segment
    #         updated_segment = rebuild_segment_axis_range(
    #             line_segment,
    #             axis_end=axis_value,
    #         )

    #     if updated_segment is None:
    #         if len(self.line_segments) == 1:
    #             return line_segment
    #         self._replace_segment(line_segment, None)
    #         replacement_segment = self.get_vertex_segment(vertex_kind)
    #         return replacement_segment

    #     self._replace_segment(line_segment, updated_segment)
    #     return updated_segment

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

    def trim_to_intersections(self) -> bool:
        if not self.line_segments or not self.intersections:
            return False

        start_intersection = next(
            (
                intersection
                for intersection in self.intersections
                if intersection.order in {
                    IntersectionOrder.START,
                    IntersectionOrder.BOTH,
                }
            ),
            None,
        )
        end_intersection = next(
            (
                intersection
                for intersection in reversed(self.intersections)
                if intersection.order in {
                    IntersectionOrder.END,
                    IntersectionOrder.BOTH,
                }
            ),
            None,
        )

        if start_intersection is None or end_intersection is None:
            return False

        if self.family_name == LineFamilyName.HORIZONTAL:
            start_axis_value = start_intersection.horizontal_axis_value
            end_axis_value = end_intersection.horizontal_axis_value
        elif self.family_name == LineFamilyName.VERTICAL:
            start_axis_value = start_intersection.vertical_axis_value
            end_axis_value = end_intersection.vertical_axis_value
        else:
            raise NotImplementedError(
                "Intersection trimming is available only for classified logical lines."
            )

        if start_axis_value > end_axis_value:
            return False

        # Jedno przecięcie (BOTH) nie daje dwóch granic do sensownego trimowania.
        if start_intersection is end_intersection:
            start_intersection.kind = LogicalLineIntersectionKind.TOUCH
            return False

        start_segment_index: int | None = None
        end_segment_index: int | None = None

        if start_intersection.intersected_segment_axis in self.line_segments:
            start_segment_index = self.line_segments.index(
                start_intersection.intersected_segment_axis
            )
        if end_intersection.intersected_segment_axis in self.line_segments:
            end_segment_index = self.line_segments.index(
                end_intersection.intersected_segment_axis
            )

        if start_segment_index is None:
            for index, line_segment in enumerate(self.line_segments):
                if line_segment.axis_start <= start_axis_value <= line_segment.axis_end:
                    start_segment_index = index
                    break

        if end_segment_index is None:
            for index in range(len(self.line_segments) - 1, -1, -1):
                line_segment = self.line_segments[index]
                if line_segment.axis_start <= end_axis_value <= line_segment.axis_end:
                    end_segment_index = index
                    break

        if start_segment_index is None or end_segment_index is None:
            return False

        if start_segment_index > end_segment_index:
            return False

        trimmed_segments = list(
            self.line_segments[start_segment_index : end_segment_index + 1]
        )
        if not trimmed_segments:
            return False

        if len(trimmed_segments) == 1:
            updated_segment = rebuild_segment_axis_range(
                trimmed_segments[0],
                axis_start=start_axis_value,
                axis_end=end_axis_value,
            )
            if updated_segment is None:
                return False
            trimmed_segments[0] = updated_segment
        else:
            first_segment = trimmed_segments[0]
            if start_axis_value > first_segment.axis_start:
                updated_first_segment = rebuild_segment_axis_range(
                    first_segment,
                    axis_start=start_axis_value,
                )
                if updated_first_segment is None:
                    return False
                trimmed_segments[0] = updated_first_segment

            last_segment = trimmed_segments[-1]
            if end_axis_value < last_segment.axis_end:
                updated_last_segment = rebuild_segment_axis_range(
                    last_segment,
                    axis_end=end_axis_value,
                )
                if updated_last_segment is None:
                    return False
                trimmed_segments[-1] = updated_last_segment

        geometry_changed = trimmed_segments != self.line_segments
        self.replace_segments(trimmed_segments)

        start_intersection.kind = LogicalLineIntersectionKind.TOUCH
        end_intersection.kind = LogicalLineIntersectionKind.TOUCH

        return geometry_changed

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
