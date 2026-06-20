import json
import tempfile
import unittest
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import cv2
import numpy as np

from application.features.datasets.commands.create_dataset_preparation.create_dataset_preparation_command import (
    CreateDatasetPreparationCommand,
)
from application.features.datasets.commands.create_dataset_preparation.create_dataset_preparation_command_handler import (
    CreateDatasetPreparationCommandHandler,
)
from application.features.datasets.dto.create_dataset_preparation_source_dto import (
    CreateDatasetPreparationSourceDto,
)
from application.features.datasets.errors.dataset_preparation_errors import (
    CreateDatasetPreparationCommandError,
)
from infrastructure.datasets.board_dataset_scanner import BoardDatasetPair
from infrastructure.datasets.board_folder_name_resolver import (
    BoardFolderNameResolver,
)
from infrastructure.datasets.idx_dataset_loader import DigitDatasetRecord
from infrastructure.reporting.dataset_preparation_report_builder import (
    DatasetPreparationReportBuilder,
)
from infrastructure.storage.dataset_preparation_artifact_cleanup import (
    DatasetPreparationWorkspaceCleanup,
)
from infrastructure.storage.dataset_preparation_artifact_writer import (
    DatasetPreparationArtifactWriter,
)
from infrastructure.storage.dataset_preparation_manifest_writer import (
    DatasetPreparationManifestWriter,
)
from infrastructure.storage.dataset_preparation_workspace_manager import (
    DatasetPreparationWorkspaceManager,
)
from infrastructure.storage.dataset_preparations_path_provider import (
    DatasetPreparationsPathProvider,
)
from infrastructure.storage.filesystem_image_artifact_writer import (
    FilesystemImageArtifactWriter,
)
from infrastructure.storage.json_file_writer import JsonFileWriter
from infrastructure.vision.cell_preprocessing_pipeline import (
    CellPreprocessingPipeline,
)
from infrastructure.vision.digit_sample_preparation_pipeline import (
    DigitSamplePreparationPipeline,
)
from infrastructure.vision.vision_image_codec import VisionImageCodec
from models.board_grid_label import BoardGridLabel
from models.cells_grid import CellsGrid


class CreateDatasetPreparationCommandHandlerTests(unittest.TestCase):
    def test_handle_should_write_digit_preparation_and_skip_zero_labels(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            preparation_root = Path(temp_directory) / "preparations"
            records = (
                DigitDatasetRecord(
                    sample_key="0",
                    image=_digit_like_image(),
                    label=0,
                ),
                DigitDatasetRecord(
                    sample_key="1",
                    image=_digit_like_image(offset=2),
                    label=8,
                ),
            )
            handler = self._create_handler(
                preparation_root=preparation_root,
                dataset_source_resolver=_DigitSourceResolver(),
                idx_dataset_loader=_IdxDatasetLoader(records),
            )

            result = handler.handle(
                CreateDatasetPreparationCommand(
                    preparation_name="digits-prep",
                    sources=(
                        CreateDatasetPreparationSourceDto(
                            name="mnist_train",
                            type="digit",
                        ),
                    ),
                )
            )

            self.assertEqual(result.status, "completed")
            self.assertEqual(result.source_reports[0].prepared_items_count, 1)
            self.assertEqual(result.source_reports[0].empty_cell_count, 1)
            self.assertEqual(result.warnings, tuple())

            index_payload = json.loads(
                (
                    preparation_root
                    / "digits-prep"
                    / "digit"
                    / "mnist_train"
                    / "index.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(
                index_payload,
                [{"fileName": "000000.png", "label": 8}],
            )
            folders_payload = json.loads(
                (
                    preparation_root
                    / "digits-prep"
                    / "digit"
                    / "folders.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(folders_payload, ["mnist_train"])
            self.assertTrue(
                (
                    preparation_root
                    / "digits-prep"
                    / "digit"
                    / "mnist_train"
                    / "000000.png"
                ).is_file()
            )

    def test_handle_should_prepare_digit_source_without_board_cleaning(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            preparation_root = Path(temp_directory) / "preparations"
            records = (
                DigitDatasetRecord(
                    sample_key="0",
                    image=np.full((28, 28), 255, dtype=np.uint8),
                    label=0,
                ),
                DigitDatasetRecord(
                    sample_key="1",
                    image=np.full((28, 28), 173, dtype=np.uint8),
                    label=4,
                ),
            )
            board_pipeline = _CountingCellPreprocessingPipeline()
            digit_preparation = _CountingDigitSamplePreparation()
            handler = self._create_handler(
                preparation_root=preparation_root,
                dataset_source_resolver=_DigitSourceResolver(),
                idx_dataset_loader=_IdxDatasetLoader(records),
                cell_preprocessing_pipeline=board_pipeline,
                digit_sample_preparation=digit_preparation,
            )

            result = handler.handle(
                CreateDatasetPreparationCommand(
                    preparation_name="digits-prep",
                    sources=(
                        CreateDatasetPreparationSourceDto(
                            name="mnist_train",
                            type="digit",
                        ),
                    ),
                )
            )

            self.assertEqual(result.status, "completed")
            self.assertEqual(board_pipeline.run_uint8_call_count, 0)
            self.assertEqual(digit_preparation.prepare_uint8_call_count, 1)
            self.assertEqual(digit_preparation.prepared_values, [173])

    def test_handle_should_write_board_preparation_with_only_non_zero_cells(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            root_path = Path(temp_directory)
            preparation_root = root_path / "preparations"
            source_root = root_path / "boards" / "v1_training"
            source_root.mkdir(parents=True)
            board_image_path = source_root / "nested" / "Image1.jpg"
            board_image_path.parent.mkdir(parents=True)
            board_label_path = board_image_path.with_suffix(".dat")
            cv2.imwrite(
                str(board_image_path),
                np.full((64, 64, 3), 255, dtype=np.uint8),
            )
            board_label_path.write_text("unused", encoding="utf-8")

            label_rows = [[0] * 9 for _ in range(9)]
            label_rows[0][0] = 1
            label_rows[0][1] = 7
            handler = self._create_handler(
                preparation_root=preparation_root,
                dataset_source_resolver=_BoardSourceResolver(source_root),
                board_dataset_scanner=_BoardDatasetScanner(
                    (
                        BoardDatasetPair(
                            group_key="nested/Image1.jpg",
                            board_name="Image1",
                            image_path=board_image_path,
                            label_path=board_label_path,
                        ),
                    )
                ),
                board_dat_parser=_BoardDatParser(label_rows),
                board_dataset_cell_extractor=_BoardDatasetCellExtractor(
                    _digit_like_image()
                ),
            )

            result = handler.handle(
                CreateDatasetPreparationCommand(
                    preparation_name="boards-prep",
                    sources=(
                        CreateDatasetPreparationSourceDto(
                            name="v1_training",
                            type="board",
                        ),
                    ),
                )
            )

            self.assertEqual(result.source_reports[0].prepared_items_count, 2)
            self.assertEqual(result.source_reports[0].empty_cell_count, 79)
            self.assertEqual(result.warnings, tuple())

            cells_index_payload = json.loads(
                (
                    preparation_root
                    / "boards-prep"
                    / "board"
                    / "v1_training"
                    / "nested__Image1"
                    / "cells"
                    / "index.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(
                cells_index_payload,
                [
                    {"fileName": "000.png", "label": 1},
                    {"fileName": "001.png", "label": 7},
                ],
            )
            file_manifest_payload = json.loads(
                (
                    preparation_root
                    / "boards-prep"
                    / "board"
                    / "v1_training"
                    / "file.json"
                ).read_text(encoding="utf-8")
            )
            self.assertEqual(file_manifest_payload, ["nested__Image1"])
            self.assertTrue(
                (
                    preparation_root
                    / "boards-prep"
                    / "board"
                    / "v1_training"
                    / "nested__Image1"
                    / "corrected-board.png"
                ).is_file()
            )

    def test_handle_should_raise_invalid_request_for_duplicate_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            handler = self._create_handler(
                preparation_root=Path(temp_directory) / "preparations",
            )

            with self.assertRaises(CreateDatasetPreparationCommandError) as raised_error:
                handler.handle(
                    CreateDatasetPreparationCommand(
                        preparation_name="prep-1",
                        sources=(
                            CreateDatasetPreparationSourceDto(
                                name="mnist_train",
                                type="digit",
                            ),
                            CreateDatasetPreparationSourceDto(
                                name="mnist_train",
                                type="digit",
                            ),
                        ),
                    )
                )

            self.assertEqual(raised_error.exception.error_type, "invalid_request")

    def test_handle_should_raise_board_not_found_when_all_boards_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            root_path = Path(temp_directory)
            preparation_root = root_path / "preparations"
            source_root = root_path / "boards" / "v1_training"
            source_root.mkdir(parents=True)
            board_image_path = source_root / "Image1.jpg"
            board_label_path = source_root / "Image1.dat"
            cv2.imwrite(
                str(board_image_path),
                np.full((32, 32, 3), 255, dtype=np.uint8),
            )
            board_label_path.write_text("unused", encoding="utf-8")
            handler = self._create_handler(
                preparation_root=preparation_root,
                dataset_source_resolver=_BoardSourceResolver(source_root),
                board_dataset_scanner=_BoardDatasetScanner(
                    (
                        BoardDatasetPair(
                            group_key="Image1.jpg",
                            board_name="Image1",
                            image_path=board_image_path,
                            label_path=board_label_path,
                        ),
                    )
                ),
                board_dat_parser=_BoardDatParser([[1] * 9 for _ in range(9)]),
                board_dataset_cell_extractor=_FailingBoardDatasetCellExtractor(),
            )

            with self.assertRaises(CreateDatasetPreparationCommandError) as raised_error:
                handler.handle(
                    CreateDatasetPreparationCommand(
                        preparation_name="boards-prep",
                        sources=(
                            CreateDatasetPreparationSourceDto(
                                name="v1_training",
                                type="board",
                            ),
                        ),
                    )
                )

            self.assertEqual(raised_error.exception.error_type, "board_not_found")
            self.assertFalse((preparation_root / "boards-prep").exists())

    def test_handle_should_skip_zero_labeled_board_cells_without_cleaning(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            root_path = Path(temp_directory)
            preparation_root = root_path / "preparations"
            source_root = root_path / "boards" / "v1_training"
            source_root.mkdir(parents=True)
            board_image_path = source_root / "Image1.jpg"
            board_label_path = source_root / "Image1.dat"
            cv2.imwrite(
                str(board_image_path),
                np.full((32, 32, 3), 255, dtype=np.uint8),
            )
            board_label_path.write_text("unused", encoding="utf-8")
            counting_pipeline = _CountingCellPreprocessingPipeline()
            handler = self._create_handler(
                preparation_root=preparation_root,
                dataset_source_resolver=_BoardSourceResolver(source_root),
                board_dataset_scanner=_BoardDatasetScanner(
                    (
                        BoardDatasetPair(
                            group_key="Image1.jpg",
                            board_name="Image1",
                            image_path=board_image_path,
                            label_path=board_label_path,
                        ),
                    )
                ),
                board_dat_parser=_BoardDatParser([[0] * 9 for _ in range(9)]),
                board_dataset_cell_extractor=_BoardDatasetCellExtractor(
                    _digit_like_image()
                ),
                cell_preprocessing_pipeline=counting_pipeline,
            )

            with self.assertRaises(CreateDatasetPreparationCommandError) as raised_error:
                handler.handle(
                    CreateDatasetPreparationCommand(
                        preparation_name="boards-prep",
                        sources=(
                            CreateDatasetPreparationSourceDto(
                                name="v1_training",
                                type="board",
                            ),
                        ),
                    )
                )

            self.assertEqual(raised_error.exception.error_type, "no_items_prepared")
            self.assertEqual(counting_pipeline.run_uint8_call_count, 0)
            self.assertFalse((preparation_root / "boards-prep").exists())

    def test_handle_should_raise_dataset_source_invalid_for_board_label_out_of_range(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            root_path = Path(temp_directory)
            preparation_root = root_path / "preparations"
            source_root = root_path / "boards" / "v1_training"
            source_root.mkdir(parents=True)
            board_image_path = source_root / "Image1.jpg"
            board_label_path = source_root / "Image1.dat"
            cv2.imwrite(
                str(board_image_path),
                np.full((32, 32, 3), 255, dtype=np.uint8),
            )
            board_label_path.write_text("unused", encoding="utf-8")
            label_rows = [[0] * 9 for _ in range(9)]
            label_rows[0][0] = 12
            handler = self._create_handler(
                preparation_root=preparation_root,
                dataset_source_resolver=_BoardSourceResolver(source_root),
                board_dataset_scanner=_BoardDatasetScanner(
                    (
                        BoardDatasetPair(
                            group_key="Image1.jpg",
                            board_name="Image1",
                            image_path=board_image_path,
                            label_path=board_label_path,
                        ),
                    )
                ),
                board_dat_parser=_BoardDatParser(label_rows),
                board_dataset_cell_extractor=_BoardDatasetCellExtractor(
                    _digit_like_image()
                ),
            )

            with self.assertRaises(CreateDatasetPreparationCommandError) as raised_error:
                handler.handle(
                    CreateDatasetPreparationCommand(
                        preparation_name="boards-prep",
                        sources=(
                            CreateDatasetPreparationSourceDto(
                                name="v1_training",
                                type="board",
                            ),
                        ),
                    )
                )

            self.assertEqual(
                raised_error.exception.error_type,
                "dataset_source_invalid",
            )
            self.assertFalse((preparation_root / "boards-prep").exists())

    def test_handle_should_cleanup_stage_directory_when_write_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_directory:
            preparation_root = Path(temp_directory) / "preparations"
            records = (
                DigitDatasetRecord(
                    sample_key="0",
                    image=_digit_like_image(),
                    label=3,
                ),
            )
            handler = self._create_handler(
                preparation_root=preparation_root,
                dataset_source_resolver=_DigitSourceResolver(),
                idx_dataset_loader=_IdxDatasetLoader(records),
                image_writer=_FailingImageArtifactWriter(),
            )

            with self.assertRaises(CreateDatasetPreparationCommandError) as raised_error:
                handler.handle(
                    CreateDatasetPreparationCommand(
                        preparation_name="digits-prep",
                        sources=(
                            CreateDatasetPreparationSourceDto(
                                name="mnist_train",
                                type="digit",
                            ),
                        ),
                    )
                )

            self.assertEqual(
                raised_error.exception.error_type,
                "dataset_preparation_write_failed",
            )
            self.assertFalse((preparation_root / "digits-prep").exists())
            self.assertFalse((preparation_root / ".digits-prep.staging").exists())

    def _create_handler(
        self,
        preparation_root: Path,
        dataset_source_resolver: object | None = None,
        board_dataset_scanner: object | None = None,
        board_dat_parser: object | None = None,
        idx_dataset_loader: object | None = None,
        board_dataset_cell_extractor: object | None = None,
        cell_preprocessing_pipeline: object | None = None,
        digit_sample_preparation: object | None = None,
        image_writer: object | None = None,
    ) -> CreateDatasetPreparationCommandHandler:
        path_provider = DatasetPreparationsPathProvider(str(preparation_root))
        workspace_manager = DatasetPreparationWorkspaceManager(path_provider)
        return CreateDatasetPreparationCommandHandler(
            dataset_source_resolver=dataset_source_resolver
            or _DigitSourceResolver(),
            board_dataset_scanner=board_dataset_scanner
            or _UnusedBoardDependency(),
            board_dat_parser=board_dat_parser or _UnusedBoardDependency(),
            idx_dataset_loader=idx_dataset_loader or _IdxDatasetLoader(tuple()),
            board_dataset_cell_extractor=board_dataset_cell_extractor
            or _UnusedBoardDependency(),
            board_cell_preprocessing_pipeline=cell_preprocessing_pipeline
            or CellPreprocessingPipeline(output_size=28),
            digit_sample_preparation=digit_sample_preparation
            or DigitSamplePreparationPipeline(),
            artifact_writer=DatasetPreparationArtifactWriter(
                path_provider=path_provider,
                image_artifact_writer=image_writer
                or FilesystemImageArtifactWriter(VisionImageCodec()),
            ),
            manifest_writer=DatasetPreparationManifestWriter(
                path_provider=path_provider,
                json_file_writer=JsonFileWriter(),
            ),
            workspace_manager=workspace_manager,
            artifact_cleanup=DatasetPreparationWorkspaceCleanup(workspace_manager),
            board_folder_name_resolver=BoardFolderNameResolver(),
            report_builder=DatasetPreparationReportBuilder(),
            utc_clock=_UtcClock(),
        )


@dataclass(frozen=True)
class _ResolvedSource:
    detected_type: str
    path: Path
    images_path: Path | None
    labels_path: Path | None


class _DigitSourceResolver:
    def resolve(self, source_name: str, requested_type: str) -> _ResolvedSource:
        del source_name
        del requested_type
        return _ResolvedSource(
            detected_type="digit",
            path=Path("."),
            images_path=Path("images.idx3-ubyte"),
            labels_path=Path("labels.idx1-ubyte"),
        )


class _BoardSourceResolver:
    def __init__(self, source_path: Path) -> None:
        self._source_path = source_path

    def resolve(self, source_name: str, requested_type: str) -> _ResolvedSource:
        del source_name
        del requested_type
        return _ResolvedSource(
            detected_type="board",
            path=self._source_path,
            images_path=None,
            labels_path=None,
        )


class _IdxDatasetLoader:
    def __init__(self, records: tuple[DigitDatasetRecord, ...]) -> None:
        self._records = records

    def load(
        self, images_path: Path, labels_path: Path
    ) -> tuple[DigitDatasetRecord, ...]:
        del images_path
        del labels_path
        return self._records


class _BoardDatasetScanner:
    def __init__(self, pairs: tuple[BoardDatasetPair, ...]) -> None:
        self._pairs = pairs

    def scan_pairs(self, source_directory: Path) -> tuple[BoardDatasetPair, ...]:
        del source_directory
        return self._pairs


class _BoardDatParser:
    def __init__(self, label_rows: list[list[int]]) -> None:
        self._label_rows = label_rows

    def parse(self, dat_file_path: Path) -> BoardGridLabel:
        del dat_file_path
        return BoardGridLabel.from_rows(self._label_rows)


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


class _FailingBoardDatasetCellExtractor:
    def extract(self, board_image: np.ndarray) -> tuple[np.ndarray, CellsGrid]:
        del board_image
        raise _BoardExtractionError("engine cells extraction failed")


class _BoardExtractionError(Exception):
    error_type = "cells_extraction_failed"


class _CountingCellPreprocessingPipeline:
    def __init__(self) -> None:
        self.run_uint8_call_count = 0

    def run_uint8(self, cell_image: np.ndarray) -> np.ndarray:
        self.run_uint8_call_count += 1
        return cell_image


class _CountingDigitSamplePreparation:
    def __init__(self) -> None:
        self.prepare_uint8_call_count = 0
        self.prepared_values: list[int] = []

    def prepare_uint8(self, sample_image: np.ndarray) -> np.ndarray:
        self.prepare_uint8_call_count += 1
        self.prepared_values.append(int(sample_image[0, 0]))
        return sample_image


class _FailingImageArtifactWriter:
    def write(self, path: Path, image: np.ndarray) -> None:
        del path
        del image
        raise OSError("disk full")


class _UnusedBoardDependency:
    def __getattr__(self, name: str) -> object:
        raise AssertionError(f"Board dependency {name} should not be used.")


class _UtcClock:
    def now(self) -> datetime:
        return datetime(2026, 6, 19, 19, 42, 11, tzinfo=UTC)


def _digit_like_image(offset: int = 0) -> np.ndarray:
    image = np.full((28, 28), 255, dtype=np.uint8)
    image[6 + offset : 22, 12:16] = 0
    image[6 + offset : 10 + offset, 8:20] = 0
    return image


if __name__ == "__main__":
    unittest.main()
