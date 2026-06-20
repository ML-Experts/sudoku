import tempfile
import unittest
from pathlib import Path

from infrastructure.storage.processed_dataset_artifact_cleanup import (
    ProcessedDatasetArtifactCleanup,
)


class ProcessedDatasetArtifactCleanupTests(unittest.TestCase):
    def test_cleanup_should_delete_existing_dataset_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            dataset_path = Path(temp_directory) / "dataset.npz"
            dataset_path.write_bytes(b"partial")

            ProcessedDatasetArtifactCleanup().cleanup(dataset_path)

            self.assertFalse(dataset_path.exists())

    def test_cleanup_should_ignore_missing_dataset_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            dataset_path = Path(temp_directory) / "dataset.npz"

            ProcessedDatasetArtifactCleanup().cleanup(dataset_path)

            self.assertFalse(dataset_path.exists())


if __name__ == "__main__":
    unittest.main()
