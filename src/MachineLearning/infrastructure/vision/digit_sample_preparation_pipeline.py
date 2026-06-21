from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from infrastructure.vision.cell_cleaning import to_grayscale


class DigitSamplePreparationPipeline:
    def prepare_uint8(
        self,
        sample_image: NDArray[np.uint8],
    ) -> NDArray[np.uint8]:
        grayscale_image = to_grayscale(sample_image)
        if grayscale_image.dtype != np.uint8:
            grayscale_image = grayscale_image.astype(np.uint8)
        return grayscale_image.copy()
