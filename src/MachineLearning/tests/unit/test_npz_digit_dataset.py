import tempfile
import unittest
from pathlib import Path

import numpy as np

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


if __name__ == "__main__":
    unittest.main()
