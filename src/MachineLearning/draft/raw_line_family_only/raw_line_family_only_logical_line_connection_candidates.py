from __future__ import annotations

import numpy as np

from raw_line_family_only_logical_line_core import (
    LogicalLine,
    LogicalLineVertexKind,
)
from raw_line_family_only_logical_line_search import (
    SearchArea,
    build_cross_axis_span_goal_points,
    is_point_in_search_area,
)
from raw_line_family_only_logical_line_connection_types import (
    ConnectionCandidate,
    ConnectionKind,
    build_candidate_sort_key,
    distance_between_vertices,
    get_source_cross_axis_anchor,
)


def collect_connection_candidates(
    binary_image: np.ndarray,
    source_line: LogicalLine,
    source_vertex_kind: LogicalLineVertexKind,
    search_area: SearchArea,
    same_axis_lines: list[LogicalLine],
    cross_axis_lines: list[LogicalLine],
) -> list[ConnectionCandidate]:
    source_vertex = source_line.get_vertex(source_vertex_kind)
    source_cross_axis_anchor = get_source_cross_axis_anchor(
        source_line,
        source_vertex_kind,
    )
    candidates: list[ConnectionCandidate] = []

    def collect_from_lines(
        target_lines: list[LogicalLine],
        connection_kind: ConnectionKind,
    ) -> None:
        for target_line in target_lines:
            if target_line is source_line:
                continue
            for target_vertex_kind in LogicalLineVertexKind:
                target_vertex = target_line.get_vertex(target_vertex_kind)
                if not is_point_in_search_area(target_vertex, search_area):
                    continue
                candidates.append(
                    ConnectionCandidate(
                        connection_kind=connection_kind,
                        target_line=target_line,
                        target_vertex_kind=target_vertex_kind,
                        distance_px=distance_between_vertices(
                            source_vertex,
                            target_vertex,
                        ),
                    )
                )

    def collect_cross_axis_span_candidates() -> None:
        for target_line in cross_axis_lines:
            if not (
                target_line.axis_start
                <= source_cross_axis_anchor
                <= target_line.axis_end
            ):
                continue

            goal_points = build_cross_axis_span_goal_points(
                binary_image,
                search_area,
                source_line,
                target_line,
                source_cross_axis_anchor,
            )
            if not goal_points:
                continue

            preferred_contact_point = min(
                goal_points,
                key=lambda point: distance_between_vertices(source_vertex, point),
            )
            candidates.append(
                ConnectionCandidate(
                    connection_kind=ConnectionKind.CROSS_AXIS_SPAN,
                    target_line=target_line,
                    target_vertex_kind=None,
                    distance_px=distance_between_vertices(
                        source_vertex,
                        preferred_contact_point,
                    ),
                    goal_points=tuple(goal_points),
                    preferred_contact_point=preferred_contact_point,
                )
            )

    collect_from_lines(same_axis_lines, ConnectionKind.SAME_AXIS)
    collect_from_lines(cross_axis_lines, ConnectionKind.CROSS_AXIS)
    collect_cross_axis_span_candidates()
    candidates.sort(key=build_candidate_sort_key)
    return candidates


__all__ = [
    "collect_connection_candidates",
]
