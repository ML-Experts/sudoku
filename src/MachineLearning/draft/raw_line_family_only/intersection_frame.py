from __future__ import annotations

from collections import defaultdict

from intersection_models import (
    LogicalLineBorderPair,
    LogicalLineFrame,
    _LogicalLineIntersectionCandidate,
)
from logical_line_core import FrameSide, LogicalLine
from models import LineFamilyName


def _family_key(family_name: object) -> object:
    return getattr(family_name, "value", family_name)


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
    intersections: list[object],
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


def _find_logical_line_frames(
    intersections: list[object],
    horizontal_logical_lines: list[LogicalLine],
    vertical_logical_lines: list[LogicalLine],
) -> list[LogicalLineFrame]:
    del horizontal_logical_lines
    del vertical_logical_lines

    lines_by_key, pair_border_line_lookup = _build_pair_border_line_lookup(
        intersections
    )
    frames: list[LogicalLineFrame] = []
    seen_frame_keys: set[tuple[int, int, int, int]] = set()
    for a_key, a_neighbors in pair_border_line_lookup.items():
        line_a = lines_by_key[a_key]
        if _family_key(line_a.family_name) != LineFamilyName.HORIZONTAL.value:
            continue

        for b_key in a_neighbors:
            line_b = lines_by_key[b_key]
            if _family_key(line_b.family_name) != LineFamilyName.VERTICAL.value:
                continue

            for c_key in pair_border_line_lookup.get(b_key, set()):
                if c_key == a_key:
                    continue

                line_c = lines_by_key[c_key]
                if _family_key(line_c.family_name) != LineFamilyName.HORIZONTAL.value:
                    continue

                for d_key in pair_border_line_lookup.get(c_key, set()):
                    if d_key == b_key:
                        continue

                    line_d = lines_by_key[d_key]
                    if _family_key(line_d.family_name) != LineFamilyName.VERTICAL.value:
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


def _apply_frame_side(frame: LogicalLineFrame | None) -> None:
    if frame is None:
        return
    frame.top_line.frame_side = FrameSide.TOP
    frame.bottom_line.frame_side = FrameSide.BOTTOM
    frame.left_line.frame_side = FrameSide.LEFT
    frame.right_line.frame_side = FrameSide.RIGHT


__all__ = [
    "find_logical_line_border_pairs",
    "_apply_frame_side",
    "_find_logical_line_frames",
    "_select_best_frame",
]
