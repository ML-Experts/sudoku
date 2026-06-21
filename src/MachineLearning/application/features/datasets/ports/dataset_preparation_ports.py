from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from application.features.datasets.dto.dataset_preparation_item_index_entry_dto import (
    DatasetPreparationItemIndexEntryDto,
)
from infrastructure.datasets.board_dataset_scanner import BoardDatasetPair
from infrastructure.datasets.idx_dataset_loader import DigitDatasetRecord
from models.board_grid_label import BoardGridLabel
from models.cells_grid import CellsGrid


class DatasetSourceResolverPort(Protocol):
    def resolve(self, source_name: str, requested_type: str) -> object: ...


class BoardDatasetScannerPort(Protocol):
    def scan_pairs(self, source_directory: Path) -> tuple[BoardDatasetPair, ...]: ...


class BoardDatParserPort(Protocol):
    def parse(self, dat_file_path: Path) -> BoardGridLabel: ...


class IdxDatasetLoaderPort(Protocol):
    def load(
        self, images_path: Path, labels_path: Path
    ) -> tuple[DigitDatasetRecord, ...]: ...


class BoardDatasetCellExtractorPort(Protocol):
    def extract(
        self, board_image: NDArray[np.uint8]
    ) -> tuple[NDArray[np.uint8], CellsGrid]: ...


class CellPreprocessingPipelinePort(Protocol):
    def run_uint8(self, cell_image: NDArray[np.uint8]) -> NDArray[np.uint8]: ...


class DigitSamplePreparationPort(Protocol):
    def prepare_uint8(
        self,
        sample_image: NDArray[np.uint8],
    ) -> NDArray[np.uint8]: ...


class DatasetPreparationArtifactWriterPort(Protocol):
    def write_corrected_board(
        self,
        stage_dir: Path,
        source_name: str,
        board_folder_name: str,
        corrected_board: NDArray[np.uint8],
    ) -> None: ...

    def write_board_cells(
        self,
        stage_dir: Path,
        source_name: str,
        board_folder_name: str,
        cell_images: tuple[NDArray[np.uint8], ...],
    ) -> None: ...

    def write_digit_samples(
        self,
        stage_dir: Path,
        source_name: str,
        sample_images: tuple[NDArray[np.uint8], ...],
    ) -> None: ...


class DatasetPreparationManifestWriterPort(Protocol):
    def write_board_folders(
        self, stage_dir: Path, source_names: tuple[str, ...]
    ) -> None: ...

    def write_digit_folders(
        self, stage_dir: Path, source_names: tuple[str, ...]
    ) -> None: ...

    def write_board_file_list(
        self,
        stage_dir: Path,
        source_name: str,
        board_folder_names: tuple[str, ...],
    ) -> None: ...

    def write_board_cells_index(
        self,
        stage_dir: Path,
        source_name: str,
        board_folder_name: str,
        entries: tuple[DatasetPreparationItemIndexEntryDto, ...],
    ) -> None: ...

    def write_digit_index(
        self,
        stage_dir: Path,
        source_name: str,
        entries: tuple[DatasetPreparationItemIndexEntryDto, ...],
    ) -> None: ...


class DatasetPreparationWorkspaceManagerPort(Protocol):
    def create_stage_dir(self, preparation_name: str) -> Path: ...

    def promote(self, preparation_name: str, stage_dir: Path) -> Path: ...

    def delete_stage_dir(self, stage_dir: Path) -> None: ...

    def delete_preparation_dir(self, preparation_name: str) -> None: ...


class DatasetPreparationArtifactCleanupPort(Protocol):
    def cleanup(self, preparation_name: str, stage_dir: Path | None) -> None: ...


class BoardFolderNameResolverPort(Protocol):
    def resolve(
        self,
        board_name: str,
        group_key: str,
        already_used: tuple[str, ...],
    ) -> str: ...


class DatasetPreparationReportBuilderPort(Protocol):
    def build_source_report(
        self,
        name: str,
        source_type: str,
        prepared_items_count: int,
        rejected_items_count: int,
        empty_cell_count: int,
    ) -> object: ...


class UtcClockPort(Protocol):
    def now(self) -> datetime: ...
