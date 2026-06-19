from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from infrastructure.storage.dataset_preparations_path_provider import (
    DatasetPreparationsPathProvider,
)
from infrastructure.storage.filesystem_image_artifact_writer import (
    FilesystemImageArtifactWriter,
)


class DatasetPreparationArtifactWriter:
    def __init__(
        self,
        path_provider: DatasetPreparationsPathProvider,
        image_artifact_writer: FilesystemImageArtifactWriter,
    ) -> None:
        self._path_provider = path_provider
        self._image_artifact_writer = image_artifact_writer

    def write_corrected_board(
        self,
        stage_dir: Path,
        source_name: str,
        board_folder_name: str,
        corrected_board: NDArray[np.uint8],
    ) -> None:
        self._image_artifact_writer.write(
            self._path_provider.board_corrected_board_path(
                stage_dir,
                source_name,
                board_folder_name,
            ),
            corrected_board,
        )

    def write_board_cells(
        self,
        stage_dir: Path,
        source_name: str,
        board_folder_name: str,
        cell_images: tuple[NDArray[np.uint8], ...],
    ) -> None:
        for cell_index, cell_image in enumerate(cell_images):
            self._image_artifact_writer.write(
                self._path_provider.board_cell_image_path(
                    stage_dir,
                    source_name,
                    board_folder_name,
                    f"{cell_index:03d}.png",
                ),
                cell_image,
            )

    def write_digit_samples(
        self,
        stage_dir: Path,
        source_name: str,
        sample_images: tuple[NDArray[np.uint8], ...],
    ) -> None:
        for sample_index, sample_image in enumerate(sample_images):
            self._image_artifact_writer.write(
                self._path_provider.digit_sample_image_path(
                    stage_dir,
                    source_name,
                    f"{sample_index:06d}.png",
                ),
                sample_image,
            )
