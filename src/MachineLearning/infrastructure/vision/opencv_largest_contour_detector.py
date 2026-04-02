import cv2
import numpy as np
from numpy.typing import NDArray

from models.board_quad import BoardQuad


class OpenCvLargestContourDetector:
    def __init__(
        self,
        contour_retrieval_mode: int,
        contour_approximation_mode: int,
        polygon_epsilon_factor: float,
    ) -> None:
        if polygon_epsilon_factor <= 0:
            raise ValueError("Polygon epsilon factor must be greater than zero.")

        self._contour_retrieval_mode = contour_retrieval_mode
        self._contour_approximation_mode = contour_approximation_mode
        self._polygon_epsilon_factor = polygon_epsilon_factor

    def detect(self, image: NDArray[np.uint8]) -> BoardQuad:
        contours, _ = cv2.findContours(
            image,
            self._contour_retrieval_mode,
            self._contour_approximation_mode,
        )
        if not contours:
            raise ValueError("No contours were found in input image.")

        largest_contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest_contour) <= 0:
            raise ValueError("Largest contour has invalid area.")

        perimeter = cv2.arcLength(largest_contour, True)
        approximation = cv2.approxPolyDP(
            largest_contour,
            self._polygon_epsilon_factor * perimeter,
            True,
        )

        board_points = approximation.reshape(-1, 2)
        if board_points.shape[0] != 4:
            minimum_area_rectangle = cv2.minAreaRect(largest_contour)
            board_points = cv2.boxPoints(minimum_area_rectangle)

        ordered_points = _order_points_clockwise(board_points)
        return BoardQuad(
            top_left=ordered_points[0],
            top_right=ordered_points[1],
            bottom_right=ordered_points[2],
            bottom_left=ordered_points[3],
        )


def _order_points_clockwise(
    points: NDArray[np.floating],
) -> tuple[tuple[float, float], ...]:
    if points.shape[0] != 4:
        raise ValueError("Expected exactly four contour points.")

    unique_points = np.unique(points, axis=0)
    if unique_points.shape[0] != 4:
        raise ValueError("Contour points are not unique.")

    points_as_float32 = points.astype(np.float32)
    sums = points_as_float32.sum(axis=1)
    diffs = np.diff(points_as_float32, axis=1)

    top_left = points_as_float32[np.argmin(sums)]
    bottom_right = points_as_float32[np.argmax(sums)]
    top_right = points_as_float32[np.argmin(diffs)]
    bottom_left = points_as_float32[np.argmax(diffs)]

    return (
        (float(top_left[0]), float(top_left[1])),
        (float(top_right[0]), float(top_right[1])),
        (float(bottom_right[0]), float(bottom_right[1])),
        (float(bottom_left[0]), float(bottom_left[1])),
    )
