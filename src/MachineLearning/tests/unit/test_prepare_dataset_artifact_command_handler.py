import json
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from application.features.datasets.commands.prepare_dataset_artifact.prepare_dataset_artifact_command import (
    PrepareDatasetArtifactCommand,
)
from application.features.datasets.commands.prepare_dataset_artifact.prepare_dataset_artifact_command_handler import (
    PrepareDatasetArtifactCommandHandler,
)
from application.features.datasets.dto.dataset_split_policy_dto import (
    DatasetSplitPolicyDto,
    SplitRatiosDto,
)
from application.features.datasets.dto.prepare_dataset_source_dto import (
    PrepareDatasetSourceDto,
)
from application.features.datasets.errors.dataset_preparation_errors import (
    PrepareDatasetArtifactCommandError,
)
from infrastructure.reporting.preparation_report_builder import (
    PreparationReportBuilder,
)
from infrastructure.storage.dataset_preparation_image_reader import (
    DatasetPreparationImageReader,
)
from infrastructure.storage.dataset_preparation_manifest_reader import (
    DatasetPreparationManifestReader,
)
from infrastructure.storage.dataset_preparation_source_reader import (
    DatasetPreparationSourceReader,
)
from infrastructure.storage.dataset_preparations_path_provider import (
    DatasetPreparationsPathProvider,
)
from infrastructure.storage.npz_dataset_artifact_writer import (
    NpzDatasetArtifactWriter,
)
from infrastructure.storage.processed_dataset_artifact_cleanup import (
    ProcessedDatasetArtifactCleanup,
)
from infrastructure.storage.temp_dataset_path_provider import (
    TempDatasetPathProvider,
)
from models.dataset_split import DatasetSplit


class PrepareDatasetArtifactCommandHandlerTests(unittest.TestCase):
    def test_handle_should_build_npz_from_digit_preparation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            root_path = Path(temp_directory)
            preparations_root = root_path / "preparations"
            datasets_root = root_path / "datasets"
            self._write_digit_preparation(
                preparations_root=preparations_root,
                preparation_name="prep-1",
                source_name="mnist_train",
                samples=(
                    ("000000.png", 3, _digit_like_image()),
                    ("000001.png", 8, _digit_like_image(offset=2)),
                ),
            )
            handler = self._create_handler(
                preparations_root=preparations_root,
                datasets_root=datasets_root,
                sample_split_assigner=_FixedSplitAssigner(
                    {
                        "000000.png": DatasetSplit.TRAIN,
                        "000001.png": DatasetSplit.TEST,
                    }
                ),
            )

            result = handler.handle(
                _build_digit_command(
                    preparation_name="prep-1",
                    dataset_name="digits-v1",
                    source_name="mnist_train",
                )
            )

            self.assertEqual(result.dataset_name, "digits-v1")
            self.assertEqual(result.file_name, "digits-v1.npz")
            self.assertEqual(result.preprocessing_profile, "default-28x28-v1")
            self.assertEqual(result.sample_counts.train, 1)
            self.assertEqual(result.sample_counts.val, 0)
            self.assertEqual(result.sample_counts.test, 1)
            self.assertEqual(result.sources[0].processed_sample_count, 2)
            self.assertEqual(result.sources[0].included_sample_count, 2)

            dataset_path = datasets_root / "digits-v1.npz"
            self.assertTrue(dataset_path.is_file())
            arrays = np.load(dataset_path)
            self.assertEqual(arrays["y_train"].tolist(), [2])
            self.assertEqual(arrays["y_test"].tolist(), [7])
            self.assertEqual(
                arrays["class_names"].tolist(),
                ["1", "2", "3", "4", "5", "6", "7", "8", "9"],
            )

    def test_handle_should_build_npz_from_board_preparation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            root_path = Path(temp_directory)
            preparations_root = root_path / "preparations"
            datasets_root = root_path / "datasets"
            self._write_board_preparation(
                preparations_root=preparations_root,
                preparation_name="prep-1",
                source_name="v1_training",
                board_folder_name="Image1",
                entries=(
                    ("000.png", 1, _digit_like_image()),
                    ("001.png", 9, _digit_like_image(offset=1)),
                ),
            )
            handler = self._create_handler(
                preparations_root=preparations_root,
                datasets_root=datasets_root,
                sample_split_assigner=_FixedSplitAssigner(
                    {"Image1": DatasetSplit.TRAIN}
                ),
            )

            result = handler.handle(
                _build_board_command(
                    preparation_name="prep-1",
                    dataset_name="boards-v1",
                    source_name="v1_training",
                )
            )

            self.assertEqual(result.sample_counts.train, 2)
            self.assertEqual(result.sources[0].processed_sample_count, 81)
            self.assertEqual(result.sources[0].included_sample_count, 2)
            self.assertEqual(result.sources[0].empty_cell_count, 79)

            arrays = np.load(datasets_root / "boards-v1.npz")
            self.assertEqual(arrays["y_train"].tolist(), [0, 8])

    def test_handle_should_raise_when_preparation_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            root_path = Path(temp_directory)
            handler = self._create_handler(
                preparations_root=root_path / "preparations",
                datasets_root=root_path / "datasets",
                sample_split_assigner=_FixedSplitAssigner({}),
            )

            with self.assertRaises(PrepareDatasetArtifactCommandError) as raised_error:
                handler.handle(
                    _build_digit_command(
                        preparation_name="missing-prep",
                        dataset_name="digits-v1",
                        source_name="mnist_train",
                    )
                )

            self.assertEqual(
                raised_error.exception.error_type,
                "dataset_preparation_not_found",
            )

    def test_handle_should_raise_for_invalid_preparation_layout(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            root_path = Path(temp_directory)
            preparations_root = root_path / "preparations"
            datasets_root = root_path / "datasets"
            preparation_root = preparations_root / "prep-1" / "digit"
            preparation_root.mkdir(parents=True)
            (preparation_root / "folders.json").write_text(
                json.dumps(["mnist_train"]),
                encoding="utf-8",
            )
            source_root = preparation_root / "mnist_train"
            source_root.mkdir()
            (source_root / "index.json").write_text(
                json.dumps([{"fileName": "000000.png"}]),
                encoding="utf-8",
            )
            handler = self._create_handler(
                preparations_root=preparations_root,
                datasets_root=datasets_root,
                sample_split_assigner=_FixedSplitAssigner({}),
            )

            with self.assertRaises(PrepareDatasetArtifactCommandError) as raised_error:
                handler.handle(
                    _build_digit_command(
                        preparation_name="prep-1",
                        dataset_name="digits-v1",
                        source_name="mnist_train",
                    )
                )

            self.assertEqual(
                raised_error.exception.error_type,
                "dataset_preparation_layout_invalid",
            )

    def test_handle_should_cleanup_partial_npz_when_write_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            root_path = Path(temp_directory)
            preparations_root = root_path / "preparations"
            datasets_root = root_path / "datasets"
            self._write_digit_preparation(
                preparations_root=preparations_root,
                preparation_name="prep-1",
                source_name="mnist_train",
                samples=(("000000.png", 3, _digit_like_image()),),
            )
            handler = self._create_handler(
                preparations_root=preparations_root,
                datasets_root=datasets_root,
                sample_split_assigner=_FixedSplitAssigner(
                    {"000000.png": DatasetSplit.TRAIN}
                ),
                writer=_FailingNpzDatasetArtifactWriter(),
            )

            with self.assertRaises(PrepareDatasetArtifactCommandError) as raised_error:
                handler.handle(
                    _build_digit_command(
                        preparation_name="prep-1",
                        dataset_name="digits-v1",
                        source_name="mnist_train",
                    )
                )

            self.assertEqual(
                raised_error.exception.error_type,
                "dataset_artifact_write_failed",
            )
            self.assertFalse((datasets_root / "digits-v1.npz").exists())

    def _create_handler(
        self,
        preparations_root: Path,
        datasets_root: Path,
        sample_split_assigner: object,
        writer: object | None = None,
    ) -> PrepareDatasetArtifactCommandHandler:
        path_provider = DatasetPreparationsPathProvider(str(preparations_root))
        manifest_reader = DatasetPreparationManifestReader(path_provider)
        return PrepareDatasetArtifactCommandHandler(
            source_reader=DatasetPreparationSourceReader(
                path_provider=path_provider,
                manifest_reader=manifest_reader,
            ),
            manifest_reader=manifest_reader,
            image_reader=DatasetPreparationImageReader(),
            sample_split_assigner=sample_split_assigner,
            npz_dataset_artifact_writer=writer or NpzDatasetArtifactWriter(),
            temp_dataset_path_provider=TempDatasetPathProvider(str(datasets_root)),
            artifact_cleanup=ProcessedDatasetArtifactCleanup(),
            preparation_report_builder=PreparationReportBuilder(),
        )

    def _write_digit_preparation(
        self,
        preparations_root: Path,
        preparation_name: str,
        source_name: str,
        samples: tuple[tuple[str, int, np.ndarray], ...],
    ) -> None:
        source_root = preparations_root / preparation_name / "digit" / source_name
        source_root.mkdir(parents=True, exist_ok=True)
        (source_root.parent / "folders.json").write_text(
            json.dumps([source_name]),
            encoding="utf-8",
        )
        index_payload = []
        for file_name, label, image in samples:
            _write_image(source_root / file_name, image)
            index_payload.append({"fileName": file_name, "label": label})
        (source_root / "index.json").write_text(
            json.dumps(index_payload),
            encoding="utf-8",
        )

    def _write_board_preparation(
        self,
        preparations_root: Path,
        preparation_name: str,
        source_name: str,
        board_folder_name: str,
        entries: tuple[tuple[str, int, np.ndarray], ...],
    ) -> None:
        board_root = (
            preparations_root
            / preparation_name
            / "board"
            / source_name
            / board_folder_name
            / "cells"
        )
        board_root.mkdir(parents=True, exist_ok=True)
        source_root = board_root.parent.parent
        (source_root.parent / "folders.json").write_text(
            json.dumps([source_name]),
            encoding="utf-8",
        )
        (source_root / "file.json").write_text(
            json.dumps([board_folder_name]),
            encoding="utf-8",
        )
        index_payload = []
        for file_name, label, image in entries:
            _write_image(board_root / file_name, image)
            index_payload.append({"fileName": file_name, "label": label})
        (board_root / "index.json").write_text(
            json.dumps(index_payload),
            encoding="utf-8",
        )


class _FixedSplitAssigner:
    def __init__(self, assignments: dict[str, DatasetSplit]) -> None:
        self._assignments = assignments

    def assign_split(
        self, split_policy: DatasetSplitPolicyDto, stable_key: str
    ) -> DatasetSplit:
        del split_policy
        return self._assignments[stable_key]


class _FailingNpzDatasetArtifactWriter:
    def write(
        self,
        output_path: Path,
        x_train,
        y_train,
        x_val,
        y_val,
        x_test,
        y_test,
        class_names,
    ) -> None:
        del x_train, y_train, x_val, y_val, x_test, y_test, class_names
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"partial")
        raise OSError("disk full")


def _build_digit_command(
    preparation_name: str,
    dataset_name: str,
    source_name: str,
) -> PrepareDatasetArtifactCommand:
    return PrepareDatasetArtifactCommand(
        preparation_name=preparation_name,
        dataset_name=dataset_name,
        split_policy=DatasetSplitPolicyDto(
            mode="ratio",
            group_by="sourceType",
            ratios=SplitRatiosDto(train=0.8, val=0.1, test=0.1),
        ),
        sources=(
            PrepareDatasetSourceDto(
                name=source_name,
                type="digit",
                splits=("mix",),
            ),
        ),
    )


def _build_board_command(
    preparation_name: str,
    dataset_name: str,
    source_name: str,
) -> PrepareDatasetArtifactCommand:
    return PrepareDatasetArtifactCommand(
        preparation_name=preparation_name,
        dataset_name=dataset_name,
        split_policy=DatasetSplitPolicyDto(
            mode="ratio",
            group_by="sourceType",
            ratios=SplitRatiosDto(train=0.8, val=0.1, test=0.1),
        ),
        sources=(
            PrepareDatasetSourceDto(
                name=source_name,
                type="board",
                splits=("mix",),
            ),
        ),
    )


def _write_image(path: Path, image: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), image)


def _digit_like_image(offset: int = 0) -> np.ndarray:
    image = np.full((28, 28), 255, dtype=np.uint8)
    image[6 + offset : 22, 12:16] = 0
    image[6 + offset : 10 + offset, 8:20] = 0
    return image


if __name__ == "__main__":
    unittest.main()
