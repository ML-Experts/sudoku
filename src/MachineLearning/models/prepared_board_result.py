from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from models.dataset_preparation_index_entry import DatasetPreparationIndexEntry


@dataclass(frozen=True)
class PreparedBoardResult:
    board_folder_name: str
    corrected_board: NDArray[np.uint8]
    cells_entries: tuple[DatasetPreparationIndexEntry, ...]
    cell_images: tuple[NDArray[np.uint8], ...]
