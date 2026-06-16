from __future__ import annotations

from frame_model import (
    LogicalLineFrameCandidate,
    LogicalLineFrameCandidateRanking,
)
from intersection_model import IntersectionOrder, LogicalLineIntersection
from logical_line_debug import get_logical_line_debug_name

TARGET_INNER_LINE_COUNT = 8


def rank_logical_line_frame_candidates(
    frame_candidates: list[LogicalLineFrameCandidate],
) -> list[LogicalLineFrameCandidate]:
    ranked_entries = [
        (frame_candidate, _build_frame_candidate_ranking(frame_candidate))
        for frame_candidate in frame_candidates
    ]
    ranked_entries.sort(
        key=lambda ranked_entry: _build_frame_candidate_sort_key(
            ranked_entry[0],
            ranked_entry[1],
        )
    )

    for ranking_position, (frame_candidate, ranking_debug) in enumerate(
        ranked_entries,
        start=1,
    ):
        frame_candidate.ranking_debug = ranking_debug
        frame_candidate.ranking_position = ranking_position
        frame_candidate.is_selected = ranking_position == 1

    return [
        frame_candidate
        for frame_candidate, _ranking_debug in ranked_entries
    ]


def select_best_logical_line_frame_candidate(
    frame_candidates: list[LogicalLineFrameCandidate],
) -> LogicalLineFrameCandidate | None:
    if not frame_candidates:
        return None

    ranked_candidates = rank_logical_line_frame_candidates(frame_candidates)
    return ranked_candidates[0]


def _build_frame_candidate_sort_key(
    frame_candidate: LogicalLineFrameCandidate,
    ranking_debug: LogicalLineFrameCandidateRanking,
) -> tuple[
    int,
    int,
    int,
    int,
    int,
    int,
    int,
    int,
    tuple[str, str, str, str],
]:
    return (
        0 if ranking_debug.has_exact_inner_line_counts else 1,
        ranking_debug.inner_line_count_deviation,
        0 if ranking_debug.matched_vertex_corner_count == 4 else 1,
        4 - ranking_debug.matched_vertex_corner_count,
        0 if ranking_debug.matched_order_corner_count == 4 else 1,
        4 - ranking_debug.matched_order_corner_count,
        8 - ranking_debug.matched_order_expectation_count,
        -ranking_debug.perimeter_px,
        _build_frame_candidate_debug_tie_break(frame_candidate),
    )


def _build_frame_candidate_debug_tie_break(
    frame_candidate: LogicalLineFrameCandidate,
) -> tuple[str, str, str, str]:
    return (
        get_logical_line_debug_name(frame_candidate.top_line),
        get_logical_line_debug_name(frame_candidate.right_line),
        get_logical_line_debug_name(frame_candidate.bottom_line),
        get_logical_line_debug_name(frame_candidate.left_line),
    )


def _build_frame_candidate_ranking(
    frame_candidate: LogicalLineFrameCandidate,
) -> LogicalLineFrameCandidateRanking:
    inner_horizontal_count = len(frame_candidate.horizontal_lines)
    inner_vertical_count = len(frame_candidate.vertical_lines)

    top_left_vertex_matches = (
        frame_candidate.top_line.start_vertex
        == frame_candidate.left_line.start_vertex
    )
    top_right_vertex_matches = (
        frame_candidate.top_line.end_vertex
        == frame_candidate.right_line.start_vertex
    )
    bottom_right_vertex_matches = (
        frame_candidate.bottom_line.end_vertex
        == frame_candidate.right_line.end_vertex
    )
    bottom_left_vertex_matches = (
        frame_candidate.bottom_line.start_vertex
        == frame_candidate.left_line.end_vertex
    )

    top_left_order_matches = _corner_orders_match(
        axis_line=frame_candidate.top_line,
        cross_axis_line=frame_candidate.left_line,
        axis_expected_order=IntersectionOrder.START,
        cross_axis_expected_order=IntersectionOrder.START,
    )
    top_right_order_matches = _corner_orders_match(
        axis_line=frame_candidate.top_line,
        cross_axis_line=frame_candidate.right_line,
        axis_expected_order=IntersectionOrder.END,
        cross_axis_expected_order=IntersectionOrder.START,
    )
    bottom_right_order_matches = _corner_orders_match(
        axis_line=frame_candidate.bottom_line,
        cross_axis_line=frame_candidate.right_line,
        axis_expected_order=IntersectionOrder.END,
        cross_axis_expected_order=IntersectionOrder.END,
    )
    bottom_left_order_matches = _corner_orders_match(
        axis_line=frame_candidate.bottom_line,
        cross_axis_line=frame_candidate.left_line,
        axis_expected_order=IntersectionOrder.START,
        cross_axis_expected_order=IntersectionOrder.END,
    )

    matched_order_expectation_count = sum(
        (
            _line_order_matches(
                frame_candidate.top_line,
                frame_candidate.left_line,
                IntersectionOrder.START,
            ),
            _line_order_matches(
                frame_candidate.left_line,
                frame_candidate.top_line,
                IntersectionOrder.START,
            ),
            _line_order_matches(
                frame_candidate.top_line,
                frame_candidate.right_line,
                IntersectionOrder.END,
            ),
            _line_order_matches(
                frame_candidate.right_line,
                frame_candidate.top_line,
                IntersectionOrder.START,
            ),
            _line_order_matches(
                frame_candidate.bottom_line,
                frame_candidate.right_line,
                IntersectionOrder.END,
            ),
            _line_order_matches(
                frame_candidate.right_line,
                frame_candidate.bottom_line,
                IntersectionOrder.END,
            ),
            _line_order_matches(
                frame_candidate.bottom_line,
                frame_candidate.left_line,
                IntersectionOrder.START,
            ),
            _line_order_matches(
                frame_candidate.left_line,
                frame_candidate.bottom_line,
                IntersectionOrder.END,
            ),
        )
    )

    perimeter_px = (
        frame_candidate.top_line.axis_length
        + frame_candidate.bottom_line.axis_length
        + frame_candidate.left_line.axis_length
        + frame_candidate.right_line.axis_length
    )

    return LogicalLineFrameCandidateRanking(
        has_exact_inner_line_counts=(
            inner_horizontal_count == TARGET_INNER_LINE_COUNT
            and inner_vertical_count == TARGET_INNER_LINE_COUNT
        ),
        inner_horizontal_count=inner_horizontal_count,
        inner_vertical_count=inner_vertical_count,
        inner_line_count_deviation=(
            abs(inner_horizontal_count - TARGET_INNER_LINE_COUNT)
            + abs(inner_vertical_count - TARGET_INNER_LINE_COUNT)
        ),
        matched_vertex_corner_count=sum(
            (
                top_left_vertex_matches,
                top_right_vertex_matches,
                bottom_right_vertex_matches,
                bottom_left_vertex_matches,
            )
        ),
        matched_order_corner_count=sum(
            (
                top_left_order_matches,
                top_right_order_matches,
                bottom_right_order_matches,
                bottom_left_order_matches,
            )
        ),
        matched_order_expectation_count=matched_order_expectation_count,
        top_left_vertex_matches=top_left_vertex_matches,
        top_right_vertex_matches=top_right_vertex_matches,
        bottom_right_vertex_matches=bottom_right_vertex_matches,
        bottom_left_vertex_matches=bottom_left_vertex_matches,
        top_left_order_matches=top_left_order_matches,
        top_right_order_matches=top_right_order_matches,
        bottom_right_order_matches=bottom_right_order_matches,
        bottom_left_order_matches=bottom_left_order_matches,
        perimeter_px=perimeter_px,
    )


def _corner_orders_match(
    axis_line,
    cross_axis_line,
    axis_expected_order: IntersectionOrder,
    cross_axis_expected_order: IntersectionOrder,
) -> bool:
    return _line_order_matches(
        axis_line,
        cross_axis_line,
        axis_expected_order,
    ) and _line_order_matches(
        cross_axis_line,
        axis_line,
        cross_axis_expected_order,
    )


def _line_order_matches(
    axis_line,
    cross_axis_line,
    expected_order: IntersectionOrder,
) -> bool:
    logical_line_intersection = _find_intersection(
        axis_line,
        get_logical_line_debug_name(cross_axis_line),
    )
    if logical_line_intersection is None:
        return False
    return logical_line_intersection.order == expected_order


def _find_intersection(
    axis_line,
    cross_axis_debug_name: str,
) -> LogicalLineIntersection | None:
    for logical_line_intersection in axis_line.intersections:
        if (
            logical_line_intersection.intersected_line_cross_axis_debug_name
            == cross_axis_debug_name
        ):
            return logical_line_intersection
    return None


__all__ = [
    "TARGET_INNER_LINE_COUNT",
    "rank_logical_line_frame_candidates",
    "select_best_logical_line_frame_candidate",
]
