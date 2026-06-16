from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from detection import RawLineFamilyResult


@dataclass(frozen=True)
class ActiveImageSelection:
    active_image_path: Path
    preview_lines: tuple[str, ...]


@dataclass(frozen=True)
class RawLineFamilyArtifacts:
    source_bgr: np.ndarray
    display_bgr: np.ndarray
    gray_image: np.ndarray
    denoise_name: str
    denoised_image: np.ndarray
    threshold_name: str
    binary_image: np.ndarray
    min_component_area_px: int
    cleanup_name: str
    clean_binary: np.ndarray
    repair_name: str
    repaired_binary: np.ndarray
    line_family_result: RawLineFamilyResult
    binary_family_overlay: np.ndarray
    source_family_overlay: np.ndarray
    binary_logical_line_overlay: np.ndarray
    source_logical_line_overlay: np.ndarray
    raw_segment_group_board: np.ndarray | None = None
    containment_prune_board: np.ndarray | None = None
    vertex_containment_merge_board: np.ndarray | None = None
    binary_post_connection_logical_line_overlay: np.ndarray | None = None
    source_post_connection_logical_line_overlay: np.ndarray | None = None
    source_logical_line_intersection_overlay: np.ndarray | None = None
    source_trimmed_logical_line_overlay: np.ndarray | None = None
    source_logical_line_frame_overlay: np.ndarray | None = None


__all__ = [
    "ActiveImageSelection",
    "RawLineFamilyArtifacts",
]
