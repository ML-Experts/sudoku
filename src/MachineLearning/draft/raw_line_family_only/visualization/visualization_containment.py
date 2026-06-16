from __future__ import annotations

import numpy as np

from detection import RawLineFamilyResult
from models import ExperimentConfig
from visualization_raw_segment_groups import (
    draw_raw_segment_groups_for_lines,
)

def build_containment_prune_board(
    source_bgr: np.ndarray,
    line_family_result: RawLineFamilyResult,
    config: ExperimentConfig,
) -> np.ndarray:
    prune_board = np.full_like(source_bgr, 24)
    pruned_lines = [
        *(
            []
            if line_family_result.horizontal_containment_prune_result is None
            else line_family_result.horizontal_containment_prune_result.pruned_logical_lines
        ),
        *(
            []
            if line_family_result.vertical_containment_prune_result is None
            else line_family_result.vertical_containment_prune_result.pruned_logical_lines
        ),
    ]
    draw_raw_segment_groups_for_lines(
        prune_board,
        pruned_lines,
        config,
    )
    return prune_board


__all__ = [
    "build_containment_prune_board",
]
