import tempfile
import unittest
from pathlib import Path

from infrastructure.storage.dataset_preparation_workspace_manager import (
    DatasetPreparationWorkspaceManager,
)
from infrastructure.storage.dataset_preparations_path_provider import (
    DatasetPreparationsPathProvider,
)


class DatasetPreparationWorkspaceManagerTests(unittest.TestCase):
    def test_create_stage_dir_should_reset_existing_staging_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            manager = self._create_manager(temp_directory)
            path_provider = DatasetPreparationsPathProvider(temp_directory)
            stage_dir = path_provider.create_stage_dir("prep-1")
            (stage_dir / "stale.txt").write_text("stale", encoding="utf-8")

            recreated_stage_dir = manager.create_stage_dir("prep-1")

            self.assertEqual(recreated_stage_dir, stage_dir)
            self.assertFalse((recreated_stage_dir / "stale.txt").exists())

    def test_promote_should_move_stage_directory_to_final_location(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            manager = self._create_manager(temp_directory)
            path_provider = DatasetPreparationsPathProvider(temp_directory)
            stage_dir = manager.create_stage_dir("prep-1")
            (stage_dir / "digit" / "mnist").mkdir(parents=True)

            target_dir = manager.promote("prep-1", stage_dir)

            self.assertEqual(target_dir, path_provider.preparation_root("prep-1"))
            self.assertTrue((target_dir / "digit" / "mnist").is_dir())
            self.assertFalse(stage_dir.exists())

    def test_delete_methods_should_remove_stage_and_final_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            manager = self._create_manager(temp_directory)
            path_provider = DatasetPreparationsPathProvider(temp_directory)
            stage_dir = manager.create_stage_dir("prep-1")
            target_dir = path_provider.preparation_root("prep-1")
            target_dir.mkdir(parents=True)

            manager.delete_stage_dir(stage_dir)
            manager.delete_preparation_dir("prep-1")

            self.assertFalse(stage_dir.exists())
            self.assertFalse(target_dir.exists())

    def _create_manager(
        self, temp_directory: str
    ) -> DatasetPreparationWorkspaceManager:
        return DatasetPreparationWorkspaceManager(
            DatasetPreparationsPathProvider(temp_directory)
        )


if __name__ == "__main__":
    unittest.main()
