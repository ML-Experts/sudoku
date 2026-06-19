from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from application.features.datasets.dto.dataset_preparation_item_index_entry_dto import (
    DatasetPreparationItemIndexEntryDto,
)


@dataclass(frozen=True)
class PreparedDigitArtifactDto:
    file_name: str
    label: int
    image: NDArray[np.uint8]


@dataclass(frozen=True)
class PreparedDigitSourceArtifactsDto:
    items: tuple[PreparedDigitArtifactDto, ...]
    index_entries: tuple[DatasetPreparationItemIndexEntryDto, ...]
    rejected_items_count: int
    empty_cell_count: int
