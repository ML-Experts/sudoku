from pydantic import BaseModel, ConfigDict, Field

from application.features.datasets.dto.dataset_preparation_source_report_dto import (
    DatasetPreparationSourceReportDto,
)


class DatasetPreparationSourceReportApiResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str
    type: str
    prepared_items_count: int = Field(alias="preparedItemsCount")
    rejected_items_count: int = Field(alias="rejectedItemsCount")
    empty_cell_count: int = Field(alias="emptyCellCount")

    @classmethod
    def from_dto(
        cls,
        source_report: DatasetPreparationSourceReportDto,
    ) -> "DatasetPreparationSourceReportApiResponse":
        return cls(
            name=source_report.name,
            type=source_report.type,
            prepared_items_count=source_report.prepared_items_count,
            rejected_items_count=source_report.rejected_items_count,
            empty_cell_count=source_report.empty_cell_count,
        )
