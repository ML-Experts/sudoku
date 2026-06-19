import json
import tempfile
import unittest
from pathlib import Path

from application.features.datasets.dto.dataset_preparation_item_index_entry_dto import (
    DatasetPreparationItemIndexEntryDto,
)
from infrastructure.storage.dataset_preparation_manifest_writer import (
    DatasetPreparationManifestWriter,
)
from infrastructure.storage.dataset_preparations_path_provider import (
    DatasetPreparationsPathProvider,
)
from infrastructure.storage.json_file_writer import JsonFileWriter


class DatasetPreparationManifestWriterTests(unittest.TestCase):
    def test_write_board_folders_should_persist_json_array(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            stage_dir = Path(temp_directory) / "stage"
            writer = self._create_writer(temp_directory)

            writer.write_board_folders(
                stage_dir=stage_dir,
                source_names=("v1_training", "v2_training"),
            )

            payload = json.loads(
                (stage_dir / "board" / "folders.json").read_text(encoding="utf-8")
            )
            self.assertEqual(payload, ["v1_training", "v2_training"])

    def test_write_board_file_list_should_persist_board_names(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            stage_dir = Path(temp_directory) / "stage"
            writer = self._create_writer(temp_directory)

            writer.write_board_file_list(
                stage_dir=stage_dir,
                source_name="v1_training",
                board_folder_names=("Image1", "nested__Image2"),
            )

            payload = json.loads(
                (stage_dir / "board" / "v1_training" / "file.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(payload, ["Image1", "nested__Image2"])

    def test_write_digit_index_should_persist_file_name_and_label(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            stage_dir = Path(temp_directory) / "stage"
            writer = self._create_writer(temp_directory)

            writer.write_digit_index(
                stage_dir=stage_dir,
                source_name="mnist_train",
                entries=(
                    DatasetPreparationItemIndexEntryDto(
                        file_name="000000.png",
                        label=3,
                    ),
                    DatasetPreparationItemIndexEntryDto(
                        file_name="000001.png",
                        label=8,
                    ),
                ),
            )

            payload = json.loads(
                (stage_dir / "digit" / "mnist_train" / "index.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(
                payload,
                [
                    {"fileName": "000000.png", "label": 3},
                    {"fileName": "000001.png", "label": 8},
                ],
            )

    def _create_writer(self, temp_directory: str) -> DatasetPreparationManifestWriter:
        return DatasetPreparationManifestWriter(
            path_provider=DatasetPreparationsPathProvider(temp_directory),
            json_file_writer=JsonFileWriter(),
        )


if __name__ == "__main__":
    unittest.main()
