from __future__ import annotations

import cv2
import numpy as np

from detection import RawLineFamilyResult
from frame_model import LogicalLineFrameCandidate
from logical_line_frame_warp import resolve_frame_candidate_corners
from logical_line_debug import get_logical_line_debug_name
from models import ExperimentConfig


def build_logical_line_frame_overlay(
    source_bgr: np.ndarray,
    binary_image: np.ndarray,
    line_family_result: RawLineFamilyResult,
    config: ExperimentConfig,
) -> np.ndarray:
    del binary_image
    source_overlay = source_bgr.copy()

    for frame_index, frame_candidate in enumerate(
        line_family_result.logical_line_frame_candidates,
        start=1,
    ):
        frame_color = _build_frame_color(frame_index - 1)
        _draw_frame_candidate(
            source_overlay,
            frame_candidate,
            frame_index,
            frame_color,
            config,
            include_selection_marker=False,
        )

    return source_overlay


def build_selected_logical_line_frame_overlay(
    source_bgr: np.ndarray,
    binary_image: np.ndarray,
    line_family_result: RawLineFamilyResult,
    config: ExperimentConfig,
) -> np.ndarray:
    del binary_image
    source_overlay = source_bgr.copy()

    selected_frame_candidate = (
        line_family_result.selected_logical_line_frame_candidate
    )
    if selected_frame_candidate is None:
        return source_overlay

    _draw_frame_candidate(
        source_overlay,
        selected_frame_candidate,
        selected_frame_candidate.ranking_position or 1,
        _build_selected_frame_color(),
        config,
        include_selection_marker=True,
    )
    return source_overlay


def _build_frame_color(frame_index: int) -> tuple[int, int, int]:
    hue = (frame_index * 37) % 180
    hsv_color = np.uint8([[[hue, 255, 255]]])
    bgr_color = cv2.cvtColor(hsv_color, cv2.COLOR_HSV2BGR)[0, 0]
    return int(bgr_color[0]), int(bgr_color[1]), int(bgr_color[2])


def _build_selected_frame_color() -> tuple[int, int, int]:
    return (0, 255, 255)


def _draw_frame_candidate(
    overlay: np.ndarray,
    frame_candidate: LogicalLineFrameCandidate,
    frame_index: int,
    frame_color: tuple[int, int, int],
    config: ExperimentConfig,
    include_selection_marker: bool,
) -> None:
    frame_vertices = _resolve_frame_vertices(frame_candidate)
    if frame_vertices is None:
        return

    top_left, top_right, bottom_right, bottom_left = frame_vertices

    for start_vertex, end_vertex in zip(
        frame_vertices,
        frame_vertices[1:] + frame_vertices[:1],
    ):
        cv2.line(
            overlay,
            start_vertex,
            end_vertex,
            frame_color,
            max(config.line_overlay_thickness + 1, 3),
            cv2.LINE_AA,
        )

    label_text = _build_frame_label(
        frame_candidate,
        frame_index,
        include_selection_marker=include_selection_marker,
    )
    center_x = int(
        round(
            (
                top_left[0]
                + top_right[0]
                + bottom_left[0]
                + bottom_right[0]
            )
            / 4.0
        )
    )
    center_y = int(
        round(
            (
                top_left[1]
                + top_right[1]
                + bottom_left[1]
                + bottom_right[1]
            )
            / 4.0
        )
    )
    text_origin = (center_x + 8, max(18, center_y - 8))
    cv2.putText(
        overlay,
        label_text,
        text_origin,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 0, 0),
        3,
        cv2.LINE_AA,
    )
    cv2.putText(
        overlay,
        label_text,
        text_origin,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        frame_color,
        1,
        cv2.LINE_AA,
    )


def _resolve_frame_vertices(
    frame_candidate: LogicalLineFrameCandidate,
) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int], tuple[int, int]] | None:
    frame_corners = resolve_frame_candidate_corners(frame_candidate)
    if frame_corners is None:
        return None

    return tuple(
        (
            int(round(point[0])),
            int(round(point[1])),
        )
        for point in frame_corners.ordered_points
    )  # type: ignore[return-value]


def _build_frame_label(
    frame_candidate: LogicalLineFrameCandidate,
    frame_index: int,
    include_selection_marker: bool,
) -> str:
    left_line_name = get_logical_line_debug_name(frame_candidate.left_line)
    right_line_name = get_logical_line_debug_name(frame_candidate.right_line)
    top_line_name = get_logical_line_debug_name(frame_candidate.top_line)
    bottom_line_name = get_logical_line_debug_name(frame_candidate.bottom_line)
    label_text = (
        f"F{frame_index:02d} "
        f"{left_line_name}->{right_line_name}->{top_line_name}->{bottom_line_name}"
    )
    if include_selection_marker and frame_candidate.is_selected:
        return f"{label_text} best"
    return label_text


__all__ = [
    "build_logical_line_frame_overlay",
    "build_selected_logical_line_frame_overlay",
]
