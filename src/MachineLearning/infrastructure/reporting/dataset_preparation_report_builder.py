from application.features.datasets.dto.dataset_preparation_source_report_dto import (
    DatasetPreparationSourceReportDto,
)


class DatasetPreparationReportBuilder:
    def build_source_report(
        self,
        name: str,
        source_type: str,
        prepared_items_count: int,
        rejected_items_count: int,
        empty_cell_count: int,
    ) -> DatasetPreparationSourceReportDto:
        return DatasetPreparationSourceReportDto(
            name=name,
            type=source_type,
            prepared_items_count=prepared_items_count,
            rejected_items_count=rejected_items_count,
            empty_cell_count=empty_cell_count,
        )
