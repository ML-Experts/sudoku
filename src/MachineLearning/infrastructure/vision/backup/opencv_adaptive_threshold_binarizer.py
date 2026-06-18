import cv2
import numpy as np
from numpy.typing import NDArray


class OpenCvAdaptiveThresholdBinarizer:
    def __init__(self, block_size: int, c_value: int) -> None:
        if block_size <= 1 or block_size % 2 == 0:
            raise ValueError("Adaptive threshold block size must be an odd value > 1.")

        self._block_size = block_size
        self._c_value = c_value

    def binarize(self, image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        if image.size == 0:
            raise ValueError("Image cannot be empty.")
        if image.ndim == 2:
            grayscale_image = image
        elif image.ndim == 3:
            grayscale_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            raise ValueError("Image must be grayscale or color.")

        return cv2.adaptiveThreshold(
            grayscale_image,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            self._block_size,
            self._c_value,
        )
