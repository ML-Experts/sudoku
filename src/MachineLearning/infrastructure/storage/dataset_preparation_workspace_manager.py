from pathlib import Path

from infrastructure.storage.dataset_preparations_path_provider import (
    DatasetPreparationsPathProvider,
)


class DatasetPreparationWorkspaceManager:
    def __init__(
        self,
        path_provider: DatasetPreparationsPathProvider,
    ) -> None:
        self._path_provider = path_provider

    def create_stage_dir(self, preparation_name: str) -> Path:
        return self._path_provider.create_stage_dir(preparation_name)

    def promote(self, preparation_name: str, stage_dir: Path) -> Path:
        try:
            return self._path_provider.promote_stage_dir(preparation_name, stage_dir)
        except OSError as error:
            raise OSError(
                "Nie udało się sfinalizować katalogu przygotowania datasetu."
            ) from error

    def delete_stage_dir(self, stage_dir: Path) -> None:
        self._path_provider.delete_stage_dir(stage_dir)

    def delete_preparation_dir(self, preparation_name: str) -> None:
        self._path_provider.delete_preparation_dir(preparation_name)
