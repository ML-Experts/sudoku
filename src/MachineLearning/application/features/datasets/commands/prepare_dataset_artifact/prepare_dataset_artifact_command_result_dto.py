from dataclasses import dataclass

from application.features.datasets.dto.prepared_dataset_source_report_dto import (
    PreparedDatasetSourceReportDto,
)
from application.features.datasets.dto.split_sample_counts_dto import (
    SplitSampleCountsDto,
)


@dataclass(frozen=True)
class PrepareDatasetArtifactCommandResultDto:
    sample_counts: SplitSampleCountsDto
    sources: tuple[PreparedDatasetSourceReportDto, ...]
    warnings: tuple[str, ...]
