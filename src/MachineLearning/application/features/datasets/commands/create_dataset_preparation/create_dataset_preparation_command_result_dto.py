from dataclasses import dataclass

from application.features.datasets.dto.dataset_preparation_source_report_dto import (
    DatasetPreparationSourceReportDto,
)


@dataclass(frozen=True)
class CreateDatasetPreparationCommandResultDto:
    preparation_name: str
    created_at_utc: str
    status: str
    source_reports: tuple[DatasetPreparationSourceReportDto, ...]
    warnings: tuple[str, ...]
