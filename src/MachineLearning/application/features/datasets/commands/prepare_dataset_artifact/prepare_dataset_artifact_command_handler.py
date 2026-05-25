import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import cv2
import numpy as np
from numpy.typing import NDArray

from application.features.datasets.commands.prepare_dataset_artifact.prepare_dataset_artifact_command import (
    PrepareDatasetArtifactCommand,
)
from application.features.datasets.commands.prepare_dataset_artifact.prepare_dataset_artifact_command_result_dto import (
    PrepareDatasetArtifactCommandResultDto,
)
from application.features.datasets.dto.canonical_prepared_sample_dto import (
    CanonicalPreparedSampleDto,
)
from application.features.datasets.dto.dataset_split_policy_dto import (
    DatasetSplitPolicyDto,
)
from application.features.datasets.dto.prepared_dataset_source_report_dto import (
    PreparedDatasetSourceReportDto,
)
from application.features.datasets.dto.split_sample_counts_dto import (
    SplitSampleCountsDto,
)
from application.features.datasets.errors.dataset_preparation_errors import (
    PrepareDatasetArtifactCommandError,
    UnsupportedPreprocessingProfileError,
)
from models.dataset_preview_index import (
    BoardCellPreviewEntry,
    BoardPreviewEntry,
    BoardSourcePreview,
    DatasetPreviewIndex,
    DigitSamplePreviewEntry,
    DigitSourcePreview,
)
from infrastructure.datasets.board_dataset_scanner import BoardDatasetPair
from infrastructure.datasets.idx_dataset_loader import DigitDatasetRecord
from models.board_grid_label import BoardGridLabel
from models.cells_grid import CellsGrid
from models.dataset_source_type import DatasetSourceType
from models.dataset_split import DatasetSplit

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ResolvedDatasetSourceDto:
    name: str
    requested_type: str
    detected_type: str
    path: Path
    images_path: Path | None
    labels_path: Path | None


class DatasetSourceResolver(Protocol):
    def resolve(self, source_name: str, requested_type: str) -> object: ...


class BoardDatasetScanner(Protocol):
    def scan_pairs(self, source_directory: Path) -> tuple[BoardDatasetPair, ...]: ...


class BoardDatParser(Protocol):
    def parse(self, dat_file_path: Path) -> BoardGridLabel: ...


class IdxDatasetLoader(Protocol):
    def load(
        self, images_path: Path, labels_path: Path
    ) -> tuple[DigitDatasetRecord, ...]: ...


class SampleSplitAssigner(Protocol):
    def assign_split(
        self, split_policy: DatasetSplitPolicyDto, stable_key: str
    ) -> DatasetSplit: ...


class CellPreprocessingPipeline(Protocol):
    def run_uint8(self, cell_image: NDArray[np.uint8]) -> NDArray[np.uint8]: ...

    def run(self, cell_image: NDArray[np.uint8]) -> NDArray[np.float32]: ...


class NpzDatasetArtifactWriter(Protocol):
    def write(
        self,
        output_path: Path,
        x_train: NDArray[np.float32],
        y_train: NDArray[np.int64],
        x_val: NDArray[np.float32],
        y_val: NDArray[np.int64],
        x_test: NDArray[np.float32],
        y_test: NDArray[np.int64],
    ) -> None: ...


class TempDatasetPathProvider(Protocol):
    def for_name(self, dataset_name: str) -> Path: ...


class DatasetPreviewPathProvider(Protocol):
    def create_stage_dir(self, dataset_name: str) -> Path: ...

    def promote_stage_dir(self, dataset_name: str, stage_dir: Path) -> Path: ...

    def index_path(self, dataset_root: Path) -> Path: ...

    def board_corrected_image_path(
        self,
        dataset_root: Path,
        source_name: str,
        board_name: str,
    ) -> Path: ...

    def board_cell_image_path(
        self,
        dataset_root: Path,
        source_name: str,
        board_name: str,
        cell_index: int,
    ) -> Path: ...

    def digit_sample_image_path(
        self,
        dataset_root: Path,
        source_name: str,
        sample_key: str,
    ) -> Path: ...

    def to_relative_path(self, dataset_root: Path, artifact_path: Path) -> str: ...


class FilesystemImageArtifactWriter(Protocol):
    def write(self, path: Path, image: NDArray[np.uint8]) -> None: ...


class DatasetPreviewIndexWriter(Protocol):
    def write(self, path: Path, preview_index: DatasetPreviewIndex) -> None: ...


class DatasetPreparationArtifactCleanup(Protocol):
    def cleanup(
        self,
        dataset_name: str,
        preview_stage_dir: Path | None,
        dataset_artifact_path: Path | None,
    ) -> None: ...


class PreparationReportBuilder(Protocol):
    def build_source_report(
        self,
        name: str,
        requested_type: str,
        detected_type: str,
        processed_sample_count: int,
        included_sample_count: int,
        empty_cell_count: int,
        rejected_sample_count: int,
        warnings: list[str] | tuple[str, ...],
    ) -> PreparedDatasetSourceReportDto: ...


class GrayscaleBlurPreprocessor(Protocol):
    def preprocess(self, image: NDArray[np.uint8]) -> NDArray[np.uint8]: ...


class AdaptiveThresholdBinarizer(Protocol):
    def binarize(self, image: NDArray[np.uint8]) -> NDArray[np.uint8]: ...


class BoardQuadDetector(Protocol):
    def detect(self, image: NDArray[np.uint8]) -> object: ...


class PerspectiveTransformer(Protocol):
    def transform(
        self, image: NDArray[np.uint8], board_quad: object
    ) -> NDArray[np.uint8]: ...


class BoardCellsExtractor(Protocol):
    def extract(self, board_image: NDArray[np.uint8]) -> CellsGrid: ...


@dataclass(frozen=True)
class ExtractedBoardCellsResult:
    corrected_board: NDArray[np.uint8]
    cells: tuple[NDArray[np.uint8], ...]


class PrepareDatasetArtifactCommandHandler:
    def __init__(
        self,
        dataset_source_resolver: DatasetSourceResolver,
        board_dataset_scanner: BoardDatasetScanner,
        board_dat_parser: BoardDatParser,
        idx_dataset_loader: IdxDatasetLoader,
        sample_split_assigner: SampleSplitAssigner,
        cell_preprocessing_pipeline: CellPreprocessingPipeline,
        npz_dataset_artifact_writer: NpzDatasetArtifactWriter,
        temp_dataset_path_provider: TempDatasetPathProvider,
        dataset_preview_path_provider: DatasetPreviewPathProvider,
        preview_image_artifact_writer: FilesystemImageArtifactWriter,
        dataset_preview_index_writer: DatasetPreviewIndexWriter,
        dataset_preparation_artifact_cleanup: DatasetPreparationArtifactCleanup,
        preparation_report_builder: PreparationReportBuilder,
        grayscale_blur_preprocessor: GrayscaleBlurPreprocessor,
        adaptive_threshold_binarizer: AdaptiveThresholdBinarizer,
        board_quad_detector: BoardQuadDetector,
        perspective_transformer: PerspectiveTransformer,
        board_cells_extractor: BoardCellsExtractor,
    ) -> None:
        self._dataset_source_resolver = dataset_source_resolver
        self._board_dataset_scanner = board_dataset_scanner
        self._board_dat_parser = board_dat_parser
        self._idx_dataset_loader = idx_dataset_loader
        self._sample_split_assigner = sample_split_assigner
        self._cell_preprocessing_pipeline = cell_preprocessing_pipeline
        self._npz_dataset_artifact_writer = npz_dataset_artifact_writer
        self._temp_dataset_path_provider = temp_dataset_path_provider
        self._dataset_preview_path_provider = dataset_preview_path_provider
        self._preview_image_artifact_writer = preview_image_artifact_writer
        self._dataset_preview_index_writer = dataset_preview_index_writer
        self._dataset_preparation_artifact_cleanup = (
            dataset_preparation_artifact_cleanup
        )
        self._preparation_report_builder = preparation_report_builder
        self._grayscale_blur_preprocessor = grayscale_blur_preprocessor
        self._adaptive_threshold_binarizer = adaptive_threshold_binarizer
        self._board_quad_detector = board_quad_detector
        self._perspective_transformer = perspective_transformer
        self._board_cells_extractor = board_cells_extractor

    def handle(
        self, command: PrepareDatasetArtifactCommand
    ) -> PrepareDatasetArtifactCommandResultDto:
        self._validate_command(command)

        all_samples: list[CanonicalPreparedSampleDto] = []
        source_reports: list[PreparedDatasetSourceReportDto] = []
        board_source_previews: list[BoardSourcePreview] = []
        digit_source_previews: list[DigitSourcePreview] = []
        global_warnings: list[str] = []
        target_path = self._temp_dataset_path_provider.for_name(command.dataset_name)
        preview_stage_dir = self._dataset_preview_path_provider.create_stage_dir(
            command.dataset_name
        )

        try:
            for source in command.sources:
                resolved_source = self._resolve_source(
                    source_name=source.name,
                    requested_type=source.type,
                )
                if resolved_source.detected_type != source.type:
                    raise PrepareDatasetArtifactCommandError(
                        error_type="raw_dataset_type_mismatch",
                        message=(
                            f"Źródło {source.name} zostało wykryte jako "
                            f"{resolved_source.detected_type} i nie pasuje "
                            f"do deklaracji {source.type}."
                        ),
                    )

                if resolved_source.detected_type == "board":
                    (
                        prepared,
                        source_report,
                        board_source_preview,
                    ) = self._prepare_board_source(
                        source_name=source.name,
                        split_policy=source.split_policy,
                        source_path=resolved_source.path,
                        preview_stage_dir=preview_stage_dir,
                    )
                    board_source_previews.append(board_source_preview)
                else:
                    (
                        prepared,
                        source_report,
                        digit_source_preview,
                    ) = self._prepare_digit_source(
                        source_name=source.name,
                        split_policy=source.split_policy,
                        images_path=resolved_source.images_path,
                        labels_path=resolved_source.labels_path,
                        preview_stage_dir=preview_stage_dir,
                    )
                    digit_source_previews.append(digit_source_preview)

                all_samples.extend(prepared)
                source_reports.append(source_report)
                global_warnings.extend(source_report.warnings)

            supervised_samples = [
                sample for sample in all_samples if sample.label is not None
            ]
            if not supervised_samples:
                raise PrepareDatasetArtifactCommandError(
                    error_type="no_samples_prepared",
                    message="Nie przygotowano żadnych próbek nadzorowanych.",
                )

            split_arrays = self._build_split_arrays(supervised_samples)
            preview_index = DatasetPreviewIndex(
                dataset_name=command.dataset_name,
                preprocessing_profile=command.preprocessing_profile,
                board_sources=tuple(board_source_previews),
                digit_sources=tuple(digit_source_previews),
            )
            self._write_preview_index(
                preview_stage_dir=preview_stage_dir,
                preview_index=preview_index,
            )

            try:
                self._npz_dataset_artifact_writer.write(
                    output_path=target_path,
                    x_train=split_arrays["x_train"],
                    y_train=split_arrays["y_train"],
                    x_val=split_arrays["x_val"],
                    y_val=split_arrays["y_val"],
                    x_test=split_arrays["x_test"],
                    y_test=split_arrays["y_test"],
                )
            except OSError as error:
                raise PrepareDatasetArtifactCommandError(
                    error_type="dataset_artifact_write_failed",
                    message="Nie udało się zapisać artefaktu datasetu.",
                ) from error

            try:
                self._dataset_preview_path_provider.promote_stage_dir(
                    command.dataset_name,
                    preview_stage_dir,
                )
            except OSError as error:
                raise PrepareDatasetArtifactCommandError(
                    error_type="dataset_preview_write_failed",
                    message="Nie udało się sfinalizować artefaktów preview.",
                ) from error
        except Exception:
            self._cleanup_partial_artifacts(
                dataset_name=command.dataset_name,
                preview_stage_dir=preview_stage_dir,
                dataset_artifact_path=target_path,
            )
            raise

        sample_counts = SplitSampleCountsDto(
            train=int(split_arrays["x_train"].shape[0]),
            val=int(split_arrays["x_val"].shape[0]),
            test=int(split_arrays["x_test"].shape[0]),
        )

        return PrepareDatasetArtifactCommandResultDto(
            sample_counts=sample_counts,
            sources=tuple(source_reports),
            warnings=tuple(global_warnings),
        )

    def _validate_command(self, command: PrepareDatasetArtifactCommand) -> None:
        if not command.dataset_name.strip():
            raise PrepareDatasetArtifactCommandError(
                error_type="invalid_request",
                message="Pole datasetName jest wymagane.",
            )
        if not command.sources:
            raise PrepareDatasetArtifactCommandError(
                error_type="invalid_request",
                message="Pole sources musi zawierać co najmniej jedno źródło.",
            )
        if command.preprocessing_profile != "default-28x28-v1":
            raise UnsupportedPreprocessingProfileError(
                command.preprocessing_profile
            )

    def _resolve_source(
        self, source_name: str, requested_type: str
    ) -> ResolvedDatasetSourceDto:
        try:
            resolved_source = self._dataset_source_resolver.resolve(
                source_name=source_name,
                requested_type=requested_type,
            )
        except ValueError as error:
            raise PrepareDatasetArtifactCommandError(
                error_type="raw_dataset_not_found",
                message=str(error),
            ) from error

        return ResolvedDatasetSourceDto(
            name=source_name,
            requested_type=requested_type,
            detected_type=resolved_source.detected_type,
            path=resolved_source.path,
            images_path=resolved_source.images_path,
            labels_path=resolved_source.labels_path,
        )

    def _prepare_board_source(
        self,
        source_name: str,
        split_policy: DatasetSplitPolicyDto,
        source_path: Path,
        preview_stage_dir: Path,
    ) -> tuple[
        list[CanonicalPreparedSampleDto],
        PreparedDatasetSourceReportDto,
        BoardSourcePreview,
    ]:
        try:
            board_pairs = self._board_dataset_scanner.scan_pairs(source_path)
        except ValueError as error:
            raise PrepareDatasetArtifactCommandError(
                error_type="dataset_source_invalid",
                message=str(error),
            ) from error

        prepared_samples: list[CanonicalPreparedSampleDto] = []
        rejected_sample_count = 0
        empty_cell_count = 0
        source_warnings: list[str] = []
        board_previews: list[BoardPreviewEntry] = []

        for board_pair in board_pairs:
            split = self._sample_split_assigner.assign_split(
                split_policy=split_policy,
                stable_key=board_pair.group_key,
            )
            try:
                board_grid_label = self._board_dat_parser.parse(
                    board_pair.label_path
                )
                board_image = self._load_board_image(board_pair.image_path)
                extracted_board = self._extract_board_cells(board_image)
            except (ValueError, OSError) as error:
                rejected_sample_count += 81
                source_warnings.append(
                    f"Pominięto planszę {board_pair.board_name}: {error}."
                )
                continue

            corrected_board_path = (
                self._dataset_preview_path_provider.board_corrected_image_path(
                    preview_stage_dir,
                    source_name,
                    board_pair.board_name,
                )
            )
            self._write_preview_image(
                image_path=corrected_board_path,
                image=extracted_board.corrected_board,
            )

            flattened_labels = board_grid_label.flatten()
            board_cell_previews: list[BoardCellPreviewEntry] = []
            for cell_index, cell_image in enumerate(extracted_board.cells):
                raw_label = flattened_labels[cell_index]
                normalized_label = None if raw_label == 0 else raw_label

                try:
                    preview_image, processed_image = (
                        self._build_preview_and_training_image(
                            cell_image
                        )
                    )
                except ValueError:
                    rejected_sample_count += 1
                    continue

                included_in_dataset = normalized_label is not None
                if normalized_label is None:
                    empty_cell_count += 1

                cell_preview_path = (
                    self._dataset_preview_path_provider.board_cell_image_path(
                        preview_stage_dir,
                        source_name,
                        board_pair.board_name,
                        cell_index,
                    )
                )
                self._write_preview_image(
                    image_path=cell_preview_path,
                    image=preview_image,
                )
                board_cell_previews.append(
                    BoardCellPreviewEntry(
                        cell_index=cell_index,
                        label=normalized_label,
                        preview_image_relative_path=(
                            self._dataset_preview_path_provider.to_relative_path(
                                preview_stage_dir,
                                cell_preview_path,
                            )
                        ),
                        included_in_dataset=included_in_dataset,
                    )
                )

                prepared_samples.append(
                    CanonicalPreparedSampleDto(
                        split=split.value,
                        label=normalized_label,
                        source_type=DatasetSourceType.BOARD_DERIVED.value,
                        source_dataset_name=source_name,
                        source_board_name=board_pair.board_name,
                        source_sample_key=None,
                        cell_index=cell_index,
                        image_28x28=processed_image,
                    )
                )

            board_previews.append(
                BoardPreviewEntry(
                    board_name=board_pair.board_name,
                    split=split.value,
                    corrected_board_image_relative_path=(
                        self._dataset_preview_path_provider.to_relative_path(
                            preview_stage_dir,
                            corrected_board_path,
                        )
                    ),
                    cells=tuple(board_cell_previews),
                )
            )

        source_report = self._preparation_report_builder.build_source_report(
            name=source_name,
            requested_type="board",
            detected_type="board",
            processed_sample_count=len(prepared_samples) + rejected_sample_count,
            included_sample_count=sum(
                1 for sample in prepared_samples if sample.label is not None
            ),
            empty_cell_count=empty_cell_count,
            rejected_sample_count=rejected_sample_count,
            warnings=source_warnings,
        )
        return (
            prepared_samples,
            source_report,
            BoardSourcePreview(
                source_name=source_name,
                boards=tuple(board_previews),
            ),
        )

    def _prepare_digit_source(
        self,
        source_name: str,
        split_policy: DatasetSplitPolicyDto,
        images_path: Path | None,
        labels_path: Path | None,
        preview_stage_dir: Path,
    ) -> tuple[
        list[CanonicalPreparedSampleDto],
        PreparedDatasetSourceReportDto,
        DigitSourcePreview,
    ]:
        if images_path is None or labels_path is None:
            raise PrepareDatasetArtifactCommandError(
                error_type="dataset_source_invalid",
                message=f"Źródło {source_name} nie zawiera kompletnej pary IDX.",
            )

        try:
            records = self._idx_dataset_loader.load(images_path, labels_path)
        except ValueError as error:
            raise PrepareDatasetArtifactCommandError(
                error_type="dataset_source_invalid",
                message=str(error),
            ) from error

        prepared_samples: list[CanonicalPreparedSampleDto] = []
        digit_previews: list[DigitSamplePreviewEntry] = []
        rejected_sample_count = 0
        for record in records:
            split = self._sample_split_assigner.assign_split(
                split_policy=split_policy,
                stable_key=record.sample_key,
            )
            try:
                preview_image, processed_image = (
                    self._build_preview_and_training_image(record.image)
                )
            except ValueError:
                rejected_sample_count += 1
                continue

            sample_preview_path = (
                self._dataset_preview_path_provider.digit_sample_image_path(
                    preview_stage_dir,
                    source_name,
                    record.sample_key,
                )
            )
            self._write_preview_image(
                image_path=sample_preview_path,
                image=preview_image,
            )
            digit_previews.append(
                DigitSamplePreviewEntry(
                    sample_index=record.sample_key,
                    split=split.value,
                    label=record.label,
                    preview_image_relative_path=(
                        self._dataset_preview_path_provider.to_relative_path(
                            preview_stage_dir,
                            sample_preview_path,
                        )
                    ),
                    included_in_dataset=True,
                )
            )

            prepared_samples.append(
                CanonicalPreparedSampleDto(
                    split=split.value,
                    label=record.label,
                    source_type=DatasetSourceType.DIGIT.value,
                    source_dataset_name=source_name,
                    source_board_name=None,
                    source_sample_key=record.sample_key,
                    cell_index=None,
                    image_28x28=processed_image,
                )
            )

        source_report = self._preparation_report_builder.build_source_report(
            name=source_name,
            requested_type="digit",
            detected_type="digit",
            processed_sample_count=len(prepared_samples) + rejected_sample_count,
            included_sample_count=len(prepared_samples),
            empty_cell_count=0,
            rejected_sample_count=rejected_sample_count,
            warnings=[],
        )
        return (
            prepared_samples,
            source_report,
            DigitSourcePreview(
                source_name=source_name,
                samples=tuple(digit_previews),
            ),
        )

    def _write_preview_image(
        self,
        image_path: Path,
        image: NDArray[np.uint8],
    ) -> None:
        try:
            self._preview_image_artifact_writer.write(image_path, image)
        except (OSError, ValueError) as error:
            raise PrepareDatasetArtifactCommandError(
                error_type="dataset_preview_write_failed",
                message="Nie udało się zapisać obrazu preview datasetu.",
            ) from error

    def _write_preview_index(
        self,
        preview_stage_dir: Path,
        preview_index: DatasetPreviewIndex,
    ) -> None:
        try:
            self._dataset_preview_index_writer.write(
                path=self._dataset_preview_path_provider.index_path(
                    preview_stage_dir
                ),
                preview_index=preview_index,
            )
        except OSError as error:
            raise PrepareDatasetArtifactCommandError(
                error_type="dataset_preview_index_write_failed",
                message="Nie udało się zapisać indeksu preview datasetu.",
            ) from error

    def _build_preview_and_training_image(
        self,
        cell_image: NDArray[np.uint8],
    ) -> tuple[NDArray[np.uint8], NDArray[np.float32]]:
        preview_image = self._cell_preprocessing_pipeline.run_uint8(cell_image)
        processed_image = preview_image.astype(np.float32) / 255.0
        return preview_image, processed_image

    def _cleanup_partial_artifacts(
        self,
        dataset_name: str,
        preview_stage_dir: Path | None,
        dataset_artifact_path: Path | None,
    ) -> None:
        try:
            self._dataset_preparation_artifact_cleanup.cleanup(
                dataset_name=dataset_name,
                preview_stage_dir=preview_stage_dir,
                dataset_artifact_path=dataset_artifact_path,
            )
        except OSError:
            LOGGER.warning(
                "Nie udało się wyczyścić częściowych artefaktów datasetu.",
                extra={"datasetName": dataset_name},
            )

    def _load_board_image(self, image_path: Path) -> NDArray[np.uint8]:
        board_image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if board_image is None:
            raise ValueError(f"Nie udało się odczytać obrazu {image_path.name}.")
        return board_image

    def _extract_board_cells(
        self, board_image: NDArray[np.uint8]
    ) -> ExtractedBoardCellsResult:
        preprocessed = self._grayscale_blur_preprocessor.preprocess(board_image)
        binary = self._adaptive_threshold_binarizer.binarize(preprocessed)
        board_quad = self._board_quad_detector.detect(binary)
        corrected_board = self._perspective_transformer.transform(
            board_image, board_quad
        )
        cells_grid = self._board_cells_extractor.extract(corrected_board)
        cells_grid.validate_dimensions(expected_rows=9, expected_cols=9)

        flattened_cells: list[NDArray[np.uint8]] = []
        for row in cells_grid.cells:
            flattened_cells.extend(row)
        return ExtractedBoardCellsResult(
            corrected_board=corrected_board,
            cells=tuple(flattened_cells),
        )

    def _build_split_arrays(
        self, supervised_samples: list[CanonicalPreparedSampleDto]
    ) -> dict[str, NDArray[np.float32] | NDArray[np.int64]]:
        by_split: dict[str, list[CanonicalPreparedSampleDto]] = {
            DatasetSplit.TRAIN.value: [],
            DatasetSplit.VAL.value: [],
            DatasetSplit.TEST.value: [],
        }

        for sample in supervised_samples:
            if sample.split not in by_split:
                continue
            by_split[sample.split].append(sample)

        return {
            "x_train": self._build_images_array(by_split[DatasetSplit.TRAIN.value]),
            "y_train": self._build_labels_array(by_split[DatasetSplit.TRAIN.value]),
            "x_val": self._build_images_array(by_split[DatasetSplit.VAL.value]),
            "y_val": self._build_labels_array(by_split[DatasetSplit.VAL.value]),
            "x_test": self._build_images_array(by_split[DatasetSplit.TEST.value]),
            "y_test": self._build_labels_array(by_split[DatasetSplit.TEST.value]),
        }

    def _build_images_array(
        self, samples: list[CanonicalPreparedSampleDto]
    ) -> NDArray[np.float32]:
        if not samples:
            return np.empty((0, 28, 28), dtype=np.float32)
        images = [sample.image_28x28 for sample in samples]
        return np.stack(images).astype(np.float32)

    def _build_labels_array(
        self, samples: list[CanonicalPreparedSampleDto]
    ) -> NDArray[np.int64]:
        if not samples:
            return np.empty((0,), dtype=np.int64)
        labels = [int(sample.label) for sample in samples if sample.label is not None]
        return np.array(labels, dtype=np.int64)
