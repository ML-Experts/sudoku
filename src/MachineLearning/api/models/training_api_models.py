from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StartTrainingBaseModelApiEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str = Field(min_length=1)
    manifest_path: str = Field(alias="manifestPath", min_length=1)
    primary_artifact_path: str = Field(
        alias="primaryArtifactPath", min_length=1
    )
    input_profile: str = Field(alias="inputProfile", min_length=1)


class StartTrainingDatasetApiEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str = Field(min_length=1)
    artifact_path: str = Field(alias="artifactPath", min_length=1)
    preprocessing_profile: str = Field(alias="preprocessingProfile", min_length=1)


class StartTrainingSettingsApiEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    mode: str = Field(min_length=1)
    training_profile_name: str = Field(alias="trainingProfileName", min_length=1)
    augmentation_profile_name: str = Field(
        alias="augmentationProfileName", min_length=1
    )
    benchmark_name: str = Field(alias="benchmarkName", min_length=1)
    seed: int


class StartTrainingOutputApiEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    run_directory_path: str = Field(alias="runDirectoryPath", min_length=1)
    reports_directory_path: str = Field(
        alias="reportsDirectoryPath", min_length=1
    )
    working_directory_path: str = Field(alias="workingDirectoryPath", min_length=1)
    produced_model_name: str = Field(alias="producedModelName", min_length=1)
    produced_model_artifacts_directory_path: str = Field(
        alias="producedModelArtifactsDirectoryPath", min_length=1
    )


class StartTrainingCallbacksApiEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    events_path: str = Field(alias="eventsPath", min_length=1)


class StartTrainingApiEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    run_name: str = Field(alias="runName", min_length=1)
    base_model: StartTrainingBaseModelApiEntry = Field(alias="baseModel")
    dataset: StartTrainingDatasetApiEntry
    training: StartTrainingSettingsApiEntry
    output: StartTrainingOutputApiEntry
    callbacks: StartTrainingCallbacksApiEntry


class AcceptedTrainingApiResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    accepted: bool
    accepted_at_utc: datetime = Field(alias="acceptedAtUtc")
    ml_job_id: str = Field(alias="mlJobId")


class CancelTrainingApiEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    run_name: str = Field(alias="runName", min_length=1)
    requested_at_utc: datetime = Field(alias="requestedAtUtc")
    reason: str = Field(min_length=1)


class CancelTrainingApiResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    accepted: bool
    run_name: str = Field(alias="runName")
    status: str | None = None
    disposition: str | None = None
