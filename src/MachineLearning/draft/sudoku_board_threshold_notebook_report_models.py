from __future__ import annotations

from dataclasses import dataclass

import numpy as np


AlignedCorners = tuple[
    tuple[float, float],
    tuple[float, float],
    tuple[float, float],
    tuple[float, float],
]


@dataclass(frozen=True)
class LineDebugArtifacts:
    line_family_result: object
    selected_repaired_binary: np.ndarray
    binary_family_overlay: np.ndarray
    source_family_overlay: np.ndarray
    binary_logical_overlay: np.ndarray
    source_logical_overlay: np.ndarray
    binary_merged_overlay: np.ndarray
    source_merged_overlay: np.ndarray
    binary_vertex_overlay: np.ndarray
    source_vertex_overlay: np.ndarray


@dataclass(frozen=True)
class FrameDebugArtifacts:
    frame_detection_result: object
    selected_frames: list[object]
    binary_frame_overlay: np.ndarray
    source_frame_overlay: np.ndarray


@dataclass(frozen=True)
class WarpDebugArtifacts:
    selected_frame: object | None
    aligned_corners: AlignedCorners | None
    aligned_corner_overlay: np.ndarray | None
    aligned_warp: np.ndarray | None


@dataclass(frozen=True)
class CellDebugArtifacts:
    selected_frame: object | None
    board_gray: np.ndarray | None
    board_contrast: np.ndarray | None
    board_binary: np.ndarray | None
    raw_cells: object | None
    cleaned_cells: object | None
    raw_contact_sheet: np.ndarray | None
    cleaned_contact_sheet: np.ndarray | None


__all__ = [
    "AlignedCorners",
    "CellDebugArtifacts",
    "FrameDebugArtifacts",
    "LineDebugArtifacts",
    "WarpDebugArtifacts",
]
