import cv2
import numpy as np
from numpy.typing import NDArray

from models.board_quad import BoardQuad


class OpenCvPerspectiveTransformer:
    def __init__(self, output_board_size: int) -> None:
        if output_board_size <= 0:
            raise ValueError("Output board size must be greater than zero.")

        self._output_board_size = output_board_size

    def transform(
        self, image: NDArray[np.uint8], board_quad: BoardQuad
    ) -> NDArray[np.uint8]:
        source_points = np.array(
            board_quad.as_clockwise_points(),
            dtype=np.float32,
        )
        max_index = float(self._output_board_size - 1)
        destination_points = np.array(
            [
                [0.0, 0.0],
                [max_index, 0.0],
                [max_index, max_index],
                [0.0, max_index],
            ],
            dtype=np.float32,
        )

        perspective_matrix = cv2.getPerspectiveTransform(
            source_points, destination_points
        )
        transformed = cv2.warpPerspective(
            image,
            perspective_matrix,
            (self._output_board_size, self._output_board_size),
        )
        if transformed.size == 0:
            raise ValueError("Perspective transform produced empty image.")

        return transformed
