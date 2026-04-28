from pydantic import BaseModel, ConfigDict, Field

from application.features.datasets.dto.prepared_dataset_source_report_dto import (
    PreparedDatasetSourceReportDto,
)


class PreparedDatasetSourceReportApiResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str
    requested_type: str = Field(alias="requestedType")
    detected_type: str = Field(alias="detectedType")
    processed_sample_count: int = Field(alias="processedSampleCount")
    included_sample_count: int = Field(alias="includedSampleCount")
    empty_cell_count: int = Field(alias="emptyCellCount")
    rejected_sample_count: int = Field(alias="rejectedSampleCount")
    warnings: list[str]

    @classmethod
    def from_dto(
        cls, source_report: PreparedDatasetSourceReportDto
    ) -> "PreparedDatasetSourceReportApiResponse":
        return cls(
            name=source_report.name,
            requested_type=source_report.requested_type,
            detected_type=source_report.detected_type,
            processed_sample_count=source_report.processed_sample_count,
            included_sample_count=source_report.included_sample_count,
            empty_cell_count=source_report.empty_cell_count,
            rejected_sample_count=source_report.rejected_sample_count,
            warnings=list(source_report.warnings),
        )
