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
from models.board_quad import BoardQuad
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


class FakeGrayscaleBlurPreprocessor:
    def preprocess(self, image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        return np.zeros((10, 10), dtype=np.uint8)


class FakeAdaptiveThresholdBinarizer:
    def binarize(self, image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        return np.ones((10, 10), dtype=np.uint8)


class FakeLargestContourDetector:
    def detect(self, image: NDArray[np.uint8]) -> BoardQuad:
        return BoardQuad(
            top_left=(0.0, 0.0),
            top_right=(10.0, 0.0),
            bottom_right=(10.0, 10.0),
            bottom_left=(0.0, 10.0),
        )


class FakePerspectiveTransformer:
    def transform(
        self, image: NDArray[np.uint8], board_quad: BoardQuad
    ) -> NDArray[np.uint8]:
        return np.zeros((20, 20, 3), dtype=np.uint8)


class PreprocessBoardCommandHandlerTests(unittest.TestCase):
    def test_handle_should_return_preprocessed_board_image(self) -> None:
        handler = PreprocessBoardCommandHandler(
            image_codec=FakeImageCodec(),
            grayscale_blur_preprocessor=FakeGrayscaleBlurPreprocessor(),
            adaptive_threshold_binarizer=FakeAdaptiveThresholdBinarizer(),
            largest_contour_detector=FakeLargestContourDetector(),
            perspective_transformer=FakePerspectiveTransformer(),
            allowed_input_mime_types=("image/jpeg", "image/png"),
            output_mime_type="image/png",
        )
        command = PreprocessBoardCommand(
            mime_type="image/jpeg", base64_image="aW5wdXQ="
        )

        result = handler.handle(command)

        self.assertEqual(result.mime_type, "image/png")
        self.assertEqual(result.base64, "ZW5jb2RlZA==")

    def test_handle_should_raise_error_for_not_allowed_mime_type(self) -> None:
        handler = PreprocessBoardCommandHandler(
            image_codec=FakeImageCodec(),
            grayscale_blur_preprocessor=FakeGrayscaleBlurPreprocessor(),
            adaptive_threshold_binarizer=FakeAdaptiveThresholdBinarizer(),
            largest_contour_detector=FakeLargestContourDetector(),
            perspective_transformer=FakePerspectiveTransformer(),
            allowed_input_mime_types=("image/png",),
            output_mime_type="image/png",
        )
        command = PreprocessBoardCommand(
            mime_type="text/plain", base64_image="aW5wdXQ="
        )

        with self.assertRaises(PreprocessBoardCommandError) as raised_error:
            handler.handle(command)

        self.assertEqual(raised_error.exception.error_type, "invalid_image_payload")

    def test_handle_should_raise_error_for_invalid_base64_payload(self) -> None:
        handler = PreprocessBoardCommandHandler(
            image_codec=FakeImageCodec(should_fail_decode_base64=True),
            grayscale_blur_preprocessor=FakeGrayscaleBlurPreprocessor(),
            adaptive_threshold_binarizer=FakeAdaptiveThresholdBinarizer(),
            largest_contour_detector=FakeLargestContourDetector(),
            perspective_transformer=FakePerspectiveTransformer(),
            allowed_input_mime_types=("image/jpeg", "image/png"),
            output_mime_type="image/png",
        )
        command = PreprocessBoardCommand(
            mime_type="image/png", base64_image="not-valid-base64"
        )

        with self.assertRaises(PreprocessBoardCommandError) as raised_error:
            handler.handle(command)

        self.assertEqual(raised_error.exception.error_type, "invalid_image_payload")


if __name__ == "__main__":
    unittest.main()
