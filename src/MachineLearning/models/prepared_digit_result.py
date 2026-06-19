from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from models.dataset_preparation_index_entry import DatasetPreparationIndexEntry


@dataclass(frozen=True)
class PreparedDigitResult:
    entries: tuple[DatasetPreparationIndexEntry, ...]
    sample_images: tuple[NDArray[np.uint8], ...]
    rejected_items_count: int
    empty_cell_count: int
