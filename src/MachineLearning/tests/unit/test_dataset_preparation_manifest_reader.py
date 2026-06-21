import json
import tempfile
import unittest
from pathlib import Path

from application.features.datasets.errors.dataset_preparation_errors import (
    PrepareDatasetArtifactCommandError,
)
from infrastructure.storage.dataset_preparation_manifest_reader import (
    DatasetPreparationManifestReader,
)
from infrastructure.storage.dataset_preparations_path_provider import (
    DatasetPreparationsPathProvider,
)
from models.dataset_source_type import DatasetSourceType


class DatasetPreparationManifestReaderTests(unittest.TestCase):
    def test_read_board_cells_index_should_read_valid_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            root_path = Path(temp_directory)
            board_root = root_path / "prep-1" / "board" / "source-a" / "Image1"
            cells_root = board_root / "cells"
            cells_root.mkdir(parents=True)
            (cells_root / "index.json").write_text(
                json.dumps(
                    [
                        {"fileName": "000.png", "label": 1},
                        {"fileName": "001.png", "label": 9},
                    ]
                ),
                encoding="utf-8",
            )

            reader = DatasetPreparationManifestReader(
                DatasetPreparationsPathProvider(str(root_path))
            )
            entries = reader.read_board_cells_index(board_root)

            self.assertEqual(len(entries), 2)
            self.assertEqual(entries[0].file_name, "000.png")
            self.assertEqual(entries[1].label, 9)

    def test_read_source_manifest_should_raise_for_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            root_path = Path(temp_directory)
            board_root = root_path / "prep-1" / "board"
            board_root.mkdir(parents=True)
            (board_root / "folders.json").write_text("{", encoding="utf-8")

            reader = DatasetPreparationManifestReader(
                DatasetPreparationsPathProvider(str(root_path))
            )

            with self.assertRaises(PrepareDatasetArtifactCommandError) as raised_error:
                reader.read_source_manifest("prep-1", DatasetSourceType.BOARD)

            self.assertEqual(
                raised_error.exception.error_type,
                "dataset_preparation_layout_invalid",
            )

    def test_read_board_cells_index_should_raise_when_more_than_81_entries(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            root_path = Path(temp_directory)
            board_root = root_path / "prep-1" / "board" / "source-a" / "Image1"
            cells_root = board_root / "cells"
            cells_root.mkdir(parents=True)
            (cells_root / "index.json").write_text(
                json.dumps(
                    [
                        {"fileName": f"{index:03d}.png", "label": 1}
                        for index in range(82)
                    ]
                ),
                encoding="utf-8",
            )

            reader = DatasetPreparationManifestReader(
                DatasetPreparationsPathProvider(str(root_path))
            )

            with self.assertRaises(PrepareDatasetArtifactCommandError) as raised_error:
                reader.read_board_cells_index(board_root)

            self.assertEqual(
                raised_error.exception.error_type,
                "dataset_preparation_layout_invalid",
            )


if __name__ == "__main__":
    unittest.main()
