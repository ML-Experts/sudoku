import tempfile
import unittest
from pathlib import Path

import numpy as np

from application.features.trainings.errors.training_run_errors import (
    TrainingRunValidationError,
)
from infrastructure.training.data.npz_digit_dataset import NpzDigitDatasetLoader


class NpzDigitDatasetLoaderTests(unittest.TestCase):
    def test_load_should_read_uc12_npz_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            dataset_path = Path(temp_directory) / "dataset.npz"
            np.savez_compressed(
                dataset_path,
                x_train=np.zeros((1, 28, 28), dtype=np.float32),
                y_train=np.array([1], dtype=np.int64),
                x_val=np.empty((0, 28, 28), dtype=np.float32),
                y_val=np.empty((0,), dtype=np.int64),
                x_test=np.empty((0, 28, 28), dtype=np.float32),
                y_test=np.empty((0,), dtype=np.int64),
            )

            arrays = NpzDigitDatasetLoader().load(str(dataset_path))

            self.assertEqual(arrays.x_train.shape, (1, 28, 28))
            self.assertEqual(arrays.y_train.tolist(), [1])

    def test_load_should_reject_labels_outside_declared_class_range(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            dataset_path = Path(temp_directory) / "dataset.npz"
            np.savez_compressed(
                dataset_path,
                x_train=np.zeros((1, 28, 28), dtype=np.float32),
                y_train=np.array([9], dtype=np.int64),
                x_val=np.empty((0, 28, 28), dtype=np.float32),
                y_val=np.empty((0,), dtype=np.int64),
                x_test=np.empty((0, 28, 28), dtype=np.float32),
                y_test=np.empty((0,), dtype=np.int64),
                class_names=np.array(
                    ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
                ),
            )

            with self.assertRaises(TrainingRunValidationError) as raised_error:
                NpzDigitDatasetLoader().load(str(dataset_path))

            self.assertEqual(
                raised_error.exception.error_type,
                "processed_dataset_invalid",
            )


if __name__ == "__main__":
    unittest.main()
