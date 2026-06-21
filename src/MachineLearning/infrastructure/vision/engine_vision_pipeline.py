from __future__ import annotations

from dataclasses import dataclass
import hashlib
import logging

import numpy as np
from numpy.typing import NDArray

from infrastructure.vision.engine.models import ExperimentConfig
from infrastructure.vision.engine.preprocessing_api import (
    extract_cells_from_board_image,
    preprocess_board_image,
)

DEFAULT_ML_READY_CELL_SIZE_PX = 28
LOGGER = logging.getLogger(__name__)


class EngineVisionPipelineError(Exception):
    def __init__(self, error_type: str, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message


@dataclass(frozen=True)
class EngineCellsGridResult:
    raw_cells_grid: tuple[tuple[NDArray[np.uint8], ...], ...]
    raw_cells_flat: tuple[NDArray[np.uint8], ...]
    ml_ready_cells_grid: tuple[tuple[NDArray[np.uint8], ...], ...]
    ml_ready_cells_flat: tuple[NDArray[np.uint8], ...]
    raw_preview_image: NDArray[np.uint8]
    ml_ready_preview_image: NDArray[np.uint8]


@dataclass(frozen=True)
class EngineBoardPipelineResult:
    warped_board_image: NDArray[np.uint8]
    cells_result: EngineCellsGridResult | None
    line_family_result: object


class EngineVisionPipeline:
    def __init__(
        self,
        *,
        output_mime_type: str,
        minimum_cell_size_px: int,
        ml_ready_cell_size_px: int = DEFAULT_ML_READY_CELL_SIZE_PX,
        **experiment_config_kwargs: object,
    ) -> None:
        self._config = ExperimentConfig(**experiment_config_kwargs)
        self._output_mime_type = output_mime_type
        self._minimum_cell_size_px = minimum_cell_size_px
        self._ml_ready_cell_size_px = ml_ready_cell_size_px

    def preprocess_board(
        self,
        source_image: NDArray[np.uint8],
    ) -> EngineBoardPipelineResult:
        config_snapshot = self._build_config_snapshot()
        LOGGER.info(
            "Engine preprocess_board started: image_signature=%s config=%s",
            _build_image_signature(source_image),
            config_snapshot,
        )
        try:
            preprocess_result = preprocess_board_image(
                source_bgr=source_image,
                config=self._config,
                output_mime_type=self._output_mime_type,
            )
        except Exception as error:
            mapped_error = self._map_engine_error(error)
            LOGGER.warning(
                "Engine preprocess_board failed: error_type=%s message=%s",
                mapped_error.error_type,
                mapped_error.message,
            )
            raise mapped_error from error

        warp_result = (
            preprocess_result.line_family_result.selected_logical_line_frame_warp_result
        )
        LOGGER.info(
            "Engine preprocess_board finished: warped_board_shape=%s has_cells_grid=%s",
            tuple(preprocess_result.warped_board_image.shape),
            warp_result is not None and warp_result.cells_grid_result is not None,
        )

        return EngineBoardPipelineResult(
            warped_board_image=preprocess_result.warped_board_image,
            cells_result=(
                None
                if warp_result is None or warp_result.cells_grid_result is None
                else _build_engine_cells_grid_result(warp_result.cells_grid_result)
            ),
            line_family_result=preprocess_result.line_family_result,
        )
 
    def extract_cells_from_warped_board(
        self,
        board_image: NDArray[np.uint8],
    ) -> EngineCellsGridResult:
        config_snapshot = self._build_config_snapshot()
        LOGGER.info(
            "Engine extract_cells_from_warped_board started: "
            "board_image_signature=%s minimum_cell_size_px=%s "
            "ml_ready_cell_size_px=%s config=%s",
            _build_image_signature(board_image),
            self._minimum_cell_size_px,
            self._ml_ready_cell_size_px,
            config_snapshot,
        )
        try:
            extract_result = extract_cells_from_board_image(
                board_image=board_image,
                config=self._config,
                output_mime_type=self._output_mime_type,
                minimum_cell_size_px=self._minimum_cell_size_px,
                ml_ready_cell_size_px=self._ml_ready_cell_size_px,
            )
        except Exception as error:
            mapped_error = self._map_engine_error(error)
            LOGGER.warning(
                "Engine extract_cells_from_warped_board failed: error_type=%s message=%s",
                mapped_error.error_type,
                mapped_error.message,
            )
            raise mapped_error from error

        cells_grid_result = extract_result.cells_grid_result
        engine_result = EngineCellsGridResult(
            raw_cells_grid=cells_grid_result.cells,
            raw_cells_flat=_flatten_cells_grid(cells_grid_result.cells),
            ml_ready_cells_grid=cells_grid_result.ml_ready_cells,
            ml_ready_cells_flat=_flatten_cells_grid(
                cells_grid_result.ml_ready_cells
            ),
            raw_preview_image=cells_grid_result.preview_image,
            ml_ready_preview_image=cells_grid_result.ml_ready_preview_image,
        )
        LOGGER.info(
            "Engine extract_cells_from_warped_board finished: "
            "raw_cells_count=%s ml_ready_cells_count=%s",
            len(engine_result.raw_cells_flat),
            len(engine_result.ml_ready_cells_flat),
        )
        return engine_result

    def preprocess_and_extract_cells(
        self,
        source_image: NDArray[np.uint8],
    ) -> EngineBoardPipelineResult:
        LOGGER.info("Engine preprocess_and_extract_cells started.")
        board_result = self.preprocess_board(source_image)
        cells_result = board_result.cells_result
        if cells_result is None:
            LOGGER.info(
                "Engine preprocess_and_extract_cells falling back to explicit cell extraction."
            )
            cells_result = self.extract_cells_from_warped_board(
                board_result.warped_board_image
            )
        LOGGER.info(
            "Engine preprocess_and_extract_cells finished: warped_board_shape=%s cells_count=%s",
            tuple(board_result.warped_board_image.shape),
            len(cells_result.raw_cells_flat),
        )
        return EngineBoardPipelineResult(
            warped_board_image=board_result.warped_board_image,
            cells_result=cells_result,
            line_family_result=board_result.line_family_result,
        )

    def _build_config_snapshot(self) -> dict[str, object]:
        return {
            "adaptive_threshold_block_size": (
                self._config.adaptive_threshold_block_size
            ),
            "adaptive_threshold_c_value": self._config.adaptive_threshold_c_value,
            "raw_hough_threshold": self._config.raw_hough_threshold,
            "raw_min_line_length_ratio": self._config.raw_min_line_length_ratio,
            "raw_max_line_gap_ratio": self._config.raw_max_line_gap_ratio,
            "line_family_angle_tolerance_degrees": (
                self._config.line_family_angle_tolerance_degrees
            ),
            "warp_output_size_px": self._config.warp_output_size_px,
            "warp_output_padding_px": self._config.warp_output_padding_px,
            "warp_cell_divisions": self._config.warp_cell_divisions,
            "warp_cells_preview_gap_px": self._config.warp_cells_preview_gap_px,
        }

    def _map_engine_error(self, error: Exception) -> EngineVisionPipelineError:
        error_type = getattr(error, "error_type", None)
        if error_type in {
            "board_not_found",
            "perspective_correction_failed",
            "invalid_board_image_shape",
            "cells_extraction_failed",
        }:
            return EngineVisionPipelineError(error_type=error_type, message=str(error))
        return EngineVisionPipelineError(
            error_type="perspective_correction_failed",
            message=str(error),
        )


def build_engine_experiment_config_kwargs(
    *,
    max_display_size: int,
    adaptive_threshold_block_size: int,
    adaptive_threshold_c_value: int,
    hough_threshold: int,
    min_line_length_ratio: float,
    max_line_gap_ratio: float,
    angle_tolerance_degrees: float,
    warp_output_size_px: int,
    warp_output_padding_px: int,
    warp_cell_divisions: int,
    warp_cells_output_mime_type: str,
    warp_cells_preview_gap_px: int = 0,
) -> dict[str, object]:
    return {
        "max_display_size": max_display_size,
        "adaptive_threshold_block_size": adaptive_threshold_block_size,
        "adaptive_threshold_c_value": adaptive_threshold_c_value,
        "raw_hough_threshold": hough_threshold,
        "raw_min_line_length_ratio": min_line_length_ratio,
        "raw_max_line_gap_ratio": max_line_gap_ratio,
        "line_family_angle_tolerance_degrees": angle_tolerance_degrees,
        "warp_output_size_px": warp_output_size_px,
        "warp_output_padding_px": warp_output_padding_px,
        "warp_cell_divisions": warp_cell_divisions,
        "warp_cells_output_mime_type": warp_cells_output_mime_type,
        "warp_cells_preview_gap_px": warp_cells_preview_gap_px,
    }


def _flatten_cells_grid(
    cells_grid: tuple[tuple[NDArray[np.uint8], ...], ...],
) -> tuple[NDArray[np.uint8], ...]:
    return tuple(cell_image for row in cells_grid for cell_image in row)


def _build_engine_cells_grid_result(cells_grid_result: object) -> EngineCellsGridResult:
    raw_cells_grid = cells_grid_result.cells
    ml_ready_cells_grid = cells_grid_result.ml_ready_cells
    return EngineCellsGridResult(
        raw_cells_grid=raw_cells_grid,
        raw_cells_flat=_flatten_cells_grid(raw_cells_grid),
        ml_ready_cells_grid=ml_ready_cells_grid,
        ml_ready_cells_flat=_flatten_cells_grid(ml_ready_cells_grid),
        raw_preview_image=cells_grid_result.preview_image,
        ml_ready_preview_image=cells_grid_result.ml_ready_preview_image,
    )


def _build_image_signature(image: NDArray[np.uint8]) -> dict[str, object]:
    image_bytes = np.ascontiguousarray(image).tobytes()
    return {
        "shape": tuple(image.shape),
        "dtype": str(image.dtype),
        "sha1": hashlib.sha1(image_bytes).hexdigest()[:12],
    }
