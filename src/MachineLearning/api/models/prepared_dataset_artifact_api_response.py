from pydantic import BaseModel, ConfigDict, Field

from api.models.prepared_dataset_source_report_api_response import (
    PreparedDatasetSourceReportApiResponse,
)
from api.models.split_sample_counts_api_response import (
    SplitSampleCountsApiResponse,
)
from application.features.datasets.commands.prepare_dataset_artifact.prepare_dataset_artifact_command_result_dto import (
    PrepareDatasetArtifactCommandResultDto,
)


class PreparedDatasetArtifactApiResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    dataset_name: str = Field(alias="datasetName")
    file_name: str = Field(alias="fileName")
    preprocessing_profile: str = Field(alias="preprocessingProfile")
    sample_counts: SplitSampleCountsApiResponse = Field(alias="sampleCounts")
    sources: list[PreparedDatasetSourceReportApiResponse]
    warnings: list[str]

    @classmethod
    def from_dto(
        cls, command_result: PrepareDatasetArtifactCommandResultDto
    ) -> "PreparedDatasetArtifactApiResponse":
        return cls(
            dataset_name=command_result.dataset_name,
            file_name=command_result.file_name,
            preprocessing_profile=command_result.preprocessing_profile,
            sample_counts=SplitSampleCountsApiResponse.from_dto(
                command_result.sample_counts
            ),
            sources=[
                PreparedDatasetSourceReportApiResponse.from_dto(source)
                for source in command_result.sources
            ],
            warnings=list(command_result.warnings),
        )
