from typing import Callable

import cv2
import numpy as np
from numpy.typing import NDArray


class OpenCvGrayscaleBlurPreprocessor:
    def __init__(
        self,
        grayscale_color_conversion_code: int,
        gaussian_kernel_size: tuple[int, int],
        gaussian_sigma_x: float,
        source_image_consumer: Callable[[NDArray[np.uint8]], None] | None = None,
    ) -> None:
        if len(gaussian_kernel_size) != 2:
            raise ValueError("Gaussian kernel size must contain two dimensions.")
        if any(size <= 0 or size % 2 == 0 for size in gaussian_kernel_size):
            raise ValueError(
                "Gaussian kernel dimensions must be positive odd values."
            )
        if gaussian_sigma_x < 0:
            raise ValueError("Gaussian sigma must not be negative.")

        self._grayscale_color_conversion_code = grayscale_color_conversion_code
        self._gaussian_kernel_size = gaussian_kernel_size
        self._gaussian_sigma_x = gaussian_sigma_x
        self._source_image_consumer = source_image_consumer

    def preprocess(self, image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        if image.size == 0:
            raise ValueError("Image cannot be empty.")
        if self._source_image_consumer is not None:
            self._source_image_consumer(image)
        if image.ndim == 2:
            grayscale_image = image
        elif image.ndim == 3:
            grayscale_image = cv2.cvtColor(
                image,
                self._grayscale_color_conversion_code,
            )
        else:
            raise ValueError("Image must be grayscale or color.")

        return cv2.GaussianBlur(
            grayscale_image,
            self._gaussian_kernel_size,
            self._gaussian_sigma_x,
        )
