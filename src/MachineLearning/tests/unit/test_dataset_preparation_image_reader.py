import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from application.features.datasets.errors.dataset_preparation_errors import (
    PrepareDatasetArtifactCommandError,
)
from infrastructure.storage.dataset_preparation_image_reader import (
    DatasetPreparationImageReader,
)


class DatasetPreparationImageReaderTests(unittest.TestCase):
    def test_read_digit_sample_should_read_28x28_image(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            source_root = Path(temp_directory)
            image_path = source_root / "000000.png"
            cv2.imwrite(str(image_path), np.full((28, 28), 255, dtype=np.uint8))

            image = DatasetPreparationImageReader().read_digit_sample(
                source_root=source_root,
                file_name="000000.png",
            )

            self.assertEqual(image.shape, (28, 28))

    def test_read_digit_sample_should_raise_when_file_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            with self.assertRaises(PrepareDatasetArtifactCommandError) as raised_error:
                DatasetPreparationImageReader().read_digit_sample(
                    source_root=Path(temp_directory),
                    file_name="000000.png",
                )

            self.assertEqual(
                raised_error.exception.error_type,
                "dataset_source_invalid",
            )

    def test_read_board_cell_should_raise_for_invalid_size(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            board_root = Path(temp_directory)
            cells_root = board_root / "cells"
            cells_root.mkdir()
            cv2.imwrite(
                str(cells_root / "000.png"),
                np.full((27, 28), 255, dtype=np.uint8),
            )

            with self.assertRaises(PrepareDatasetArtifactCommandError) as raised_error:
                DatasetPreparationImageReader().read_board_cell(
                    board_root=board_root,
                    file_name="000.png",
                )

            self.assertEqual(
                raised_error.exception.error_type,
                "dataset_source_invalid",
            )


if __name__ == "__main__":
    unittest.main()
