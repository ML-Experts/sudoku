from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from models import ToleranceRectangle


@dataclass(frozen=True, slots=True)
class SearchArea:
    mask: np.ndarray
    min_x: int
    max_x: int
    min_y: int
    max_y: int


def build_search_area(
    image_shape: tuple[int, int],
    tolerance_rectangle: ToleranceRectangle,
) -> SearchArea:
    mask = np.zeros(image_shape[:2], dtype=np.uint8)
    corners = np.array(tolerance_rectangle.corners, dtype=np.int32)
    cv2.fillConvexPoly(mask, corners, 1)
    x_coordinates = corners[:, 0]
    y_coordinates = corners[:, 1]
    max_width = image_shape[1] - 1
    max_height = image_shape[0] - 1
    return SearchArea(
        mask=mask.astype(bool),
        min_x=max(0, int(x_coordinates.min())),
        max_x=min(max_width, int(x_coordinates.max())),
        min_y=max(0, int(y_coordinates.min())),
        max_y=min(max_height, int(y_coordinates.max())),
    )


def is_point_in_search_area(
    point: tuple[int, int],
    search_area: SearchArea,
) -> bool:
    x_coord, y_coord = point
    if (
        x_coord < search_area.min_x
        or x_coord > search_area.max_x
        or y_coord < search_area.min_y
        or y_coord > search_area.max_y
    ):
        return False
    return bool(search_area.mask[y_coord, x_coord])


__all__ = [
    "SearchArea",
    "build_search_area",
    "is_point_in_search_area",
]
