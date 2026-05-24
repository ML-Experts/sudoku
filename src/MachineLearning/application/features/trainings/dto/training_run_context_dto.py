from dataclasses import dataclass

from models.model_manifest import ModelManifest


@dataclass(frozen=True)
class BaseModelReferenceDto:
    name: str
    directory_path: str
    manifest_path: str
    primary_artifact_path: str
    input_profile: str
    source_type: str


@dataclass(frozen=True)
class ProcessedDatasetReferenceDto:
    name: str
    file_path: str
    preprocessing_profile: str


@dataclass(frozen=True)
class TrainingParametersDto:
    epochs: int
    learning_rate: float
    batch_size: int
    early_stopping_patience: int
    lr_scheduler_patience: int
    lr_scheduler_factor: float
    fine_tuning_policy: str
    early_stopping_min_delta: float = 0.001
    warmup_epochs: int = 0
    use_best_checkpoint: bool = True


@dataclass(frozen=True)
class ResolvedTrainingConfigurationDto:
    training_mode: str
    training_profile_name: str
    augmentation_profile_name: str
    benchmark_name: str
    seed: int
    training_parameters: TrainingParametersDto


@dataclass(frozen=True)
class OutputRegistryModelDto:
    name: str
    directory_path: str


@dataclass(frozen=True)
class TrainingOutputPathsDto:
    run_directory_path: str
    report_directory_path: str
    benchmark_directory_path: str
    temporary_working_directory_path: str


@dataclass(frozen=True)
class TrainingRunContextDto:
    run_name: str
    base_model: BaseModelReferenceDto
    processed_dataset: ProcessedDatasetReferenceDto
    resolved_configuration: ResolvedTrainingConfigurationDto
    output_model: OutputRegistryModelDto
    output_paths: TrainingOutputPathsDto
    model_manifest: ModelManifest
