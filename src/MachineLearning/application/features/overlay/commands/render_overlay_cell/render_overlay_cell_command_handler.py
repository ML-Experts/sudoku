import logging
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from application.features.overlay.commands.render_overlay_cell.render_overlay_cell_command import (
    RenderOverlayCellCommand,
)
from application.features.overlay.commands.render_overlay_cell.render_overlay_cell_command_result_dto import (
    RenderOverlayCellCommandResultDto,
)
from application.features.overlay.dto.rendered_overlay_cell_result_dto import (
    RenderedOverlayCellResultDto,
)
from application.features.overlay.errors.render_overlay_cell_errors import (
    RenderOverlayCellValidationError,
)
from models.overlay_cell_position import OverlayCellPosition
from models.overlay_digit import OverlayDigit
from models.preprocessing_image import PreprocessingImage

INVALID_IMAGE_PAYLOAD_MESSAGE = (
    "Niepoprawny obraz wejściowy. Sprawdź poprawność MIME oraz zawartości base64."
)
CELL_IMAGE_NOT_PROCESSABLE_MESSAGE = (
    "Nie udało się wykorzystać obrazu komórki jako canvasa overlay."
)
OVERLAY_RENDER_FAILED_MESSAGE = "Nie udało się wyrenderować cyfry na komórce."

_logger = logging.getLogger(__name__)


class ImageCodec(Protocol):
    def decode_base64_image(
        self,
        base64_image: str,
        mime_type: str,
    ) -> PreprocessingImage: ...

    def decode_image(self, image: PreprocessingImage) -> NDArray[np.uint8]: ...

    def encode_image(
        self,
        image: NDArray[np.uint8],
        mime_type: str,
    ) -> PreprocessingImage: ...

    def encode_to_base64(self, image: PreprocessingImage) -> str: ...


class TextOverlayRenderer(Protocol):
    def render_centered_text(
        self,
        image: NDArray[np.uint8],
        text: str,
    ) -> NDArray[np.uint8]: ...


class RenderOverlayCellCommandHandler:
    def __init__(
        self,
        image_codec: ImageCodec,
        text_overlay_renderer: TextOverlayRenderer,
        allowed_input_mime_types: tuple[str, ...],
    ) -> None:
        self._image_codec = image_codec
        self._text_overlay_renderer = text_overlay_renderer
        self._allowed_input_mime_types = {
            mime_type.strip().lower() for mime_type in allowed_input_mime_types
        }

    def handle(
        self,
        command: RenderOverlayCellCommand,
    ) -> RenderOverlayCellCommandResultDto:
        _logger.info(
            "Overlay cell request received for digit=%s row=%s col=%s mime=%s",
            command.digit,
            command.row_index,
            command.column_index,
            command.mime_type,
        )

        self._validate_command(command)
        overlay_digit = self._build_overlay_digit(command.digit)
        self._build_overlay_cell_position(
            row_index=command.row_index,
            column_index=command.column_index,
        )

        decoded_image = self._decode_cell_image(command)
        self._validate_decoded_image(decoded_image)
        rendered_image = self._render_digit_overlay(
            decoded_image=decoded_image,
            digit=overlay_digit,
        )
        result = self._encode_response_image(
            rendered_image=rendered_image,
            mime_type=command.mime_type,
        )
        _logger.info(
            "Overlay cell render succeeded for digit=%s row=%s col=%s",
            command.digit,
            command.row_index,
            command.column_index,
        )
        return self._to_command_result(result)

    def _validate_command(self, command: RenderOverlayCellCommand) -> None:
        normalized_mime_type = command.mime_type.strip().lower()
        if (
            not normalized_mime_type
            or normalized_mime_type not in self._allowed_input_mime_types
        ):
            _logger.warning("Overlay cell rejected due to invalid mime type.")
            raise RenderOverlayCellValidationError(
                "invalid_image_payload",
                INVALID_IMAGE_PAYLOAD_MESSAGE,
            )
        if not command.base64_image.strip():
            _logger.warning("Overlay cell rejected due to empty base64 payload.")
            raise RenderOverlayCellValidationError(
                "invalid_image_payload",
                INVALID_IMAGE_PAYLOAD_MESSAGE,
            )

    def _build_overlay_digit(self, digit: int) -> OverlayDigit:
        try:
            return OverlayDigit(value=digit)
        except ValueError as error:
            _logger.warning("Overlay cell rejected due to invalid digit.")
            raise RenderOverlayCellValidationError(
                "invalid_digit",
                "Pole digit musi zawierać cyfrę od 1 do 9.",
            ) from error

    def _build_overlay_cell_position(
        self,
        row_index: int | None,
        column_index: int | None,
    ) -> OverlayCellPosition:
        try:
            return OverlayCellPosition(
                row_index=row_index,
                column_index=column_index,
            )
        except ValueError as error:
            _logger.warning(
                "Overlay cell rejected due to invalid row/column range."
            )
            raise RenderOverlayCellValidationError(
                "invalid_cell_position",
                "rowIndex i columnIndex muszą mieścić się w zakresie 0..8.",
            ) from error

    def _decode_cell_image(
        self,
        command: RenderOverlayCellCommand,
    ) -> NDArray[np.uint8]:
        try:
            encoded_input_image = self._image_codec.decode_base64_image(
                base64_image=command.base64_image,
                mime_type=command.mime_type,
            )
            return self._image_codec.decode_image(encoded_input_image)
        except ValueError as error:
            _logger.warning("Overlay cell rejected due to invalid image payload.")
            raise RenderOverlayCellValidationError(
                "invalid_image_payload",
                INVALID_IMAGE_PAYLOAD_MESSAGE,
            ) from error

    def _validate_decoded_image(self, decoded_image: NDArray[np.uint8]) -> None:
        if decoded_image.size == 0:
            raise RenderOverlayCellValidationError(
                "cell_image_not_processable",
                CELL_IMAGE_NOT_PROCESSABLE_MESSAGE,
            )

        if decoded_image.ndim == 2:
            height, width = decoded_image.shape
            channels = 1
        elif decoded_image.ndim == 3:
            height, width, channels = decoded_image.shape
        else:
            raise RenderOverlayCellValidationError(
                "cell_image_not_processable",
                CELL_IMAGE_NOT_PROCESSABLE_MESSAGE,
            )

        if height <= 0 or width <= 0 or channels not in (1, 3, 4):
            raise RenderOverlayCellValidationError(
                "cell_image_not_processable",
                CELL_IMAGE_NOT_PROCESSABLE_MESSAGE,
            )

    def _render_digit_overlay(
        self,
        decoded_image: NDArray[np.uint8],
        digit: OverlayDigit,
    ) -> NDArray[np.uint8]:
        try:
            return self._text_overlay_renderer.render_centered_text(
                image=decoded_image,
                text=str(digit.value),
            )
        except ValueError as error:
            _logger.error("Overlay renderer failed due to invalid canvas.")
            raise RenderOverlayCellValidationError(
                "overlay_render_failed",
                OVERLAY_RENDER_FAILED_MESSAGE,
            ) from error

    def _encode_response_image(
        self,
        rendered_image: NDArray[np.uint8],
        mime_type: str,
    ) -> RenderedOverlayCellResultDto:
        try:
            encoded_image = self._image_codec.encode_image(
                image=rendered_image,
                mime_type=mime_type,
            )
        except ValueError as error:
            _logger.error("Overlay renderer failed during image encoding.")
            raise RenderOverlayCellValidationError(
                "overlay_render_failed",
                OVERLAY_RENDER_FAILED_MESSAGE,
            ) from error

        return RenderedOverlayCellResultDto(
            mime_type=encoded_image.mime_type,
            base64=self._image_codec.encode_to_base64(encoded_image),
        )

    def _to_command_result(
        self,
        result: RenderedOverlayCellResultDto,
    ) -> RenderOverlayCellCommandResultDto:
        return RenderOverlayCellCommandResultDto(
            mime_type=result.mime_type,
            base64=result.base64,
        )
