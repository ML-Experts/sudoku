import json
import tempfile
import unittest
from pathlib import Path

from infrastructure.storage.dataset_preview_index_writer import (
    DatasetPreviewIndexWriter,
)
from infrastructure.storage.json_file_writer import JsonFileWriter
from models.dataset_preview_index import (
    BoardCellPreviewEntry,
    BoardPreviewEntry,
    BoardSourcePreview,
    DatasetPreviewIndex,
    DigitSamplePreviewEntry,
    DigitSourcePreview,
)


class DatasetPreviewIndexWriterTests(unittest.TestCase):
    def test_write_should_serialize_preview_index_with_camel_case_keys(
        self,
    ) -> None:
        preview_index = DatasetPreviewIndex(
            dataset_name="digits-v1",
            preprocessing_profile="default-28x28-v1",
            board_sources=(
                BoardSourcePreview(
                    source_name="board-source",
                    boards=(
                        BoardPreviewEntry(
                            board_name="board-1",
                            split="train",
                            corrected_board_image_relative_path=(
                                "board/board-source/board-1/corrected-board.png"
                            ),
                            cells=(
                                BoardCellPreviewEntry(
                                    cell_index=0,
                                    label=None,
                                    preview_image_relative_path=(
                                        "board/board-source/board-1/cells/000.png"
                                    ),
                                    included_in_dataset=False,
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            digit_sources=(
                DigitSourcePreview(
                    source_name="digit-source",
                    samples=(
                        DigitSamplePreviewEntry(
                            sample_index="42",
                            split="test",
                            label=7,
                            preview_image_relative_path="digit/digit-source/42.png",
                            included_in_dataset=True,
                        ),
                    ),
                ),
            ),
        )

        with tempfile.TemporaryDirectory() as temp_directory:
            index_path = Path(temp_directory) / "index.json"
            DatasetPreviewIndexWriter(JsonFileWriter()).write(
                index_path,
                preview_index,
            )

            payload = json.loads(index_path.read_text(encoding="utf-8"))

        self.assertEqual(payload["datasetName"], "digits-v1")
        self.assertEqual(
            payload["boardSources"][0]["boards"][0][
                "correctedBoardImageRelativePath"
            ],
            "board/board-source/board-1/corrected-board.png",
        )
        self.assertEqual(
            payload["boardSources"][0]["boards"][0]["cells"][0][
                "includedInDataset"
            ],
            False,
        )
        self.assertEqual(
            payload["digitSources"][0]["samples"][0]["sampleIndex"],
            "42",
        )


if __name__ == "__main__":
    unittest.main()
