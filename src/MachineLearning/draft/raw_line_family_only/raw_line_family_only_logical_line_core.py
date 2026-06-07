from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import TYPE_CHECKING

import numpy as np

from raw_line_family_only_geometry import (
    LineSegmentIntersectionResult,
    angle_difference_degrees,
    build_line_segment_from_points,
    line_segments_intersect,
)
from raw_line_family_only_models import (
    LineFamilyName,
    LineSegment,
    SegmentOrigin,
    ToleranceRectangle,
)

if TYPE_CHECKING:
    from raw_line_family_only_intersections import LogicalLineIntersection


def segment_sort_key(
    line_segment: LineSegment,
) -> tuple[int, int, int, int]:
    return (
        line_segment.axis_start,
        line_segment.axis_end,
        line_segment.cross_axis_start,
        line_segment.cross_axis_end,
    )


def _rasterize_line_points(
    start: tuple[int, int],
    end: tuple[int, int],
) -> list[tuple[int, int]]:
    delta_x = end[0] - start[0]
    delta_y = end[1] - start[1]
    step_count = max(abs(delta_x), abs(delta_y))
    if step_count == 0:
        return [start]

    points: list[tuple[int, int]] = []
    for step_index in range(step_count + 1):
        ratio = step_index / float(step_count)
        point = (
            int(round(start[0] + delta_x * ratio)),
            int(round(start[1] + delta_y * ratio)),
        )
        if not points or points[-1] != point:
            points.append(point)
    return points


def _point_axis_value(
    family_name: LineFamilyName,
    point: tuple[int, int],
) -> int:
    if family_name == LineFamilyName.HORIZONTAL:
        return point[0]
    if family_name == LineFamilyName.VERTICAL:
        return point[1]
    raise NotImplementedError("Point axis value is available only for classified lines.")


def _supporting_line_intersection_point(
    first_segment: LineSegment,
    second_segment: LineSegment,
) -> tuple[float, float] | None:
    x1, y1 = first_segment.start
    x2, y2 = first_segment.end
    x3, y3 = second_segment.start
    x4, y4 = second_segment.end
    denominator = (
        (x1 - x2) * (y3 - y4)
        - (y1 - y2) * (x3 - x4)
    )
    if abs(float(denominator)) <= 1e-6:
        return None

    determinant_first = x1 * y2 - y1 * x2
    determinant_second = x3 * y4 - y3 * x4
    intersection_x = (
        determinant_first * (x3 - x4)
        - (x1 - x2) * determinant_second
    ) / float(denominator)
    intersection_y = (
        determinant_first * (y3 - y4)
        - (y1 - y2) * determinant_second
    ) / float(denominator)
    return float(intersection_x), float(intersection_y)


def _point_on_segment_axis(
    line_segment: LineSegment,
    axis_value: int,
) -> tuple[int, int]:
    if line_segment.family_name == LineFamilyName.HORIZONTAL:
        axis_start = line_segment.start[0]
        axis_end = line_segment.end[0]
        if axis_end == axis_start:
            return line_segment.start
        ratio = (axis_value - axis_start) / float(axis_end - axis_start)
        return (
            int(axis_value),
            int(
                round(
                    line_segment.start[1]
                    + (line_segment.end[1] - line_segment.start[1]) * ratio
                )
            ),
        )

    if line_segment.family_name == LineFamilyName.VERTICAL:
        axis_start = line_segment.start[1]
        axis_end = line_segment.end[1]
        if axis_end == axis_start:
            return line_segment.start
        ratio = (axis_value - axis_start) / float(axis_end - axis_start)
        return (
            int(
                round(
                    line_segment.start[0]
                    + (line_segment.end[0] - line_segment.start[0]) * ratio
                )
            ),
            int(axis_value),
        )

    raise NotImplementedError(
        "Point interpolation is available only for classified segments."
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
        raw_segments = sorted(
            [
                line_segment
                for line_segment in self.line_segments
                if line_segment.origin == SegmentOrigin.RAW
            ],
            key=segment_sort_key,
        )
        if not raw_segments:
            self.raw_segment_group_results = []
            return

        raw_segment_group_results: list[RawSegmentGroupResult] = []
        remaining_segments = raw_segments

        while remaining_segments:
            candidate_window, trailing_segments = self._collect_raw_candidate_window(
                remaining_segments
            )
            raw_segment_group_result = self._build_raw_segment_group_result(
                candidate_window,
                binary_image=binary_image,
                reference_angle_degrees=reference_angle_degrees,
                angle_tolerance_degrees=angle_tolerance_degrees,
                black_gap_tolerance_px=black_gap_tolerance_px,
            )
            raw_segment_group_results.append(raw_segment_group_result)
            remaining_segments = sorted(
                [
                    *raw_segment_group_result.deferred_segments,
                    *trailing_segments,
                ],
                key=segment_sort_key,
            )

        raw_segment_group_results = self._repair_adjacent_raw_group_boundaries(
            raw_segment_group_results
        )
        self.raw_segment_group_results = raw_segment_group_results
        self.replace_segments(
            [
                group_result.output_segment
                for group_result in raw_segment_group_results
            ]
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

    def _collect_raw_candidate_window(
        self,
        line_segments: list[LineSegment],
    ) -> tuple[list[LineSegment], list[LineSegment]]:
        if not line_segments:
            return [], []

        candidate_window = [line_segments[0]]
        current_axis_end = line_segments[0].axis_end
        segment_index = 1
        while segment_index < len(line_segments):
            line_segment = line_segments[segment_index]
            if line_segment.axis_start > current_axis_end + 1:
                break
            candidate_window.append(line_segment)
            current_axis_end = max(current_axis_end, line_segment.axis_end)
            segment_index += 1

        return candidate_window, line_segments[segment_index:]

    def _build_raw_segment_group_result(
        self,
        candidate_segments: list[LineSegment],
        binary_image: np.ndarray,
        reference_angle_degrees: float,
        angle_tolerance_degrees: float,
        black_gap_tolerance_px: int,
    ) -> RawSegmentGroupResult:
        if not candidate_segments:
            raise ValueError("candidate_segments cannot be empty.")

        seed_segment = candidate_segments[0]
        valid_boundary_segments = [
            line_segment
            for line_segment in candidate_segments
            if angle_difference_degrees(
                line_segment.angle_degrees,
                reference_angle_degrees,
            )
            <= angle_tolerance_degrees
        ]
        if seed_segment not in valid_boundary_segments:
            valid_boundary_segments.insert(0, seed_segment)

        trial_boundary_segment = max(
            valid_boundary_segments,
            key=lambda line_segment: (
                line_segment.axis_end,
                line_segment.axis_start,
            ),
        )
        trial_segment = build_line_segment_from_points(
            start=seed_segment.start,
            end=trial_boundary_segment.end,
            family_name=self.family_name,
            origin=SegmentOrigin.RAW,
        )
        first_invalid_gap_point = self._find_first_invalid_black_gap_point(
            binary_image=binary_image,
            line_segment=trial_segment,
            black_gap_tolerance_px=black_gap_tolerance_px,
        )
        accepted_boundary_segment = trial_boundary_segment
        status = RawSegmentGroupStatus.SINGLE_SEGMENT

        if first_invalid_gap_point is not None:
            gap_axis_value = _point_axis_value(
                self.family_name,
                first_invalid_gap_point,
            )
            accepted_boundary_candidates = [
                line_segment
                for line_segment in valid_boundary_segments
                if line_segment.axis_end < gap_axis_value
            ]
            if accepted_boundary_candidates:
                accepted_boundary_segment = max(
                    accepted_boundary_candidates,
                    key=lambda line_segment: (
                        line_segment.axis_end,
                        line_segment.axis_start,
                    ),
                )
            else:
                accepted_boundary_segment = seed_segment
            status = RawSegmentGroupStatus.TRIMMED_BY_BLACK_GAP
        elif len(candidate_segments) > 1:
            status = RawSegmentGroupStatus.MERGED

        output_segment = build_line_segment_from_points(
            start=seed_segment.start,
            end=accepted_boundary_segment.end,
            family_name=self.family_name,
            origin=SegmentOrigin.RAW,
        )
        valid_boundary_segment_set = set(valid_boundary_segments)
        used_segments = tuple(
            line_segment
            for line_segment in candidate_segments
            if line_segment == seed_segment
            or (
                line_segment in valid_boundary_segment_set
                and line_segment.axis_end <= accepted_boundary_segment.axis_end
            )
        )
        used_segment_set = set(used_segments)
        deferred_segments = tuple(
            line_segment
            for line_segment in candidate_segments
            if line_segment not in used_segment_set
        )

        return RawSegmentGroupResult(
            seed_segment=seed_segment,
            consumed_segments=tuple(candidate_segments),
            used_segments=used_segments,
            deferred_segments=deferred_segments,
            trial_segment=trial_segment,
            output_segment=output_segment,
            accepted_boundary_segment=accepted_boundary_segment,
            first_invalid_gap_point=first_invalid_gap_point,
            status=status,
        )

    def _find_first_invalid_black_gap_point(
        self,
        binary_image: np.ndarray,
        line_segment: LineSegment,
        black_gap_tolerance_px: int,
    ) -> tuple[int, int] | None:
        black_gap_start: tuple[int, int] | None = None
        black_gap_length = 0
        image_height, image_width = binary_image.shape[:2]

        for point in _rasterize_line_points(line_segment.start, line_segment.end):
            x_coord, y_coord = point
            is_white = (
                0 <= x_coord < image_width
                and 0 <= y_coord < image_height
                and binary_image[y_coord, x_coord] == 255
            )
            if is_white:
                black_gap_start = None
                black_gap_length = 0
                continue

            if black_gap_start is None:
                black_gap_start = point
            black_gap_length += 1
            if black_gap_length > black_gap_tolerance_px:
                return black_gap_start

        return None

    def _repair_adjacent_raw_group_boundaries(
        self,
        raw_segment_group_results: list[RawSegmentGroupResult],
    ) -> list[RawSegmentGroupResult]:
        if len(raw_segment_group_results) < 2:
            return raw_segment_group_results

        repaired_group_results = list(raw_segment_group_results)
        for group_index in range(len(repaired_group_results) - 1):
            repaired_pair = self._repair_raw_group_pair(
                repaired_group_results[group_index],
                repaired_group_results[group_index + 1],
            )
            if repaired_pair is None:
                continue
            repaired_group_results[group_index] = repaired_pair[0]
            repaired_group_results[group_index + 1] = repaired_pair[1]

        return repaired_group_results

    def _repair_raw_group_pair(
        self,
        first_group_result: RawSegmentGroupResult,
        second_group_result: RawSegmentGroupResult,
    ) -> tuple[RawSegmentGroupResult, RawSegmentGroupResult] | None:
        first_segment = first_group_result.output_segment
        second_segment = second_group_result.output_segment
        if first_segment.axis_start > second_segment.axis_start:
            first_group_result, second_group_result = (
                second_group_result,
                first_group_result,
            )
            first_segment, second_segment = second_segment, first_segment

        if first_segment.axis_end < second_segment.axis_start:
            return None

        overlap_axis_start = max(first_segment.axis_start, second_segment.axis_start)
        overlap_axis_end = min(first_segment.axis_end, second_segment.axis_end)
        if overlap_axis_start > overlap_axis_end:
            return None

        preferred_axis_value = float(overlap_axis_start + overlap_axis_end) / 2.0
        intersection_point = _supporting_line_intersection_point(
            first_segment,
            second_segment,
        )
        if intersection_point is not None:
            intersection_axis_value = (
                intersection_point[0]
                if self.family_name == LineFamilyName.HORIZONTAL
                else intersection_point[1]
            )
            if overlap_axis_start - 1.0 <= intersection_axis_value <= overlap_axis_end + 1.0:
                preferred_axis_value = intersection_axis_value

        candidate_pairs: list[
            tuple[LineSegment, LineSegment, tuple[float, float, float], int]
        ] = []
        for boundary_axis in range(overlap_axis_start - 1, overlap_axis_end + 1):
            candidate_pair = self._build_repaired_group_pair(
                first_segment=first_segment,
                second_segment=second_segment,
                first_end_axis=boundary_axis,
                second_start_axis=boundary_axis + 1,
            )
            if candidate_pair is None:
                continue
            repaired_first_segment, repaired_second_segment = candidate_pair
            score = (
                abs(repaired_first_segment.length - repaired_second_segment.length),
                abs(float(boundary_axis) - preferred_axis_value),
                abs(repaired_first_segment.axis_end - first_segment.axis_end)
                + abs(repaired_second_segment.axis_start - second_segment.axis_start),
            )
            candidate_pairs.append(
                (
                    repaired_first_segment,
                    repaired_second_segment,
                    score,
                    boundary_axis,
                )
            )

        if not candidate_pairs:
            return None

        repaired_first_segment, repaired_second_segment, _, _ = min(
            candidate_pairs,
            key=lambda candidate: (
                candidate[2][0],
                candidate[2][1],
            ),
        )
        return (
            replace(first_group_result, output_segment=repaired_first_segment),
            replace(second_group_result, output_segment=repaired_second_segment),
        )

    def _build_repaired_group_pair(
        self,
        first_segment: LineSegment,
        second_segment: LineSegment,
        first_end_axis: int,
        second_start_axis: int,
    ) -> tuple[LineSegment, LineSegment] | None:
        repaired_first_segment = self._rebuild_segment_axis_range(
            first_segment,
            axis_end=first_end_axis,
        )
        repaired_second_segment = self._rebuild_segment_axis_range(
            second_segment,
            axis_start=second_start_axis,
        )
        if repaired_first_segment is None or repaired_second_segment is None:
            return None
        if repaired_first_segment.axis_end + 1 != repaired_second_segment.axis_start:
            return None
        return repaired_first_segment, repaired_second_segment

    def _rebuild_segment_axis_range(
        self,
        line_segment: LineSegment,
        axis_start: int | None = None,
        axis_end: int | None = None,
    ) -> LineSegment | None:
        updated_axis_start = (
            line_segment.axis_start if axis_start is None else int(axis_start)
        )
        updated_axis_end = line_segment.axis_end if axis_end is None else int(axis_end)
        if updated_axis_start >= updated_axis_end:
            return None

        updated_start = (
            line_segment.start
            if axis_start is None
            else _point_on_segment_axis(line_segment, updated_axis_start)
        )
        updated_end = (
            line_segment.end
            if axis_end is None
            else _point_on_segment_axis(line_segment, updated_axis_end)
        )
        repaired_segment = build_line_segment_from_points(
            start=updated_start,
            end=updated_end,
            family_name=line_segment.family_name,
            origin=line_segment.origin,
        )
        if repaired_segment.length <= 0.0:
            return None
        return repaired_segment

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
