import unittest

import numpy as np
from numpy.typing import NDArray

from application.features.preprocessing.commands.preprocess_board.preprocess_board_command import (
    PreprocessBoardCommand,
)
from application.features.preprocessing.commands.preprocess_board.preprocess_board_command_handler import (
    PreprocessBoardCommandError,
    PreprocessBoardCommandHandler,
)
from models.preprocessing_image import PreprocessingImage


class FakeImageCodec:
    def __init__(self, should_fail_decode_base64: bool = False) -> None:
        self._should_fail_decode_base64 = should_fail_decode_base64

    def decode_base64_image(
        self, base64_image: str, mime_type: str
    ) -> PreprocessingImage:
        if self._should_fail_decode_base64:
            raise ValueError("Invalid base64 payload.")
        return PreprocessingImage(mime_type=mime_type, image_bytes=b"input")

    def decode_image(self, image: PreprocessingImage) -> NDArray[np.uint8]:
        return np.zeros((10, 10, 3), dtype=np.uint8)

    def encode_image(
        self, image: NDArray[np.uint8], mime_type: str
    ) -> PreprocessingImage:
        return PreprocessingImage(mime_type=mime_type, image_bytes=b"output")

    def encode_to_base64(self, image: PreprocessingImage) -> str:
        return "ZW5jb2RlZA=="


class RecordingImageCodec(FakeImageCodec):
    def __init__(self) -> None:
        super().__init__()
        self.encoded_images: list[NDArray[np.uint8]] = []

    def encode_image(
        self, image: NDArray[np.uint8], mime_type: str
    ) -> PreprocessingImage:
        self.encoded_images.append(np.copy(image))
        return super().encode_image(image, mime_type)


class DistinctSourceImageCodec(FakeImageCodec):
    def decode_image(self, image: PreprocessingImage) -> NDArray[np.uint8]:
        return np.full((10, 10, 3), 7, dtype=np.uint8)


class FakeBoardPreprocessor:
    def __init__(
        self,
        result: NDArray[np.uint8] | None = None,
        error: Exception | None = None,
    ) -> None:
        self._result = (
            result if result is not None else np.zeros((20, 20, 3), dtype=np.uint8)
        )
        self._error = error
        self.inputs: list[NDArray[np.uint8]] = []

    def preprocess(self, image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        self.inputs.append(np.copy(image))
        if self._error is not None:
            raise self._error
        return self._result


class FakeEngineError(Exception):
    def __init__(self, error_type: str) -> None:
        super().__init__(error_type)
        self.error_type = error_type


class PreprocessBoardCommandHandlerTests(unittest.TestCase):
    def test_handle_should_return_preprocessed_board_image(self) -> None:
        handler = PreprocessBoardCommandHandler(
            image_codec=FakeImageCodec(),
            board_preprocessor=FakeBoardPreprocessor(),
            allowed_input_mime_types=("image/jpeg", "image/png"),
            output_mime_type="image/png",
        )
        command = PreprocessBoardCommand(
            mime_type="image/jpeg", base64_image="aW5wdXQ="
        )

        result = handler.handle(command)

        self.assertEqual(result.mime_type, "image/png")
        self.assertEqual(result.base64, "ZW5jb2RlZA==")

    def test_handle_should_preprocess_source_image(self) -> None:
        board_preprocessor = FakeBoardPreprocessor()
        handler = PreprocessBoardCommandHandler(
            image_codec=DistinctSourceImageCodec(),
            board_preprocessor=board_preprocessor,
            allowed_input_mime_types=("image/jpeg", "image/png"),
            output_mime_type="image/png",
        )

        handler.handle(
            PreprocessBoardCommand(
                mime_type="image/jpeg",
                base64_image="aW5wdXQ=",
            )
        )

        self.assertEqual(len(board_preprocessor.inputs), 1)
        self.assertEqual(board_preprocessor.inputs[0].shape, (10, 10, 3))
        self.assertEqual(int(np.max(board_preprocessor.inputs[0])), 7)

    def test_handle_should_raise_error_for_not_allowed_mime_type(self) -> None:
        handler = PreprocessBoardCommandHandler(
            image_codec=FakeImageCodec(),
            board_preprocessor=FakeBoardPreprocessor(),
            allowed_input_mime_types=("image/png",),
            output_mime_type="image/png",
        )

        with self.assertRaises(PreprocessBoardCommandError) as raised_error:
            handler.handle(
                PreprocessBoardCommand(
                    mime_type="text/plain",
                    base64_image="aW5wdXQ=",
                )
            )

        self.assertEqual(raised_error.exception.error_type, "invalid_image_payload")

    def test_handle_should_map_board_not_found_error(self) -> None:
        handler = PreprocessBoardCommandHandler(
            image_codec=FakeImageCodec(),
            board_preprocessor=FakeBoardPreprocessor(
                error=FakeEngineError("board_not_found")
            ),
            allowed_input_mime_types=("image/jpeg", "image/png"),
            output_mime_type="image/png",
        )

        with self.assertRaises(PreprocessBoardCommandError) as raised_error:
            handler.handle(
                PreprocessBoardCommand(
                    mime_type="image/png",
                    base64_image="aW5wdXQ=",
                )
            )

        self.assertEqual(raised_error.exception.error_type, "board_not_found")

    def test_handle_should_map_other_preprocessing_error(self) -> None:
        handler = PreprocessBoardCommandHandler(
            image_codec=FakeImageCodec(),
            board_preprocessor=FakeBoardPreprocessor(
                error=FakeEngineError("perspective_correction_failed")
            ),
            allowed_input_mime_types=("image/jpeg", "image/png"),
            output_mime_type="image/png",
        )

        with self.assertRaises(PreprocessBoardCommandError) as raised_error:
            handler.handle(
                PreprocessBoardCommand(
                    mime_type="image/png",
                    base64_image="aW5wdXQ=",
                )
            )

        self.assertEqual(
            raised_error.exception.error_type,
            "perspective_correction_failed",
        )

    def test_handle_should_raise_error_for_invalid_base64_payload(self) -> None:
        handler = PreprocessBoardCommandHandler(
            image_codec=FakeImageCodec(should_fail_decode_base64=True),
            board_preprocessor=FakeBoardPreprocessor(),
            allowed_input_mime_types=("image/jpeg", "image/png"),
            output_mime_type="image/png",
        )

        with self.assertRaises(PreprocessBoardCommandError) as raised_error:
            handler.handle(
                PreprocessBoardCommand(
                    mime_type="image/png",
                    base64_image="not-valid-base64",
                )
            )

        self.assertEqual(raised_error.exception.error_type, "invalid_image_payload")

    def test_handle_should_encode_result_of_board_preprocessor(self) -> None:
        image_codec = RecordingImageCodec()
        handler = PreprocessBoardCommandHandler(
            image_codec=image_codec,
            board_preprocessor=FakeBoardPreprocessor(
                result=np.full((12, 12, 3), 5, dtype=np.uint8)
            ),
            allowed_input_mime_types=("image/jpeg", "image/png"),
            output_mime_type="image/png",
        )

        handler.handle(
            PreprocessBoardCommand(
                mime_type="image/jpeg",
                base64_image="aW5wdXQ=",
            )
        )

        self.assertEqual(int(np.max(image_codec.encoded_images[-1])), 5)


if __name__ == "__main__":
    unittest.main()
