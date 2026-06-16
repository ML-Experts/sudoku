from __future__ import annotations

from logical_line_core import LogicalLine
from logical_line_intersections import assign_logical_line_intersections


def trim_logical_lines_to_intersections(
    horizontal_logical_lines: list[LogicalLine],
    vertical_logical_lines: list[LogicalLine],
) -> bool:
    assign_logical_line_intersections(
        horizontal_logical_lines,
        vertical_logical_lines,
    )

    any_trimmed = False

    for logical_line in horizontal_logical_lines:
        if logical_line.trim_to_intersections():
            any_trimmed = True

    for logical_line in vertical_logical_lines:
        if logical_line.trim_to_intersections():
            any_trimmed = True

    assign_logical_line_intersections(
        horizontal_logical_lines,
        vertical_logical_lines,
    )

    return any_trimmed


__all__ = [
    "trim_logical_lines_to_intersections",
]