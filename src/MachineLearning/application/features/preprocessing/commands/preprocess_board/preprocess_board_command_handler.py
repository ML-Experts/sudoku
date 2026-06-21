from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from application.features.preprocessing.commands.preprocess_board.preprocess_board_command import (
    PreprocessBoardCommand,
)
from application.features.preprocessing.commands.preprocess_board.preprocess_board_command_result_dto import (
    PreprocessBoardCommandResultDto,
)
from models.preprocessing_image import PreprocessingImage

INVALID_IMAGE_PAYLOAD_MESSAGE = (
    "Niepoprawny obraz wejściowy. Sprawdź poprawność MIME oraz zawartości base64."
)
BOARD_NOT_FOUND_MESSAGE = "Nie udało się wykryć krawędzi planszy Sudoku."
PERSPECTIVE_CORRECTION_FAILED_MESSAGE = (
    "Nie udało się wykonać korekcji perspektywy planszy."
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


class BoardPreprocessor(Protocol):
    def preprocess(self, image: NDArray[np.uint8]) -> NDArray[np.uint8]: ...


class PreprocessBoardCommandError(Exception):
    def __init__(self, error_type: str, message: str) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message


class PreprocessBoardCommandHandler:
    def __init__(
        self,
        image_codec: ImageCodec,
        board_preprocessor: BoardPreprocessor,
        allowed_input_mime_types: tuple[str, ...],
        output_mime_type: str,
    ) -> None:
        self._image_codec = image_codec
        self._board_preprocessor = board_preprocessor
        self._allowed_input_mime_types = {
            mime_type.strip().lower() for mime_type in allowed_input_mime_types
        }
        self._output_mime_type = output_mime_type

    def handle(
        self, command: PreprocessBoardCommand
    ) -> PreprocessBoardCommandResultDto:
        self._validate_command(command)

        try:
            encoded_input_image = self._image_codec.decode_base64_image(
                base64_image=command.base64_image,
                mime_type=command.mime_type,
            )
            source_image = self._image_codec.decode_image(encoded_input_image)
        except ValueError as error:
            raise PreprocessBoardCommandError(
                error_type="invalid_image_payload",
                message=INVALID_IMAGE_PAYLOAD_MESSAGE,
            ) from error

        try:
            board_image = self._board_preprocessor.preprocess(source_image)
        except Exception as error:
            error_type = getattr(error, "error_type", None)
            if error_type == "board_not_found":
                raise PreprocessBoardCommandError(
                    error_type="board_not_found",
                    message=BOARD_NOT_FOUND_MESSAGE,
                ) from error
            raise PreprocessBoardCommandError(
                error_type="perspective_correction_failed",
                message=PERSPECTIVE_CORRECTION_FAILED_MESSAGE,
            ) from error

        try:
            encoded_output_image = self._image_codec.encode_image(
                board_image, self._output_mime_type
            )
            board_base64 = self._image_codec.encode_to_base64(
                encoded_output_image
            )
        except ValueError as error:
            raise PreprocessBoardCommandError(
                error_type="perspective_correction_failed",
                message=PERSPECTIVE_CORRECTION_FAILED_MESSAGE,
            ) from error

        return PreprocessBoardCommandResultDto(
            mime_type=self._output_mime_type,
            base64=board_base64,
        )

    def _validate_command(self, command: PreprocessBoardCommand) -> None:
        normalized_mime_type = command.mime_type.strip().lower()
        if not normalized_mime_type:
            raise PreprocessBoardCommandError(
                error_type="invalid_image_payload",
                message=INVALID_IMAGE_PAYLOAD_MESSAGE,
            )

        if normalized_mime_type not in self._allowed_input_mime_types:
            raise PreprocessBoardCommandError(
                error_type="invalid_image_payload",
                message=INVALID_IMAGE_PAYLOAD_MESSAGE,
            )

        if not command.base64_image.strip():
            raise PreprocessBoardCommandError(
                error_type="invalid_image_payload",
                message=INVALID_IMAGE_PAYLOAD_MESSAGE,
            )
