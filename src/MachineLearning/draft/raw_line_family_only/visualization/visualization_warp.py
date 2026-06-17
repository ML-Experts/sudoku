from __future__ import annotations

import numpy as np

from detection import RawLineFamilyResult
from logical_line_frame_warp import build_corner_overlay
from models import ExperimentConfig


def build_selected_frame_warp_overlay(
    source_bgr: np.ndarray,
    binary_image: np.ndarray,
    line_family_result: RawLineFamilyResult,
    config: ExperimentConfig,
) -> np.ndarray:
    del binary_image

    warp_result = line_family_result.selected_logical_line_frame_warp_result
    if warp_result is None:
        return source_bgr.copy()

    return build_corner_overlay(
        source_bgr=source_bgr,
        frame_corners=warp_result.source_corners,
        color_bgr=(0, 200, 0),
        label_prefix="W",
        thickness=max(config.line_overlay_thickness, 2),
    )


__all__ = ["build_selected_frame_warp_overlay"]
