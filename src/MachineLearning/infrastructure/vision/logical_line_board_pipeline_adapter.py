from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np
from numpy.typing import NDArray

from infrastructure.vision.engine.binary import (
    apply_directional_close_repair,
    apply_soft_component_cleanup,
)
from infrastructure.vision.engine.detection import (
    RawLineFamilyResult,
    detect_line_families,
)
from infrastructure.vision.engine.display import resize_for_display
from infrastructure.vision.engine.frame_model import LogicalLineFrameCandidate
from infrastructure.vision.engine.logical_line_frame_warp import (
    build_destination_square_corners,
    resolve_frame_candidate_corners,
    warp_selected_frame_to_square,
)
from infrastructure.vision.engine.models import ExperimentConfig
from infrastructure.vision.engine.preprocessing_api import (
    build_board_preprocessing_artifacts,
)
from models.board_quad import BoardQuad


@dataclass(slots=True)
class _CachedBoardDetection:
    source_image_identity: int
    board_quad: BoardQuad
    display_image: NDArray[np.uint8]
    frame_candidate: LogicalLineFrameCandidate


class LogicalLineBoardPipelineAdapter:
    def __init__(
        self,
        *,
        max_display_size: int,
        adaptive_threshold_block_size: int,
        adaptive_threshold_c_value: int,
        hough_threshold: int,
        min_line_length_ratio: float,
        max_line_gap_ratio: float,
        angle_tolerance_degrees: float,
        minimum_board_area_ratio: float,
        minimum_family_segments: int,
        minimum_distinct_lines_per_family: int,
        warp_output_size_px: int,
        warp_output_padding_px: int,
        warp_cell_divisions: int = 9,
        warp_cells_output_mime_type: str = "image/png",
        warp_cells_preview_gap_px: int = 2,
    ) -> None:
        self._config = ExperimentConfig(
            max_display_size=max_display_size,
            adaptive_threshold_block_size=adaptive_threshold_block_size,
            adaptive_threshold_c_value=adaptive_threshold_c_value,
            raw_hough_threshold=hough_threshold,
            raw_min_line_length_ratio=min_line_length_ratio,
            raw_max_line_gap_ratio=max_line_gap_ratio,
            line_family_angle_tolerance_degrees=angle_tolerance_degrees,
            warp_output_size_px=warp_output_size_px,
            warp_output_padding_px=warp_output_padding_px,
            warp_cell_divisions=warp_cell_divisions,
            warp_cells_output_mime_type=warp_cells_output_mime_type,
            warp_cells_preview_gap_px=warp_cells_preview_gap_px,
        )
        self._minimum_board_area_ratio = minimum_board_area_ratio
        self._minimum_family_segments = minimum_family_segments
        self._minimum_distinct_lines_per_family = (
            minimum_distinct_lines_per_family
        )
        self._remembered_source_image: NDArray[np.uint8] | None = None
        self._cached_detection: _CachedBoardDetection | None = None

    def remember_source_image(self, image: NDArray[np.uint8]) -> None:
        self._remembered_source_image = image
        self._cached_detection = None

    def detect_board_quad(self, image: NDArray[np.uint8]) -> BoardQuad:
        if self._remembered_source_image is not None:
            return self._detect_from_remembered_source(self._remembered_source_image)
        self._cached_detection = None
        return self._detect_from_detection_image(image)

    def warp_board(
        self,
        image: NDArray[np.uint8],
        board_quad: BoardQuad,
    ) -> NDArray[np.uint8]:
        if self._can_use_cached_detection(image, board_quad):
            cached_detection = self._cached_detection
            if cached_detection is None:
                raise ValueError("Cached board detection is not available.")
            warp_result = warp_selected_frame_to_square(
                image=cached_detection.display_image,
                frame_candidate=cached_detection.frame_candidate,
                output_size_px=self._config.warp_output_size_px,
                padding_px=self._config.warp_output_padding_px,
                grid_division_count=self._config.warp_cell_divisions,
                cells_output_mime_type=self._config.warp_cells_output_mime_type,
                cells_preview_gap_px=self._config.warp_cells_preview_gap_px,
                ml_ready_adaptive_block_size=(
                    self._config.adaptive_threshold_block_size
                ),
                ml_ready_adaptive_c=self._config.adaptive_threshold_c_value,
            )
            if warp_result is None or warp_result.warped_image.size == 0:
                raise ValueError("Perspective transform produced empty image.")
            return warp_result.warped_image

        return self._warp_from_board_quad(image, board_quad)

    def _detect_from_remembered_source(
        self,
        source_image: NDArray[np.uint8],
    ) -> BoardQuad:
        source_bgr = self._ensure_bgr(source_image)
        display_source_image = resize_for_display(
            source_image,
            self._config.max_display_size,
        )
        preprocessing_artifacts = build_board_preprocessing_artifacts(
            source_bgr=source_bgr,
            config=self._config,
        )
        line_family_result = detect_line_families(
            preprocessing_artifacts.clean_binary,
            self._config,
            pixel_connection_binary_image=preprocessing_artifacts.repaired_binary,
            warp_source_image=None,
        )
        frame_candidate = line_family_result.selected_logical_line_frame_candidate
        if frame_candidate is None:
            raise ValueError("Sudoku board frame was not detected.")

        self._validate_line_family_result(line_family_result)
        frame_corners = resolve_frame_candidate_corners(frame_candidate)
        if frame_corners is None:
            raise ValueError("Sudoku board frame corners could not be resolved.")

        scale_x = float(source_bgr.shape[1]) / float(
            preprocessing_artifacts.display_bgr.shape[1]
        )
        scale_y = float(source_bgr.shape[0]) / float(
            preprocessing_artifacts.display_bgr.shape[0]
        )
        board_quad = BoardQuad(
            top_left=(
                float(frame_corners.top_left[0] * scale_x),
                float(frame_corners.top_left[1] * scale_y),
            ),
            top_right=(
                float(frame_corners.top_right[0] * scale_x),
                float(frame_corners.top_right[1] * scale_y),
            ),
            bottom_right=(
                float(frame_corners.bottom_right[0] * scale_x),
                float(frame_corners.bottom_right[1] * scale_y),
            ),
            bottom_left=(
                float(frame_corners.bottom_left[0] * scale_x),
                float(frame_corners.bottom_left[1] * scale_y),
            ),
        )
        self._validate_detected_board_area(board_quad, source_bgr)
        self._cached_detection = _CachedBoardDetection(
            source_image_identity=id(source_image),
            board_quad=board_quad,
            display_image=display_source_image,
            frame_candidate=frame_candidate,
        )
        return board_quad

    def _detect_from_detection_image(
        self,
        image: NDArray[np.uint8],
    ) -> BoardQuad:
        if image.size == 0:
            raise ValueError("Board image cannot be empty.")

        grayscale_image = self._to_grayscale(image)
        binary_image = self._ensure_binary_foreground(grayscale_image)
        detection_binary, scale_x, scale_y = self._resize_for_detection(binary_image)
        _, clean_binary = apply_soft_component_cleanup(
            detection_binary,
            self._config,
        )
        repaired_binary = apply_directional_close_repair(
            clean_binary,
            self._config,
        )
        line_family_result = detect_line_families(
            clean_binary,
            self._config,
            pixel_connection_binary_image=repaired_binary,
            warp_source_image=None,
        )
        frame_candidate = line_family_result.selected_logical_line_frame_candidate
        if frame_candidate is None:
            raise ValueError("Sudoku board frame was not detected.")

        self._validate_line_family_result(line_family_result)
        frame_corners = resolve_frame_candidate_corners(frame_candidate)
        if frame_corners is None:
            raise ValueError("Sudoku board frame corners could not be resolved.")

        board_quad = BoardQuad(
            top_left=(
                float(frame_corners.top_left[0] * scale_x),
                float(frame_corners.top_left[1] * scale_y),
            ),
            top_right=(
                float(frame_corners.top_right[0] * scale_x),
                float(frame_corners.top_right[1] * scale_y),
            ),
            bottom_right=(
                float(frame_corners.bottom_right[0] * scale_x),
                float(frame_corners.bottom_right[1] * scale_y),
            ),
            bottom_left=(
                float(frame_corners.bottom_left[0] * scale_x),
                float(frame_corners.bottom_left[1] * scale_y),
            ),
        )
        self._validate_detected_board_area(board_quad, grayscale_image)
        return board_quad

    def _validate_line_family_result(
        self,
        line_family_result: RawLineFamilyResult,
    ) -> None:
        if (
            len(line_family_result.horizontal_segments)
            < self._minimum_family_segments
            or len(line_family_result.vertical_segments)
            < self._minimum_family_segments
        ):
            raise ValueError("Detected line families are too sparse for a board.")

        if (
            len(line_family_result.horizontal_logical_lines)
            < self._minimum_distinct_lines_per_family
            or len(line_family_result.vertical_logical_lines)
            < self._minimum_distinct_lines_per_family
        ):
            raise ValueError("Detected logical lines are insufficient for a Sudoku grid.")

    def _can_use_cached_detection(
        self,
        image: NDArray[np.uint8],
        board_quad: BoardQuad,
    ) -> bool:
        cached_detection = self._cached_detection
        if cached_detection is None:
            return False
        return (
            cached_detection.source_image_identity == id(image)
            and cached_detection.board_quad == board_quad
        )

    def _warp_from_board_quad(
        self,
        image: NDArray[np.uint8],
        board_quad: BoardQuad,
    ) -> NDArray[np.uint8]:
        source_points = np.array(
            board_quad.as_clockwise_points(),
            dtype=np.float32,
        )
        destination_points = build_destination_square_corners(
            output_size_px=self._config.warp_output_size_px,
            padding_px=self._config.warp_output_padding_px,
            grid_division_count=self._config.warp_cell_divisions,
        )
        perspective_matrix = cv2.getPerspectiveTransform(
            source_points,
            destination_points,
        )
        transformed = cv2.warpPerspective(
            image,
            perspective_matrix,
            (
                self._config.warp_output_size_px,
                self._config.warp_output_size_px,
            ),
        )
        if transformed.size == 0:
            raise ValueError("Perspective transform produced empty image.")
        return transformed

    def _ensure_bgr(self, image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        if image.ndim == 2:
            return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        if image.ndim == 3:
            return image
        raise ValueError("Board image must be grayscale or color.")

    def _to_grayscale(self, image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        if image.ndim == 2:
            return image
        if image.ndim == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        raise ValueError("Board image must be grayscale or color.")

    def _ensure_binary_foreground(
        self,
        grayscale_image: NDArray[np.uint8],
    ) -> NDArray[np.uint8]:
        if grayscale_image.dtype != np.uint8:
            normalized = cv2.normalize(
                grayscale_image,
                None,
                0,
                255,
                cv2.NORM_MINMAX,
            )
            grayscale_image = normalized.astype(np.uint8)

        unique_values = np.unique(grayscale_image)
        if len(unique_values) <= 2:
            binary_image = np.where(grayscale_image > 0, 255, 0).astype(np.uint8)
        else:
            _, binary_image = cv2.threshold(
                grayscale_image,
                0,
                255,
                cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU,
            )

        white_ratio = float(np.count_nonzero(binary_image)) / float(binary_image.size)
        if white_ratio > 0.5:
            binary_image = cv2.bitwise_not(binary_image)
        return binary_image

    def _resize_for_detection(
        self,
        binary_image: NDArray[np.uint8],
    ) -> tuple[NDArray[np.uint8], float, float]:
        resized_binary = resize_for_display(
            binary_image,
            self._config.max_display_size,
        )
        scale_x = float(binary_image.shape[1]) / float(resized_binary.shape[1])
        scale_y = float(binary_image.shape[0]) / float(resized_binary.shape[0])
        return resized_binary, scale_x, scale_y

    def _validate_detected_board_area(
        self,
        board_quad: BoardQuad,
        image: NDArray[np.uint8],
    ) -> None:
        polygon = np.array(board_quad.as_clockwise_points(), dtype=np.float32)
        board_area = abs(float(cv2.contourArea(polygon.reshape(-1, 1, 2))))
        image_area = float(image.shape[0] * image.shape[1])
        if image_area <= 0.0:
            raise ValueError("Board image must have positive area.")
        if board_area / image_area < self._minimum_board_area_ratio:
            raise ValueError("Detected board area is below the configured threshold.")
