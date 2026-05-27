import sys
import unittest
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DRAFT_DIR = PROJECT_ROOT / "draft"
if str(DRAFT_DIR) not in sys.path:
    sys.path.insert(0, str(DRAFT_DIR))

from sudoku_board_threshold_line_geometry import build_detected_line_segment  # noqa: E402
from sudoku_board_threshold_line_merge import build_merged_line  # noqa: E402
from sudoku_board_threshold_models import EndpointConnection, LineFrame  # noqa: E402
from sudoku_board_threshold_warp import (  # noqa: E402
    aligned_frame_corners,
    warp_image_from_corners,
)


def build_endpoint_connection(
    horizontal_line_index: int,
    vertical_line_index: int,
    aligned_point: tuple[int, int],
) -> EndpointConnection:
    return EndpointConnection(
        horizontal_line_index=horizontal_line_index,
        horizontal_vertex_index=0,
        vertical_line_index=vertical_line_index,
        vertical_vertex_index=0,
        horizontal_vertex=aligned_point,
        vertical_vertex=aligned_point,
        aligned_point=aligned_point,
        touch_point=aligned_point,
    )


def build_line_frame() -> LineFrame:
    top_line = build_merged_line(
        "horizontal",
        0.0,
        [build_detected_line_segment((20, 10), (80, 10))],
    )
    bottom_line = build_merged_line(
        "horizontal",
        0.0,
        [build_detected_line_segment((20, 90), (80, 90))],
    )
    left_line = build_merged_line(
        "vertical",
        90.0,
        [build_detected_line_segment((15, 10), (15, 90))],
    )
    right_line = build_merged_line(
        "vertical",
        90.0,
        [build_detected_line_segment((85, 10), (85, 90))],
    )

    top_left_connection = build_endpoint_connection(0, 0, (18, 10))
    top_right_connection = build_endpoint_connection(0, 1, (82, 10))
    bottom_right_connection = build_endpoint_connection(1, 1, (83, 90))
    bottom_left_connection = build_endpoint_connection(1, 0, (17, 90))

    return LineFrame(
        top_line_index=0,
        bottom_line_index=1,
        left_line_index=0,
        right_line_index=1,
        top_line=top_line,
        bottom_line=bottom_line,
        left_line=left_line,
        right_line=right_line,
        top_left_connection=top_left_connection,
        top_right_connection=top_right_connection,
        bottom_right_connection=bottom_right_connection,
        bottom_left_connection=bottom_left_connection,
        corners=((18, 10), (82, 10), (83, 90), (17, 90)),
        area_px=5120.0,
        perimeter_px=288.0,
        horizontal_line_count=10,
        vertical_line_count=10,
        inner_horizontal_line_count=8,
        inner_vertical_line_count=8,
        shared_horizontal_line_count=10,
        shared_vertical_line_count=10,
        outer_margin_line_count=0,
        grid_distance_score=0,
        priority_score=1.0,
    )


class SudokuBoardThresholdWarpTests(unittest.TestCase):
    def test_aligned_frame_corners_should_return_frame_corners_for_warp(
        self,
    ) -> None:
        frame = build_line_frame()

        self.assertEqual(
            aligned_frame_corners(frame),
            ((18.0, 10.0), (82.0, 10.0), (83.0, 90.0), (17.0, 90.0)),
        )

    def test_warp_image_from_corners_should_return_square_image(
        self,
    ) -> None:
        source_image = np.zeros((120, 120, 3), dtype=np.uint8)
        source_image[10:91, 17:84] = (0, 255, 0)

        warped = warp_image_from_corners(
            source_image,
            ((18.0, 10.0), (82.0, 10.0), (83.0, 90.0), (17.0, 90.0)),
            output_size=96,
            padding_pixels=0,
        )

        self.assertEqual(warped.shape, (96, 96, 3))
        self.assertGreater(int(np.count_nonzero(warped[:, :, 1])), 0)


if __name__ == "__main__":
    unittest.main()
