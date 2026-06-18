from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .binary import (
    apply_directional_close_repair,
    apply_gaussian_threshold,
    apply_median_denoise,
    apply_soft_component_cleanup,
)
from .detection import RawLineFamilyResult, detect_line_families
from .display import resize_for_display
from .logical_line_frame_cell_preprocessing import DEFAULT_OUTPUT_SIZE_PX
from .logical_line_frame_cells import (
    LogicalLineFrameCellsGridResult,
    build_warped_frame_cells_grid_result,
)
from .models import ExperimentConfig
from .preprocessing_api_codec import (
    decode_image_api_entry,
    encode_image_api_response,
)
from .preprocessing_api_models import (
    CellsGridApiResponse,
    ImageApiEntry,
    ImageApiResponse,
)

INVALID_IMAGE_PAYLOAD_MESSAGE = (
    "Niepoprawny obraz wejściowy. Sprawdź poprawność MIME oraz zawartości base64."
)
BOARD_NOT_FOUND_MESSAGE = "Nie udało się wykryć krawędzi planszy Sudoku."
PERSPECTIVE_CORRECTION_FAILED_MESSAGE = (
    "Nie udało się wykonać korekcji perspektywy planszy."
)
INVALID_BOARD_IMAGE_SHAPE_MESSAGE = (
    "Obraz planszy ma nieprawidłowy rozmiar lub kształt do podziału na siatkę 9x9."
)
CELLS_EXTRACTION_FAILED_MESSAGE = (
    "Nie udało się poprawnie podzielić planszy na siatkę 9x9."
)


class PreprocessBoardApiError(Exception):
    def __init__(self, error_type: str, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message


class ExtractCellsApiError(Exception):
    def __init__(self, error_type: str, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message


@dataclass(frozen=True, slots=True)
class BoardPreprocessingArtifacts:
    display_bgr: np.ndarray
    gray_image: np.ndarray
    denoised_image: np.ndarray
    binary_image: np.ndarray
    min_component_area_px: int
    clean_binary: np.ndarray
    repaired_binary: np.ndarray


@dataclass(frozen=True, slots=True)
class PreprocessBoardApiResult:
    api_response: ImageApiResponse
    warped_board_image: np.ndarray
    line_family_result: RawLineFamilyResult
    preprocessing_artifacts: BoardPreprocessingArtifacts


@dataclass(frozen=True, slots=True)
class ExtractCellsApiResult:
    api_response: CellsGridApiResponse
    cells_grid_result: LogicalLineFrameCellsGridResult


def preprocess_board_image_entry(
    image_entry: ImageApiEntry,
    config: ExperimentConfig,
    output_mime_type: str = "image/png",
) -> PreprocessBoardApiResult:
    try:
        source_bgr = decode_image_api_entry(image_entry)
    except ValueError as error:
        raise PreprocessBoardApiError(
            error_type="invalid_image_payload",
            message=INVALID_IMAGE_PAYLOAD_MESSAGE,
        ) from error

    return preprocess_board_image(
        source_bgr=source_bgr,
        config=config,
        output_mime_type=output_mime_type,
    )


def preprocess_board_image(
    source_bgr: np.ndarray,
    config: ExperimentConfig,
    output_mime_type: str = "image/png",
) -> PreprocessBoardApiResult:
    preprocessing_artifacts = build_board_preprocessing_artifacts(
        source_bgr=source_bgr,
        config=config,
    )
    try:
        line_family_result = detect_line_families(
            preprocessing_artifacts.clean_binary,
            config,
            pixel_connection_binary_image=preprocessing_artifacts.repaired_binary,
            warp_source_image=preprocessing_artifacts.display_bgr,
        )
    except ValueError as error:
        raise PreprocessBoardApiError(
            error_type="perspective_correction_failed",
            message=PERSPECTIVE_CORRECTION_FAILED_MESSAGE,
        ) from error
    warp_result = line_family_result.selected_logical_line_frame_warp_result
    if warp_result is None:
        raise PreprocessBoardApiError(
            error_type="board_not_found",
            message=BOARD_NOT_FOUND_MESSAGE,
        )

    try:
        api_response = encode_image_api_response(
            image=warp_result.warped_image,
            mime_type=output_mime_type,
        )
    except ValueError as error:
        raise PreprocessBoardApiError(
            error_type="perspective_correction_failed",
            message=PERSPECTIVE_CORRECTION_FAILED_MESSAGE,
        ) from error

    return PreprocessBoardApiResult(
        api_response=api_response,
        warped_board_image=warp_result.warped_image,
        line_family_result=line_family_result,
        preprocessing_artifacts=preprocessing_artifacts,
    )


def build_board_preprocessing_artifacts(
    source_bgr: np.ndarray,
    config: ExperimentConfig,
) -> BoardPreprocessingArtifacts:
    display_bgr = resize_for_display(source_bgr, config.max_display_size)
    gray_image = cv2.cvtColor(display_bgr, cv2.COLOR_BGR2GRAY)
    denoised_image = apply_median_denoise(gray_image, config)
    binary_image = apply_gaussian_threshold(denoised_image, config)
    min_component_area_px, clean_binary = apply_soft_component_cleanup(
        binary_image,
        config,
    )
    repaired_binary = apply_directional_close_repair(clean_binary, config)
    return BoardPreprocessingArtifacts(
        display_bgr=display_bgr,
        gray_image=gray_image,
        denoised_image=denoised_image,
        binary_image=binary_image,
        min_component_area_px=min_component_area_px,
        clean_binary=clean_binary,
        repaired_binary=repaired_binary,
    )


def extract_cells_from_board_image_entry(
    image_entry: ImageApiEntry,
    config: ExperimentConfig,
    output_mime_type: str | None = None,
    minimum_cell_size_px: int = 8,
    ml_ready_cell_size_px: int = DEFAULT_OUTPUT_SIZE_PX,
) -> ExtractCellsApiResult:
    try:
        board_image = decode_image_api_entry(image_entry)
    except ValueError as error:
        raise ExtractCellsApiError(
            error_type="invalid_image_payload",
            message=INVALID_IMAGE_PAYLOAD_MESSAGE,
        ) from error

    return extract_cells_from_board_image(
        board_image=board_image,
        config=config,
        output_mime_type=output_mime_type,
        minimum_cell_size_px=minimum_cell_size_px,
        ml_ready_cell_size_px=ml_ready_cell_size_px,
    )


def extract_cells_from_board_image(
    board_image: np.ndarray,
    config: ExperimentConfig,
    output_mime_type: str | None = None,
    minimum_cell_size_px: int = 8,
    ml_ready_cell_size_px: int = DEFAULT_OUTPUT_SIZE_PX,
) -> ExtractCellsApiResult:
    _validate_board_image_shape(
        board_image=board_image,
        grid_size=config.warp_cell_divisions,
        minimum_cell_size_px=minimum_cell_size_px,
    )

    effective_output_mime_type = output_mime_type or config.warp_cells_output_mime_type
    try:
        cells_grid_result = build_warped_frame_cells_grid_result(
            board_image=board_image,
            output_mime_type=effective_output_mime_type,
            grid_rows=config.warp_cell_divisions,
            grid_cols=config.warp_cell_divisions,
            preview_gap_px=config.warp_cells_preview_gap_px,
            ml_ready_cell_size_px=ml_ready_cell_size_px,
            ml_ready_adaptive_block_size=config.adaptive_threshold_block_size,
            ml_ready_adaptive_c=config.adaptive_threshold_c_value,
        )
    except ValueError as error:
        raise ExtractCellsApiError(
            error_type="cells_extraction_failed",
            message=CELLS_EXTRACTION_FAILED_MESSAGE,
        ) from error

    return ExtractCellsApiResult(
        api_response=cells_grid_result.api_response,
        cells_grid_result=cells_grid_result,
    )


def _validate_board_image_shape(
    board_image: np.ndarray,
    grid_size: int,
    minimum_cell_size_px: int,
) -> None:
    if minimum_cell_size_px <= 0:
        raise ValueError("minimum_cell_size_px must be positive.")
    if board_image.size == 0:
        raise ExtractCellsApiError(
            error_type="invalid_board_image_shape",
            message=INVALID_BOARD_IMAGE_SHAPE_MESSAGE,
        )
    if board_image.ndim not in (2, 3):
        raise ExtractCellsApiError(
            error_type="invalid_board_image_shape",
            message=INVALID_BOARD_IMAGE_SHAPE_MESSAGE,
        )

    board_height, board_width = board_image.shape[:2]
    minimum_height = grid_size * minimum_cell_size_px
    minimum_width = grid_size * minimum_cell_size_px
    if board_height < minimum_height or board_width < minimum_width:
        raise ExtractCellsApiError(
            error_type="invalid_board_image_shape",
            message=INVALID_BOARD_IMAGE_SHAPE_MESSAGE,
        )


__all__ = [
    "BOARD_NOT_FOUND_MESSAGE",
    "BoardPreprocessingArtifacts",
    "CELLS_EXTRACTION_FAILED_MESSAGE",
    "ExtractCellsApiError",
    "ExtractCellsApiResult",
    "INVALID_BOARD_IMAGE_SHAPE_MESSAGE",
    "INVALID_IMAGE_PAYLOAD_MESSAGE",
    "PERSPECTIVE_CORRECTION_FAILED_MESSAGE",
    "PreprocessBoardApiError",
    "PreprocessBoardApiResult",
    "build_board_preprocessing_artifacts",
    "extract_cells_from_board_image",
    "extract_cells_from_board_image_entry",
    "preprocess_board_image",
    "preprocess_board_image_entry",
]
