from __future__ import annotations

from pathlib import Path
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from application.features.datasets.dto.dataset_split_policy_dto import (
    DatasetSplitPolicyDto,
)
from application.features.datasets.dto.prepared_dataset_source_report_dto import (
    PreparedDatasetSourceReportDto,
)
from models.dataset_preparation_board_manifest import (
    DatasetPreparationBoardManifest,
)
from models.dataset_preparation_index_entry import DatasetPreparationIndexEntry
from models.dataset_preparation_source_manifest import (
    DatasetPreparationSourceManifest,
)
from models.dataset_source_type import DatasetSourceType
from models.dataset_split import DatasetSplit


class DatasetPreparationSourceReaderPort(Protocol):
    def resolve_source_root(
        self,
        preparation_name: str,
        source_name: str,
        source_type: DatasetSourceType,
    ) -> Path: ...


class DatasetPreparationManifestReaderPort(Protocol):
    def read_source_manifest(
        self,
        preparation_name: str,
        source_type: DatasetSourceType,
    ) -> DatasetPreparationSourceManifest: ...

    def read_board_manifest(
        self,
        source_root: Path,
    ) -> DatasetPreparationBoardManifest: ...

    def read_board_cells_index(
        self,
        board_root: Path,
    ) -> tuple[DatasetPreparationIndexEntry, ...]: ...

    def read_digit_index(
        self,
        source_root: Path,
    ) -> tuple[DatasetPreparationIndexEntry, ...]: ...


class DatasetPreparationImageReaderPort(Protocol):
    def read_board_cell(
        self,
        board_root: Path,
        file_name: str,
    ) -> NDArray[np.uint8]: ...

    def read_digit_sample(
        self,
        source_root: Path,
        file_name: str,
    ) -> NDArray[np.uint8]: ...


class SampleSplitAssignerPort(Protocol):
    def assign_split(
        self,
        split_policy: DatasetSplitPolicyDto,
        stable_key: str,
    ) -> DatasetSplit: ...


class NpzDatasetArtifactWriterPort(Protocol):
    def write(
        self,
        output_path: Path,
        x_train: NDArray[np.float32],
        y_train: NDArray[np.int64],
        x_val: NDArray[np.float32],
        y_val: NDArray[np.int64],
        x_test: NDArray[np.float32],
        y_test: NDArray[np.int64],
        class_names: tuple[str, ...],
    ) -> None: ...


class TempDatasetPathProviderPort(Protocol):
    def for_name(self, dataset_name: str) -> Path: ...


class ProcessedDatasetArtifactCleanupPort(Protocol):
    def cleanup(self, dataset_artifact_path: Path | None) -> None: ...


class PreparationReportBuilderPort(Protocol):
    def build_source_report(
        self,
        name: str,
        requested_type: str,
        detected_type: str,
        processed_sample_count: int,
        included_sample_count: int,
        empty_cell_count: int,
        rejected_sample_count: int,
        warnings: list[str] | tuple[str, ...],
    ) -> PreparedDatasetSourceReportDto: ...
