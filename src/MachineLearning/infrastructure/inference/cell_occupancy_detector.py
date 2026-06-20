import base64

import cv2
import numpy as np
from numpy.typing import NDArray

from models.cell_occupancy import CellOccupancy


class CellOccupancyDetector:
    """
    Detects whether a Sudoku cell is empty.

    Assumption:
    The input image is already a binary foreground mask, not a raw grayscale image.

    Expected mask:
    - uint8:
        0   = background
        255 = foreground / dark element from original cell image

    - float32:
        0.0 = background
        1.0 = foreground

    Detection heuristic:
    1. Convert input to boolean foreground mask.
    2. Extract the exact central 50% x 50% square of the cell.
       This corresponds to:
       - quadrant 4 of quadrant 1,
       - quadrant 3 of quadrant 2,
       - quadrant 2 of quadrant 3,
       - quadrant 1 of quadrant 4.
    3. Remove artifacts inside this central square:
       - long thin horizontal / vertical lines,
       - tiny disconnected components.
    4. Count remaining foreground ratio in the center.
    5. If the ratio is <= threshold, the cell is empty.
    """


    def detect(
        self,
        image: NDArray[np.float32] | NDArray[np.uint8],
        inner_margin_ratio: float,
        dark_pixel_ratio_threshold: float,
        center_area_ratio: float,
        min_component_area_ratio: float,
        line_artifact_min_span_ratio: float,
        line_artifact_max_thickness_ratio: float
    ) -> CellOccupancy:
        """
        Parameters
        ----------
        image:
            A 2D binary mask:
            - uint8: 0 / 255
            - float32: 0.0 / 1.0

        inner_margin_ratio:
            Removes the outer border area before central-area analysis.

        dark_pixel_ratio_threshold:
            Maximum filtered foreground ratio in the central area
            that is still considered empty.

            Current config value 0.02 can stay.
        """
        if image.size == 0:
            raise ValueError("Image cannot be empty.")

        if image.ndim != 2:
            raise ValueError("Expected a 2D grayscale image.")

        if image.dtype == np.uint8:
            image_uint8 = image
        else:
            image_float = image.astype(np.float32)

            if float(np.max(image_float)) <= 1.0:
                image_float = image_float * 255.0

            image_uint8 = np.clip(image_float, 0.0, 255.0).astype(np.uint8)

        success, encoded_image = cv2.imencode(".png", image_uint8)

        if not success:
            raise ValueError("Failed to encode image as PNG.")

        bs64: str = base64.b64encode(encoded_image.tobytes()).decode("utf-8")

        if image.size == 0:
            raise ValueError("Cell image cannot be empty.")

        if image.ndim != 2:
            raise ValueError("Cell occupancy detector expects a 2D image.")

        if not 0.0 <= inner_margin_ratio < 0.5:
            raise ValueError("Inner margin ratio must be in range [0.0, 0.5).")

        if not 0.0 <= dark_pixel_ratio_threshold <= 1.0:
            raise ValueError(
                "Dark pixel ratio threshold must be in range [0.0, 1.0]."
            )

        foreground_mask = self._to_foreground_mask(image)
        cropped_foreground_mask = self._crop_inner_margin(
            mask=foreground_mask,
            inner_margin_ratio=inner_margin_ratio,
        )

        center_mask = self._extract_center_square(
            mask=cropped_foreground_mask,
            center_area_ratio=center_area_ratio,
        )

        if center_mask.size == 0:
            raise ValueError("Center mask window is empty.")

        filtered_center_mask = self._remove_center_artifacts(
            center_mask,
            center_area_ratio,
            min_component_area_ratio,
            line_artifact_min_span_ratio,
            line_artifact_max_thickness_ratio
        )

        dark_pixel_ratio = float(np.mean(filtered_center_mask > 0))

        return CellOccupancy(
            is_empty=dark_pixel_ratio <= dark_pixel_ratio_threshold,
            dark_pixel_ratio=dark_pixel_ratio,
        )

    # ============================================================
    # Input conversion
    # ============================================================

    def _to_foreground_mask(
        self,
        image: NDArray[np.float32] | NDArray[np.uint8],
    ) -> NDArray[np.uint8]:
        """
        Converts input binary representation to uint8 foreground mask:
        - 0 = background
        - 1 = foreground

        Supports:
        - uint8 0 / 255
        - float32 0.0 / 1.0
        - float32 0.0 / 255.0
        """
        if image.dtype == np.uint8:
            return (image > 127).astype(np.uint8)

        image_float = image.astype(np.float32)
        max_value = float(np.max(image_float))

        if max_value <= 1.0:
            return (image_float > 0.5).astype(np.uint8)

        return (image_float > 127.0).astype(np.uint8)

    # ============================================================
    # Central square
    # ============================================================

    def _crop_inner_margin(
        self,
        mask: NDArray[np.uint8],
        inner_margin_ratio: float,
    ) -> NDArray[np.uint8]:
        if inner_margin_ratio == 0.0:
            return mask

        height, width = mask.shape
        margin_y = int(round(height * inner_margin_ratio))
        margin_x = int(round(width * inner_margin_ratio))

        max_margin_y = max((height - 1) // 2, 0)
        max_margin_x = max((width - 1) // 2, 0)
        margin_y = min(margin_y, max_margin_y)
        margin_x = min(margin_x, max_margin_x)

        cropped_mask = mask[
            margin_y : height - margin_y,
            margin_x : width - margin_x,
        ]
        if cropped_mask.size == 0:
            raise ValueError("Inner-margin crop produced an empty mask.")

        return cropped_mask

    def _extract_center_square(
        self,
        mask: NDArray[np.uint8],
        center_area_ratio: float,
    ) -> NDArray[np.uint8]:
        """
        Extracts the exact central square.

        For ratio = 0.50:
        - middle 50% of width,
        - middle 50% of height.
        """
        if not 0.0 < center_area_ratio <= 1.0:
            raise ValueError("Center area ratio must be in range (0.0, 1.0].")

        height, width = mask.shape

        center_height = max(1, int(round(height * center_area_ratio)))
        center_width = max(1, int(round(width * center_area_ratio)))

        start_y = (height - center_height) // 2
        start_x = (width - center_width) // 2

        end_y = start_y + center_height
        end_x = start_x + center_width

        return mask[start_y:end_y, start_x:end_x]

    # ============================================================
    # Artifact filtering inside the central square
    # ============================================================

    def _remove_center_artifacts(
        self,
        center_mask: NDArray[np.uint8],
        center_area_ratio: float,
        min_component_area_ratio: float,
        line_artifact_min_span_ratio: float,
        line_artifact_max_thickness_ratio: float
    ) -> NDArray[np.uint8]:
        """
        Removes central artifacts that are not likely to be a digit:
        - small isolated components,
        - long thin horizontal / vertical lines.

        This is needed because some empty cells still contain
        scattered foreground pixels in the central square.
        """
        if center_mask.size == 0:
            return center_mask

        component_count, labels, stats, _ = cv2.connectedComponentsWithStats(
            center_mask,
            connectivity=8,
        )

        if component_count <= 1:
            return center_mask

        center_height, center_width = center_mask.shape
        reference_size = min(center_height, center_width)
        center_area = center_height * center_width

        minimum_component_area = max(
            2,
            int(round(center_area * min_component_area_ratio)),
        )

        minimum_line_span = max(
            2,
            int(round(reference_size * line_artifact_min_span_ratio)),
        )

        maximum_line_thickness = max(
            1,
            int(round(reference_size * line_artifact_max_thickness_ratio)),
        )

        filtered_mask = center_mask.copy()

        for label in range(1, component_count):
            left, top, width, height, area = stats[label]

            width = int(width)
            height = int(height)
            area = int(area)

            is_small_component = area < minimum_component_area

            is_horizontal_line_artifact = (
                width >= minimum_line_span
                and height <= maximum_line_thickness
            )

            is_vertical_line_artifact = (
                height >= minimum_line_span
                and width <= maximum_line_thickness
            )

            if (
                is_small_component
                or is_horizontal_line_artifact
                or is_vertical_line_artifact
            ):
                filtered_mask[labels == label] = 0

        return filtered_mask