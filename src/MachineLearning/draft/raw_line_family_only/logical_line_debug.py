from __future__ import annotations

from typing import TYPE_CHECKING

from models import LineFamilyName

if TYPE_CHECKING:
    from logical_line_core import LogicalLine


def logical_line_naming_sort_key(
    logical_line: "LogicalLine",
) -> tuple[int, int, int, int, int, int]:
    return (
        min(logical_line.cross_axis_start, logical_line.cross_axis_end),
        logical_line.axis_start,
        logical_line.axis_end,
        logical_line.start_vertex[0],
        logical_line.start_vertex[1],
        logical_line.end_vertex[0],
    )


def assign_logical_line_debug_names(
    logical_lines: list["LogicalLine"],
    line_prefix: str,
) -> None:
    for line_index, logical_line in enumerate(
        sorted(logical_lines, key=logical_line_naming_sort_key),
        start=1,
    ):
        logical_line.debug_name = f"{line_prefix}{line_index}"


def get_logical_line_debug_name(logical_line: "LogicalLine") -> str:
    if logical_line.debug_name:
        return logical_line.debug_name

    if logical_line.family_name == LineFamilyName.HORIZONTAL:
        return "H?"
    if logical_line.family_name == LineFamilyName.VERTICAL:
        return "V?"
    return "?"


def logical_line_debug_sort_key(logical_line: "LogicalLine") -> tuple[int, int, str]:
    debug_name = get_logical_line_debug_name(logical_line)
    family_prefix = debug_name[:1]
    family_order = 2
    if family_prefix == "H":
        family_order = 0
    elif family_prefix == "V":
        family_order = 1

    suffix = debug_name[1:]
    if suffix.isdigit():
        return (family_order, int(suffix), debug_name)

    return (family_order, 10**9, debug_name)


__all__ = [
    "assign_logical_line_debug_names",
    "get_logical_line_debug_name",
    "logical_line_debug_sort_key",
    "logical_line_naming_sort_key",
]
