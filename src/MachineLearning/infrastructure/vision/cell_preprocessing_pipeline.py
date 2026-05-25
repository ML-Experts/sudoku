import cv2
import numpy as np
from numpy.typing import NDArray


class CellPreprocessingPipeline:
    def __init__(self, output_size: int = 28) -> None:
        if output_size <= 0:
            raise ValueError("Output size must be greater than zero.")
        self._output_size = output_size

    def run(self, cell_image: NDArray[np.uint8]) -> NDArray[np.float32]:
        preview_image = self.run_uint8(cell_image)
        normalized_image = preview_image.astype(np.float32) / 255.0
        return normalized_image

    def run_uint8(self, cell_image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        binary_image = self.build_foreground_mask(cell_image)
        return self._center_foreground(binary_image)

    def build_foreground_mask(
        self,
        cell_image: NDArray[np.uint8],
    ) -> NDArray[np.uint8]:
        if cell_image.size == 0:
            raise ValueError("Cell image cannot be empty.")

        grayscale_image = self._to_grayscale(cell_image)
        sharpened_image = self._sharpen(grayscale_image)
        return cv2.adaptiveThreshold(
            sharpened_image,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            11,
            2,
        )

    def _to_grayscale(self, image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        if image.ndim == 2:
            return image
        if image.ndim == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        raise ValueError("Unsupported image dimensions.")

    def _sharpen(self, image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        sharpen_kernel = np.array(
            [[0, -1, 0], [-1, 5, -1], [0, -1, 0]],
            dtype=np.float32,
        )
        return cv2.filter2D(image, -1, sharpen_kernel)

    def _center_foreground(self, image: NDArray[np.uint8]) -> NDArray[np.uint8]:
        foreground_points = cv2.findNonZero(image)
        canvas = np.zeros(
            (self._output_size, self._output_size),
            dtype=np.uint8,
        )
        if foreground_points is None:
            return canvas

        x, y, width, height = cv2.boundingRect(foreground_points)
        cropped = image[y : y + height, x : x + width]
        target_inner_size = max(self._output_size - 8, 1)
        resize_scale = min(
            target_inner_size / max(height, 1),
            target_inner_size / max(width, 1),
        )
        resized_width = max(1, int(round(width * resize_scale)))
        resized_height = max(1, int(round(height * resize_scale)))
        resized = cv2.resize(
            cropped,
            (resized_width, resized_height),
            interpolation=cv2.INTER_AREA,
        )

        offset_x = (self._output_size - resized_width) // 2
        offset_y = (self._output_size - resized_height) // 2
        canvas[
            offset_y : offset_y + resized_height,
            offset_x : offset_x + resized_width,
        ] = resized
        return canvas
