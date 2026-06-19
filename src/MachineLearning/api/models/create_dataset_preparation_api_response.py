from pydantic import BaseModel, ConfigDict, Field

from api.models.dataset_preparation_source_report_api_response import (
    DatasetPreparationSourceReportApiResponse,
)
from application.features.datasets.commands.create_dataset_preparation.create_dataset_preparation_command_result_dto import (
    CreateDatasetPreparationCommandResultDto,
)


class CreateDatasetPreparationApiResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    preparation_name: str = Field(alias="preparationName")
    created_at_utc: str = Field(alias="createdAtUtc")
    status: str
    source_reports: list[DatasetPreparationSourceReportApiResponse] = Field(
        alias="sourceReports"
    )
    warnings: list[str]

    @classmethod
    def from_dto(
        cls,
        command_result: CreateDatasetPreparationCommandResultDto,
    ) -> "CreateDatasetPreparationApiResponse":
        return cls(
            preparation_name=command_result.preparation_name,
            created_at_utc=command_result.created_at_utc,
            status=command_result.status,
            source_reports=[
                DatasetPreparationSourceReportApiResponse.from_dto(report)
                for report in command_result.source_reports
            ],
            warnings=list(command_result.warnings),
        )
