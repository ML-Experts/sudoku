from dataclasses import dataclass

from application.features.datasets.dto.prepare_dataset_source_dto import (
    PrepareDatasetSourceDto,
)


@dataclass(frozen=True)
class PrepareDatasetArtifactCommand:
    dataset_name: str
    sources: tuple[PrepareDatasetSourceDto, ...]
    preprocessing_profile: str
