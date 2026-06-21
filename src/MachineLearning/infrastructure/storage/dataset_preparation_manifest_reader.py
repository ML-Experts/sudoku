import json
from pathlib import Path

from application.features.datasets.errors.dataset_preparation_errors import (
    DatasetPreparationLayoutInvalidError,
)
from infrastructure.storage.dataset_preparations_path_provider import (
    DatasetPreparationsPathProvider,
)
from models.dataset_preparation_board_manifest import (
    DatasetPreparationBoardManifest,
)
from models.dataset_preparation_index_entry import DatasetPreparationIndexEntry
from models.dataset_preparation_source_manifest import (
    DatasetPreparationSourceManifest,
)
from models.dataset_source_type import DatasetSourceType


class DatasetPreparationManifestReader:
    def __init__(
        self,
        path_provider: DatasetPreparationsPathProvider,
    ) -> None:
        self._path_provider = path_provider

    def read_source_manifest(
        self,
        preparation_name: str,
        source_type: DatasetSourceType,
    ) -> DatasetPreparationSourceManifest:
        if source_type == DatasetSourceType.BOARD:
            manifest_path = self._path_provider.board_folders_manifest_path(
                self._path_provider.preparation_root(preparation_name)
            )
        else:
            manifest_path = self._path_provider.digit_folders_manifest_path(
                self._path_provider.preparation_root(preparation_name)
            )

        payload = self._read_json_list(
            manifest_path=manifest_path,
            invalid_message=(
                "Przygotowanie datasetu ma niepoprawny układ plików."
            ),
        )
        source_names: list[str] = []
        for item in payload:
            if not isinstance(item, str) or not item.strip():
                raise DatasetPreparationLayoutInvalidError(
                    "Przygotowanie datasetu ma niepoprawny układ plików."
                )
            source_names.append(item)

        return DatasetPreparationSourceManifest(source_names=tuple(source_names))

    def read_board_manifest(
        self,
        source_root: Path,
    ) -> DatasetPreparationBoardManifest:
        payload = self._read_json_list(
            manifest_path=source_root / "file.json",
            invalid_message=(
                "Przygotowanie datasetu ma niepoprawny układ plików."
            ),
        )
        board_folder_names: list[str] = []
        for item in payload:
            if not isinstance(item, str) or not item.strip():
                raise DatasetPreparationLayoutInvalidError(
                    "Przygotowanie datasetu ma niepoprawny układ plików."
                )
            board_folder_names.append(item)

        return DatasetPreparationBoardManifest(
            board_folder_names=tuple(board_folder_names)
        )

    def read_board_cells_index(
        self,
        board_root: Path,
    ) -> tuple[DatasetPreparationIndexEntry, ...]:
        return self._read_index_entries(board_root / "cells" / "index.json")

    def read_digit_index(
        self,
        source_root: Path,
    ) -> tuple[DatasetPreparationIndexEntry, ...]:
        return self._read_index_entries(source_root / "index.json")

    def _read_index_entries(
        self,
        manifest_path: Path,
    ) -> tuple[DatasetPreparationIndexEntry, ...]:
        payload = self._read_json_list(
            manifest_path=manifest_path,
            invalid_message=(
                "Przygotowanie datasetu ma niepoprawny układ plików."
            ),
        )
        entries: list[DatasetPreparationIndexEntry] = []
        for item in payload:
            if not isinstance(item, dict):
                raise DatasetPreparationLayoutInvalidError(
                    "Przygotowanie datasetu ma niepoprawny układ plików."
                )

            file_name = item.get("fileName")
            label = item.get("label")
            if not self._is_valid_png_file_name(file_name):
                raise DatasetPreparationLayoutInvalidError(
                    "Przygotowanie datasetu ma niepoprawny układ plików."
                )
            if not isinstance(label, int) or label < 1 or label > 9:
                raise DatasetPreparationLayoutInvalidError(
                    "Przygotowanie datasetu ma niepoprawny układ plików."
                )

            entries.append(
                DatasetPreparationIndexEntry(file_name=file_name, label=label)
            )

        if manifest_path.name == "index.json" and "cells" in manifest_path.parts:
            if len(entries) > 81:
                raise DatasetPreparationLayoutInvalidError(
                    "Przygotowanie datasetu ma niepoprawny układ plików."
                )

        return tuple(entries)

    def _read_json_list(
        self,
        manifest_path: Path,
        invalid_message: str,
    ) -> list[object]:
        if not manifest_path.is_file():
            raise DatasetPreparationLayoutInvalidError(invalid_message)

        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise DatasetPreparationLayoutInvalidError(invalid_message) from error

        if not isinstance(payload, list):
            raise DatasetPreparationLayoutInvalidError(invalid_message)

        return payload

    def _is_valid_png_file_name(self, value: object) -> bool:
        if not isinstance(value, str) or not value.endswith(".png"):
            return False
        if "/" in value or "\\" in value:
            return False
        stem = value.removesuffix(".png")
        return bool(stem) and stem.isdigit()
