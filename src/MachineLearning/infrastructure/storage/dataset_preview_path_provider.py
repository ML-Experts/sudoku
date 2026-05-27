import shutil
from pathlib import Path


class DatasetPreviewPathProvider:
    def __init__(
        self,
        previews_directory_path: str,
        index_file_name: str = "index.json",
    ) -> None:
        self._previews_directory_path = Path(previews_directory_path)
        self._index_file_name = index_file_name

    def dataset_root(self, dataset_name: str) -> Path:
        return self._previews_directory_path / dataset_name

    def create_stage_dir(self, dataset_name: str) -> Path:
        stage_dir = self._previews_directory_path / f".{dataset_name}.staging"
        if stage_dir.exists():
            shutil.rmtree(stage_dir)
        stage_dir.mkdir(parents=True, exist_ok=True)
        return stage_dir

    def promote_stage_dir(self, dataset_name: str, stage_dir: Path) -> Path:
        target_dir = self.dataset_root(dataset_name)
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.parent.mkdir(parents=True, exist_ok=True)
        stage_dir.replace(target_dir)
        return target_dir

    def delete_stage_dir(self, stage_dir: Path) -> None:
        if stage_dir.exists():
            shutil.rmtree(stage_dir)

    def delete_dataset_dir(self, dataset_name: str) -> None:
        dataset_dir = self.dataset_root(dataset_name)
        if dataset_dir.exists():
            shutil.rmtree(dataset_dir)

    def index_path(self, dataset_root: Path) -> Path:
        return dataset_root / self._index_file_name

    def board_corrected_image_path(
        self,
        dataset_root: Path,
        source_name: str,
        board_name: str,
    ) -> Path:
        return (
            dataset_root
            / "board"
            / self._sanitize_component(source_name)
            / self._sanitize_component(board_name)
            / "corrected-board.png"
        )

    def board_cell_image_path(
        self,
        dataset_root: Path,
        source_name: str,
        board_name: str,
        cell_index: int,
    ) -> Path:
        return (
            dataset_root
            / "board"
            / self._sanitize_component(source_name)
            / self._sanitize_component(board_name)
            / "cells"
            / f"{cell_index:03d}.png"
        )

    def digit_sample_image_path(
        self,
        dataset_root: Path,
        source_name: str,
        sample_key: str,
    ) -> Path:
        return (
            dataset_root
            / "digit"
            / self._sanitize_component(source_name)
            / f"{self._sanitize_component(sample_key)}.png"
        )

    def to_relative_path(self, dataset_root: Path, artifact_path: Path) -> str:
        return artifact_path.relative_to(dataset_root).as_posix()

    def _sanitize_component(self, value: str) -> str:
        sanitized = value.strip().replace("\\", "_").replace("/", "_")
        sanitized = sanitized.replace(":", "_").replace(" ", "_")
        return sanitized or "unnamed"
