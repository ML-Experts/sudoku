from application.features.datasets.dto.prepared_dataset_source_report_dto import (
    PreparedDatasetSourceReportDto,
)


class PreparationReportBuilder:
    def build_source_report(
        self,
        name: str,
        requested_type: str,
        detected_type: str,
        processed_sample_count: int,
        included_sample_count: int,
        empty_cell_count: int,
        rejected_sample_count: int,
        warnings: list[str] | tuple[str, ...],
    ) -> PreparedDatasetSourceReportDto:
        return PreparedDatasetSourceReportDto(
            name=name,
            requested_type=requested_type,
            detected_type=detected_type,
            processed_sample_count=processed_sample_count,
            included_sample_count=included_sample_count,
            empty_cell_count=empty_cell_count,
            rejected_sample_count=rejected_sample_count,
            warnings=tuple(warnings),
        )
