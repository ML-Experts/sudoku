import json
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from application.features.datasets.commands.prepare_dataset_artifact.prepare_dataset_artifact_command import (
    PrepareDatasetArtifactCommand,
)
from application.features.datasets.commands.prepare_dataset_artifact.prepare_dataset_artifact_command_handler import (
    PrepareDatasetArtifactCommandError,
    PrepareDatasetArtifactCommandHandler,
)
from application.features.datasets.dto.dataset_split_policy_dto import (
    DatasetSplitPolicyDto,
    SplitRatiosDto,
)
from application.features.datasets.dto.prepare_dataset_source_dto import (
    PrepareDatasetSourceDto,
)
from infrastructure.datasets.board_dataset_scanner import BoardDatasetPair
from infrastructure.datasets.idx_dataset_loader import DigitDatasetRecord
from infrastructure.reporting.preparation_report_builder import (
    PreparationReportBuilder,
)
from infrastructure.storage.dataset_preparation_artifact_cleanup import (
    DatasetPreparationArtifactCleanup,
)
from infrastructure.storage.dataset_preview_index_writer import (
    DatasetPreviewIndexWriter,
)
from infrastructure.storage.dataset_preview_path_provider import (
    DatasetPreviewPathProvider,
)
from infrastructure.storage.filesystem_image_artifact_writer import (
    FilesystemImageArtifactWriter,
)
from infrastructure.storage.json_file_writer import JsonFileWriter
from infrastructure.storage.npz_dataset_artifact_writer import (
    NpzDatasetArtifactWriter,
)
from infrastructure.storage.temp_dataset_path_provider import (
    TempDatasetPathProvider,
)
from infrastructure.vision.cell_preprocessing_pipeline import (
    CellPreprocessingPipeline,
)
from infrastructure.vision.vision_image_codec import VisionImageCodec
from models.board_grid_label import BoardGridLabel
from models.cells_grid import CellsGrid
from models.dataset_split import DatasetSplit


@dataclass(frozen=True)
class _ResolvedSource:
    detected_type: str
    path: Path
    images_path: Path | None
    labels_path: Path | None


class _DatasetSourceResolver:
    def resolve(self, source_name: str, requested_type: str) -> _ResolvedSource:
        return _ResolvedSource(
            detected_type="digit",
            path=Path("."),
            images_path=Path("images.idx3-ubyte"),
            labels_path=Path("labels.idx1-ubyte"),
        )


class _IdxDatasetLoader:
    def __init__(self, records: tuple[DigitDatasetRecord, ...]) -> None:
        self._records = records

    def load(
        self, images_path: Path, labels_path: Path
    ) -> tuple[DigitDatasetRecord, ...]:
        return self._records


class _BoardDatasetScanner:
    def __init__(self, pairs: tuple[BoardDatasetPair, ...]) -> None:
        self._pairs = pairs

    def scan_pairs(self, source_directory: Path) -> tuple[BoardDatasetPair, ...]:
        return self._pairs


class _BoardDatParser:
    def __init__(self, label_rows: list[list[int]] | None = None) -> None:
        self._label_rows = label_rows or [[1] * 9 for _ in range(9)]

    def parse(self, dat_file_path: Path) -> BoardGridLabel:
        return BoardGridLabel.from_rows(self._label_rows)


class _SampleSplitAssigner:
    def __init__(self, assignments: dict[str, DatasetSplit]) -> None:
        self._assignments = assignments

    def assign_split(
        self, split_policy: DatasetSplitPolicyDto, stable_key: str
    ) -> DatasetSplit:
        return self._assignments[stable_key]


class _UnusedBoardDependency:
    def __getattr__(self, name: str) -> object:
        raise AssertionError(f"Board dependency {name} should not be used.")


class _BoardExtractorFailure(Exception):
    error_type = "cells_extraction_failed"


class _FailingBoardDatasetCellExtractor:
    def extract(self, board_image: np.ndarray) -> object:
        raise _BoardExtractorFailure("engine cells extraction failed")


class _BoardDatasetCellExtractor:
    def __init__(self, cell_image: np.ndarray) -> None:
        self._cell_image = cell_image

    def extract(self, board_image: np.ndarray) -> tuple[np.ndarray, CellsGrid]:
        return (
            board_image,
            CellsGrid.from_rows(
                [[self._cell_image.copy() for _ in range(9)] for _ in range(9)]
            ),
        )


class _FailingImageArtifactWriter:
    def write(self, path: Path, image: np.ndarray) -> None:
        raise OSError("disk full")


class PrepareDatasetArtifactCommandHandlerTests(unittest.TestCase):
    def test_handle_should_write_digit_preview_index_and_npz_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            root_path = Path(temp_directory)
            preview_root = root_path / "previews"
            dataset_root = root_path / "datasets"
            records = (
                DigitDatasetRecord(
                    sample_key="0",
                    image=_digit_like_image(),
                    label=3,
                ),
                DigitDatasetRecord(
                    sample_key="1",
                    image=_digit_like_image(offset=2),
                    label=8,
                ),
            )
            handler = self._create_handler(
                dataset_root=dataset_root,
                preview_root=preview_root,
                idx_loader=_IdxDatasetLoader(records),
                sample_split_assigner=_SampleSplitAssigner(
                    {
                        "0": DatasetSplit.TRAIN,
                        "1": DatasetSplit.TEST,
                    }
                ),
            )

            result = handler.handle(_build_digit_command())

            self.assertEqual(result.sample_counts.train, 1)
            self.assertEqual(result.sample_counts.val, 0)
            self.assertEqual(result.sample_counts.test, 1)
            self.assertEqual(result.sources[0].processed_sample_count, 2)

            dataset_path = dataset_root / "digits-v1.npz"
            preview_index_path = preview_root / "digits-v1" / "index.json"
            self.assertTrue(dataset_path.is_file())
            self.assertTrue(preview_index_path.is_file())
            self.assertTrue(
                (preview_root / "digits-v1" / "digit" / "mnist" / "0.png").is_file()
            )
            self.assertTrue(
                (preview_root / "digits-v1" / "digit" / "mnist" / "1.png").is_file()
            )

            preview_index = json.loads(preview_index_path.read_text(encoding="utf-8"))
            self.assertEqual(preview_index["datasetName"], "digits-v1")
            self.assertEqual(
                preview_index["digitSources"][0]["samples"][0]["sampleIndex"],
                "0",
            )
            self.assertEqual(
                preview_index["digitSources"][0]["samples"][1]["split"],
                "test",
            )

            arrays = np.load(dataset_path)
            self.assertEqual(arrays["x_train"].shape[0], 1)
            self.assertEqual(arrays["x_test"].shape[0], 1)
            self.assertEqual(arrays["y_train"].tolist(), [2])
            self.assertEqual(arrays["y_test"].tolist(), [7])
            self.assertEqual(
                arrays["class_names"].tolist(),
                ["1", "2", "3", "4", "5", "6", "7", "8", "9"],
            )

    def test_handle_should_normalize_board_labels_to_zero_based_training_indices(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            root_path = Path(temp_directory)
            preview_root = root_path / "previews"
            dataset_root = root_path / "datasets"
            source_root = root_path / "boards" / "board-source"
            source_root.mkdir(parents=True)
            board_image_path = source_root / "sample.jpg"
            board_label_path = source_root / "sample.dat"
            cv2.imwrite(
                str(board_image_path),
                np.full((64, 64, 3), 255, dtype=np.uint8),
            )
            board_label_path.write_text("unused", encoding="utf-8")

            label_rows = [[0] * 9 for _ in range(9)]
            label_rows[0][0] = 1
            label_rows[0][1] = 9

            handler = self._create_handler(
                dataset_root=dataset_root,
                preview_root=preview_root,
                idx_loader=_IdxDatasetLoader(tuple()),
                sample_split_assigner=_SampleSplitAssigner(
                    {"sample.jpg": DatasetSplit.TRAIN}
                ),
                dataset_source_resolver=_BoardSourceResolver(source_root),
                board_dataset_scanner=_BoardDatasetScanner(
                    (
                        BoardDatasetPair(
                            group_key="sample.jpg",
                            board_name="sample",
                            image_path=board_image_path,
                            label_path=board_label_path,
                        ),
                    )
                ),
                board_dat_parser=_BoardDatParser(label_rows=label_rows),
                board_dataset_cell_extractor=_BoardDatasetCellExtractor(
                    _digit_like_image()
                ),
            )

            result = handler.handle(_build_board_command())

            self.assertEqual(result.sample_counts.train, 2)
            self.assertEqual(result.sample_counts.val, 0)
            self.assertEqual(result.sample_counts.test, 0)

            dataset_path = dataset_root / "boards-v1.npz"
            preview_index_path = preview_root / "boards-v1" / "index.json"
            arrays = np.load(dataset_path)
            self.assertEqual(arrays["y_train"].tolist(), [0, 8])
            self.assertEqual(
                arrays["class_names"].tolist(),
                ["1", "2", "3", "4", "5", "6", "7", "8", "9"],
            )

            preview_index = json.loads(preview_index_path.read_text(encoding="utf-8"))
            cells = preview_index["boardSources"][0]["boards"][0]["cells"]
            self.assertEqual(cells[0]["label"], 1)
            self.assertEqual(cells[1]["label"], 9)
            self.assertTrue(cells[0]["includedInDataset"])
            self.assertTrue(cells[1]["includedInDataset"])
            self.assertFalse(cells[2]["includedInDataset"])

    def test_handle_should_skip_zero_labeled_digit_samples_from_training(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            root_path = Path(temp_directory)
            preview_root = root_path / "previews"
            dataset_root = root_path / "datasets"
            records = (
                DigitDatasetRecord(
                    sample_key="0",
                    image=_digit_like_image(),
                    label=0,
                ),
                DigitDatasetRecord(
                    sample_key="1",
                    image=_digit_like_image(offset=1),
                    label=9,
                ),
            )
            handler = self._create_handler(
                dataset_root=dataset_root,
                preview_root=preview_root,
                idx_loader=_IdxDatasetLoader(records),
                sample_split_assigner=_SampleSplitAssigner(
                    {
                        "0": DatasetSplit.TRAIN,
                        "1": DatasetSplit.TRAIN,
                    }
                ),
            )

            result = handler.handle(_build_digit_command())

            self.assertEqual(result.sample_counts.train, 1)
            self.assertEqual(result.sources[0].empty_cell_count, 1)
            self.assertEqual(result.sources[0].included_sample_count, 1)

            dataset_path = dataset_root / "digits-v1.npz"
            preview_index_path = preview_root / "digits-v1" / "index.json"
            arrays = np.load(dataset_path)
            self.assertEqual(arrays["y_train"].tolist(), [8])

            preview_index = json.loads(preview_index_path.read_text(encoding="utf-8"))
            samples = preview_index["digitSources"][0]["samples"]
            self.assertEqual(samples[0]["label"], 0)
            self.assertFalse(samples[0]["includedInDataset"])
            self.assertEqual(samples[1]["label"], 9)
            self.assertTrue(samples[1]["includedInDataset"])

    def test_handle_should_cleanup_partial_artifacts_when_preview_write_fails(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            root_path = Path(temp_directory)
            preview_root = root_path / "previews"
            dataset_root = root_path / "datasets"
            handler = self._create_handler(
                dataset_root=dataset_root,
                preview_root=preview_root,
                idx_loader=_IdxDatasetLoader(
                    (
                        DigitDatasetRecord(
                            sample_key="0",
                            image=_digit_like_image(),
                            label=3,
                        ),
                    )
                ),
                sample_split_assigner=_SampleSplitAssigner(
                    {"0": DatasetSplit.TRAIN}
                ),
                preview_image_writer=_FailingImageArtifactWriter(),
            )

            with self.assertRaises(PrepareDatasetArtifactCommandError) as raised_error:
                handler.handle(_build_digit_command())

            self.assertEqual(
                raised_error.exception.error_type,
                "dataset_preview_write_failed",
            )
            self.assertFalse((dataset_root / "digits-v1.npz").exists())
            self.assertFalse((preview_root / "digits-v1").exists())
            self.assertFalse((preview_root / ".digits-v1.staging").exists())

    def test_handle_should_map_engine_board_errors_to_domain_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            root_path = Path(temp_directory)
            preview_root = root_path / "previews"
            dataset_root = root_path / "datasets"
            source_root = root_path / "boards" / "board-source"
            source_root.mkdir(parents=True)
            board_image_path = source_root / "sample.jpg"
            board_label_path = source_root / "sample.dat"
            cv2.imwrite(
                str(board_image_path),
                np.zeros((32, 32, 3), dtype=np.uint8),
            )
            board_label_path.write_text("unused", encoding="utf-8")

            handler = self._create_handler(
                dataset_root=dataset_root,
                preview_root=preview_root,
                idx_loader=_IdxDatasetLoader(tuple()),
                sample_split_assigner=_SampleSplitAssigner(
                    {"sample.jpg": DatasetSplit.TRAIN}
                ),
                dataset_source_resolver=_BoardSourceResolver(source_root),
                board_dataset_scanner=_BoardDatasetScanner(
                    (
                        BoardDatasetPair(
                            group_key="sample.jpg",
                            board_name="sample",
                            image_path=board_image_path,
                            label_path=board_label_path,
                        ),
                    )
                ),
                board_dat_parser=_BoardDatParser(),
                board_dataset_cell_extractor=_FailingBoardDatasetCellExtractor(),
            )

            with self.assertRaises(PrepareDatasetArtifactCommandError) as raised_error:
                handler.handle(_build_board_command())

            self.assertEqual(raised_error.exception.error_type, "board_not_found")

    def _create_handler(
        self,
        dataset_root: Path,
        preview_root: Path,
        idx_loader: _IdxDatasetLoader,
        sample_split_assigner: _SampleSplitAssigner,
        preview_image_writer: object | None = None,
        dataset_source_resolver: object | None = None,
        board_dataset_scanner: object | None = None,
        board_dat_parser: object | None = None,
        board_dataset_cell_extractor: object | None = None,
    ) -> PrepareDatasetArtifactCommandHandler:
        preview_path_provider = DatasetPreviewPathProvider(str(preview_root))
        return PrepareDatasetArtifactCommandHandler(
            dataset_source_resolver=dataset_source_resolver
            or _DatasetSourceResolver(),
            board_dataset_scanner=board_dataset_scanner
            or _UnusedBoardDependency(),
            board_dat_parser=board_dat_parser or _UnusedBoardDependency(),
            idx_dataset_loader=idx_loader,
            sample_split_assigner=sample_split_assigner,
            cell_preprocessing_pipeline=CellPreprocessingPipeline(output_size=28),
            npz_dataset_artifact_writer=NpzDatasetArtifactWriter(),
            temp_dataset_path_provider=TempDatasetPathProvider(str(dataset_root)),
            dataset_preview_path_provider=preview_path_provider,
            preview_image_artifact_writer=preview_image_writer
            or FilesystemImageArtifactWriter(VisionImageCodec()),
            dataset_preview_index_writer=DatasetPreviewIndexWriter(
                JsonFileWriter()
            ),
            dataset_preparation_artifact_cleanup=(
                DatasetPreparationArtifactCleanup(preview_path_provider)
            ),
            preparation_report_builder=PreparationReportBuilder(),
            board_dataset_cell_extractor=board_dataset_cell_extractor
            or _UnusedBoardDependency(),
        )


def _build_digit_command() -> PrepareDatasetArtifactCommand:
    return PrepareDatasetArtifactCommand(
        dataset_name="digits-v1",
        preprocessing_profile="default-28x28-v1",
        sources=(
            PrepareDatasetSourceDto(
                name="mnist",
                type="digit",
                split_policy=DatasetSplitPolicyDto(
                    mode="selected",
                    group_by="sample",
                    ratios=SplitRatiosDto(train=1.0, val=0.0, test=0.0),
                ),
            ),
        ),
    )


def _build_board_command() -> PrepareDatasetArtifactCommand:
    return PrepareDatasetArtifactCommand(
        dataset_name="boards-v1",
        preprocessing_profile="default-28x28-v1",
        sources=(
            PrepareDatasetSourceDto(
                name="board-source",
                type="board",
                split_policy=DatasetSplitPolicyDto(
                    mode="selected",
                    group_by="board",
                    ratios=SplitRatiosDto(train=1.0, val=0.0, test=0.0),
                ),
            ),
        ),
    )


@dataclass(frozen=True)
class _ResolvedBoardSource:
    detected_type: str
    path: Path
    images_path: Path | None
    labels_path: Path | None


class _BoardSourceResolver:
    def __init__(self, path: Path) -> None:
        self._path = path

    def resolve(self, source_name: str, requested_type: str) -> _ResolvedBoardSource:
        return _ResolvedBoardSource(
            detected_type="board",
            path=self._path,
            images_path=None,
            labels_path=None,
        )


def _digit_like_image(offset: int = 0) -> np.ndarray:
    image = np.full((28, 28), 255, dtype=np.uint8)
    image[6 + offset : 22, 12:16] = 0
    image[6 + offset : 10 + offset, 8:20] = 0
    return image


if __name__ == "__main__":
    unittest.main()
