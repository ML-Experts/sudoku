from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from enum import Enum
import math

import cv2
import numpy as np

from raw_line_family_only_geometry import (
    LineSegmentIntersectionResult,
    build_line_segment_from_points,
    line_segments_intersect,
)
from raw_line_family_only_models import (
    LineFamilyName,
    LineSegment,
    SegmentOrigin,
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


class LogicalLineVertexKind(Enum):
    START = "start"
    END = "end"


class ConnectionKind(Enum):
    SAME_AXIS = "same_axis"
    CROSS_AXIS = "cross_axis"


@dataclass(frozen=True, slots=True)
class SearchArea:
    mask: np.ndarray
    min_x: int
    max_x: int
    min_y: int
    max_y: int


@dataclass(frozen=True, slots=True)
class ConnectionCandidate:
    connection_kind: ConnectionKind
    target_line: "LogicalLine"
    target_vertex_kind: LogicalLineVertexKind
    distance_px: float


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
            "reference_vertex must match LogicalLine.start_vertex or LogicalLine.end_vertex."
        )

    def _validate_family(self, family_name: LineFamilyName) -> None:
        if family_name != self.family_name:
            raise ValueError(
                "LogicalLine and segment/logical line must belong to the same family."
            )


def _build_search_area(
    image_shape: tuple[int, int],
    tolerance_rectangle: ToleranceRectangle,
) -> SearchArea:
    mask = np.zeros(image_shape[:2], dtype=np.uint8)
    corners = np.array(tolerance_rectangle.corners, dtype=np.int32)
    cv2.fillConvexPoly(mask, corners, 1)
    x_coordinates = corners[:, 0]
    y_coordinates = corners[:, 1]
    max_width = image_shape[1] - 1
    max_height = image_shape[0] - 1
    return SearchArea(
        mask=mask.astype(bool),
        min_x=max(0, int(x_coordinates.min())),
        max_x=min(max_width, int(x_coordinates.max())),
        min_y=max(0, int(y_coordinates.min())),
        max_y=min(max_height, int(y_coordinates.max())),
    )


def _is_point_in_search_area(
    point: tuple[int, int],
    search_area: SearchArea,
) -> bool:
    x_coord, y_coord = point
    if (
        x_coord < search_area.min_x
        or x_coord > search_area.max_x
        or y_coord < search_area.min_y
        or y_coord > search_area.max_y
    ):
        return False
    return bool(search_area.mask[y_coord, x_coord])


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


def _filter_white_points(
    binary_image: np.ndarray,
    points: list[tuple[int, int]],
    search_area: SearchArea,
) -> list[tuple[int, int]]:
    white_points: list[tuple[int, int]] = []
    for point in points:
        x_coord, y_coord = point
        if not _is_point_in_search_area(point, search_area):
            continue
        if binary_image[y_coord, x_coord] != 255:
            continue
        white_points.append(point)
    return white_points


def _build_segment_window_points(
    binary_image: np.ndarray,
    line_segment: LineSegment,
    search_area: SearchArea,
) -> list[tuple[int, int]]:
    return _filter_white_points(
        binary_image,
        _rasterize_line_points(line_segment.start, line_segment.end),
        search_area,
    )


def _build_start_points(
    binary_image: np.ndarray,
    source_line: LogicalLine,
    source_vertex_kind: LogicalLineVertexKind,
    search_area: SearchArea,
    start_tolerance_px: int,
) -> list[tuple[int, int]]:
    source_vertex = source_line.get_vertex(source_vertex_kind)
    source_segment = source_line.get_vertex_segment(source_vertex_kind)
    candidate_points = _build_segment_window_points(
        binary_image,
        source_segment,
        search_area,
    )
    if (
        _is_point_in_search_area(source_vertex, search_area)
        and binary_image[source_vertex[1], source_vertex[0]] == 255
        and source_vertex not in candidate_points
    ):
        candidate_points.append(source_vertex)

    start_points = [
        point
        for point in candidate_points
        if max(abs(point[0] - source_vertex[0]), abs(point[1] - source_vertex[1]))
        <= start_tolerance_px
    ]
    start_points.sort(
        key=lambda point: (
            max(abs(point[0] - source_vertex[0]), abs(point[1] - source_vertex[1])),
            abs(point[0] - source_vertex[0]) + abs(point[1] - source_vertex[1]),
        )
    )
    return start_points


def _reconstruct_path(
    parents: dict[tuple[int, int], tuple[int, int] | None],
    terminal_point: tuple[int, int],
) -> list[tuple[int, int]]:
    path: list[tuple[int, int]] = []
    current_point: tuple[int, int] | None = terminal_point
    while current_point is not None:
        path.append(current_point)
        current_point = parents[current_point]
    path.reverse()
    return path


def _find_white_pixel_path_bfs(
    binary_image: np.ndarray,
    search_area: SearchArea,
    start_points: list[tuple[int, int]],
    goal_points: list[tuple[int, int]],
) -> list[tuple[int, int]] | None:
    if not start_points or not goal_points:
        return None

    goal_set = set(goal_points)
    queue: deque[tuple[int, int]] = deque()
    parents: dict[tuple[int, int], tuple[int, int] | None] = {}

    for point in start_points:
        if point in parents:
            continue
        parents[point] = None
        queue.append(point)

    neighbors = ((1, 0), (-1, 0), (0, 1), (0, -1))
    max_width = binary_image.shape[1]
    max_height = binary_image.shape[0]

    while queue:
        current_point = queue.popleft()
        if current_point in goal_set:
            return _reconstruct_path(parents, current_point)

        current_x, current_y = current_point
        for delta_x, delta_y in neighbors:
            next_point = (current_x + delta_x, current_y + delta_y)
            next_x, next_y = next_point
            if next_x < 0 or next_x >= max_width or next_y < 0 or next_y >= max_height:
                continue
            if next_point in parents:
                continue
            if not _is_point_in_search_area(next_point, search_area):
                continue
            if binary_image[next_y, next_x] != 255:
                continue
            parents[next_point] = current_point
            queue.append(next_point)

    return None


def _path_to_segments(
    path_points: list[tuple[int, int]],
    family_name: LineFamilyName,
    origin: SegmentOrigin,
) -> list[LineSegment]:
    if len(path_points) < 2:
        return []

    segments: list[LineSegment] = []
    run_start = path_points[0]
    previous_point = path_points[0]
    previous_direction = (
        path_points[1][0] - path_points[0][0],
        path_points[1][1] - path_points[0][1],
    )

    for current_point in path_points[1:]:
        current_direction = (
            current_point[0] - previous_point[0],
            current_point[1] - previous_point[1],
        )
        if current_direction != previous_direction:
            if run_start != previous_point:
                segments.append(
                    build_line_segment_from_points(
                        run_start,
                        previous_point,
                        family_name=family_name,
                        origin=origin,
                    )
                )
            run_start = previous_point
            previous_direction = current_direction
        previous_point = current_point

    if run_start != previous_point:
        segments.append(
            build_line_segment_from_points(
                run_start,
                previous_point,
                family_name=family_name,
                origin=origin,
            )
        )

    return segments


def _add_path_segments(
    logical_line: LogicalLine,
    path_points: list[tuple[int, int]],
    origin: SegmentOrigin,
) -> None:
    for line_segment in _path_to_segments(
        path_points,
        family_name=logical_line.family_name,
        origin=origin,
    ):
        logical_line.add_segment(line_segment)


def _build_same_axis_goal_sets(
    binary_image: np.ndarray,
    search_area: SearchArea,
    target_line: LogicalLine,
    target_vertex_kind: LogicalLineVertexKind,
) -> list[list[tuple[int, int]]]:
    goal_sets: list[list[tuple[int, int]]] = []
    target_vertex = target_line.get_vertex(target_vertex_kind)
    if (
        _is_point_in_search_area(target_vertex, search_area)
        and binary_image[target_vertex[1], target_vertex[0]] == 255
    ):
        goal_sets.append([target_vertex])

    target_segment = target_line.get_vertex_segment(target_vertex_kind)
    segment_window_points = _build_segment_window_points(
        binary_image,
        target_segment,
        search_area,
    )
    if segment_window_points:
        goal_sets.append(segment_window_points)

    return goal_sets


def _build_cross_axis_goal_band(
    binary_image: np.ndarray,
    search_area: SearchArea,
    source_line: LogicalLine,
    target_vertex: tuple[int, int],
) -> list[tuple[int, int]]:
    goal_points: list[tuple[int, int]] = []
    if source_line.family_name == LineFamilyName.HORIZONTAL:
        target_x = target_vertex[0]
        if target_x < search_area.min_x or target_x > search_area.max_x:
            return []
        for y_coord in range(search_area.min_y, search_area.max_y + 1):
            if not search_area.mask[y_coord, target_x]:
                continue
            if binary_image[y_coord, target_x] != 255:
                continue
            goal_points.append((target_x, y_coord))
        return goal_points

    target_y = target_vertex[1]
    if target_y < search_area.min_y or target_y > search_area.max_y:
        return []
    for x_coord in range(search_area.min_x, search_area.max_x + 1):
        if not search_area.mask[target_y, x_coord]:
            continue
        if binary_image[target_y, x_coord] != 255:
            continue
        goal_points.append((x_coord, target_y))
    return goal_points


def _build_cross_axis_goal_sets(
    binary_image: np.ndarray,
    search_area: SearchArea,
    source_line: LogicalLine,
    target_line: LogicalLine,
    target_vertex_kind: LogicalLineVertexKind,
) -> list[list[tuple[int, int]]]:
    target_vertex = target_line.get_vertex(target_vertex_kind)
    goal_sets = _build_same_axis_goal_sets(
        binary_image,
        search_area,
        target_line,
        target_vertex_kind,
    )
    goal_band = _build_cross_axis_goal_band(
        binary_image,
        search_area,
        source_line,
        target_vertex,
    )
    if goal_band:
        goal_sets.append(goal_band)
    return goal_sets


def _try_find_path(
    binary_image: np.ndarray,
    search_area: SearchArea,
    start_points: list[tuple[int, int]],
    goal_sets: list[list[tuple[int, int]]],
) -> list[tuple[int, int]] | None:
    for goal_points in goal_sets:
        path_points = _find_white_pixel_path_bfs(
            binary_image,
            search_area,
            start_points,
            goal_points,
        )
        if path_points is not None:
            return path_points
    return None


def _distance_between_vertices(
    first_vertex: tuple[int, int],
    second_vertex: tuple[int, int],
) -> float:
    return math.hypot(
        first_vertex[0] - second_vertex[0],
        first_vertex[1] - second_vertex[1],
    )


def _build_candidate_sort_key(
    candidate: ConnectionCandidate,
) -> tuple[int, float]:
    connection_kind_priority = (
        0 if candidate.connection_kind == ConnectionKind.SAME_AXIS else 1
    )
    return connection_kind_priority, candidate.distance_px


def _collect_connection_candidates(
    source_line: LogicalLine,
    source_vertex_kind: LogicalLineVertexKind,
    search_area: SearchArea,
    same_axis_lines: list[LogicalLine],
    cross_axis_lines: list[LogicalLine],
) -> list[ConnectionCandidate]:
    source_vertex = source_line.get_vertex(source_vertex_kind)
    candidates: list[ConnectionCandidate] = []

    def collect_from_lines(
        target_lines: list[LogicalLine],
        connection_kind: ConnectionKind,
    ) -> None:
        for target_line in target_lines:
            if target_line is source_line:
                continue
            for target_vertex_kind in LogicalLineVertexKind:
                target_vertex = target_line.get_vertex(target_vertex_kind)
                if not _is_point_in_search_area(target_vertex, search_area):
                    continue
                candidates.append(
                    ConnectionCandidate(
                        connection_kind=connection_kind,
                        target_line=target_line,
                        target_vertex_kind=target_vertex_kind,
                        distance_px=_distance_between_vertices(
                            source_vertex,
                            target_vertex,
                        ),
                    )
                )

    collect_from_lines(same_axis_lines, ConnectionKind.SAME_AXIS)
    collect_from_lines(cross_axis_lines, ConnectionKind.CROSS_AXIS)
    candidates.sort(key=_build_candidate_sort_key)
    return candidates


def _remove_logical_line(
    logical_lines: list[LogicalLine],
    target_line: LogicalLine,
) -> None:
    for line_index, logical_line in enumerate(logical_lines):
        if logical_line is target_line:
            del logical_lines[line_index]
            return


def _contains_logical_line(
    logical_lines: list[LogicalLine],
    target_line: LogicalLine,
) -> bool:
    return any(logical_line is target_line for logical_line in logical_lines)


def _try_connect_same_axis_candidate(
    binary_image: np.ndarray,
    source_line: LogicalLine,
    source_vertex_kind: LogicalLineVertexKind,
    search_area: SearchArea,
    candidate: ConnectionCandidate,
    axis_gap_tolerance_px: int,
    same_axis_lines: list[LogicalLine],
) -> bool:
    start_points = _build_start_points(
        binary_image,
        source_line,
        source_vertex_kind,
        search_area,
        start_tolerance_px=axis_gap_tolerance_px,
    )
    path_points = _try_find_path(
        binary_image,
        search_area,
        start_points,
        _build_same_axis_goal_sets(
            binary_image,
            search_area,
            candidate.target_line,
            candidate.target_vertex_kind,
        ),
    )
    if path_points is None:
        return False

    _add_path_segments(
        source_line,
        path_points,
        origin=SegmentOrigin.SAME_AXIS_CONNECTION,
    )
    source_line.merge_logical_line(candidate.target_line)
    _remove_logical_line(same_axis_lines, candidate.target_line)
    return True


def _try_connect_cross_axis_candidate(
    binary_image: np.ndarray,
    source_line: LogicalLine,
    source_vertex_kind: LogicalLineVertexKind,
    search_area: SearchArea,
    candidate: ConnectionCandidate,
    axis_gap_tolerance_px: int,
    cross_axis_thickness_px: int,
    rectangle_vector_length_px: int,
    rectangle_padding_px: int,
) -> bool:
    source_start_points = _build_start_points(
        binary_image,
        source_line,
        source_vertex_kind,
        search_area,
        start_tolerance_px=max(cross_axis_thickness_px, axis_gap_tolerance_px),
    )
    source_path_points = _try_find_path(
        binary_image,
        search_area,
        source_start_points,
        _build_cross_axis_goal_sets(
            binary_image,
            search_area,
            source_line,
            candidate.target_line,
            candidate.target_vertex_kind,
        ),
    )
    if source_path_points is None:
        return False

    reciprocal_vertex = source_line.get_vertex(source_vertex_kind)
    reciprocal_rectangle = candidate.target_line.build_tolerance_rectangle(
        reference_vertex=candidate.target_line.get_vertex(candidate.target_vertex_kind),
        direction_length=rectangle_vector_length_px,
        padding=rectangle_padding_px,
    )
    reciprocal_search_area = _build_search_area(
        binary_image.shape,
        reciprocal_rectangle,
    )
    if not _is_point_in_search_area(reciprocal_vertex, reciprocal_search_area):
        return False

    reciprocal_start_points = _build_start_points(
        binary_image,
        candidate.target_line,
        candidate.target_vertex_kind,
        reciprocal_search_area,
        start_tolerance_px=max(cross_axis_thickness_px, axis_gap_tolerance_px),
    )
    reciprocal_path_points = _try_find_path(
        binary_image,
        reciprocal_search_area,
        reciprocal_start_points,
        _build_cross_axis_goal_sets(
            binary_image,
            reciprocal_search_area,
            candidate.target_line,
            source_line,
            source_vertex_kind,
        ),
    )
    if reciprocal_path_points is None:
        return False

    _add_path_segments(
        source_line,
        source_path_points,
        origin=SegmentOrigin.CROSS_AXIS_CONNECTION,
    )
    _add_path_segments(
        candidate.target_line,
        reciprocal_path_points,
        origin=SegmentOrigin.CROSS_AXIS_CONNECTION,
    )
    return True


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
        merged_lines.sort(
            key=lambda logical_line: (logical_line.axis_start, logical_line.axis_end)
        )

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


def connect_logical_lines_by_pixels(
    binary_image: np.ndarray,
    horizontal_logical_lines: list[LogicalLine],
    vertical_logical_lines: list[LogicalLine],
    axis_gap_tolerance_px: int,
    cross_axis_thickness_px: int,
    rectangle_vector_length_px: int,
    rectangle_padding_px: int,
) -> tuple[list[LogicalLine], list[LogicalLine]]:
    connected_horizontal_lines = list(horizontal_logical_lines)
    connected_vertical_lines = list(vertical_logical_lines)
    has_changes = True

    while has_changes:
        has_changes = False
        for source_lines, same_axis_lines, cross_axis_lines in (
            (
                connected_horizontal_lines,
                connected_horizontal_lines,
                connected_vertical_lines,
            ),
            (
                connected_vertical_lines,
                connected_vertical_lines,
                connected_horizontal_lines,
            ),
        ):
            for source_line in list(source_lines):
                if not _contains_logical_line(source_lines, source_line):
                    continue
                for source_vertex_kind in LogicalLineVertexKind:
                    source_vertex = source_line.get_vertex(source_vertex_kind)
                    tolerance_rectangle = source_line.build_tolerance_rectangle(
                        reference_vertex=source_vertex,
                        direction_length=rectangle_vector_length_px,
                        padding=rectangle_padding_px,
                    )
                    search_area = _build_search_area(
                        binary_image.shape,
                        tolerance_rectangle,
                    )
                    connection_candidates = _collect_connection_candidates(
                        source_line,
                        source_vertex_kind,
                        search_area,
                        same_axis_lines,
                        cross_axis_lines,
                    )
                    for candidate in connection_candidates:
                        if candidate.connection_kind == ConnectionKind.SAME_AXIS:
                            was_connected = _try_connect_same_axis_candidate(
                                binary_image,
                                source_line,
                                source_vertex_kind,
                                search_area,
                                candidate,
                                axis_gap_tolerance_px=axis_gap_tolerance_px,
                                same_axis_lines=same_axis_lines,
                            )
                        else:
                            was_connected = _try_connect_cross_axis_candidate(
                                binary_image,
                                source_line,
                                source_vertex_kind,
                                search_area,
                                candidate,
                                axis_gap_tolerance_px=axis_gap_tolerance_px,
                                cross_axis_thickness_px=cross_axis_thickness_px,
                                rectangle_vector_length_px=rectangle_vector_length_px,
                                rectangle_padding_px=rectangle_padding_px,
                            )

                        if not was_connected:
                            continue

                        has_changes = True
                        break

                    if has_changes:
                        break
                if has_changes:
                    break
            if has_changes:
                break

    return connected_horizontal_lines, connected_vertical_lines


__all__ = [
    "LogicalLine",
    "build_logical_lines",
    "connect_logical_lines_by_pixels",
    "merge_logical_lines",
]
