from __future__ import annotations

import numpy as np

from detection import RawLineFamilyResult
from models import ExperimentConfig
from visualization_logical_lines import draw_logical_lines_for_lines


def build_vertex_containment_merge_board(
    source_bgr: np.ndarray,
    line_family_result: RawLineFamilyResult,
    config: ExperimentConfig,
) -> np.ndarray:
    merge_board = np.full_like(source_bgr, 24)
    merged_lines = [
        *line_family_result.horizontal_post_merge_logical_lines,
        *line_family_result.vertical_post_merge_logical_lines,
    ]
    draw_logical_lines_for_lines(
        merge_board,
        merged_lines,
        config,
    )
    return merge_board


__all__ = [
    "build_vertex_containment_merge_board",
]
