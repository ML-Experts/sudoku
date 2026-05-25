from pathlib import Path
from typing import Any

from infrastructure.storage.json_file_writer import JsonFileWriter
from models.dataset_preview_index import DatasetPreviewIndex


class DatasetPreviewIndexWriter:
    def __init__(self, json_file_writer: JsonFileWriter) -> None:
        self._json_file_writer = json_file_writer

    def write(self, path: Path, preview_index: DatasetPreviewIndex) -> None:
        self._json_file_writer.write(
            path=path,
            payload=self._serialize(preview_index),
        )

    def _serialize(
        self, preview_index: DatasetPreviewIndex
    ) -> dict[str, Any]:
        return {
            "datasetName": preview_index.dataset_name,
            "preprocessingProfile": preview_index.preprocessing_profile,
            "boardSources": [
                {
                    "sourceName": board_source.source_name,
                    "boards": [
                        {
                            "boardName": board.board_name,
                            "split": board.split,
                            "correctedBoardImageRelativePath": (
                                board.corrected_board_image_relative_path
                            ),
                            "cells": [
                                {
                                    "cellIndex": cell.cell_index,
                                    "label": cell.label,
                                    "previewImageRelativePath": (
                                        cell.preview_image_relative_path
                                    ),
                                    "includedInDataset": (
                                        cell.included_in_dataset
                                    ),
                                }
                                for cell in board.cells
                            ],
                        }
                        for board in board_source.boards
                    ],
                }
                for board_source in preview_index.board_sources
            ],
            "digitSources": [
                {
                    "sourceName": digit_source.source_name,
                    "samples": [
                        {
                            "sampleIndex": sample.sample_index,
                            "split": sample.split,
                            "label": sample.label,
                            "previewImageRelativePath": (
                                sample.preview_image_relative_path
                            ),
                            "includedInDataset": sample.included_in_dataset,
                        }
                        for sample in digit_source.samples
                    ],
                }
                for digit_source in preview_index.digit_sources
            ],
        }
