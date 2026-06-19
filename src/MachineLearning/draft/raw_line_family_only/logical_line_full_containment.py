from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING


import numpy as np

from logical_line_cross_axis_continuity import (
    LogicalLineCrossAxisGroup,
    group_logical_lines_by_cross_axis_continuity,
)


if TYPE_CHECKING:
    from logical_line_core import LogicalLine


@dataclass(frozen=True, slots=True)
class PruneContainedLogicalLinesResult:
    input_logical_lines: list[LogicalLine]
    pruned_logical_lines: list[LogicalLine]
    removed_logical_lines: list[LogicalLine]
    cross_axis_groups: list[LogicalLineCrossAxisGroup]


def logical_line_is_contained_on_axis(
    container_line: "LogicalLine",
    candidate_line: "LogicalLine",
) -> bool:
    return (
        container_line.axis_start <= candidate_line.axis_start
        and candidate_line.axis_end <= container_line.axis_end
    )


def prune_logical_lines_by_full_axis_containment(
    binary_image: np.ndarray,
    logical_lines: list[LogicalLine],
) -> PruneContainedLogicalLinesResult:
    """
    Dzieli posortowaną grupę logical lines na mniejsze grupy containment.
    
    Wynik:
    - pierwsza linia w każdej podgrupie to container_line
    - oraz removed_logical_lines zawiera wszystkie linie, które zostały usunięte z candidates_lines
    - logical_lines zawiera kontener i wszystkie linie zawarte
      w jego axis_start..axis_end
    """    
    
    if not logical_lines:
        return PruneContainedLogicalLinesResult(
            input_logical_lines=logical_lines,
            pruned_logical_lines=[],
            removed_logical_lines=[],
            cross_axis_groups=[]
        )

    if len(logical_lines) == 1:
        group: LogicalLineCrossAxisGroup = group_logical_lines_by_cross_axis_continuity(
            logical_lines[0], 
            binary_image, 
            []
        )

        return PruneContainedLogicalLinesResult(
            input_logical_lines=logical_lines,
            pruned_logical_lines=logical_lines,
            removed_logical_lines=[],
            cross_axis_groups=[group]
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

            if logical_line_is_contained_on_axis(container_line, logical_line):
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

        groups.append(group)

    pruned_lines: list[LogicalLine] = [group.anchor_line for group in groups]

    removed_lines: list[LogicalLine] = [
        logical_line
        for group in groups
        for logical_line in group.grouped_logical_lines
    ]

    return PruneContainedLogicalLinesResult(
        input_logical_lines=logical_lines,
        pruned_logical_lines=pruned_lines,
        removed_logical_lines=removed_lines,
        cross_axis_groups=groups
    )



__all__ = [
    "PruneContainedLogicalLinesResult",
    "prune_logical_lines_by_full_axis_containment"
]