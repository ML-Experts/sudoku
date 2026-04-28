from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from models.dataset_source_type import DatasetSourceType
from models.dataset_split import DatasetSplit


@dataclass(frozen=True)
class CanonicalPreparedSample:
    split: DatasetSplit
    label: int | None
    source_type: DatasetSourceType
    source_dataset_name: str
    source_board_name: str | None
    cell_index: int | None
    image_28x28: NDArray[np.float32]
