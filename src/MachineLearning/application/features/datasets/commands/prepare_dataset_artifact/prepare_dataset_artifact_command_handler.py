import logging
from dataclasses import dataclass
from pathlib import Path

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
    SplitRatiosDto,
)
from application.features.datasets.dto.prepared_dataset_source_report_dto import (
    PreparedDatasetSourceReportDto,
)
from application.features.datasets.dto.prepare_dataset_source_dto import (
    PrepareDatasetSourceDto,
)
from application.features.datasets.dto.split_sample_counts_dto import (
    SplitSampleCountsDto,
)
from application.features.datasets.errors.dataset_preparation_errors import (
    DatasetSourceInvalidError,
    PrepareDatasetArtifactCommandError,
)
from application.features.datasets.ports.processed_dataset_artifact_ports import (
    DatasetPreparationImageReaderPort,
    DatasetPreparationManifestReaderPort,
    DatasetPreparationSourceReaderPort,
    NpzDatasetArtifactWriterPort,
    PreparationReportBuilderPort,
    ProcessedDatasetArtifactCleanupPort,
    SampleSplitAssignerPort,
    TempDatasetPathProviderPort,
)
from models.dataset_source_type import DatasetSourceType
from models.dataset_split import DatasetSplit

LOGGER = logging.getLogger(__name__)
_SUPPORTED_SOURCE_TYPES = {
    DatasetSourceType.BOARD.value,
    DatasetSourceType.DIGIT.value,
}
_SUPPORTED_SPLITS = {
    DatasetSplit.TRAIN.value,
    DatasetSplit.VAL.value,
    DatasetSplit.TEST.value,
}
_DEFAULT_PREPROCESSING_PROFILE = "default-28x28-v1"


@dataclass(frozen=True)
class _PreparedSourceResult:
    samples: tuple[CanonicalPreparedSampleDto, ...]
    report: PreparedDatasetSourceReportDto


class PrepareDatasetArtifactCommandHandler:
    def __init__(
        self,
        source_reader: DatasetPreparationSourceReaderPort,
        manifest_reader: DatasetPreparationManifestReaderPort,
        image_reader: DatasetPreparationImageReaderPort,
        sample_split_assigner: SampleSplitAssignerPort,
        npz_dataset_artifact_writer: NpzDatasetArtifactWriterPort,
        temp_dataset_path_provider: TempDatasetPathProviderPort,
        artifact_cleanup: ProcessedDatasetArtifactCleanupPort,
        preparation_report_builder: PreparationReportBuilderPort,
    ) -> None:
        self._source_reader = source_reader
        self._manifest_reader = manifest_reader
        self._image_reader = image_reader
        self._sample_split_assigner = sample_split_assigner
        self._npz_dataset_artifact_writer = npz_dataset_artifact_writer
        self._temp_dataset_path_provider = temp_dataset_path_provider
        self._artifact_cleanup = artifact_cleanup
        self._preparation_report_builder = preparation_report_builder

    def handle(
        self,
        command: PrepareDatasetArtifactCommand,
    ) -> PrepareDatasetArtifactCommandResultDto:
        self._validate_command(command)

        all_samples: list[CanonicalPreparedSampleDto] = []
        source_reports: list[PreparedDatasetSourceReportDto] = []
        warnings: list[str] = []
        target_path = self._temp_dataset_path_provider.for_name(command.dataset_name)
        LOGGER.info(
            "Dataset preparation started: preparation=%s dataset=%s source_count=%s target_path=%s",
            command.preparation_name,
            command.dataset_name,
            len(command.sources),
            target_path,
        )

        try:
            for source in command.sources:
                LOGGER.info(
                    "Preparing dataset source: preparation=%s dataset=%s source=%s type=%s",
                    command.preparation_name,
                    command.dataset_name,
                    source.name,
                    source.type,
                )
                source_type = DatasetSourceType(source.type.strip().lower())
                source_root = self._source_reader.resolve_source_root(
                    preparation_name=command.preparation_name,
                    source_name=source.name,
                    source_type=source_type,
                )
                if source_type == DatasetSourceType.BOARD:
                    source_result = self._prepare_board_source(
                        source=source,
                        source_root=source_root,
                        split_policy=command.split_policy,
                    )
                else:
                    source_result = self._prepare_digit_source(
                        source=source,
                        source_root=source_root,
                        split_policy=command.split_policy,
                    )

                all_samples.extend(source_result.samples)
                source_reports.append(source_result.report)
                warnings.extend(source_result.report.warnings)
                LOGGER.info(
                    "Dataset source prepared: dataset=%s source=%s included_samples=%s rejected_samples=%s",
                    command.dataset_name,
                    source.name,
                    source_result.report.included_sample_count,
                    source_result.report.rejected_sample_count,
                )

            if not all_samples:
                raise PrepareDatasetArtifactCommandError(
                    error_type="no_samples_prepared",
                    message=(
                        "Po złożeniu datasetu nie pozostały żadne próbki nadzorowane."
                    ),
                )

            split_arrays = self._build_split_arrays(all_samples)
            try:
                self._npz_dataset_artifact_writer.write(
                    output_path=target_path,
                    x_train=split_arrays["x_train"],
                    y_train=split_arrays["y_train"],
                    x_val=split_arrays["x_val"],
                    y_val=split_arrays["y_val"],
                    x_test=split_arrays["x_test"],
                    y_test=split_arrays["y_test"],
                    class_names=self._build_class_names(),
                )
            except OSError as error:
                raise PrepareDatasetArtifactCommandError(
                    error_type="dataset_artifact_write_failed",
                    message="Nie udało się zapisać artefaktu datasetu.",
                ) from error
        except Exception as error:
            LOGGER.exception(
                "Dataset preparation failed: preparation=%s dataset=%s error_type=%s",
                command.preparation_name,
                command.dataset_name,
                getattr(error, "error_type", type(error).__name__),
            )
            self._cleanup_partial_artifact(target_path)
            raise

        sample_counts = SplitSampleCountsDto(
            train=int(split_arrays["x_train"].shape[0]),
            val=int(split_arrays["x_val"].shape[0]),
            test=int(split_arrays["x_test"].shape[0]),
        )
        LOGGER.info(
            "Dataset preparation succeeded: dataset=%s train=%s val=%s test=%s",
            command.dataset_name,
            sample_counts.train,
            sample_counts.val,
            sample_counts.test,
        )
        return PrepareDatasetArtifactCommandResultDto(
            dataset_name=command.dataset_name,
            file_name=f"{command.dataset_name}.npz",
            preprocessing_profile=_DEFAULT_PREPROCESSING_PROFILE,
            sample_counts=sample_counts,
            sources=tuple(source_reports),
            warnings=tuple(warnings),
        )

    def _validate_command(self, command: PrepareDatasetArtifactCommand) -> None:
        if not self._is_valid_path_component(command.preparation_name):
            raise PrepareDatasetArtifactCommandError(
                error_type="invalid_request",
                message=(
                    "Pole preparationName jest wymagane i musi być poprawną nazwą katalogu."
                ),
            )
        if not self._is_valid_path_component(command.dataset_name):
            raise PrepareDatasetArtifactCommandError(
                error_type="invalid_request",
                message=(
                    "Pole datasetName jest wymagane i musi być poprawną nazwą pliku."
                ),
            )
        if not command.sources:
            raise PrepareDatasetArtifactCommandError(
                error_type="invalid_request",
                message="Pole sources musi zawierać co najmniej jedno źródło.",
            )

        self._validate_split_policy(command.split_policy)

        seen_sources: set[tuple[str, str]] = set()
        for source in command.sources:
            normalized_type = source.type.strip().lower()
            if normalized_type not in _SUPPORTED_SOURCE_TYPES:
                raise PrepareDatasetArtifactCommandError(
                    error_type="invalid_request",
                    message=f"Typ źródła {source.type} nie jest obsługiwany.",
                )
            if not self._is_valid_path_component(source.name):
                raise PrepareDatasetArtifactCommandError(
                    error_type="invalid_request",
                    message=(
                        "Każde źródło musi zawierać poprawną nazwę bez separatorów ścieżek."
                    ),
                )
            self._normalize_source_splits(source.splits)
            source_key = (source.name, normalized_type)
            if source_key in seen_sources:
                raise PrepareDatasetArtifactCommandError(
                    error_type="invalid_request",
                    message="Lista sources zawiera duplikaty.",
                )
            seen_sources.add(source_key)

    def _validate_split_policy(self, split_policy: DatasetSplitPolicyDto) -> None:
        if split_policy.mode.strip().lower() != "ratio":
            raise PrepareDatasetArtifactCommandError(
                error_type="invalid_request",
                message="Pole splitPolicy.mode musi mieć wartość ratio.",
            )
        if split_policy.group_by.strip() != "sourceType":
            raise PrepareDatasetArtifactCommandError(
                error_type="invalid_request",
                message=(
                    "Pole splitPolicy.groupBy musi mieć wartość sourceType."
                ),
            )

        ratios = split_policy.ratios
        if min(ratios.train, ratios.val, ratios.test) < 0:
            raise PrepareDatasetArtifactCommandError(
                error_type="invalid_request",
                message="Pola splitPolicy.ratios nie mogą być ujemne.",
            )

        total = ratios.train + ratios.val + ratios.test
        if not np.isclose(total, 1.0, atol=1e-6):
            raise PrepareDatasetArtifactCommandError(
                error_type="invalid_request",
                message="Suma splitPolicy.ratios musi wynosić 1.0.",
            )

    def _prepare_board_source(
        self,
        source: PrepareDatasetSourceDto,
        source_root: Path,
        split_policy: DatasetSplitPolicyDto,
    ) -> _PreparedSourceResult:
        board_manifest = self._manifest_reader.read_board_manifest(source_root)
        prepared_samples: list[CanonicalPreparedSampleDto] = []
        warnings: list[str] = []
        processed_sample_count = 0
        included_sample_count = 0
        empty_cell_count = 0
        rejected_sample_count = 0

        for board_folder_name in board_manifest.board_folder_names:
            board_root = source_root / board_folder_name
            split = self._resolve_split(
                stable_key=board_folder_name,
                allowed_splits=source.splits,
                split_policy=split_policy,
            )
            index_entries = self._manifest_reader.read_board_cells_index(board_root)
            processed_sample_count += 81
            empty_cell_count += 81 - len(index_entries)

            for cell_index, index_entry in enumerate(index_entries):
                try:
                    image = self._image_reader.read_board_cell(
                        board_root=board_root,
                        file_name=index_entry.file_name,
                    )
                except DatasetSourceInvalidError as error:
                    rejected_sample_count += 1
                    warning_message = (
                        f"Pominięto komórkę {index_entry.file_name} "
                        f"w planszy {board_folder_name}: {error.message}"
                    )
                    warnings.append(warning_message)
                    LOGGER.warning(
                        "Board cell skipped: source=%s board=%s file=%s message=%s",
                        source.name,
                        board_folder_name,
                        index_entry.file_name,
                        error.message,
                    )
                    continue

                prepared_samples.append(
                    CanonicalPreparedSampleDto(
                        split=split.value,
                        label=self._normalize_label(index_entry.label),
                        source_type=DatasetSourceType.BOARD.value,
                        source_dataset_name=source.name,
                        source_board_name=board_folder_name,
                        source_sample_key=index_entry.file_name,
                        cell_index=cell_index,
                        image_28x28=self._to_training_image(image),
                    )
                )
                included_sample_count += 1

        return _PreparedSourceResult(
            samples=tuple(prepared_samples),
            report=self._preparation_report_builder.build_source_report(
                name=source.name,
                requested_type=DatasetSourceType.BOARD.value,
                detected_type=DatasetSourceType.BOARD.value,
                processed_sample_count=processed_sample_count,
                included_sample_count=included_sample_count,
                empty_cell_count=empty_cell_count,
                rejected_sample_count=rejected_sample_count,
                warnings=warnings,
            ),
        )

    def _prepare_digit_source(
        self,
        source: PrepareDatasetSourceDto,
        source_root: Path,
        split_policy: DatasetSplitPolicyDto,
    ) -> _PreparedSourceResult:
        index_entries = self._manifest_reader.read_digit_index(source_root)
        prepared_samples: list[CanonicalPreparedSampleDto] = []
        warnings: list[str] = []
        processed_sample_count = len(index_entries)
        included_sample_count = 0
        rejected_sample_count = 0

        for index_entry in index_entries:
            split = self._resolve_split(
                stable_key=index_entry.file_name,
                allowed_splits=source.splits,
                split_policy=split_policy,
            )
            try:
                image = self._image_reader.read_digit_sample(
                    source_root=source_root,
                    file_name=index_entry.file_name,
                )
            except DatasetSourceInvalidError as error:
                rejected_sample_count += 1
                warning_message = (
                    f"Pominięto próbkę {index_entry.file_name} "
                    f"w źródle {source.name}: {error.message}"
                )
                warnings.append(warning_message)
                LOGGER.warning(
                    "Digit sample skipped: source=%s file=%s message=%s",
                    source.name,
                    index_entry.file_name,
                    error.message,
                )
                continue

            prepared_samples.append(
                CanonicalPreparedSampleDto(
                    split=split.value,
                    label=self._normalize_label(index_entry.label),
                    source_type=DatasetSourceType.DIGIT.value,
                    source_dataset_name=source.name,
                    source_board_name=None,
                    source_sample_key=index_entry.file_name,
                    cell_index=None,
                    image_28x28=self._to_training_image(image),
                )
            )
            included_sample_count += 1

        return _PreparedSourceResult(
            samples=tuple(prepared_samples),
            report=self._preparation_report_builder.build_source_report(
                name=source.name,
                requested_type=DatasetSourceType.DIGIT.value,
                detected_type=DatasetSourceType.DIGIT.value,
                processed_sample_count=processed_sample_count,
                included_sample_count=included_sample_count,
                empty_cell_count=0,
                rejected_sample_count=rejected_sample_count,
                warnings=warnings,
            ),
        )

    def _resolve_split(
        self,
        stable_key: str,
        allowed_splits: tuple[str, ...],
        split_policy: DatasetSplitPolicyDto,
    ) -> DatasetSplit:
        normalized_splits = self._normalize_source_splits(allowed_splits)
        if normalized_splits == ("mix",):
            return self._sample_split_assigner.assign_split(
                split_policy=split_policy,
                stable_key=stable_key,
            )

        explicit_splits = tuple(
            DatasetSplit(split_name) for split_name in normalized_splits
        )
        if len(explicit_splits) == 1:
            return explicit_splits[0]

        effective_policy = self._build_subset_split_policy(
            split_policy=split_policy,
            allowed_splits=explicit_splits,
        )
        return self._sample_split_assigner.assign_split(
            split_policy=effective_policy,
            stable_key=stable_key,
        )

    def _normalize_source_splits(
        self,
        splits: tuple[str, ...] | list[str],
    ) -> tuple[str, ...]:
        normalized = tuple(split.strip().lower() for split in splits)
        if not normalized or any(not split for split in normalized):
            raise PrepareDatasetArtifactCommandError(
                error_type="invalid_request",
                message="Pole sources[].splits musi zawierać co najmniej jedną wartość.",
            )
        if "mix" in normalized:
            if normalized != ("mix",):
                raise PrepareDatasetArtifactCommandError(
                    error_type="invalid_request",
                    message=(
                        "Wartość mix nie może występować razem z innymi splitami."
                    ),
                )
            return normalized
        if any(split not in _SUPPORTED_SPLITS for split in normalized):
            raise PrepareDatasetArtifactCommandError(
                error_type="invalid_request",
                message="Pole sources[].splits zawiera nieobsługiwane wartości.",
            )
        if len(set(normalized)) != len(normalized):
            raise PrepareDatasetArtifactCommandError(
                error_type="invalid_request",
                message="Pole sources[].splits zawiera duplikaty.",
            )
        return normalized

    def _build_subset_split_policy(
        self,
        split_policy: DatasetSplitPolicyDto,
        allowed_splits: tuple[DatasetSplit, ...],
    ) -> DatasetSplitPolicyDto:
        weights = {
            DatasetSplit.TRAIN: split_policy.ratios.train,
            DatasetSplit.VAL: split_policy.ratios.val,
            DatasetSplit.TEST: split_policy.ratios.test,
        }
        total = sum(weights[split_name] for split_name in allowed_splits)
        if total <= 0:
            raise PrepareDatasetArtifactCommandError(
                error_type="invalid_request",
                message=(
                    "Nie można wyznaczyć splitu dla wybranych sources[].splits przy zerowych ratio."
                ),
            )

        return DatasetSplitPolicyDto(
            mode=split_policy.mode,
            group_by=split_policy.group_by,
            ratios=SplitRatiosDto(
                train=(
                    weights.get(DatasetSplit.TRAIN, 0.0) / total
                    if DatasetSplit.TRAIN in allowed_splits
                    else 0.0
                ),
                val=(
                    weights.get(DatasetSplit.VAL, 0.0) / total
                    if DatasetSplit.VAL in allowed_splits
                    else 0.0
                ),
                test=(
                    weights.get(DatasetSplit.TEST, 0.0) / total
                    if DatasetSplit.TEST in allowed_splits
                    else 0.0
                ),
            ),
        )

    def _build_split_arrays(
        self,
        samples: list[CanonicalPreparedSampleDto],
    ) -> dict[str, NDArray[np.float32] | NDArray[np.int64]]:
        by_split: dict[str, list[CanonicalPreparedSampleDto]] = {
            DatasetSplit.TRAIN.value: [],
            DatasetSplit.VAL.value: [],
            DatasetSplit.TEST.value: [],
        }
        for sample in samples:
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
        self,
        samples: list[CanonicalPreparedSampleDto],
    ) -> NDArray[np.float32]:
        if not samples:
            return np.empty((0, 28, 28), dtype=np.float32)
        return np.stack([sample.image_28x28 for sample in samples]).astype(
            np.float32
        )

    def _build_labels_array(
        self,
        samples: list[CanonicalPreparedSampleDto],
    ) -> NDArray[np.int64]:
        if not samples:
            return np.empty((0,), dtype=np.int64)
        return np.array([int(sample.label) for sample in samples], dtype=np.int64)

    def _build_class_names(self) -> tuple[str, ...]:
        return tuple(str(digit) for digit in range(1, 10))

    def _to_training_image(self, image: NDArray[np.uint8]) -> NDArray[np.float32]:
        return image.astype(np.float32) / 255.0

    def _normalize_label(self, label: int) -> int:
        return label - 1

    def _cleanup_partial_artifact(
        self,
        dataset_artifact_path: Path | None,
    ) -> None:
        try:
            self._artifact_cleanup.cleanup(dataset_artifact_path)
        except OSError:
            LOGGER.warning(
                "Nie udało się wyczyścić częściowego artefaktu datasetu.",
                extra={"datasetArtifactPath": str(dataset_artifact_path)},
            )

    def _is_valid_path_component(self, value: str) -> bool:
        stripped_value = value.strip()
        if not stripped_value or stripped_value in {".", ".."}:
            return False
        return "/" not in stripped_value and "\\" not in stripped_value
