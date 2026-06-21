import shutil
from pathlib import Path


class DatasetPreparationsPathProvider:
    def __init__(self, preparations_directory_path: str) -> None:
        self._preparations_directory_path = Path(preparations_directory_path)

    def preparation_root(self, preparation_name: str) -> Path:
        return self._preparations_directory_path / preparation_name

    def board_root(self, preparation_name: str) -> Path:
        return self.preparation_root(preparation_name) / "board"

    def digit_root(self, preparation_name: str) -> Path:
        return self.preparation_root(preparation_name) / "digit"

    def board_source_root(
        self, preparation_name: str, source_name: str
    ) -> Path:
        return self.board_root(preparation_name) / source_name

    def digit_source_root(
        self, preparation_name: str, source_name: str
    ) -> Path:
        return self.digit_root(preparation_name) / source_name

    def create_stage_dir(self, preparation_name: str) -> Path:
        stage_dir = (
            self._preparations_directory_path / f".{preparation_name}.staging"
        )
        if stage_dir.exists():
            shutil.rmtree(stage_dir)
        stage_dir.mkdir(parents=True, exist_ok=True)
        return stage_dir

    def promote_stage_dir(
        self, preparation_name: str, stage_dir: Path
    ) -> Path:
        target_dir = self.preparation_root(preparation_name)
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.parent.mkdir(parents=True, exist_ok=True)
        stage_dir.replace(target_dir)
        return target_dir

    def delete_stage_dir(self, stage_dir: Path) -> None:
        if stage_dir.exists():
            shutil.rmtree(stage_dir)

    def delete_preparation_dir(self, preparation_name: str) -> None:
        preparation_dir = self.preparation_root(preparation_name)
        if preparation_dir.exists():
            shutil.rmtree(preparation_dir)

    def board_folders_manifest_path(self, stage_dir: Path) -> Path:
        return stage_dir / "board" / "folders.json"

    def digit_folders_manifest_path(self, stage_dir: Path) -> Path:
        return stage_dir / "digit" / "folders.json"

    def board_file_manifest_path(
        self, stage_dir: Path, source_name: str
    ) -> Path:
        return stage_dir / "board" / source_name / "file.json"

    def board_corrected_board_path(
        self,
        stage_dir: Path,
        source_name: str,
        board_folder_name: str,
    ) -> Path:
        return (
            stage_dir
            / "board"
            / source_name
            / board_folder_name
            / "corrected-board.png"
        )

    def board_cells_index_path(
        self,
        stage_dir: Path,
        source_name: str,
        board_folder_name: str,
    ) -> Path:
        return (
            stage_dir
            / "board"
            / source_name
            / board_folder_name
            / "cells"
            / "index.json"
        )

    def board_cell_image_path(
        self,
        stage_dir: Path,
        source_name: str,
        board_folder_name: str,
        file_name: str,
    ) -> Path:
        return (
            stage_dir
            / "board"
            / source_name
            / board_folder_name
            / "cells"
            / file_name
        )

    def digit_index_path(self, stage_dir: Path, source_name: str) -> Path:
        return stage_dir / "digit" / source_name / "index.json"

    def digit_sample_image_path(
        self,
        stage_dir: Path,
        source_name: str,
        file_name: str,
    ) -> Path:
        return stage_dir / "digit" / source_name / file_name
