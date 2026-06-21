from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from numpy.typing import NDArray

from application.features.datasets.commands.create_dataset_preparation.create_dataset_preparation_command import (
    CreateDatasetPreparationCommand,
)
from application.features.datasets.commands.create_dataset_preparation.create_dataset_preparation_command_result_dto import (
    CreateDatasetPreparationCommandResultDto,
)
from application.features.datasets.dto.dataset_preparation_item_index_entry_dto import (
    DatasetPreparationItemIndexEntryDto,
)
from application.features.datasets.dto.dataset_preparation_source_report_dto import (
    DatasetPreparationSourceReportDto,
)
from application.features.datasets.errors.dataset_preparation_errors import (
    BoardNotFoundError,
    CreateDatasetPreparationCommandError,
    DatasetPreparationFinalizeFailedError,
    DatasetPreparationWriteFailedError,
)
from application.features.datasets.ports.dataset_preparation_ports import (
    BoardDatParserPort,
    BoardDatasetCellExtractorPort,
    BoardDatasetScannerPort,
    BoardFolderNameResolverPort,
    CellPreprocessingPipelinePort,
    DigitSamplePreparationPort,
    DatasetPreparationArtifactCleanupPort,
    DatasetPreparationArtifactWriterPort,
    DatasetPreparationManifestWriterPort,
    DatasetPreparationReportBuilderPort,
    DatasetPreparationWorkspaceManagerPort,
    DatasetSourceResolverPort,
    IdxDatasetLoaderPort,
    UtcClockPort,
)
from models.board_grid_label import BoardGridLabel
from models.cells_grid import CellsGrid
from models.dataset_preparation_status import DatasetPreparationStatus
from models.dataset_source_type import DatasetSourceType

LOGGER = logging.getLogger(__name__)
_SUPPORTED_SOURCE_TYPES = {
    DatasetSourceType.BOARD.value,
    DatasetSourceType.DIGIT.value,
}


@dataclass(frozen=True)
class _ResolvedDatasetSource:
    detected_type: str
    path: Path
    images_path: Path | None
    labels_path: Path | None


@dataclass(frozen=True)
class _PreparedBoardSourceResult:
    report: DatasetPreparationSourceReportDto
    warnings: tuple[str, ...]
    board_folder_names: tuple[str, ...]


@dataclass(frozen=True)
class _PreparedDigitSourceResult:
    report: DatasetPreparationSourceReportDto
    warnings: tuple[str, ...]


class CreateDatasetPreparationCommandHandler:
    def __init__(
        self,
        dataset_source_resolver: DatasetSourceResolverPort,
        board_dataset_scanner: BoardDatasetScannerPort,
        board_dat_parser: BoardDatParserPort,
        idx_dataset_loader: IdxDatasetLoaderPort,
        board_dataset_cell_extractor: BoardDatasetCellExtractorPort,
        board_cell_preprocessing_pipeline: CellPreprocessingPipelinePort,
        digit_sample_preparation: DigitSamplePreparationPort,
        artifact_writer: DatasetPreparationArtifactWriterPort,
        manifest_writer: DatasetPreparationManifestWriterPort,
        workspace_manager: DatasetPreparationWorkspaceManagerPort,
        artifact_cleanup: DatasetPreparationArtifactCleanupPort,
        board_folder_name_resolver: BoardFolderNameResolverPort,
        report_builder: DatasetPreparationReportBuilderPort,
        utc_clock: UtcClockPort,
    ) -> None:
        self._dataset_source_resolver = dataset_source_resolver
        self._board_dataset_scanner = board_dataset_scanner
        self._board_dat_parser = board_dat_parser
        self._idx_dataset_loader = idx_dataset_loader
        self._board_dataset_cell_extractor = board_dataset_cell_extractor
        self._board_cell_preprocessing_pipeline = board_cell_preprocessing_pipeline
        self._digit_sample_preparation = digit_sample_preparation
        self._artifact_writer = artifact_writer
        self._manifest_writer = manifest_writer
        self._workspace_manager = workspace_manager
        self._artifact_cleanup = artifact_cleanup
        self._board_folder_name_resolver = board_folder_name_resolver
        self._report_builder = report_builder
        self._utc_clock = utc_clock

    def handle(
        self, command: CreateDatasetPreparationCommand
    ) -> CreateDatasetPreparationCommandResultDto:
        self._validate_command(command)

        stage_dir = self._workspace_manager.create_stage_dir(
            command.preparation_name
        )
        source_reports: list[DatasetPreparationSourceReportDto] = []
        warnings: list[str] = []
        board_source_names: list[str] = []
        digit_source_names: list[str] = []

        LOGGER.info(
            "Dataset preparation request started: preparation=%s source_count=%s source_types=%s",
            command.preparation_name,
            len(command.sources),
            [source.type for source in command.sources],
        )

        try:
            for source in command.sources:
                LOGGER.info(
                    "Preparing dataset source: preparation=%s source=%s type=%s",
                    command.preparation_name,
                    source.name,
                    source.type,
                )
                resolved_source = self._resolve_source(
                    source_name=source.name,
                    requested_type=source.type,
                )
                self._ensure_type_matches(
                    source_name=source.name,
                    requested_type=source.type,
                    detected_type=resolved_source.detected_type,
                )

                if resolved_source.detected_type == DatasetSourceType.BOARD.value:
                    board_result = self._prepare_board_source(
                        stage_dir=stage_dir,
                        source_name=source.name,
                        source_path=resolved_source.path,
                    )
                    source_reports.append(board_result.report)
                    warnings.extend(board_result.warnings)
                    board_source_names.append(source.name)
                else:
                    digit_result = self._prepare_digit_source(
                        stage_dir=stage_dir,
                        source_name=source.name,
                        images_path=resolved_source.images_path,
                        labels_path=resolved_source.labels_path,
                    )
                    source_reports.append(digit_result.report)
                    warnings.extend(digit_result.warnings)
                    digit_source_names.append(source.name)

            self._ensure_anything_prepared(source_reports)
            self._manifest_writer.write_board_folders(
                stage_dir=stage_dir,
                source_names=tuple(board_source_names),
            )
            self._manifest_writer.write_digit_folders(
                stage_dir=stage_dir,
                source_names=tuple(digit_source_names),
            )
            try:
                self._workspace_manager.promote(
                    command.preparation_name,
                    stage_dir,
                )
            except OSError as error:
                raise DatasetPreparationFinalizeFailedError(
                    "Nie udało się sfinalizować katalogu przygotowania datasetu."
                ) from error
        except CreateDatasetPreparationCommandError:
            self._cleanup(command.preparation_name, stage_dir)
            raise
        except OSError as error:
            self._cleanup(command.preparation_name, stage_dir)
            raise DatasetPreparationWriteFailedError(
                "Nie udało się zapisać artefaktów przygotowania datasetu."
            ) from error
        except Exception:
            self._cleanup(command.preparation_name, stage_dir)
            raise

        created_at_utc = self._format_utc(self._utc_clock.now())
        LOGGER.info(
            "Dataset preparation request succeeded: preparation=%s sources=%s warnings_count=%s",
            command.preparation_name,
            len(source_reports),
            len(warnings),
        )
        return CreateDatasetPreparationCommandResultDto(
            preparation_name=command.preparation_name,
            created_at_utc=created_at_utc,
            status=DatasetPreparationStatus.COMPLETED.value,
            source_reports=tuple(source_reports),
            warnings=tuple(warnings),
        )

    def _validate_command(self, command: CreateDatasetPreparationCommand) -> None:
        if not self._is_valid_path_component(command.preparation_name):
            raise CreateDatasetPreparationCommandError(
                error_type="invalid_request",
                message="Pole preparationName jest wymagane i musi być poprawną nazwą katalogu.",
            )
        if not command.sources:
            raise CreateDatasetPreparationCommandError(
                error_type="invalid_request",
                message="Pole sources musi zawierać co najmniej jedno źródło.",
            )

        seen_sources: set[tuple[str, str]] = set()
        for source in command.sources:
            normalized_type = source.type.strip().lower()
            if normalized_type not in _SUPPORTED_SOURCE_TYPES:
                raise CreateDatasetPreparationCommandError(
                    error_type="invalid_request",
                    message=f"Typ źródła {source.type} nie jest obsługiwany.",
                )
            if not self._is_valid_path_component(source.name):
                raise CreateDatasetPreparationCommandError(
                    error_type="invalid_request",
                    message=(
                        "Każde źródło musi zawierać poprawną nazwę bez separatorów ścieżek."
                    ),
                )
            source_key = (source.name, normalized_type)
            if source_key in seen_sources:
                raise CreateDatasetPreparationCommandError(
                    error_type="invalid_request",
                    message="Lista sources zawiera duplikaty.",
                )
            seen_sources.add(source_key)

    def _resolve_source(
        self,
        source_name: str,
        requested_type: str,
    ) -> _ResolvedDatasetSource:
        try:
            resolved_source = self._dataset_source_resolver.resolve(
                source_name=source_name,
                requested_type=requested_type,
            )
        except ValueError as error:
            raise CreateDatasetPreparationCommandError(
                error_type="raw_dataset_not_found",
                message=str(error),
            ) from error

        return _ResolvedDatasetSource(
            detected_type=resolved_source.detected_type,
            path=resolved_source.path,
            images_path=resolved_source.images_path,
            labels_path=resolved_source.labels_path,
        )

    def _ensure_type_matches(
        self,
        source_name: str,
        requested_type: str,
        detected_type: str,
    ) -> None:
        if requested_type != detected_type:
            raise CreateDatasetPreparationCommandError(
                error_type="raw_dataset_type_mismatch",
                message=(
                    f"Źródło {source_name} zostało wykryte jako {detected_type} "
                    f"i nie pasuje do deklaracji {requested_type}."
                ),
            )

    def _prepare_board_source(
        self,
        stage_dir: Path,
        source_name: str,
        source_path: Path,
    ) -> _PreparedBoardSourceResult:
        try:
            board_pairs = self._board_dataset_scanner.scan_pairs(source_path)
        except ValueError as error:
            raise CreateDatasetPreparationCommandError(
                error_type="dataset_source_invalid",
                message=str(error),
            ) from error

        board_folder_names: list[str] = []
        warnings: list[str] = []
        prepared_items_count = 0
        rejected_items_count = 0
        empty_cell_count = 0
        valid_board_count = 0

        for board_pair in board_pairs:
            LOGGER.info(
                "Preparing board item: source=%s board=%s",
                source_name,
                board_pair.board_name,
            )
            try:
                prepared_board = self._prepare_single_board(
                    board_pair,
                    board_folder_names,
                )
            except CreateDatasetPreparationCommandError:
                raise
            except (OSError, ValueError) as error:
                rejected_items_count += 1
                warning_message = (
                    f"Pominięto planszę {board_pair.board_name}: {error}"
                )
                warnings.append(warning_message)
                LOGGER.warning(
                    "Board item rejected: source=%s board=%s message=%s",
                    source_name,
                    board_pair.board_name,
                    error,
                )
                continue
            except Exception as error:
                if getattr(error, "error_type", None) in {
                    "board_not_found",
                    "perspective_correction_failed",
                    "invalid_board_image_shape",
                    "cells_extraction_failed",
                }:
                    rejected_items_count += 1
                    warning_message = (
                        f"Pominięto planszę {board_pair.board_name}: {error}"
                    )
                    warnings.append(warning_message)
                    LOGGER.warning(
                        "Board item rejected by engine: source=%s board=%s message=%s",
                        source_name,
                        board_pair.board_name,
                        error,
                    )
                    continue
                raise

            valid_board_count += 1
            if not prepared_board.index_entries:
                warnings.append(
                    f"Plansza {prepared_board.board_folder_name} nie dała żadnej zapisanej komórki 1..9."
                )
                LOGGER.warning(
                    "Board item produced no labeled cells: source=%s board=%s",
                    source_name,
                    prepared_board.board_folder_name,
                )
                continue

            try:
                self._artifact_writer.write_corrected_board(
                    stage_dir=stage_dir,
                    source_name=source_name,
                    board_folder_name=prepared_board.board_folder_name,
                    corrected_board=prepared_board.corrected_board,
                )
                self._artifact_writer.write_board_cells(
                    stage_dir=stage_dir,
                    source_name=source_name,
                    board_folder_name=prepared_board.board_folder_name,
                    cell_images=prepared_board.cell_images,
                )
                self._manifest_writer.write_board_cells_index(
                    stage_dir=stage_dir,
                    source_name=source_name,
                    board_folder_name=prepared_board.board_folder_name,
                    entries=prepared_board.index_entries,
                )
            except OSError as error:
                raise DatasetPreparationWriteFailedError(
                    "Nie udało się zapisać artefaktów board w przygotowaniu datasetu."
                ) from error

            board_folder_names.append(prepared_board.board_folder_name)
            prepared_items_count += len(prepared_board.index_entries)
            empty_cell_count += 81 - len(prepared_board.index_entries)

        if valid_board_count == 0:
            raise BoardNotFoundError()

        try:
            self._manifest_writer.write_board_file_list(
                stage_dir=stage_dir,
                source_name=source_name,
                board_folder_names=tuple(board_folder_names),
            )
        except OSError as error:
            raise DatasetPreparationWriteFailedError(
                "Nie udało się zapisać manifestu board/file.json."
            ) from error

        report = self._report_builder.build_source_report(
            name=source_name,
            source_type=DatasetSourceType.BOARD.value,
            prepared_items_count=prepared_items_count,
            rejected_items_count=rejected_items_count,
            empty_cell_count=empty_cell_count,
        )
        LOGGER.info(
            "Board source prepared: source=%s prepared_items=%s rejected_items=%s empty_cells=%s",
            source_name,
            prepared_items_count,
            rejected_items_count,
            empty_cell_count,
        )
        return _PreparedBoardSourceResult(
            report=report,
            warnings=tuple(warnings),
            board_folder_names=tuple(board_folder_names),
        )

    def _prepare_single_board(
        self,
        board_pair: object,
        already_used_folder_names: list[str],
    ) -> _PreparedBoardArtifact:
        board_grid_label = self._parse_board_grid_label(board_pair.label_path)
        board_image = self._load_board_image(board_pair.image_path)
        corrected_board, cells_grid = self._board_dataset_cell_extractor.extract(
            board_image
        )
        flattened_cells = self._flatten_cells_grid(cells_grid)
        flattened_labels = board_grid_label.flatten()
        if len(flattened_cells) != len(flattened_labels):
            raise CreateDatasetPreparationCommandError(
                error_type="dataset_source_invalid",
                message=(
                    "Liczba wyciętych komórek nie zgadza się z etykietami planszy."
                ),
            )

        board_folder_name = self._board_folder_name_resolver.resolve(
            board_name=board_pair.board_name,
            group_key=board_pair.group_key,
            already_used=tuple(already_used_folder_names),
        )

        index_entries: list[DatasetPreparationItemIndexEntryDto] = []
        cell_images: list[NDArray[np.uint8]] = []
        for cell_index, cell_image in enumerate(flattened_cells):
            label = flattened_labels[cell_index]
            if not self._should_save_board_cell(label):
                continue
            processed_cell = self._clean_labeled_board_cell(cell_image)
            file_name = f"{len(index_entries):03d}.png"
            index_entries.append(
                DatasetPreparationItemIndexEntryDto(
                    file_name=file_name,
                    label=label,
                )
            )
            cell_images.append(processed_cell)

        return _PreparedBoardArtifact(
            board_folder_name=board_folder_name,
            corrected_board=corrected_board,
            index_entries=tuple(index_entries),
            cell_images=tuple(cell_images),
        )

    def _prepare_digit_source(
        self,
        stage_dir: Path,
        source_name: str,
        images_path: Path | None,
        labels_path: Path | None,
    ) -> _PreparedDigitSourceResult:
        if images_path is None or labels_path is None:
            raise CreateDatasetPreparationCommandError(
                error_type="dataset_source_invalid",
                message=f"Źródło {source_name} nie zawiera kompletnej pary IDX.",
            )

        try:
            records = self._idx_dataset_loader.load(images_path, labels_path)
        except ValueError as error:
            raise CreateDatasetPreparationCommandError(
                error_type="dataset_source_invalid",
                message=str(error),
            ) from error

        warnings: list[str] = []
        index_entries: list[DatasetPreparationItemIndexEntryDto] = []
        sample_images: list[NDArray[np.uint8]] = []
        rejected_items_count = 0
        empty_cell_count = 0

        for record in records:
            if record.label < 0 or record.label > 9:
                raise CreateDatasetPreparationCommandError(
                    error_type="dataset_source_invalid",
                    message="Źródło digit zawiera etykietę spoza zakresu 0..9.",
                )
            if record.label == 0:
                empty_cell_count += 1
                continue
            try:
                processed_image = self._digit_sample_preparation.prepare_uint8(
                    record.image
                )
            except ValueError as error:
                rejected_items_count += 1
                warning_message = (
                    f"Pominięto próbkę digit {record.sample_key}: {error}"
                )
                warnings.append(warning_message)
                LOGGER.warning(
                    "Digit item rejected: source=%s sample=%s message=%s",
                    source_name,
                    record.sample_key,
                    error,
                )
                continue

            file_name = f"{len(index_entries):06d}.png"
            index_entries.append(
                DatasetPreparationItemIndexEntryDto(
                    file_name=file_name,
                    label=record.label,
                )
            )
            sample_images.append(processed_image)

        try:
            self._artifact_writer.write_digit_samples(
                stage_dir=stage_dir,
                source_name=source_name,
                sample_images=tuple(sample_images),
            )
            self._manifest_writer.write_digit_index(
                stage_dir=stage_dir,
                source_name=source_name,
                entries=tuple(index_entries),
            )
        except OSError as error:
            raise DatasetPreparationWriteFailedError(
                "Nie udało się zapisać artefaktów digit w przygotowaniu datasetu."
            ) from error

        if not index_entries:
            warnings.append(
                f"Źródło digit {source_name} nie dało żadnej zapisanej próbki 1..9."
            )

        report = self._report_builder.build_source_report(
            name=source_name,
            source_type=DatasetSourceType.DIGIT.value,
            prepared_items_count=len(index_entries),
            rejected_items_count=rejected_items_count,
            empty_cell_count=empty_cell_count,
        )
        LOGGER.info(
            "Digit source prepared: source=%s prepared_items=%s rejected_items=%s empty_cells=%s",
            source_name,
            len(index_entries),
            rejected_items_count,
            empty_cell_count,
        )
        return _PreparedDigitSourceResult(
            report=report,
            warnings=tuple(warnings),
        )

    def _ensure_anything_prepared(
        self, source_reports: list[DatasetPreparationSourceReportDto]
    ) -> None:
        if sum(report.prepared_items_count for report in source_reports) == 0:
            raise CreateDatasetPreparationCommandError(
                error_type="no_items_prepared",
                message="Nie zapisano żadnych próbek do przygotowania datasetu.",
            )

    def _cleanup(self, preparation_name: str, stage_dir: Path) -> None:
        LOGGER.info(
            "Cleaning dataset preparation workspace: preparation=%s stage_dir=%s",
            preparation_name,
            stage_dir,
        )
        try:
            self._artifact_cleanup.cleanup(
                preparation_name=preparation_name,
                stage_dir=stage_dir,
            )
        except OSError:
            LOGGER.warning(
                "Nie udało się wyczyścić częściowych artefaktów przygotowania datasetu.",
                extra={"preparationName": preparation_name},
            )

    def _load_board_image(self, image_path: Path) -> NDArray[np.uint8]:
        board_image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if board_image is None:
            raise ValueError(f"Nie udało się odczytać obrazu {image_path.name}.")
        return board_image

    def _flatten_cells_grid(
        self, cells_grid: CellsGrid
    ) -> tuple[NDArray[np.uint8], ...]:
        cells_grid.validate_dimensions(expected_rows=9, expected_cols=9)
        flattened_cells: list[NDArray[np.uint8]] = []
        for row in cells_grid.cells:
            flattened_cells.extend(row)
        return tuple(flattened_cells)

    def _parse_board_grid_label(self, label_path: Path) -> BoardGridLabel:
        try:
            return self._board_dat_parser.parse(label_path)
        except ValueError as error:
            raise CreateDatasetPreparationCommandError(
                error_type="dataset_source_invalid",
                message=str(error),
            ) from error

    def _should_save_board_cell(self, label: int) -> bool:
        if label == 0:
            return False
        if 1 <= label <= 9:
            return True
        raise CreateDatasetPreparationCommandError(
            error_type="dataset_source_invalid",
            message="Źródło board zawiera etykietę spoza zakresu 0..9.",
        )

    def _clean_labeled_board_cell(
        self,
        cell_image: NDArray[np.uint8],
    ) -> NDArray[np.uint8]:
        return self._board_cell_preprocessing_pipeline.run_uint8(cell_image)

    def _is_valid_path_component(self, value: str) -> bool:
        stripped_value = value.strip()
        if not stripped_value or stripped_value in {".", ".."}:
            return False
        return "/" not in stripped_value and "\\" not in stripped_value

    def _format_utc(self, value: object) -> str:
        return value.isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class _PreparedBoardArtifact:
    board_folder_name: str
    corrected_board: NDArray[np.uint8]
    index_entries: tuple[DatasetPreparationItemIndexEntryDto, ...]
    cell_images: tuple[NDArray[np.uint8], ...]
