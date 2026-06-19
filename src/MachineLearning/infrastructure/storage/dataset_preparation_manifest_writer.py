from application.features.datasets.dto.dataset_preparation_item_index_entry_dto import (
    DatasetPreparationItemIndexEntryDto,
)
from infrastructure.storage.dataset_preparations_path_provider import (
    DatasetPreparationsPathProvider,
)
from infrastructure.storage.json_file_writer import JsonFileWriter


class DatasetPreparationManifestWriter:
    def __init__(
        self,
        path_provider: DatasetPreparationsPathProvider,
        json_file_writer: JsonFileWriter,
    ) -> None:
        self._path_provider = path_provider
        self._json_file_writer = json_file_writer

    def write_board_folders(
        self,
        stage_dir,
        source_names: tuple[str, ...],
    ) -> None:
        self._json_file_writer.write(
            self._path_provider.board_folders_manifest_path(stage_dir),
            list(source_names),
        )

    def write_digit_folders(
        self,
        stage_dir,
        source_names: tuple[str, ...],
    ) -> None:
        self._json_file_writer.write(
            self._path_provider.digit_folders_manifest_path(stage_dir),
            list(source_names),
        )

    def write_board_file_list(
        self,
        stage_dir,
        source_name: str,
        board_folder_names: tuple[str, ...],
    ) -> None:
        self._json_file_writer.write(
            self._path_provider.board_file_manifest_path(stage_dir, source_name),
            list(board_folder_names),
        )

    def write_board_cells_index(
        self,
        stage_dir,
        source_name: str,
        board_folder_name: str,
        entries: tuple[DatasetPreparationItemIndexEntryDto, ...],
    ) -> None:
        self._json_file_writer.write(
            self._path_provider.board_cells_index_path(
                stage_dir,
                source_name,
                board_folder_name,
            ),
            [self._serialize_index_entry(entry) for entry in entries],
        )

    def write_digit_index(
        self,
        stage_dir,
        source_name: str,
        entries: tuple[DatasetPreparationItemIndexEntryDto, ...],
    ) -> None:
        self._json_file_writer.write(
            self._path_provider.digit_index_path(stage_dir, source_name),
            [self._serialize_index_entry(entry) for entry in entries],
        )

    def _serialize_index_entry(
        self, entry: DatasetPreparationItemIndexEntryDto
    ) -> dict[str, int | str]:
        return {
            "fileName": entry.file_name,
            "label": entry.label,
        }
