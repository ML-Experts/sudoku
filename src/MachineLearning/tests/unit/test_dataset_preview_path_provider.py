import tempfile
import unittest
from pathlib import Path

from infrastructure.storage.dataset_preview_path_provider import (
    DatasetPreviewPathProvider,
)


class DatasetPreviewPathProviderTests(unittest.TestCase):
    def test_paths_should_be_deterministic_and_relative(self) -> None:
        provider = DatasetPreviewPathProvider("/tmp/dataset-previews")
        dataset_root = provider.dataset_root("digits-v1")
        corrected_board_path = provider.board_corrected_image_path(
            dataset_root=dataset_root,
            source_name="boards-source",
            board_name="board 01",
        )
        cell_path = provider.board_cell_image_path(
            dataset_root=dataset_root,
            source_name="boards-source",
            board_name="board 01",
            cell_index=7,
        )
        digit_path = provider.digit_sample_image_path(
            dataset_root=dataset_root,
            source_name="digit-source",
            sample_key="sample:42",
        )

        self.assertEqual(
            corrected_board_path,
            Path(
                "/tmp/dataset-previews/digits-v1/board/boards-source/"
                "board_01/corrected-board.png"
            ),
        )
        self.assertEqual(
            provider.to_relative_path(dataset_root, cell_path),
            "board/boards-source/board_01/cells/007.png",
        )
        self.assertEqual(
            provider.to_relative_path(dataset_root, digit_path),
            "digit/digit-source/sample_42.png",
        )

    def test_create_stage_dir_and_promote_should_replace_existing_dataset_dir(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            provider = DatasetPreviewPathProvider(temp_directory)
            existing_root = provider.dataset_root("digits-v1")
            existing_root.mkdir(parents=True, exist_ok=True)
            (existing_root / "old.txt").write_text("old", encoding="utf-8")

            stage_dir = provider.create_stage_dir("digits-v1")
            (stage_dir / "new.txt").write_text("new", encoding="utf-8")

            promoted_root = provider.promote_stage_dir("digits-v1", stage_dir)

            self.assertEqual(promoted_root, existing_root)
            self.assertFalse((promoted_root / "old.txt").exists())
            self.assertEqual(
                (promoted_root / "new.txt").read_text(encoding="utf-8"),
                "new",
            )


if __name__ == "__main__":
    unittest.main()
