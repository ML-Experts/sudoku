from __future__ import annotations

from logical_line_core import LogicalLine
from frame_model import (
    LogicalLineBoundaryGroup,
    LogicalLineFrameCandidate,
)
from intersection_model import IntersectionOrder, LogicalLineIntersection

def build_boundary_groups(
    logical_lines: list[LogicalLine],
    cross_axis_lines: list[LogicalLine],
) -> list[LogicalLineBoundaryGroup]:

    cross_axis_lines_by_debug_name: dict[str, LogicalLine] = {
        logical_line.debug_name: logical_line
        for logical_line in cross_axis_lines
    }

    groups_by_key: dict[tuple[str, str], LogicalLineBoundaryGroup] = {}
    for logical_line in logical_lines:
        boundary_pair = _extract_boundary_pair(logical_line)
        if boundary_pair is None:
            continue

        start_intersection, end_intersection = boundary_pair
        group_key = (
            start_intersection.intersected_line_cross_axis_debug_name,
            end_intersection.intersected_line_cross_axis_debug_name,
        )

        if group_key in groups_by_key:
            groups_by_key[group_key].touching_lines.append(logical_line)
        else:
            groups_by_key[group_key] = LogicalLineBoundaryGroup(
                line_start_axis=cross_axis_lines_by_debug_name[start_intersection.intersected_line_cross_axis_debug_name],
                line_end_axis=cross_axis_lines_by_debug_name[end_intersection.intersected_line_cross_axis_debug_name],
                touching_lines=[logical_line]
            )

    groups = list(groups_by_key.values())
    return sorted(
        groups,
        key=lambda group: (
            -len(group.touching_lines)
        )
    )      


def find_logical_line_frame_candidates(
    horizontal_boundary_groups: list[LogicalLineBoundaryGroup],
    vertical_boundary_groups: list[LogicalLineBoundaryGroup],
) -> list[LogicalLineFrameCandidate]:
    frame_candidates: list[LogicalLineFrameCandidate] = []
    
    horizontal_line_by_key: dict[str, LogicalLine] = {
        group.line_start_axis.debug_name: group.line_start_axis
        for group in horizontal_boundary_groups
    } | {
        group.line_end_axis.debug_name: group.line_end_axis
        for group in horizontal_boundary_groups
    }

    vertical_line_by_key: dict[str, LogicalLine] = {
        logical_line.line_start_axis.debug_name: logical_line.line_start_axis
        for logical_line in vertical_boundary_groups
    } | {
        logical_line.line_end_axis.debug_name: logical_line.line_end_axis
        for logical_line in vertical_boundary_groups
    }

    for horizontal_boundary_group in horizontal_boundary_groups:
        for vertical_boundary_group in vertical_boundary_groups:
            if not _check_boundary_group_intersection(horizontal_boundary_group, vertical_boundary_group):
                continue
            
            frame_candidate: LogicalLineFrameCandidate = LogicalLineFrameCandidate(
                top_line=vertical_line_by_key[vertical_boundary_group.line_start_axis.debug_name],
                bottom_line=vertical_line_by_key[vertical_boundary_group.line_end_axis.debug_name],
                left_line=horizontal_line_by_key[horizontal_boundary_group.line_start_axis.debug_name],
                right_line=horizontal_line_by_key[horizontal_boundary_group.line_end_axis.debug_name],
                horizontal_lines=tuple(horizontal_boundary_group.touching_lines),
                vertical_lines=tuple(vertical_boundary_group.touching_lines)
            )
            frame_candidates.append(frame_candidate)

    return frame_candidates


def _extract_boundary_pair(
    logical_line: LogicalLine,
) -> tuple[LogicalLineIntersection, LogicalLineIntersection] | None:
    start_intersection: LogicalLineIntersection | None = None
    end_intersection: LogicalLineIntersection | None = None

    for intersection in logical_line.intersections:
        if intersection.order == IntersectionOrder.BOTH:
            return None
        if intersection.order == IntersectionOrder.START:
            start_intersection = intersection
        if intersection.order == IntersectionOrder.END:
            end_intersection = intersection

        if start_intersection is not None and end_intersection is not None and start_intersection.intersected_line_cross_axis_debug_name != end_intersection.intersected_line_cross_axis_debug_name:
            return start_intersection, end_intersection

    return None

def _check_boundary_group_intersection(
    horizontal_boundary_group: LogicalLineBoundaryGroup,
    vertical_boundary_group: LogicalLineBoundaryGroup,
) -> bool:
    horizontal_start_intersections_names: set[str] = {
        intersection.intersected_line_cross_axis_debug_name
        for intersection in horizontal_boundary_group.line_start_axis.intersections
    }
    horizontal_end_intersections_names: set[str] = {
        intersection.intersected_line_cross_axis_debug_name
        for intersection in horizontal_boundary_group.line_end_axis.intersections
    }
    vertical_start_intersections_names: set[str] = {
        intersection.intersected_line_cross_axis_debug_name
        for intersection in vertical_boundary_group.line_start_axis.intersections
    }
    vertical_end_intersections_names: set[str] = {
        intersection.intersected_line_cross_axis_debug_name
        for intersection in vertical_boundary_group.line_end_axis.intersections
    }
    
    if(horizontal_boundary_group.line_start_axis.debug_name not in vertical_start_intersections_names):
        return False
    if(horizontal_boundary_group.line_start_axis.debug_name not in vertical_end_intersections_names):
        return False        
    if(horizontal_boundary_group.line_end_axis.debug_name not in vertical_start_intersections_names):
        return False
    if(horizontal_boundary_group.line_end_axis.debug_name not in vertical_end_intersections_names):
        return False
    if(vertical_boundary_group.line_end_axis.debug_name not in horizontal_start_intersections_names):
        return False
    if(vertical_boundary_group.line_end_axis.debug_name not in horizontal_end_intersections_names):
        return False
    if(vertical_boundary_group.line_start_axis.debug_name not in horizontal_start_intersections_names):
        return False
    if(vertical_boundary_group.line_start_axis.debug_name not in horizontal_end_intersections_names):
        return False

    return True
    

__all__ = [
    "build_boundary_groups",
    "find_logical_line_frame_candidates",
]
