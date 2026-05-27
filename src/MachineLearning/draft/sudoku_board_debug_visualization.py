from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from sudoku_board_debug_candidates import DistinctLineCandidate
from sudoku_board_debug_geometry import BoardQuad, LineSegment
from sudoku_board_debug_line_experiment import LineExperimentResult, MergedLineCandidate


@dataclass(frozen=True)
class LineExperimentOverlays:
    binary_display_image: np.ndarray
    binary_debug_image: np.ndarray
    raw_segments_overlay: np.ndarray
    family_overlay: np.ndarray
    filtered_overlay: np.ndarray
    final_overlay: np.ndarray
    final_overlay_on_source: np.ndarray


def show_image(axis, image: np.ndarray, title: str, *, is_bgr: bool = False) -> None:
    display_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) if is_bgr else image
    if not is_bgr and display_image.ndim == 2:
        axis.imshow(display_image, cmap="gray", vmin=0, vmax=255)
    else:
        axis.imshow(display_image)
    axis.set_title(title)
    axis.axis("off")


def draw_line_segment(
    image: np.ndarray,
    line_segment: LineSegment,
    color: tuple[int, int, int],
    thickness: int,
) -> None:
    start_point = (int(round(line_segment.start[0])), int(round(line_segment.start[1])))
    end_point = (int(round(line_segment.end[0])), int(round(line_segment.end[1])))
    cv2.line(image, start_point, end_point, color, thickness, cv2.LINE_AA)


def draw_candidate_segments(
    image: np.ndarray,
    candidate: DistinctLineCandidate,
    color: tuple[int, int, int],
    thickness: int,
) -> None:
    for line_segment in candidate.segments:
        draw_line_segment(image, line_segment, color, thickness)


def draw_board_quad(
    source_image: np.ndarray,
    board_quad: BoardQuad,
    color: tuple[int, int, int] = (0, 255, 0),
    thickness: int = 6,
) -> np.ndarray:
    overlay = source_image.copy()
    points = np.array(board_quad.as_clockwise_points(), dtype=np.int32).reshape((-1, 1, 2))
    cv2.polylines(overlay, [points], isClosed=True, color=color, thickness=thickness)
    for index, point in enumerate(points.reshape((-1, 2))):
        cv2.circle(overlay, tuple(point), radius=10, color=(255, 0, 0), thickness=-1)
        label_origin = (int(point[0]) + 12, int(point[1]) - 12)
        cv2.putText(
            overlay,
            str(index),
            label_origin,
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (255, 0, 0),
            2,
            cv2.LINE_AA,
        )
    return overlay


def draw_candidate_labels(
    image: np.ndarray,
    candidates: list[DistinctLineCandidate],
    color: tuple[int, int, int],
) -> None:
    image_height, image_width = image.shape[:2]
    for index, candidate in enumerate(candidates):
        anchor_point = candidate.line.point
        label_x = int(np.clip(anchor_point[0], 10, image_width - 40))
        label_y = int(np.clip(anchor_point[1], 20, image_height - 10))
        cv2.putText(
            image,
            str(index),
            (label_x, label_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2,
            cv2.LINE_AA,
        )


def draw_legacy_overlay(
    source_image: np.ndarray,
    board_quad: BoardQuad,
) -> np.ndarray:
    return draw_board_quad(source_image, board_quad)


def draw_line_family_overlay(
    source_image: np.ndarray,
    debug_data: dict[str, object],
) -> np.ndarray:
    overlay = source_image.copy()
    best_candidate = debug_data["best_candidate"]
    primary_pair = best_candidate.primary_pair
    secondary_pair = best_candidate.secondary_pair

    for line_segment in debug_data["primary_family"]:
        draw_line_segment(overlay, line_segment, (255, 165, 0), 1)
    for line_segment in debug_data["secondary_family"]:
        draw_line_segment(overlay, line_segment, (0, 255, 255), 1)

    for candidate in debug_data["primary_candidates"]:
        draw_candidate_segments(overlay, candidate, (255, 0, 255), 2)
    for candidate in debug_data["secondary_candidates"]:
        draw_candidate_segments(overlay, candidate, (0, 255, 0), 2)

    for candidate in primary_pair:
        draw_candidate_segments(overlay, candidate, (0, 0, 255), 4)
    for candidate in secondary_pair:
        draw_candidate_segments(overlay, candidate, (255, 0, 0), 4)

    draw_candidate_labels(overlay, debug_data["primary_candidates"], (255, 0, 255))
    draw_candidate_labels(overlay, debug_data["secondary_candidates"], (0, 200, 0))
    return draw_board_quad(overlay, best_candidate.board_quad, color=(255, 255, 255), thickness=3)


def draw_quad_candidate_overlay(
    source_image: np.ndarray,
    debug_data: dict[str, object],
) -> np.ndarray:
    overlay = source_image.copy()
    best_candidate = debug_data["best_candidate"]
    primary_pair = best_candidate.primary_pair
    secondary_pair = best_candidate.secondary_pair

    for candidate in debug_data["primary_candidates"]:
        draw_candidate_segments(overlay, candidate, (255, 165, 0), 1)
    for candidate in debug_data["secondary_candidates"]:
        draw_candidate_segments(overlay, candidate, (255, 255, 0), 1)

    for candidate in primary_pair:
        draw_candidate_segments(overlay, candidate, (255, 0, 255), 3)
    for candidate in secondary_pair:
        draw_candidate_segments(overlay, candidate, (0, 255, 255), 3)

    return draw_board_quad(overlay, best_candidate.board_quad, color=(0, 255, 0), thickness=5)


def candidate_draw_points(
    candidate: MergedLineCandidate,
) -> tuple[tuple[int, int], tuple[int, int]]:
    if candidate.line is None:
        raise ValueError("Merged line candidate is missing fitted line.")
    start_point = candidate.line.point + candidate.line.direction * candidate.span_start
    end_point = candidate.line.point + candidate.line.direction * candidate.span_end
    return (
        (int(round(float(start_point[0]))), int(round(float(start_point[1])))),
        (int(round(float(end_point[0]))), int(round(float(end_point[1])))),
    )


def draw_raw_segments_overlay(
    base_image: np.ndarray,
    line_segments: list[LineSegment],
) -> np.ndarray:
    overlay = base_image.copy()
    for line_segment in line_segments:
        start_point = tuple(int(round(value)) for value in line_segment.start)
        end_point = tuple(int(round(value)) for value in line_segment.end)
        cv2.line(overlay, start_point, end_point, (180, 180, 180), 1)
    return overlay


def draw_family_overlay(
    base_image: np.ndarray,
    primary_segments: list[LineSegment],
    secondary_segments: list[LineSegment],
) -> np.ndarray:
    overlay = base_image.copy()
    for line_segment in primary_segments:
        start_point = tuple(int(round(value)) for value in line_segment.start)
        end_point = tuple(int(round(value)) for value in line_segment.end)
        cv2.line(overlay, start_point, end_point, (255, 165, 0), 1)
    for line_segment in secondary_segments:
        start_point = tuple(int(round(value)) for value in line_segment.start)
        end_point = tuple(int(round(value)) for value in line_segment.end)
        cv2.line(overlay, start_point, end_point, (0, 255, 255), 1)
    return overlay


def draw_merged_candidates_overlay(
    base_image: np.ndarray,
    primary_candidates: list[MergedLineCandidate],
    secondary_candidates: list[MergedLineCandidate],
) -> np.ndarray:
    overlay = base_image.copy()
    for family_prefix, candidates, color in (
        ("P", primary_candidates, (255, 0, 255)),
        ("S", secondary_candidates, (0, 220, 0)),
    ):
        for candidate_index, candidate in enumerate(candidates):
            start_point, end_point = candidate_draw_points(candidate)
            cv2.line(overlay, start_point, end_point, color, 2)
            anchor_x = int(round((start_point[0] + end_point[0]) / 2.0))
            anchor_y = int(round((start_point[1] + end_point[1]) / 2.0))
            label = f"{family_prefix}{candidate_index}|span={candidate.span_length:.0f}"
            cv2.putText(
                overlay,
                label,
                (max(10, anchor_x - 40), max(20, anchor_y - 4)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                color,
                1,
                cv2.LINE_AA,
            )
    return overlay


def build_line_experiment_overlays(
    source_image: np.ndarray,
    binary_image: np.ndarray,
    result: LineExperimentResult,
) -> LineExperimentOverlays:
    # Keep the adaptive-threshold foreground white on black for debugging.
    binary_display_image = binary_image.copy()
    binary_debug_image = cv2.cvtColor(binary_display_image, cv2.COLOR_GRAY2BGR)
    return LineExperimentOverlays(
        binary_display_image=binary_display_image,
        binary_debug_image=binary_debug_image,
        raw_segments_overlay=draw_raw_segments_overlay(
            binary_debug_image,
            result.raw_segments,
        ),
        family_overlay=draw_family_overlay(
            binary_debug_image,
            result.primary_segments,
            result.secondary_segments,
        ),
        filtered_overlay=draw_merged_candidates_overlay(
            binary_debug_image,
            result.primary_filtered_candidates,
            result.secondary_filtered_candidates,
        ),
        final_overlay=draw_merged_candidates_overlay(
            binary_debug_image,
            result.primary_final_candidates,
            result.secondary_final_candidates,
        ),
        final_overlay_on_source=draw_merged_candidates_overlay(
            source_image,
            result.primary_final_candidates,
            result.secondary_final_candidates,
        ),
    )
