from __future__ import annotations

import numpy as np

from sudoku_board_threshold_models import MergedLine


def candidate_interval_bridge_positions(
    first_line: MergedLine,
    second_line: MergedLine,
) -> tuple[tuple[float, float, float], ...]:
    candidates: dict[tuple[float, float, float], tuple[float, float, float]] = {}

    for first_start, first_end in first_line.support_intervals:
        for second_start, second_end in second_line.support_intervals:
            first_interval = (float(first_start), float(first_end))
            second_interval = (float(second_start), float(second_end))
            endpoint_candidates = (
                (first_interval[0], second_interval, True),
                (first_interval[1], second_interval, True),
                (second_interval[0], first_interval, False),
                (second_interval[1], first_interval, False),
            )
            for endpoint_position, opposite_interval, endpoint_on_first in (
                endpoint_candidates
            ):
                opposite_position = float(
                    np.clip(
                        endpoint_position,
                        opposite_interval[0],
                        opposite_interval[1],
                    )
                )
                gap = abs(endpoint_position - opposite_position)

                if endpoint_on_first:
                    candidate_positions = (
                        float(endpoint_position),
                        opposite_position,
                    )
                else:
                    candidate_positions = (
                        opposite_position,
                        float(endpoint_position),
                    )
                candidate = (
                    float(candidate_positions[0]),
                    float(candidate_positions[1]),
                    float(gap),
                )
                candidate_key = (
                    round(candidate[0], 4),
                    round(candidate[1], 4),
                    round(candidate[2], 4),
                )
                candidates[candidate_key] = candidate

    ordered_candidates = tuple(
        sorted(
            candidates.values(),
            key=lambda candidate: (candidate[2], candidate[0], candidate[1]),
        )
    )
    return ordered_candidates


def closest_interval_bridge_positions(
    first_line: MergedLine,
    second_line: MergedLine,
) -> tuple[float, float, float] | None:
    bridge_candidates = candidate_interval_bridge_positions(first_line, second_line)
    if not bridge_candidates:
        return None
    return bridge_candidates[0]


__all__ = [
    "candidate_interval_bridge_positions",
    "closest_interval_bridge_positions",
]
