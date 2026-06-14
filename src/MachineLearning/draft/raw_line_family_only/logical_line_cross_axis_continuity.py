from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING


import numpy as np

from logical_line_search import (
    try_find_white_path_from_point_to_logical_line
)

if TYPE_CHECKING:
    from logical_line_core import LogicalLine


@dataclass(frozen=True, slots=True)
class LogicalLineCrossAxisGroup:
    cross_axis_start: int
    cross_axis_end: int
    anchor_line: LogicalLine
    grouped_logical_lines: list[LogicalLine]
    grouped_logical_line_ids: set[int]


def logical_line_is_smaller_or_equal(
    container_line: "LogicalLine",
    candidate_line: "LogicalLine",
) -> bool:
    return candidate_line.axis_length <= container_line.axis_length


def find_candidates_in_cross_axis(
    container_line: LogicalLine,
    binary_image: np.ndarray,
    logical_lines: list["LogicalLine"],
    max_cross_axis_delta_px: int = 1
) -> list[LogicalLine]:
   
    candidates_lines: list[LogicalLine] = []

    cross_axis_group_start_min: int = container_line.cross_axis_start
    cross_axis_group_end_max: int = container_line.cross_axis_end
    
    candidates_lines: list[LogicalLine] = find_candidates_in_cross_axis_backward(
        container_line,
        binary_image,
        logical_lines,
        cross_axis_group_start_min,
        cross_axis_group_end_max,
        max_cross_axis_delta_px
    )

    if candidates_lines:
        cross_axis_group_start_min = min(
            cross_axis_group_start_min,
            min(line.cross_axis_start for line in candidates_lines),
        )
        cross_axis_group_end_max = max(
            cross_axis_group_end_max,
            max(line.cross_axis_end for line in candidates_lines),
        )

    candidates_lines += find_candidates_in_cross_axis_forward(
        container_line,
        binary_image,
        logical_lines,
        cross_axis_group_start_min,
        cross_axis_group_end_max,
        max_cross_axis_delta_px
    )    

    return candidates_lines

def find_candidates_in_cross_axis_forward(
    container_line: LogicalLine,
    binary_image: np.ndarray,
    logical_lines: list["LogicalLine"],
    cross_axis_group_start_min: int,
    cross_axis_group_end_max: int,
    max_cross_axis_delta_px: int = 1
) -> list[LogicalLine]:
   
    length: int = len(logical_lines)
    candidates_lines: list[LogicalLine] = []
    
    
    index: int = logical_lines.index(container_line) + 1
    while index < length:
        candidate_line = logical_lines[index]
        section_to_start = abs(cross_axis_group_start_min - candidate_line.cross_axis_end)
        section_to_end = abs(cross_axis_group_end_max - candidate_line.cross_axis_start)
        
        section_min = min(section_to_start, section_to_end)

        if check_if_logical_line_is_contained_in_cross_axis(
            binary_image,
            container_line,
            candidate_line,
            section_min,
            cross_axis_group_start_min,
            cross_axis_group_end_max,
            max_cross_axis_delta_px
        ) is False:
            break;

        cross_axis_group_start_min = min(cross_axis_group_start_min, candidate_line.cross_axis_start)
        cross_axis_group_end_max = max(cross_axis_group_end_max, candidate_line.cross_axis_end)

        candidates_lines.append(candidate_line)
        index += 1;

    return candidates_lines


def find_candidates_in_cross_axis_backward(
    container_line: LogicalLine,
    binary_image: np.ndarray,
    logical_lines: list["LogicalLine"],
    cross_axis_group_start_min: int,
    cross_axis_group_end_max: int,
    max_cross_axis_delta_px: int = 1
) -> list[LogicalLine]:
   
    candidates_lines: list[LogicalLine] = []
            
    index: int = logical_lines.index(container_line) - 1
    while index >= 0:
        candidate_line = logical_lines[index]
        section_to_start = abs(cross_axis_group_start_min - candidate_line.cross_axis_end)
        section_to_end = abs(cross_axis_group_end_max - candidate_line.cross_axis_start)
        
        section_min = min(section_to_start, section_to_end)

        if check_if_logical_line_is_contained_in_cross_axis(
            binary_image,
            container_line,
            candidate_line,
            section_min,
            cross_axis_group_start_min,
            cross_axis_group_end_max,
            max_cross_axis_delta_px
        ) is False:
            break;

        cross_axis_group_start_min = min(cross_axis_group_start_min, candidate_line.cross_axis_start)
        cross_axis_group_end_max = max(cross_axis_group_end_max, candidate_line.cross_axis_end)

        candidates_lines.append(candidate_line)
        index -= 1;

    return candidates_lines

def check_if_logical_line_is_contained_in_cross_axis(
    binary_image: np.ndarray,
    container_line: LogicalLine,
    candidate_line: LogicalLine,
    section_min: int,
    cross_axis_group_start_min: int,
    cross_axis_group_end_max: int,
    max_cross_axis_delta_px: int = 1
) -> bool:

        if section_min <= max_cross_axis_delta_px:
            return True
        elif cross_axis_group_start_min <= candidate_line.cross_axis_start and cross_axis_group_end_max >= candidate_line.cross_axis_start:
            return True
        elif cross_axis_group_start_min <= candidate_line.cross_axis_end and cross_axis_group_end_max >= candidate_line.cross_axis_end:
            return True
        elif(try_find_white_path_from_point_to_logical_line(
            binary_image,
            candidate_line.start_vertex,
            container_line
        )) is not None:
            return True
        elif(try_find_white_path_from_point_to_logical_line(
            binary_image,
            candidate_line.end_vertex,
            container_line
        )) is not None:
            return True    
            
        return False;
    
    
def group_logical_lines_by_cross_axis_continuity(
    anchor_line: LogicalLine,
    binary_image: np.ndarray,
    logical_lines: list["LogicalLine"],
) -> LogicalLineCrossAxisGroup:
    """
    Grupuje logiczne linie na podstawie ciągłości osi poprzecznej.    
    Zwraca listę grup, gdzie każda grupa zawiera listę logicznych linii, które mają ciągłą oś poprzeczną.  
    Grupa może zawierać jedną logiczną linię, jeśli nie ma innych logicznych linii w tym samym miejscu osi poprzecznej.
    """

    if not logical_lines:
        return LogicalLineCrossAxisGroup(
            cross_axis_start=anchor_line.cross_axis_start,
            cross_axis_end=anchor_line.cross_axis_end,
            anchor_line=anchor_line,
            grouped_logical_lines=[],
            grouped_logical_line_ids=set()
        )

    sorted_lines = sorted(
        logical_lines + [anchor_line],
        key=lambda logical_line: (
            min(
                abs(logical_line.cross_axis_start), 
                abs(logical_line.cross_axis_end)
            )
        )
    )

    candidates_lines: list[LogicalLine] = find_candidates_in_cross_axis(anchor_line, binary_image, sorted_lines)

    proune_lines: list[LogicalLine] = candidates_lines + [anchor_line]

    min_cross_axis_start = min(
        min(line.cross_axis_start for line in proune_lines),
        min(line.cross_axis_end for line in proune_lines)
    )

    max_cross_axis_end = max( 
        max(line.cross_axis_start for line in proune_lines),
        max(line.cross_axis_end for line in proune_lines)
    )

    ids: set[int] = {id(line) for line in candidates_lines}

    return LogicalLineCrossAxisGroup(
        cross_axis_start=min_cross_axis_start,
        cross_axis_end=max_cross_axis_end,
        anchor_line=anchor_line,
        grouped_logical_lines=candidates_lines,
        grouped_logical_line_ids=ids
    )


__all__ = [
    "LogicalLineCrossAxisGroup",
    "group_logical_lines_by_cross_axis_continuity"
]