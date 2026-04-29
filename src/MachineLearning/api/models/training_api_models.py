from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StartTrainingBaseModelApiEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str = Field(min_length=1)
    directory_path: str = Field(alias="directoryPath", min_length=1)
    manifest_path: str = Field(alias="manifestPath", min_length=1)
    primary_artifact_path: str = Field(
        alias="primaryArtifactPath", min_length=1
    )
    input_profile: str = Field(alias="inputProfile", min_length=1)
    source_type: str = Field(alias="sourceType", min_length=1)


class StartTrainingProcessedDatasetApiEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str = Field(min_length=1)
    file_path: str = Field(alias="filePath", min_length=1)
    preprocessing_profile: str = Field(alias="preprocessingProfile", min_length=1)


class ResolvedTrainingConfigurationApiEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    training_mode: str = Field(alias="trainingMode", min_length=1)
    training_profile_name: str = Field(alias="trainingProfileName", min_length=1)
    augmentation_profile_name: str = Field(
        alias="augmentationProfileName", min_length=1
    )
    benchmark_name: str = Field(alias="benchmarkName", min_length=1)
    seed: int


class OutputRegistryModelApiEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str = Field(min_length=1)
    directory_path: str = Field(alias="directoryPath", min_length=1)


class TrainingOutputPathsApiEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    run_directory_path: str = Field(alias="runDirectoryPath", min_length=1)
    report_directory_path: str = Field(alias="reportDirectoryPath", min_length=1)
    benchmark_directory_path: str = Field(
        alias="benchmarkDirectoryPath", min_length=1
    )
    temporary_working_directory_path: str = Field(
        alias="temporaryWorkingDirectoryPath", min_length=1
    )


class StartTrainingRunApiEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    run_name: str = Field(alias="runName", min_length=1)
    base_model: StartTrainingBaseModelApiEntry = Field(alias="baseModel")
    processed_dataset: StartTrainingProcessedDatasetApiEntry = Field(
        alias="processedDataset"
    )
    resolved_configuration: ResolvedTrainingConfigurationApiEntry = Field(
        alias="resolvedConfiguration"
    )
    output_model: OutputRegistryModelApiEntry = Field(alias="outputModel")
    output_paths: TrainingOutputPathsApiEntry = Field(alias="outputPaths")


class StartedTrainingRunApiResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    run_name: str = Field(alias="runName")
    status: str
    accepted_at_utc: datetime = Field(alias="acceptedAtUtc")
    warnings: list[str]


class CancelTrainingRunApiResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    run_name: str = Field(alias="runName")
    status: str | None = None
    request_disposition: str = Field(alias="requestDisposition")
    cancellation_requested_at_utc: datetime | None = Field(
        alias="cancellationRequestedAtUtc"
    )


class TrainingRunProgressApiEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    percent: float | None = None
    epoch_current: int | None = Field(default=None, alias="epochCurrent")
    epoch_total: int | None = Field(default=None, alias="epochTotal")
    eta_seconds: int | None = Field(default=None, alias="etaSeconds")


class TrainingRunResultApiEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    produced_model_name: str = Field(alias="producedModelName")
    report_status: str = Field(alias="reportStatus")
    can_use_produced_model_for_inference: bool = Field(
        alias="canUseProducedModelForInference"
    )
    primary_artifact_relative_path: str = Field(
        alias="primaryArtifactRelativePath"
    )
    summary_relative_path: str | None = Field(alias="summaryRelativePath")
    metrics_relative_path: str | None = Field(alias="metricsRelativePath")
    confusion_matrix_relative_path: str | None = Field(
        alias="confusionMatrixRelativePath"
    )


class TrainingRunFailureApiEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    error_type: str = Field(alias="errorType")
    message: str
    can_use_produced_model_for_inference: bool = Field(
        alias="canUseProducedModelForInference"
    )


class TrainingRunEventApiEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    event_type: str = Field(alias="eventType")
    sequence: int
    run_name: str = Field(alias="runName")
    status: str
    stage: str
    occurred_at_utc: datetime = Field(alias="occurredAtUtc")
    message: str | None
    progress: TrainingRunProgressApiEntry | None
    warnings: list[str]
    result: TrainingRunResultApiEntry | None
    failure: TrainingRunFailureApiEntry | None


# Backward-compatible import names are intentionally not preserved for the
# request model: BE 06 sends the resolved UC-06 contract above.
