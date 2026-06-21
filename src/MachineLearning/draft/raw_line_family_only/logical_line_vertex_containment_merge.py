from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING


import numpy as np

from logical_line_cross_axis_continuity import (
    LogicalLineCrossAxisGroup,
    group_logical_lines_by_cross_axis_continuity,
)

from models import (
    ExperimentConfig
)

if TYPE_CHECKING:
    from logical_line_core import LogicalLine

@dataclass(frozen=True, slots=True)
class MergeVertexContainedLogicalLinesResult:
    input_logical_lines: list[LogicalLine]
    merged_logical_lines: list[LogicalLine]
    consumed_logical_lines: list[LogicalLine]
    merge_groups: list[LogicalLineCrossAxisGroup]
    

def logical_line_is_vertex_contained_on_axis(
    container_line: "LogicalLine",
    candidate_line: "LogicalLine",
) -> bool:

    start_inside = (
        container_line.axis_start
        <= candidate_line.axis_start
        <= container_line.axis_end
    )
    end_inside = (
        container_line.axis_start
        <= candidate_line.axis_end
        <= container_line.axis_end
    )

    return start_inside or end_inside


def merge_logical_lines_by_vertex_axis_containment(
    binary_image: np.ndarray,
    logical_lines: list[LogicalLine],
    reference_angle_degrees: float,
    config: ExperimentConfig,
) -> MergeVertexContainedLogicalLinesResult:
    """
    Merge logical lines by vertex axis containment.

    Args:
        binary_image: The binary image to use for the merge.
        logical_lines: The logical lines to merge.
        reference_angle_degrees: The reference angle to use for the merge.
        config: The configuration to use for the merge.

    Returns:
        A MergeVertexContainedLogicalLinesResult object containing the merged logical lines, consumed logical lines, and merge groups.
    """    
    
    if not logical_lines:
        return MergeVertexContainedLogicalLinesResult(
            input_logical_lines=logical_lines,
            merged_logical_lines=[],
            consumed_logical_lines=[],
            merge_groups=[]
        )

    if len(logical_lines) == 1:
        group: LogicalLineCrossAxisGroup = group_logical_lines_by_cross_axis_continuity(
            logical_lines[0], 
            binary_image, 
            []
        )

        return MergeVertexContainedLogicalLinesResult(
            input_logical_lines=logical_lines,
            merged_logical_lines=logical_lines,
            consumed_logical_lines=[],
            merge_groups=[group]
        )

    sorted_group_lines: list[LogicalLine] = sorted(
        logical_lines,
        key=lambda logical_line: (
            -logical_line.axis_length,
            logical_line.axis_start,
            logical_line.axis_end
        )
    )

    groups: list[LogicalLineCrossAxisGroup] = []
    remaining_lines = list(sorted_group_lines)

    while remaining_lines:
        container_line: LogicalLine = remaining_lines[0]
        contained_lines: list[LogicalLine] = []
        next_remaining_lines: list[LogicalLine] = []
        
        for logical_line in remaining_lines:
            if logical_line is container_line:
                continue

            if logical_line_is_vertex_contained_on_axis(container_line, logical_line):
                contained_lines.append(logical_line)
                continue

            next_remaining_lines.append(logical_line)

        group: LogicalLineCrossAxisGroup = group_logical_lines_by_cross_axis_continuity(container_line, binary_image, contained_lines)
        
        getback_to_next_remaining_lines: list[LogicalLine] = [
            line
            for line in contained_lines
            if id(line) not in group.grouped_logical_line_ids
        ]

        remaining_lines: list[LogicalLine] = sorted(
            next_remaining_lines + getback_to_next_remaining_lines,
            key=lambda logical_line: (
                -logical_line.axis_length,
                logical_line.axis_start,
                logical_line.axis_end
            )
        )

        for consumed_line in group.grouped_logical_lines:
            container_line.merge_logical_line(consumed_line)
        
        container_line.group_raw_segments(
            binary_image=binary_image,
            reference_angle_degrees=reference_angle_degrees,
            angle_tolerance_degrees=config.line_family_angle_tolerance_degrees,
            black_gap_tolerance_px=config.raw_segment_group_black_gap_tolerance_px,
        )

        groups.append(group)

    merged_logical_lines: list[LogicalLine] = [group.anchor_line for group in groups]

    consumed_logical_lines: list[LogicalLine] = [
        logical_line
        for group in groups
        for logical_line in group.grouped_logical_lines
    ]


    return MergeVertexContainedLogicalLinesResult(
        input_logical_lines=logical_lines,
        merged_logical_lines=merged_logical_lines,
        consumed_logical_lines=consumed_logical_lines,
        merge_groups=groups
    )


__all__ = [
    "MergeVertexContainedLogicalLinesResult",
    "merge_logical_lines_by_vertex_axis_containment"
]