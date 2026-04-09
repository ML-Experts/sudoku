from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from application.features.preprocessing.commands.extract_cells.extract_cells_command import (
    ExtractCellsCommand,
)
from application.features.preprocessing.commands.extract_cells.extract_cells_command_result_dto import (
    ExtractCellsCommandResultDto,
    ExtractedCellImageDto,
)
from models.cells_grid import CellsGrid
from models.preprocessing_image import PreprocessingImage

INVALID_IMAGE_PAYLOAD_MESSAGE = (
    "Niepoprawny obraz wejściowy. Sprawdź poprawność MIME oraz zawartości base64."
)
INVALID_BOARD_IMAGE_SHAPE_MESSAGE = (
    "Obraz planszy ma nieprawidłowy rozmiar lub kształt do podziału na siatkę 9x9."
)
CELLS_EXTRACTION_FAILED_MESSAGE = (
    "Nie udało się poprawnie podzielić planszy na siatkę 9x9."
)


class ImageCodec(Protocol):
    def decode_base64_image(
        self, base64_image: str, mime_type: str
    ) -> PreprocessingImage: ...

    def decode_image(self, image: PreprocessingImage) -> NDArray[np.uint8]: ...

    def encode_image(
        self, image: NDArray[np.uint8], mime_type: str
    ) -> PreprocessingImage: ...

    def encode_to_base64(self, image: PreprocessingImage) -> str: ...


class BoardCellsExtractor(Protocol):
    def extract(self, board_image: NDArray[np.uint8]) -> CellsGrid: ...


class ExtractCellsCommandError(Exception):
    def __init__(self, error_type: str, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message


class ExtractCellsCommandHandler:
    def __init__(
        self,
        image_codec: ImageCodec,
        board_cells_extractor: BoardCellsExtractor,
        allowed_input_mime_types: tuple[str, ...],
        output_mime_type: str,
        expected_grid_rows: int,
        expected_grid_cols: int,
        minimum_cell_size_px: int,
    ) -> None:
        if expected_grid_rows <= 0:
            raise ValueError("Expected grid rows must be greater than zero.")
        if expected_grid_cols <= 0:
            raise ValueError("Expected grid cols must be greater than zero.")
        if minimum_cell_size_px <= 0:
            raise ValueError(
                "Minimum cell size in pixels must be greater than zero."
            )

        self._image_codec = image_codec
        self._board_cells_extractor = board_cells_extractor
        self._allowed_input_mime_types = {
            mime_type.strip().lower() for mime_type in allowed_input_mime_types
        }
        self._output_mime_type = output_mime_type
        self._expected_grid_rows = expected_grid_rows
        self._expected_grid_cols = expected_grid_cols
        self._minimum_cell_size_px = minimum_cell_size_px

    def handle(self, command: ExtractCellsCommand) -> ExtractCellsCommandResultDto:
        self._validate_command(command)

        try:
            encoded_input_image = self._image_codec.decode_base64_image(
                base64_image=command.base64_image,
                mime_type=command.mime_type,
            )
            source_image = self._image_codec.decode_image(encoded_input_image)
        except ValueError as error:
            raise ExtractCellsCommandError(
                error_type="invalid_image_payload",
                message=INVALID_IMAGE_PAYLOAD_MESSAGE,
            ) from error

        self._validate_board_image_shape(source_image)

        try:
            cells_grid = self._board_cells_extractor.extract(source_image)
            cells_grid.validate_dimensions(
                expected_rows=self._expected_grid_rows,
                expected_cols=self._expected_grid_cols,
            )
            encoded_cells = self._encode_cells_grid(cells_grid)
        except ValueError as error:
            raise ExtractCellsCommandError(
                error_type="cells_extraction_failed",
                message=CELLS_EXTRACTION_FAILED_MESSAGE,
            ) from error

        return ExtractCellsCommandResultDto(cells=encoded_cells)

    def _validate_command(self, command: ExtractCellsCommand) -> None:
        normalized_mime_type = command.mime_type.strip().lower()
        if not normalized_mime_type:
            raise ExtractCellsCommandError(
                error_type="invalid_image_payload",
                message=INVALID_IMAGE_PAYLOAD_MESSAGE,
            )

        if normalized_mime_type not in self._allowed_input_mime_types:
            raise ExtractCellsCommandError(
                error_type="invalid_image_payload",
                message=INVALID_IMAGE_PAYLOAD_MESSAGE,
            )

        if not command.base64_image.strip():
            raise ExtractCellsCommandError(
                error_type="invalid_image_payload",
                message=INVALID_IMAGE_PAYLOAD_MESSAGE,
            )

    def _validate_board_image_shape(self, image: NDArray[np.uint8]) -> None:
        if image.size == 0:
            raise ExtractCellsCommandError(
                error_type="invalid_board_image_shape",
                message=INVALID_BOARD_IMAGE_SHAPE_MESSAGE,
            )
        if image.ndim not in (2, 3):
            raise ExtractCellsCommandError(
                error_type="invalid_board_image_shape",
                message=INVALID_BOARD_IMAGE_SHAPE_MESSAGE,
            )

        board_height, board_width = image.shape[:2]
        minimum_height = self._expected_grid_rows * self._minimum_cell_size_px
        minimum_width = self._expected_grid_cols * self._minimum_cell_size_px
        if board_height < minimum_height or board_width < minimum_width:
            raise ExtractCellsCommandError(
                error_type="invalid_board_image_shape",
                message=INVALID_BOARD_IMAGE_SHAPE_MESSAGE,
            )

    def _encode_cells_grid(
        self, cells_grid: CellsGrid
    ) -> tuple[tuple[ExtractedCellImageDto, ...], ...]:
        encoded_rows: list[tuple[ExtractedCellImageDto, ...]] = []
        for row in cells_grid.cells:
            encoded_row: list[ExtractedCellImageDto] = []
            for cell_image in row:
                encoded_cell_image = self._image_codec.encode_image(
                    cell_image,
                    self._output_mime_type,
                )
                cell_base64 = self._image_codec.encode_to_base64(
                    encoded_cell_image
                )
                encoded_row.append(
                    ExtractedCellImageDto(
                        mime_type=self._output_mime_type,
                        base64=cell_base64,
                    )
                )
            encoded_rows.append(tuple(encoded_row))

        return tuple(encoded_rows)
