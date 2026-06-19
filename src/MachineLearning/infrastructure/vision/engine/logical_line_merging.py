from __future__ import annotations

from .logical_line_core import LogicalLine, segment_sort_key
from .models import LineSegment


def build_logical_lines(
    line_segments: list[LineSegment],
    cross_axis_thickness_px: int,
    axis_gap_tolerance_px: int,
) -> list[LogicalLine]:
    if not line_segments:
        return []

    sorted_segments = sorted(line_segments, key=segment_sort_key)
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


__all__ = [
    "build_logical_lines",
    "merge_logical_lines",
]
