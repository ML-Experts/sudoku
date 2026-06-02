from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import Enum

from raw_line_family_only_logical_line_core import FrameSide, LogicalLine
from raw_line_family_only_models import LineFamilyName, LineSegment


_EPSILON = 1e-6


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


def _cross_product(
    first_vector: tuple[float, float],
    second_vector: tuple[float, float],
) -> float:
    return (
        first_vector[0] * second_vector[1]
        - first_vector[1] * second_vector[0]
    )


def _subtract_points(
    first_point: tuple[int, int],
    second_point: tuple[int, int],
) -> tuple[float, float]:
    return (
        float(first_point[0] - second_point[0]),
        float(first_point[1] - second_point[1]),
    )


def _is_point_on_segment(
    point: tuple[int, int],
    line_segment: LineSegment,
) -> bool:
    x, y = point
    x1, y1 = line_segment.start
    x2, y2 = line_segment.end

    cross_value = (x - x1) * (y2 - y1) - (y - y1) * (x2 - x1)
    if abs(cross_value) > _EPSILON:
        return False

    min_x = min(x1, x2) - _EPSILON
    max_x = max(x1, x2) + _EPSILON
    min_y = min(y1, y2) - _EPSILON
    max_y = max(y1, y2) + _EPSILON
    return min_x <= x <= max_x and min_y <= y <= max_y


def _is_endpoint_intersection(
    t_value: float,
    u_value: float,
) -> bool:
    return (
        abs(t_value) <= _EPSILON
        or abs(t_value - 1.0) <= _EPSILON
        or abs(u_value) <= _EPSILON
        or abs(u_value - 1.0) <= _EPSILON
    )


def find_segment_intersection(
    horizontal_segment: LineSegment,
    vertical_segment: LineSegment,
) -> tuple[tuple[int, int], LogicalLineIntersectionKind] | None:
    if horizontal_segment.family_name != LineFamilyName.HORIZONTAL:
        raise ValueError("horizontal_segment must belong to the horizontal family.")
    if vertical_segment.family_name != LineFamilyName.VERTICAL:
        raise ValueError("vertical_segment must belong to the vertical family.")

    horizontal_start = horizontal_segment.start
    vertical_start = vertical_segment.start
    horizontal_vector = _subtract_points(horizontal_segment.end, horizontal_start)
    vertical_vector = _subtract_points(vertical_segment.end, vertical_start)
    cross_value = _cross_product(horizontal_vector, vertical_vector)
    offset_vector = _subtract_points(vertical_start, horizontal_start)

    if abs(cross_value) <= _EPSILON:
        shared_points = [
            point
            for point in (
                horizontal_segment.start,
                horizontal_segment.end,
                vertical_segment.start,
                vertical_segment.end,
            )
            if (
                _is_point_on_segment(point, horizontal_segment)
                and _is_point_on_segment(point, vertical_segment)
            )
        ]
        if not shared_points:
            return None

        first_shared_point = min(shared_points)
        return first_shared_point, LogicalLineIntersectionKind.TOUCH

    t_value = _cross_product(offset_vector, vertical_vector) / cross_value
    u_value = _cross_product(offset_vector, horizontal_vector) / cross_value
    if not (
        -_EPSILON <= t_value <= 1.0 + _EPSILON
        and -_EPSILON <= u_value <= 1.0 + _EPSILON
    ):
        return None

    intersection_x = horizontal_start[0] + horizontal_vector[0] * t_value
    intersection_y = horizontal_start[1] + horizontal_vector[1] * t_value
    intersection_point = (
        int(round(intersection_x)),
        int(round(intersection_y)),
    )
    if _is_endpoint_intersection(t_value, u_value):
        return intersection_point, LogicalLineIntersectionKind.TOUCH
    return intersection_point, LogicalLineIntersectionKind.CROSS


def _collect_segment_intersection_candidates(
    horizontal_line: LogicalLine,
    vertical_line: LogicalLine,
) -> list[
    tuple[
        LineSegment,
        LineSegment,
        tuple[int, int],
        LogicalLineIntersectionKind,
    ]
]:
    if horizontal_line.family_name != LineFamilyName.HORIZONTAL:
        raise ValueError("horizontal_line must belong to the horizontal family.")
    if vertical_line.family_name != LineFamilyName.VERTICAL:
        raise ValueError("vertical_line must belong to the vertical family.")

    candidates: list[
        tuple[
            LineSegment,
            LineSegment,
            tuple[int, int],
            LogicalLineIntersectionKind,
        ]
    ] = []
    for horizontal_segment_index, horizontal_segment in enumerate(
        horizontal_line.line_segments
    ):
        for vertical_segment_index, vertical_segment in enumerate(
            vertical_line.line_segments
        ):
            intersection_result = find_segment_intersection(
                horizontal_segment,
                vertical_segment,
            )
            if intersection_result is None:
                continue

            intersection_point, intersection_kind = intersection_result
            candidates.append(
                (
                    horizontal_segment,
                    vertical_segment,
                    intersection_point,
                    intersection_kind,
                )
            )

    return candidates


def _select_representative_segment_intersection(
    candidates: list[
        tuple[
            LineSegment,
            LineSegment,
            tuple[int, int],
            LogicalLineIntersectionKind,
        ]
    ],
) -> tuple[
    LineSegment,
    LineSegment,
    tuple[int, int],
    LogicalLineIntersectionKind,
] | None:
    if not candidates:
        return None

    sorted_candidates = sorted(
        candidates,
        key=lambda candidate: (
            candidate[2][0],
            candidate[2][1],
            0 if candidate[3] == LogicalLineIntersectionKind.CROSS else 1,
            candidate[0].axis_start,
            candidate[1].axis_start,
        ),
    )
    return sorted_candidates[0]


def _find_logical_line_intersection_candidate(
    horizontal_line: LogicalLine,
    vertical_line: LogicalLine,
) -> _LogicalLineIntersectionCandidate | None:
    candidates = _collect_segment_intersection_candidates(
        horizontal_line,
        vertical_line,
    )
    representative_intersection = _select_representative_segment_intersection(
        candidates
    )
    if representative_intersection is None:
        return None

    (
        horizontal_segment,
        vertical_segment,
        intersection_point,
        intersection_kind,
    ) = representative_intersection
    return _LogicalLineIntersectionCandidate(
        ref_horizontal_line=horizontal_line,
        ref_vertical_line=vertical_line,
        ref_horizontal_segment=horizontal_segment,
        ref_vertical_segment=vertical_segment,
        point=intersection_point,
        kind=intersection_kind,
    )


def find_logical_line_intersection(
    horizontal_line: LogicalLine,
    vertical_line: LogicalLine,
) -> LogicalLineIntersection | None:
    candidate = _find_logical_line_intersection_candidate(
        horizontal_line,
        vertical_line,
    )
    if candidate is None:
        return None
    return LogicalLineIntersection(
        ref_horizontal_line=candidate.ref_horizontal_line,
        ref_vertical_line=candidate.ref_vertical_line,
        ref_horizontal_segment=candidate.ref_horizontal_segment,
        ref_vertical_segment=candidate.ref_vertical_segment,
        point=candidate.point,
        kind=candidate.kind,
    )


def _build_line_lookup(
    horizontal_logical_lines: list[LogicalLine],
    vertical_logical_lines: list[LogicalLine],
) -> tuple[dict[int, LogicalLine], dict[int, list[object]]]:
    lines_by_key: dict[int, LogicalLine] = {}
    intersections_by_key: dict[int, list[object]] = {}
    for logical_line in (*horizontal_logical_lines, *vertical_logical_lines):
        line_key = id(logical_line)
        lines_by_key[line_key] = logical_line
        intersections_by_key.setdefault(line_key, [])

    return lines_by_key, intersections_by_key


def _sort_line_intersections(
    line_intersections: list[object],
    family_name: LineFamilyName,
) -> list[object]:
    if family_name == LineFamilyName.HORIZONTAL:
        return sorted(
            line_intersections,
            key=lambda intersection: (
                intersection.horizontal_axis_value,
                intersection.vertical_axis_value,
            ),
        )

    return sorted(
        line_intersections,
        key=lambda intersection: (
            intersection.vertical_axis_value,
            intersection.horizontal_axis_value,
        ),
    )


def _assign_boundary_orders(
    lines_by_key: dict[int, LogicalLine],
    intersections_by_key: dict[int, list[object]],
    family_name: LineFamilyName,
) -> None:
    for line_key, logical_line in lines_by_key.items():
        if logical_line.family_name != family_name:
            continue

        line_intersections = intersections_by_key.get(line_key, [])
        if family_name == LineFamilyName.HORIZONTAL:
            for intersection in line_intersections:
                intersection.horizontal_order = IntersectionOrder.NONE
        else:
            for intersection in line_intersections:
                intersection.vertical_order = IntersectionOrder.NONE
        sorted_intersections = _sort_line_intersections(
            line_intersections,
            family_name,
        )

        if not sorted_intersections:
            continue

        if len(sorted_intersections) == 1:
            if family_name == LineFamilyName.HORIZONTAL:
                sorted_intersections[0].horizontal_order = IntersectionOrder.BOTH
            else:
                sorted_intersections[0].vertical_order = IntersectionOrder.BOTH
            continue

        for intersection in sorted_intersections[1:-1]:
            if family_name == LineFamilyName.HORIZONTAL:
                intersection.horizontal_order = IntersectionOrder.MIDDLE
            else:
                intersection.vertical_order = IntersectionOrder.MIDDLE

        if family_name == LineFamilyName.HORIZONTAL:
            sorted_intersections[0].horizontal_order = IntersectionOrder.START
            sorted_intersections[-1].horizontal_order = IntersectionOrder.END
        else:
            sorted_intersections[0].vertical_order = IntersectionOrder.START
            sorted_intersections[-1].vertical_order = IntersectionOrder.END


def _collect_candidate_intersections(
    horizontal_logical_lines: list[LogicalLine],
    vertical_logical_lines: list[LogicalLine],
) -> list[_LogicalLineIntersectionCandidate]:
    intersections: list[_LogicalLineIntersectionCandidate] = []
    for horizontal_line in horizontal_logical_lines:
        for vertical_line in vertical_logical_lines:
            intersection = _find_logical_line_intersection_candidate(
                horizontal_line,
                vertical_line,
            )
            if intersection is not None:
                intersections.append(intersection)
    return intersections


def _build_candidate_lookup(
    horizontal_logical_lines: list[LogicalLine],
    vertical_logical_lines: list[LogicalLine],
    intersections: list[_LogicalLineIntersectionCandidate],
) -> tuple[
    dict[int, LogicalLine],
    dict[int, list[_LogicalLineIntersectionCandidate]],
]:
    lines_by_key, intersections_by_key = _build_line_lookup(
        horizontal_logical_lines,
        vertical_logical_lines,
    )
    typed_lookup: dict[int, list[_LogicalLineIntersectionCandidate]] = {
        line_key: []
        for line_key in intersections_by_key
    }
    for intersection in intersections:
        typed_lookup[id(intersection.ref_horizontal_line)].append(intersection)
        typed_lookup[id(intersection.ref_vertical_line)].append(intersection)
    return lines_by_key, typed_lookup


def _prune_lines_by_minimum_intersection_count(
    horizontal_logical_lines: list[LogicalLine],
    vertical_logical_lines: list[LogicalLine],
    intersections: list[_LogicalLineIntersectionCandidate],
    minimum_intersection_count: int,
    protected_line_keys: set[int] | None = None,
) -> tuple[
    list[LogicalLine],
    list[LogicalLine],
    list[_LogicalLineIntersectionCandidate],
]:
    active_horizontal_lines = list(horizontal_logical_lines)
    active_vertical_lines = list(vertical_logical_lines)
    active_intersections = list(intersections)
    protected_keys = protected_line_keys or set()

    while True:
        _, intersections_by_key = _build_candidate_lookup(
            active_horizontal_lines,
            active_vertical_lines,
            active_intersections,
        )
        removable_line_keys = {
            line_key
            for line_key in intersections_by_key
            if (
                line_key not in protected_keys
                and len(intersections_by_key[line_key]) < minimum_intersection_count
            )
        }
        if not removable_line_keys:
            return (
                active_horizontal_lines,
                active_vertical_lines,
                active_intersections,
            )

        active_horizontal_lines = [
            logical_line
            for logical_line in active_horizontal_lines
            if id(logical_line) not in removable_line_keys
        ]
        active_vertical_lines = [
            logical_line
            for logical_line in active_vertical_lines
            if id(logical_line) not in removable_line_keys
        ]
        active_intersections = [
            intersection
            for intersection in active_intersections
            if (
                id(intersection.ref_horizontal_line) not in removable_line_keys
                and id(intersection.ref_vertical_line) not in removable_line_keys
            )
        ]


def _build_pair_border_line_lookup(
    intersections: list[object],
) -> tuple[dict[int, LogicalLine], dict[int, set[int]]]:
    lines_by_key: dict[int, LogicalLine] = {}
    pair_border_line_lookup: dict[int, set[int]] = defaultdict(set)
    for intersection in intersections:
        if not intersection.is_mutual_boundary:
            continue

        horizontal_key = id(intersection.ref_horizontal_line)
        vertical_key = id(intersection.ref_vertical_line)
        lines_by_key[horizontal_key] = intersection.ref_horizontal_line
        lines_by_key[vertical_key] = intersection.ref_vertical_line
        pair_border_line_lookup[horizontal_key].add(vertical_key)
        pair_border_line_lookup[vertical_key].add(horizontal_key)

    return lines_by_key, pair_border_line_lookup


def _logical_line_sort_key(logical_line: LogicalLine) -> tuple[str, int, int]:
    return (
        logical_line.family_name.value,
        logical_line.axis_start,
        logical_line.cross_axis_start,
    )


def find_logical_line_border_pairs(
    intersections: list[LogicalLineIntersection],
) -> list[LogicalLineBorderPair]:
    lines_by_key, pair_border_line_lookup = _build_pair_border_line_lookup(
        intersections
    )
    border_pairs: list[LogicalLineBorderPair] = []
    for line_key in sorted(
        pair_border_line_lookup,
        key=lambda current_key: _logical_line_sort_key(lines_by_key[current_key]),
    ):
        border_lines = tuple(
            sorted(
                (
                    lines_by_key[border_key]
                    for border_key in pair_border_line_lookup[line_key]
                ),
                key=_logical_line_sort_key,
            )
        )
        border_pairs.append(
            LogicalLineBorderPair(
                ref_line=lines_by_key[line_key],
                border_lines=border_lines,
            )
        )

    return border_pairs


def _line_cross_axis_center(logical_line: LogicalLine) -> float:
    return (logical_line.cross_axis_start + logical_line.cross_axis_end) / 2.0


def _create_frame_from_lines(
    horizontal_lines: tuple[LogicalLine, LogicalLine],
    vertical_lines: tuple[LogicalLine, LogicalLine],
) -> LogicalLineFrame:
    top_line, bottom_line = sorted(
        horizontal_lines,
        key=_line_cross_axis_center,
    )
    left_line, right_line = sorted(
        vertical_lines,
        key=_line_cross_axis_center,
    )
    return LogicalLineFrame(
        top_line=top_line,
        bottom_line=bottom_line,
        left_line=left_line,
        right_line=right_line,
    )


def _clear_logical_line_metadata(
    horizontal_logical_lines: list[LogicalLine],
    vertical_logical_lines: list[LogicalLine],
) -> None:
    for logical_line in (*horizontal_logical_lines, *vertical_logical_lines):
        logical_line.frame_side = FrameSide.NONE
        logical_line.intersections.clear()


def _find_logical_line_frames(
    intersections: list[object],
    horizontal_logical_lines: list[LogicalLine],
    vertical_logical_lines: list[LogicalLine],
) -> list[LogicalLineFrame]:
    lines_by_key, pair_border_line_lookup = _build_pair_border_line_lookup(
        intersections
    )
    frames: list[LogicalLineFrame] = []
    seen_frame_keys: set[tuple[int, int, int, int]] = set()
    for a_key, a_neighbors in pair_border_line_lookup.items():
        line_a = lines_by_key[a_key]
        if line_a.family_name != LineFamilyName.HORIZONTAL:
            continue

        for b_key in a_neighbors:
            line_b = lines_by_key[b_key]
            if line_b.family_name != LineFamilyName.VERTICAL:
                continue

            for c_key in pair_border_line_lookup.get(b_key, set()):
                if c_key == a_key:
                    continue

                line_c = lines_by_key[c_key]
                if line_c.family_name != LineFamilyName.HORIZONTAL:
                    continue

                for d_key in pair_border_line_lookup.get(c_key, set()):
                    if d_key == b_key:
                        continue

                    line_d = lines_by_key[d_key]
                    if line_d.family_name != LineFamilyName.VERTICAL:
                        continue
                    if a_key not in pair_border_line_lookup.get(d_key, set()):
                        continue

                    frame_key = tuple(sorted((a_key, b_key, c_key, d_key)))
                    if len(set(frame_key)) != 4 or frame_key in seen_frame_keys:
                        continue

                    horizontal_lines = (
                        line_a,
                        line_c,
                    )
                    vertical_lines = (
                        line_b,
                        line_d,
                    )
                    frames.append(
                        _create_frame_from_lines(
                            horizontal_lines,
                            vertical_lines,
                        )
                    )
                    seen_frame_keys.add(frame_key)

    return frames


def _frame_area(frame: LogicalLineFrame) -> float:
    frame_width = abs(
        _line_cross_axis_center(frame.right_line)
        - _line_cross_axis_center(frame.left_line)
    )
    frame_height = abs(
        _line_cross_axis_center(frame.bottom_line)
        - _line_cross_axis_center(frame.top_line)
    )
    return frame_width * frame_height


def _select_best_frame(
    frames: list[LogicalLineFrame],
    intersections_by_key: dict[int, list[_LogicalLineIntersectionCandidate]],
) -> LogicalLineFrame | None:
    if not frames:
        return None

    return min(
        frames,
        key=lambda frame: (
            sum(
                abs(len(intersections_by_key.get(id(logical_line), [])) - 10)
                for logical_line in frame.lines
            ),
            -_frame_area(frame),
        ),
    )


def _build_public_intersections(
    horizontal_logical_lines: list[LogicalLine],
    vertical_logical_lines: list[LogicalLine],
    candidate_intersections: list[_LogicalLineIntersectionCandidate],
) -> list[LogicalLineIntersection]:
    _clear_logical_line_metadata(
        horizontal_logical_lines,
        vertical_logical_lines,
    )
    public_intersections = [
        LogicalLineIntersection(
            ref_horizontal_line=candidate.ref_horizontal_line,
            ref_vertical_line=candidate.ref_vertical_line,
            ref_horizontal_segment=candidate.ref_horizontal_segment,
            ref_vertical_segment=candidate.ref_vertical_segment,
            point=candidate.point,
            kind=candidate.kind,
        )
        for candidate in candidate_intersections
    ]
    lines_by_key, intersections_by_key = _build_line_lookup(
        horizontal_logical_lines,
        vertical_logical_lines,
    )
    for intersection in public_intersections:
        intersections_by_key[id(intersection.ref_horizontal_line)].append(intersection)
        intersections_by_key[id(intersection.ref_vertical_line)].append(intersection)

    _assign_boundary_orders(
        lines_by_key,
        intersections_by_key,
        LineFamilyName.HORIZONTAL,
    )
    _assign_boundary_orders(
        lines_by_key,
        intersections_by_key,
        LineFamilyName.VERTICAL,
    )
    for logical_line in horizontal_logical_lines:
        logical_line.intersections.extend(
            _sort_line_intersections(
                intersections_by_key.get(id(logical_line), []),
                LineFamilyName.HORIZONTAL,
            )
        )
    for logical_line in vertical_logical_lines:
        logical_line.intersections.extend(
            _sort_line_intersections(
                intersections_by_key.get(id(logical_line), []),
                LineFamilyName.VERTICAL,
            )
        )

    return public_intersections


def _apply_frame_side(frame: LogicalLineFrame | None) -> None:
    if frame is None:
        return
    frame.top_line.frame_side = FrameSide.TOP
    frame.bottom_line.frame_side = FrameSide.BOTTOM
    frame.left_line.frame_side = FrameSide.LEFT
    frame.right_line.frame_side = FrameSide.RIGHT


def analyze_logical_line_intersections(
    horizontal_logical_lines: list[LogicalLine],
    vertical_logical_lines: list[LogicalLine],
) -> LogicalLineIntersectionAnalysis:
    _clear_logical_line_metadata(
        horizontal_logical_lines,
        vertical_logical_lines,
    )
    candidate_intersections = _collect_candidate_intersections(
        horizontal_logical_lines,
        vertical_logical_lines,
    )
    (
        active_horizontal_lines,
        active_vertical_lines,
        active_intersections,
    ) = _prune_lines_by_minimum_intersection_count(
        horizontal_logical_lines,
        vertical_logical_lines,
        candidate_intersections,
        minimum_intersection_count=2,
    )
    lines_by_key, intersections_by_key = _build_candidate_lookup(
        active_horizontal_lines,
        active_vertical_lines,
        active_intersections,
    )
    _assign_boundary_orders(
        lines_by_key,
        intersections_by_key,
        LineFamilyName.HORIZONTAL,
    )
    _assign_boundary_orders(
        lines_by_key,
        intersections_by_key,
        LineFamilyName.VERTICAL,
    )
    candidate_frames = _find_logical_line_frames(
        active_intersections,
        active_horizontal_lines,
        active_vertical_lines,
    )
    best_frame = _select_best_frame(
        candidate_frames,
        intersections_by_key,
    )
    protected_line_keys = (
        {id(logical_line) for logical_line in best_frame.lines}
        if best_frame is not None
        else set()
    )
    (
        active_horizontal_lines,
        active_vertical_lines,
        active_intersections,
    ) = _prune_lines_by_minimum_intersection_count(
        active_horizontal_lines,
        active_vertical_lines,
        active_intersections,
        minimum_intersection_count=10,
        protected_line_keys=protected_line_keys,
    )
    public_intersections = _build_public_intersections(
        active_horizontal_lines,
        active_vertical_lines,
        active_intersections,
    )
    _apply_frame_side(best_frame)
    return LogicalLineIntersectionAnalysis(
        frame=best_frame,
        horizontal_lines=active_horizontal_lines,
        vertical_lines=active_vertical_lines,
        intersections=public_intersections,
    )


def find_logical_line_frames(
    intersections: list[LogicalLineIntersection],
    horizontal_logical_lines: list[LogicalLine],
    vertical_logical_lines: list[LogicalLine],
) -> list[LogicalLineFrame]:
    return _find_logical_line_frames(
        intersections,
        horizontal_logical_lines,
        vertical_logical_lines,
    )


def find_logical_line_intersections(
    horizontal_logical_lines: list[LogicalLine],
    vertical_logical_lines: list[LogicalLine],
) -> list[LogicalLineIntersection]:
    analysis = analyze_logical_line_intersections(
        horizontal_logical_lines,
        vertical_logical_lines,
    )
    return analysis.intersections


__all__ = [
    "IntersectionOrder",
    "LogicalLineIntersectionAnalysis",
    "LogicalLineIntersection",
    "LogicalLineBorderPair",
    "LogicalLineFrame",
    "LogicalLineIntersectionKind",
    "analyze_logical_line_intersections",
    "find_logical_line_border_pairs",
    "find_logical_line_frames",
    "find_logical_line_intersection",
    "find_logical_line_intersections",
    "find_segment_intersection",
]
