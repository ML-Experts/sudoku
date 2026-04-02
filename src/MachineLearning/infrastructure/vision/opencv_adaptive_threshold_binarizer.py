import cv2
import numpy as np
from numpy.typing import NDArray


class OpenCvAdaptiveThresholdBinarizer:
    def __init__(self, block_size: int, c_value: int) -> None:
        if block_size <= 1:
            raise ValueError("Adaptive threshold block size must be > 1.")
        if block_size % 2 == 0:
            raise ValueError("Adaptive threshold block size must be odd.")

        self._block_size = block_size
        self._c_value = c_value

    def binarize(self, image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        if image.size == 0:
            raise ValueError("Input image is empty.")
        if image.ndim != 2:
            raise ValueError("Adaptive threshold expects a grayscale image.")

        return cv2.adaptiveThreshold(
            image,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            self._block_size,
            self._c_value,
        )
