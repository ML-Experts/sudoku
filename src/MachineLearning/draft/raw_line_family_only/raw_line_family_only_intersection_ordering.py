from __future__ import annotations

from raw_line_family_only_intersection_models import (
    IntersectionOrder,
    LogicalLineIntersection,
    _LogicalLineIntersectionCandidate,
)
from raw_line_family_only_logical_line_core import FrameSide, LogicalLine
from raw_line_family_only_models import LineFamilyName


def _family_key(family_name: object) -> object:
    return getattr(family_name, "value", family_name)


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
        if _family_key(logical_line.family_name) != family_name.value:
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


def _clear_logical_line_metadata(
    horizontal_logical_lines: list[LogicalLine],
    vertical_logical_lines: list[LogicalLine],
) -> None:
    for logical_line in (*horizontal_logical_lines, *vertical_logical_lines):
        logical_line.frame_side = FrameSide.NONE
        logical_line.intersections.clear()


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


__all__ = [
    "_assign_boundary_orders",
    "_build_line_lookup",
    "_build_public_intersections",
    "_clear_logical_line_metadata",
    "_sort_line_intersections",
]
