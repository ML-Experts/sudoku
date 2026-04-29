from dataclasses import dataclass

from application.features.trainings.dto.training_run_context_dto import (
    BaseModelReferenceDto,
    OutputRegistryModelDto,
    ProcessedDatasetReferenceDto,
    ResolvedTrainingConfigurationDto,
    TrainingOutputPathsDto,
)


@dataclass(frozen=True)
class StartTrainingRunCommand:
    run_name: str
    base_model: BaseModelReferenceDto
    processed_dataset: ProcessedDatasetReferenceDto
    resolved_configuration: ResolvedTrainingConfigurationDto
    output_model: OutputRegistryModelDto
    output_paths: TrainingOutputPathsDto
