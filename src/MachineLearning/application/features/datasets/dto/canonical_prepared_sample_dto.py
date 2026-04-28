from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class CanonicalPreparedSampleDto:
    split: str
    label: int | None
    source_type: str
    source_dataset_name: str
    source_board_name: str | None
    cell_index: int | None
    image_28x28: NDArray[np.float32]
