import cv2
import numpy as np
from numpy.typing import NDArray


class OpenCvGrayscaleBlurPreprocessor:
    def __init__(
        self,
        grayscale_color_conversion_code: int,
        gaussian_kernel_size: tuple[int, int],
        gaussian_sigma_x: float,
    ) -> None:
        kernel_width, kernel_height = gaussian_kernel_size
        if kernel_width <= 0 or kernel_height <= 0:
            raise ValueError("Gaussian kernel size must be greater than zero.")
        if kernel_width % 2 == 0 or kernel_height % 2 == 0:
            raise ValueError("Gaussian kernel size must have odd values.")

        self._grayscale_color_conversion_code = grayscale_color_conversion_code
        self._gaussian_kernel_size = gaussian_kernel_size
        self._gaussian_sigma_x = gaussian_sigma_x

    def preprocess(self, image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        if image.size == 0:
            raise ValueError("Input image is empty.")

        grayscale = cv2.cvtColor(image, self._grayscale_color_conversion_code)
        return cv2.GaussianBlur(
            grayscale,
            self._gaussian_kernel_size,
            self._gaussian_sigma_x,
        )
