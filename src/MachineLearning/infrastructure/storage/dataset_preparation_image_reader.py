from pathlib import Path

import cv2
import numpy as np
from numpy.typing import NDArray

from application.features.datasets.errors.dataset_preparation_errors import (
    DatasetSourceInvalidError,
)


class DatasetPreparationImageReader:
    def read_board_cell(
        self,
        board_root: Path,
        file_name: str,
    ) -> NDArray[np.uint8]:
        return self._read_image(board_root / "cells" / file_name)

    def read_digit_sample(
        self,
        source_root: Path,
        file_name: str,
    ) -> NDArray[np.uint8]:
        return self._read_image(source_root / file_name)

    def _read_image(self, image_path: Path) -> NDArray[np.uint8]:
        if not image_path.is_file():
            raise DatasetSourceInvalidError(
                f"Brakuje pliku obrazu {image_path.name}."
            )

        image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise DatasetSourceInvalidError(
                f"Nie udało się odczytać obrazu {image_path.name}."
            )
        if image.shape != (28, 28):
            raise DatasetSourceInvalidError(
                f"Obraz {image_path.name} nie ma rozmiaru 28x28."
            )

        return image.astype(np.uint8)
