import unittest

import cv2
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
from infrastructure.vision.opencv_largest_contour_detector import (
    OpenCvBoardEdgeDetector,
)
from infrastructure.vision.opencv_perspective_transformer import (
    OpenCvPerspectiveTransformer,
)


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


class FakeGrayscaleBlurPreprocessor:
    def preprocess(self, image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        return np.zeros((10, 10), dtype=np.uint8)


class FakeAdaptiveThresholdBinarizer:
    def binarize(self, image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        return np.ones((10, 10), dtype=np.uint8)


class FakeBoardQuadDetector:
    def detect(self, image: NDArray[np.uint8]) -> BoardQuad:
        return BoardQuad(
            top_left=(0.0, 0.0),
            top_right=(10.0, 0.0),
            bottom_right=(10.0, 10.0),
            bottom_left=(0.0, 10.0),
        )


class SequentialBoardQuadDetector:
    def __init__(self, responses: list[object]) -> None:
        self._responses = responses
        self.calls = 0

    def detect(self, image: NDArray[np.uint8]) -> BoardQuad:
        self.calls += 1
        response = self._responses[
            min(self.calls - 1, len(self._responses) - 1)
        ]
        if isinstance(response, Exception):
            raise response
        return response


class FakePerspectiveTransformer:
    def transform(
        self, image: NDArray[np.uint8], board_quad: BoardQuad
    ) -> NDArray[np.uint8]:
        return np.zeros((20, 20, 3), dtype=np.uint8)


class TrackingPerspectiveTransformer:
    def __init__(self) -> None:
        self.calls = 0

    def transform(
        self, image: NDArray[np.uint8], board_quad: BoardQuad
    ) -> NDArray[np.uint8]:
        self.calls += 1
        return np.full((20, 20, 3), self.calls, dtype=np.uint8)


class PreprocessBoardCommandHandlerTests(unittest.TestCase):
    def test_handle_should_return_preprocessed_board_image(self) -> None:
        handler = PreprocessBoardCommandHandler(
            image_codec=FakeImageCodec(),
            grayscale_blur_preprocessor=FakeGrayscaleBlurPreprocessor(),
            adaptive_threshold_binarizer=FakeAdaptiveThresholdBinarizer(),
            board_quad_detector=FakeBoardQuadDetector(),
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
            board_quad_detector=FakeBoardQuadDetector(),
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

    def test_handle_should_apply_single_refinement_pass_when_enabled(self) -> None:
        image_codec = RecordingImageCodec()
        board_quad = BoardQuad(
            top_left=(0.0, 0.0),
            top_right=(10.0, 0.0),
            bottom_right=(10.0, 10.0),
            bottom_left=(0.0, 10.0),
        )
        board_quad_detector = SequentialBoardQuadDetector(
            [board_quad, board_quad]
        )
        perspective_transformer = TrackingPerspectiveTransformer()
        handler = PreprocessBoardCommandHandler(
            image_codec=image_codec,
            grayscale_blur_preprocessor=FakeGrayscaleBlurPreprocessor(),
            adaptive_threshold_binarizer=FakeAdaptiveThresholdBinarizer(),
            board_quad_detector=board_quad_detector,
            perspective_transformer=perspective_transformer,
            allowed_input_mime_types=("image/jpeg", "image/png"),
            output_mime_type="image/png",
            board_refinement_passes=1,
        )
        command = PreprocessBoardCommand(
            mime_type="image/jpeg", base64_image="aW5wdXQ="
        )

        result = handler.handle(command)

        self.assertEqual(result.mime_type, "image/png")
        self.assertEqual(board_quad_detector.calls, 2)
        self.assertEqual(perspective_transformer.calls, 2)
        self.assertEqual(int(np.max(image_codec.encoded_images[-1])), 2)

    def test_handle_should_keep_first_pass_when_refinement_fails(self) -> None:
        image_codec = RecordingImageCodec()
        board_quad = BoardQuad(
            top_left=(0.0, 0.0),
            top_right=(10.0, 0.0),
            bottom_right=(10.0, 10.0),
            bottom_left=(0.0, 10.0),
        )
        board_quad_detector = SequentialBoardQuadDetector(
            [board_quad, ValueError("No refined board found.")]
        )
        perspective_transformer = TrackingPerspectiveTransformer()
        handler = PreprocessBoardCommandHandler(
            image_codec=image_codec,
            grayscale_blur_preprocessor=FakeGrayscaleBlurPreprocessor(),
            adaptive_threshold_binarizer=FakeAdaptiveThresholdBinarizer(),
            board_quad_detector=board_quad_detector,
            perspective_transformer=perspective_transformer,
            allowed_input_mime_types=("image/jpeg", "image/png"),
            output_mime_type="image/png",
            board_refinement_passes=1,
        )
        command = PreprocessBoardCommand(
            mime_type="image/jpeg", base64_image="aW5wdXQ="
        )

        result = handler.handle(command)

        self.assertEqual(result.mime_type, "image/png")
        self.assertEqual(board_quad_detector.calls, 2)
        self.assertEqual(perspective_transformer.calls, 1)
        self.assertEqual(int(np.max(image_codec.encoded_images[-1])), 1)

    def test_handle_should_raise_error_for_invalid_base64_payload(self) -> None:
        handler = PreprocessBoardCommandHandler(
            image_codec=FakeImageCodec(should_fail_decode_base64=True),
            grayscale_blur_preprocessor=FakeGrayscaleBlurPreprocessor(),
            adaptive_threshold_binarizer=FakeAdaptiveThresholdBinarizer(),
            board_quad_detector=FakeBoardQuadDetector(),
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


class OpenCvBoardEdgeDetectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.detector = OpenCvBoardEdgeDetector(
            canny_threshold_1=50,
            canny_threshold_2=150,
            hough_threshold=80,
            min_line_length_ratio=0.2,
            max_line_gap_ratio=0.04,
            angle_tolerance_degrees=12.0,
            outer_line_window_ratio=0.1,
            minimum_board_area_ratio=0.1,
            minimum_family_segments=4,
            line_position_merge_distance_ratio=0.03,
            minimum_distinct_lines_per_family=5,
        )

    def test_detect_should_return_outer_quad_for_sudoku_like_grid(self) -> None:
        image = np.zeros((500, 700), dtype=np.uint8)
        expected_corners = (
            (150.0, 80.0),
            (520.0, 120.0),
            (560.0, 420.0),
            (110.0, 390.0),
        )

        polygon = np.array(expected_corners, dtype=np.int32)
        cv2.polylines(image, [polygon], True, 255, 3)

        for fraction in np.linspace(0, 1, 10):
            left_start = (1 - fraction) * polygon[0] + fraction * polygon[3]
            left_end = (1 - fraction) * polygon[1] + fraction * polygon[2]
            cv2.line(
                image,
                tuple(np.round(left_start).astype(int)),
                tuple(np.round(left_end).astype(int)),
                255,
                1,
            )

            top_start = (1 - fraction) * polygon[0] + fraction * polygon[1]
            top_end = (1 - fraction) * polygon[3] + fraction * polygon[2]
            cv2.line(
                image,
                tuple(np.round(top_start).astype(int)),
                tuple(np.round(top_end).astype(int)),
                255,
                1,
            )

        detected_quad = self.detector.detect(image)

        for detected_point, expected_point in zip(
            detected_quad.as_clockwise_points(),
            expected_corners,
        ):
            self.assertAlmostEqual(detected_point[0], expected_point[0], delta=55.0)
            self.assertAlmostEqual(detected_point[1], expected_point[1], delta=25.0)

    def test_detect_should_reject_plain_rectangle_without_grid(self) -> None:
        image = np.zeros((300, 500), dtype=np.uint8)
        cv2.rectangle(image, (50, 50), (450, 250), 255, 3)

        with self.assertRaises(ValueError):
            self.detector.detect(image)


class OpenCvPerspectiveTransformerTests(unittest.TestCase):
    def test_transform_should_keep_board_away_from_output_edges(self) -> None:
        image = np.zeros((100, 100), dtype=np.uint8)
        image[10:14, 10:90] = 255
        image[86:90, 10:90] = 255
        image[10:90, 10:14] = 255
        image[10:90, 86:90] = 255

        transformer = OpenCvPerspectiveTransformer(
            output_board_size=100,
            output_padding_pixels=8,
        )
        board_quad = BoardQuad(
            top_left=(10.0, 10.0),
            top_right=(89.0, 10.0),
            bottom_right=(89.0, 89.0),
            bottom_left=(10.0, 89.0),
        )

        transformed = transformer.transform(image, board_quad)

        self.assertEqual(transformed.shape, (100, 100))
        self.assertEqual(int(np.max(transformed[0, :])), 0)
        self.assertEqual(int(np.max(transformed[:, 0])), 0)
        self.assertGreater(int(np.max(transformed[7:11, :])), 0)
        self.assertGreater(int(np.max(transformed[:, 7:11])), 0)

    def test_init_should_reject_padding_that_consumes_output(self) -> None:
        with self.assertRaises(ValueError):
            OpenCvPerspectiveTransformer(
                output_board_size=16,
                output_padding_pixels=8,
            )


if __name__ == "__main__":
    unittest.main()
