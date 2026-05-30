from __future__ import annotations

from dataclasses import dataclass, field

from raw_line_family_only_geometry import (
    LineSegmentIntersectionResult,
    line_segments_intersect,
)
from raw_line_family_only_models import (
    LineFamilyName,
    LineSegment,
    ToleranceRectangle,
)


def _segment_sort_key(
    line_segment: LineSegment,
) -> tuple[int, int, int, int]:
    return (
        line_segment.axis_start,
        line_segment.axis_end,
        line_segment.cross_axis_start,
        line_segment.cross_axis_end,
    )


@dataclass(slots=True)
class LogicalLine:
    family_name: LineFamilyName
    line_segments: list[LineSegment] = field(
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

    def add_segment(self, line_segment: LineSegment) -> None:
        self._validate_family(line_segment.family_name)

        insertion_index = len(self.line_segments)
        for current_index, current_segment in enumerate(self.line_segments):
            if _segment_sort_key(line_segment) < _segment_sort_key(current_segment):
                insertion_index = current_index
                break

        self.line_segments.insert(insertion_index, line_segment)
        self._refresh_boundary_segments()

    def merge_logical_line(self, other_line: "LogicalLine") -> None:
        self._validate_family(other_line.family_name)
        for line_segment in other_line.line_segments:
            self.add_segment(line_segment)

    def does_segment_touch(
        self,
        line_segment: LineSegment,
        cross_axis_thickness_px: int,
        axis_gap_tolerance_px: int,
    ) -> LineSegmentIntersectionResult:
        self._validate_family(line_segment.family_name)
        if not self.line_segments:
            return LineSegmentIntersectionResult(intersects=True)

        if line_segment.axis_start >= self.axis_start and line_segment.axis_end <= self.axis_end:
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

    def _validate_family(self, family_name: LineFamilyName) -> None:
        if family_name != self.family_name:
            raise ValueError(
                "LogicalLine and segment/logical line must belong to the same family."
            )


def build_logical_lines(
    line_segments: list[LineSegment],
    cross_axis_thickness_px: int,
    axis_gap_tolerance_px: int,
) -> list[LogicalLine]:
    if not line_segments:
        return []

    sorted_segments = sorted(line_segments, key=_segment_sort_key)
    logical_lines: list[LogicalLine] = []

    while sorted_segments:
        seed_segment = sorted_segments.pop(0)
        logical_line = LogicalLine(family_name=seed_segment.family_name)
        logical_line.add_segment(seed_segment)

        has_changes = True
        while has_changes:
            has_changes = False
            remaining_segments: list[LineSegment] = []
            for line_segment in sorted_segments:
                intersection_result = logical_line.does_segment_touch(
                    line_segment,
                    cross_axis_thickness_px=cross_axis_thickness_px,
                    axis_gap_tolerance_px=axis_gap_tolerance_px,
                )
                if intersection_result.intersects:
                    if intersection_result.bridge_segment is not None:
                        logical_line.add_segment(intersection_result.bridge_segment)
                    logical_line.add_segment(line_segment)
                    has_changes = True
                    continue
                remaining_segments.append(line_segment)
            sorted_segments = remaining_segments

        logical_lines.append(logical_line)

    return merge_logical_lines(
        logical_lines,
        cross_axis_thickness_px=cross_axis_thickness_px,
        axis_gap_tolerance_px=axis_gap_tolerance_px,
    )


def merge_logical_lines(
    logical_lines: list[LogicalLine],
    cross_axis_thickness_px: int,
    axis_gap_tolerance_px: int,
) -> list[LogicalLine]:
    merged_lines = list(logical_lines)
    has_changes = True

    while has_changes:
        has_changes = False
        merged_lines.sort(key=lambda logical_line: (logical_line.axis_start, logical_line.axis_end))

        for first_index, first_line in enumerate(merged_lines):
            for second_index in range(first_index + 1, len(merged_lines)):
                second_line = merged_lines[second_index]
                if not first_line.does_logical_line_touch(
                    second_line,
                    cross_axis_thickness_px=cross_axis_thickness_px,
                    axis_gap_tolerance_px=axis_gap_tolerance_px,
                ):
                    continue

                del merged_lines[second_index]
                has_changes = True
                break

            if has_changes:
                break

    return merged_lines


def build_tolerance_rectangles(
    logical_lines: list[LogicalLine],
    direction_length: int,
    padding: int,
) -> list[ToleranceRectangle]:
    recognition_vectors = {
        LineFamilyName.HORIZONTAL: (1.0, 0.0),
        LineFamilyName.VERTICAL: (0.0, 1.0),
    }

    tolerance_rectangles: list[ToleranceRectangle] = []
    for logical_line in logical_lines:
        recognition_vector = recognition_vectors.get(logical_line.family_name)
        if recognition_vector is None:
            continue

        tolerance_rectangles.append(
            ToleranceRectangle(
                reference_point=logical_line.end_vertex,
                recognition_vector=recognition_vector,
                vector_length=direction_length,
                padding=padding,
            )
        )

    return tolerance_rectangles


__all__ = [
    "LogicalLine",
    "build_logical_lines",
    "build_tolerance_rectangles",
    "merge_logical_lines",
]
