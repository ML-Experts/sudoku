from pathlib import Path


class TempDatasetPathProvider:
    def __init__(self, temp_datasets_directory_path: str) -> None:
        self._temp_datasets_directory_path = Path(temp_datasets_directory_path)

    def for_name(self, dataset_name: str) -> Path:
        return self._temp_datasets_directory_path / f"{dataset_name}.npz"
