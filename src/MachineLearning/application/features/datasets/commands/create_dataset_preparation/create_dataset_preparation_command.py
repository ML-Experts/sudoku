from dataclasses import dataclass

from application.features.datasets.dto.create_dataset_preparation_source_dto import (
    CreateDatasetPreparationSourceDto,
)


@dataclass(frozen=True)
class CreateDatasetPreparationCommand:
    preparation_name: str
    sources: tuple[CreateDatasetPreparationSourceDto, ...]
