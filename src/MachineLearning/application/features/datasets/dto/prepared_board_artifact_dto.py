from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from application.features.datasets.dto.dataset_preparation_item_index_entry_dto import (
    DatasetPreparationItemIndexEntryDto,
)


@dataclass(frozen=True)
class PreparedBoardArtifactDto:
    board_folder_name: str
    corrected_board: NDArray[np.uint8]
    cell_images: tuple[NDArray[np.uint8], ...]
    index_entries: tuple[DatasetPreparationItemIndexEntryDto, ...]
