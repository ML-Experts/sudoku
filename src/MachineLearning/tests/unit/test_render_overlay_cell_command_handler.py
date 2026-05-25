import base64
import unittest

import numpy as np
from numpy.typing import NDArray

from application.features.overlay.commands.render_overlay_cell.render_overlay_cell_command import (
    RenderOverlayCellCommand,
)
from application.features.overlay.commands.render_overlay_cell.render_overlay_cell_command_handler import (
    RenderOverlayCellCommandHandler,
)
from application.features.overlay.errors.render_overlay_cell_errors import (
    RenderOverlayCellValidationError,
)
from models.preprocessing_image import PreprocessingImage


class _ImageCodec:
    def __init__(
        self,
        decoded_image: NDArray[np.uint8] | None = None,
        should_fail_decode_base64: bool = False,
    ) -> None:
        self._decoded_image = (
            decoded_image
            if decoded_image is not None
            else np.full((32, 32, 3), 255, dtype=np.uint8)
        )
        self._should_fail_decode_base64 = should_fail_decode_base64

    def decode_base64_image(
        self,
        base64_image: str,
        mime_type: str,
    ) -> PreprocessingImage:
        if self._should_fail_decode_base64:
            raise ValueError("invalid base64")
        return PreprocessingImage(mime_type=mime_type, image_bytes=b"input")

    def decode_image(self, image: PreprocessingImage) -> NDArray[np.uint8]:
        return self._decoded_image

    def encode_image(
        self,
        image: NDArray[np.uint8],
        mime_type: str,
    ) -> PreprocessingImage:
        return PreprocessingImage(mime_type=mime_type, image_bytes=b"rendered")

    def encode_to_base64(self, image: PreprocessingImage) -> str:
        return base64.b64encode(image.image_bytes).decode("ascii")


class _TextOverlayRenderer:
    def __init__(self, should_fail: bool = False) -> None:
        self._should_fail = should_fail
        self.last_text: str | None = None

    def render_centered_text(
        self,
        image: NDArray[np.uint8],
        text: str,
    ) -> NDArray[np.uint8]:
        if self._should_fail:
            raise ValueError("cannot render")
        self.last_text = text
        rendered = image.copy()
        rendered[10:22, 10:22] = 0
        return rendered


class RenderOverlayCellCommandHandlerTests(unittest.TestCase):
    def test_handle_should_return_rendered_cell_result(self) -> None:
        renderer = _TextOverlayRenderer()
        handler = self._create_handler(text_overlay_renderer=renderer)

        result = handler.handle(self._command())

        self.assertEqual(result.mime_type, "image/png")
        self.assertEqual(result.base64, "cmVuZGVyZWQ=")
        self.assertEqual(renderer.last_text, "4")

    def test_handle_should_reject_invalid_digit(self) -> None:
        handler = self._create_handler()

        with self.assertRaises(RenderOverlayCellValidationError) as context:
            handler.handle(self._command(digit=0))

        self.assertEqual(context.exception.error_type, "invalid_digit")

    def test_handle_should_reject_invalid_cell_position(self) -> None:
        handler = self._create_handler()

        with self.assertRaises(RenderOverlayCellValidationError) as context:
            handler.handle(self._command(row_index=9))

        self.assertEqual(context.exception.error_type, "invalid_cell_position")

    def test_handle_should_reject_invalid_image_payload(self) -> None:
        handler = self._create_handler(
            image_codec=_ImageCodec(should_fail_decode_base64=True)
        )

        with self.assertRaises(RenderOverlayCellValidationError) as context:
            handler.handle(self._command())

        self.assertEqual(context.exception.error_type, "invalid_image_payload")

    def test_handle_should_reject_non_processable_cell_canvas(self) -> None:
        handler = self._create_handler(
            image_codec=_ImageCodec(
                decoded_image=np.zeros((0, 0, 3), dtype=np.uint8)
            )
        )

        with self.assertRaises(RenderOverlayCellValidationError) as context:
            handler.handle(self._command())

        self.assertEqual(
            context.exception.error_type,
            "cell_image_not_processable",
        )

    def test_handle_should_map_renderer_failure_to_overlay_render_failed(
        self,
    ) -> None:
        handler = self._create_handler(
            text_overlay_renderer=_TextOverlayRenderer(should_fail=True)
        )

        with self.assertRaises(RenderOverlayCellValidationError) as context:
            handler.handle(self._command())

        self.assertEqual(context.exception.error_type, "overlay_render_failed")

    def _create_handler(
        self,
        image_codec: _ImageCodec | None = None,
        text_overlay_renderer: _TextOverlayRenderer | None = None,
    ) -> RenderOverlayCellCommandHandler:
        return RenderOverlayCellCommandHandler(
            image_codec=image_codec or _ImageCodec(),
            text_overlay_renderer=text_overlay_renderer or _TextOverlayRenderer(),
            allowed_input_mime_types=("image/png",),
        )

    def _command(
        self,
        digit: int = 4,
        row_index: int | None = 0,
        column_index: int | None = 2,
    ) -> RenderOverlayCellCommand:
        return RenderOverlayCellCommand(
            mime_type="image/png",
            base64_image="dGVzdA==",
            digit=digit,
            row_index=row_index,
            column_index=column_index,
        )


if __name__ == "__main__":
    unittest.main()
