import cv2
import numpy as np
from numpy.typing import NDArray

from infrastructure.vision.engine.binary import (
    apply_directional_close_repair,
    apply_soft_component_cleanup,
)
from infrastructure.vision.engine.detection import detect_line_families
from infrastructure.vision.engine.display import resize_for_display
from infrastructure.vision.engine.logical_line_frame_warp import (
    resolve_frame_candidate_corners,
)
from infrastructure.vision.engine.models import ExperimentConfig
from infrastructure.vision.logical_line_board_pipeline_adapter import (
    LogicalLineBoardPipelineAdapter,
)
from models.board_quad import BoardQuad


class OpenCvBoardEdgeDetector:
    def __init__(
        self,
        canny_threshold_1: int,
        canny_threshold_2: int,
        hough_threshold: int,
        min_line_length_ratio: float,
        max_line_gap_ratio: float,
        angle_tolerance_degrees: float,
        outer_line_window_ratio: float,
        minimum_board_area_ratio: float,
        minimum_family_segments: int,
        line_position_merge_distance_ratio: float,
        minimum_distinct_lines_per_family: int,
        max_display_size: int = 1600,
        board_pipeline_adapter: LogicalLineBoardPipelineAdapter | None = None,
    ) -> None:
        del canny_threshold_1
        del canny_threshold_2
        del outer_line_window_ratio
        del line_position_merge_distance_ratio

        if hough_threshold <= 0:
            raise ValueError("Hough threshold must be greater than zero.")
        if not 0.0 < min_line_length_ratio <= 1.0:
            raise ValueError("Minimum line length ratio must be in range (0, 1].")
        if not 0.0 <= max_line_gap_ratio <= 1.0:
            raise ValueError("Maximum line gap ratio must be in range [0, 1].")
        if angle_tolerance_degrees <= 0:
            raise ValueError("Angle tolerance must be greater than zero.")
        if not 0.0 <= minimum_board_area_ratio <= 1.0:
            raise ValueError("Minimum board area ratio must be in range [0, 1].")
        if minimum_family_segments <= 0:
            raise ValueError("Minimum family segments must be greater than zero.")
        if minimum_distinct_lines_per_family <= 0:
            raise ValueError(
                "Minimum distinct lines per family must be greater than zero."
            )
        if max_display_size <= 0:
            raise ValueError("Max display size must be greater than zero.")

        self._config = ExperimentConfig(
            max_display_size=max_display_size,
            raw_hough_threshold=hough_threshold,
            raw_min_line_length_ratio=min_line_length_ratio,
            raw_max_line_gap_ratio=max_line_gap_ratio,
            line_family_angle_tolerance_degrees=angle_tolerance_degrees,
        )
        self._minimum_board_area_ratio = minimum_board_area_ratio
        self._minimum_family_segments = minimum_family_segments
        self._minimum_distinct_lines_per_family = minimum_distinct_lines_per_family
        self._board_pipeline_adapter = board_pipeline_adapter

    def detect(self, image: NDArray[np.uint8]) -> BoardQuad:
        if self._board_pipeline_adapter is not None:
            return self._board_pipeline_adapter.detect_board_quad(image)
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

        if (
            len(line_family_result.horizontal_segments) < self._minimum_family_segments
            or len(line_family_result.vertical_segments) < self._minimum_family_segments
        ):
            raise ValueError("Detected line families are too sparse for a board.")

        if (
            len(line_family_result.horizontal_logical_lines)
            < self._minimum_distinct_lines_per_family
            or len(line_family_result.vertical_logical_lines)
            < self._minimum_distinct_lines_per_family
        ):
            raise ValueError("Detected logical lines are insufficient for a Sudoku grid.")

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
        grayscale_image: NDArray[np.uint8],
    ) -> None:
        polygon = np.array(board_quad.as_clockwise_points(), dtype=np.float32)
        board_area = abs(float(cv2.contourArea(polygon.reshape(-1, 1, 2))))
        image_area = float(grayscale_image.shape[0] * grayscale_image.shape[1])
        if image_area <= 0.0:
            raise ValueError("Board image must have positive area.")

        if board_area / image_area < self._minimum_board_area_ratio:
            raise ValueError("Detected board area is below the configured threshold.")
