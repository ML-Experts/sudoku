from pathlib import Path

from application.features.datasets.errors.dataset_preparation_errors import (
    DatasetPreparationNotFoundError,
    DatasetPreparationSourceNotFoundError,
)
from infrastructure.storage.dataset_preparation_manifest_reader import (
    DatasetPreparationManifestReader,
)
from infrastructure.storage.dataset_preparations_path_provider import (
    DatasetPreparationsPathProvider,
)
from models.dataset_source_type import DatasetSourceType


class DatasetPreparationSourceReader:
    def __init__(
        self,
        path_provider: DatasetPreparationsPathProvider,
        manifest_reader: DatasetPreparationManifestReader,
    ) -> None:
        self._path_provider = path_provider
        self._manifest_reader = manifest_reader

    def resolve_source_root(
        self,
        preparation_name: str,
        source_name: str,
        source_type: DatasetSourceType,
    ) -> Path:
        preparation_root = self._path_provider.preparation_root(preparation_name)
        if not preparation_root.is_dir():
            raise DatasetPreparationNotFoundError(preparation_name)

        source_manifest = self._manifest_reader.read_source_manifest(
            preparation_name=preparation_name,
            source_type=source_type,
        )
        if source_name not in source_manifest.source_names:
            raise DatasetPreparationSourceNotFoundError(
                preparation_name=preparation_name,
                source_name=source_name,
                source_type=source_type.value,
            )

        if source_type == DatasetSourceType.BOARD:
            source_root = self._path_provider.board_source_root(
                preparation_name=preparation_name,
                source_name=source_name,
            )
        else:
            source_root = self._path_provider.digit_source_root(
                preparation_name=preparation_name,
                source_name=source_name,
            )

        if not source_root.is_dir():
            raise DatasetPreparationSourceNotFoundError(
                preparation_name=preparation_name,
                source_name=source_name,
                source_type=source_type.value,
            )

        return source_root
