import base64
import unittest

import numpy as np
from numpy.typing import NDArray

from application.features.preprocessing.commands.extract_cells.extract_cells_command import (
    ExtractCellsCommand,
)
from application.features.preprocessing.commands.extract_cells.extract_cells_command_handler import (
    ExtractCellsCommandError,
    ExtractCellsCommandHandler,
)
from models.cells_grid import CellsGrid
from models.preprocessing_image import PreprocessingImage


class FakeImageCodec:
    def __init__(
        self,
        decoded_image: NDArray[np.uint8] | None = None,
        should_fail_decode_base64: bool = False,
    ) -> None:
        self._decoded_image = (
            decoded_image
            if decoded_image is not None
            else np.zeros((90, 90, 3), dtype=np.uint8)
        )
        self._should_fail_decode_base64 = should_fail_decode_base64
        self._encoded_cell_counter = 0

    def decode_base64_image(
        self, base64_image: str, mime_type: str
    ) -> PreprocessingImage:
        if self._should_fail_decode_base64:
            raise ValueError("Invalid base64 payload.")
        return PreprocessingImage(mime_type=mime_type, image_bytes=b"input")

    def decode_image(self, image: PreprocessingImage) -> NDArray[np.uint8]:
        return self._decoded_image

    def encode_image(
        self, image: NDArray[np.uint8], mime_type: str
    ) -> PreprocessingImage:
        self._encoded_cell_counter += 1
        return PreprocessingImage(
            mime_type=mime_type,
            image_bytes=f"cell-{self._encoded_cell_counter}".encode("ascii"),
        )

    def encode_to_base64(self, image: PreprocessingImage) -> str:
        return base64.b64encode(image.image_bytes).decode("ascii")


class FakeBoardCellsExtractor:
    def __init__(
        self,
        rows: int = 9,
        cols: int = 9,
        error: Exception | None = None,
    ) -> None:
        self._rows = rows
        self._cols = cols
        self._error = error

    def extract(self, board_image: NDArray[np.uint8]) -> CellsGrid:
        if self._error is not None:
            raise self._error
        return CellsGrid.from_rows(
            [
                [
                    np.full((10, 10), row_index + col_index, dtype=np.uint8)
                    for col_index in range(self._cols)
                ]
                for row_index in range(self._rows)
            ]
        )


class FakeEngineError(Exception):
    def __init__(self, error_type: str) -> None:
        super().__init__(error_type)
        self.error_type = error_type


class ExtractCellsCommandHandlerTests(unittest.TestCase):
    def test_handle_should_return_cells_grid_result(self) -> None:
        handler = ExtractCellsCommandHandler(
            image_codec=FakeImageCodec(),
            board_cells_extractor=FakeBoardCellsExtractor(rows=9, cols=9),
            allowed_input_mime_types=("image/jpeg", "image/png"),
            output_mime_type="image/png",
            expected_grid_rows=9,
            expected_grid_cols=9,
        )
        command = ExtractCellsCommand(
            mime_type="image/png",
            base64_image="aW5wdXQ=",
        )

        result = handler.handle(command)

        self.assertEqual(len(result.cells), 9)
        self.assertTrue(all(len(row) == 9 for row in result.cells))
        self.assertEqual(result.cells[0][0].mime_type, "image/png")
        self.assertEqual(result.cells[0][0].base64, "Y2VsbC0x")
        self.assertEqual(result.cells[8][8].base64, "Y2VsbC04MQ==")

    def test_handle_should_raise_error_for_non_9x9_grid(self) -> None:
        handler = ExtractCellsCommandHandler(
            image_codec=FakeImageCodec(),
            board_cells_extractor=FakeBoardCellsExtractor(rows=8, cols=9),
            allowed_input_mime_types=("image/jpeg", "image/png"),
            output_mime_type="image/png",
            expected_grid_rows=9,
            expected_grid_cols=9,
        )
        command = ExtractCellsCommand(
            mime_type="image/png",
            base64_image="aW5wdXQ=",
        )

        with self.assertRaises(ExtractCellsCommandError) as raised_error:
            handler.handle(command)

        self.assertEqual(
            raised_error.exception.error_type, "cells_extraction_failed"
        )

    def test_handle_should_raise_error_for_small_board_image(self) -> None:
        handler = ExtractCellsCommandHandler(
            image_codec=FakeImageCodec(),
            board_cells_extractor=FakeBoardCellsExtractor(
                error=FakeEngineError("invalid_board_image_shape")
            ),
            allowed_input_mime_types=("image/jpeg", "image/png"),
            output_mime_type="image/png",
            expected_grid_rows=9,
            expected_grid_cols=9,
        )
        command = ExtractCellsCommand(
            mime_type="image/png",
            base64_image="aW5wdXQ=",
        )

        with self.assertRaises(ExtractCellsCommandError) as raised_error:
            handler.handle(command)

        self.assertEqual(
            raised_error.exception.error_type, "invalid_board_image_shape"
        )

    def test_handle_should_raise_error_for_invalid_base64_payload(
        self,
    ) -> None:
        handler = ExtractCellsCommandHandler(
            image_codec=FakeImageCodec(should_fail_decode_base64=True),
            board_cells_extractor=FakeBoardCellsExtractor(rows=9, cols=9),
            allowed_input_mime_types=("image/jpeg", "image/png"),
            output_mime_type="image/png",
            expected_grid_rows=9,
            expected_grid_cols=9,
        )
        command = ExtractCellsCommand(
            mime_type="image/png",
            base64_image="not-valid-base64",
        )

        with self.assertRaises(ExtractCellsCommandError) as raised_error:
            handler.handle(command)

        self.assertEqual(
            raised_error.exception.error_type, "invalid_image_payload"
        )


if __name__ == "__main__":
    unittest.main()
