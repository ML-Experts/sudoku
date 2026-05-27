import sys
import unittest
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DRAFT_DIR = PROJECT_ROOT / "draft"
if str(DRAFT_DIR) not in sys.path:
    sys.path.insert(0, str(DRAFT_DIR))

from sudoku_board_threshold_line_bridge import (  # noqa: E402
    bridge_line_family_gaps,
    closest_interval_bridge_positions,
    line_bridge_candidate,
)
from sudoku_board_threshold_line_geometry import build_detected_line_segment  # noqa: E402
from sudoku_board_threshold_line_merge import build_merged_line  # noqa: E402
from sudoku_board_threshold_line_touch import (  # noqa: E402
    resolve_last_touch_endpoint_connections,
)
from sudoku_board_threshold_models import ExperimentConfig  # noqa: E402


class SudokuBoardThresholdLineBridgeTests(unittest.TestCase):
    def test_closest_interval_bridge_positions_should_handle_overlapping_spans(
        self,
    ) -> None:
        first_line = build_merged_line(
            "vertical",
            90.0,
            [build_detected_line_segment((10, 10), (10, 60))],
        )
        second_line = build_merged_line(
            "vertical",
            90.0,
            [build_detected_line_segment((14, 40), (14, 90))],
        )

        bridge_positions = closest_interval_bridge_positions(first_line, second_line)

        self.assertIsNotNone(bridge_positions)
        first_position, second_position, gap_px = bridge_positions or (0.0, 0.0, 0.0)
        self.assertEqual(gap_px, 0.0)
        self.assertAlmostEqual(first_position, 50.0)
        self.assertAlmostEqual(second_position, 50.0)

    def test_bridge_line_family_gaps_should_merge_overlapping_lines_when_pixels_connect(
        self,
    ) -> None:
        binary_image = np.zeros((100, 100), dtype=np.uint8)
        binary_image[10:61, 10] = 255
        binary_image[40:91, 14] = 255
        binary_image[50, 10:15] = 255

        first_line = build_merged_line(
            "vertical",
            90.0,
            [build_detected_line_segment((10, 10), (10, 60))],
        )
        second_line = build_merged_line(
            "vertical",
            90.0,
            [build_detected_line_segment((14, 40), (14, 90))],
        )

        direct_bridge = line_bridge_candidate(
            binary_image=binary_image,
            first_line=first_line,
            second_line=second_line,
            family_angle_degrees=90.0,
            family_name="vertical",
            first_line_index=0,
            second_line_index=1,
            projection_tolerance_px=10.0,
            max_gap_px=20.0,
            endpoint_tolerance_px=4.0,
        )

        self.assertIsNotNone(direct_bridge)

        merged_lines, bridges, _, _, _ = bridge_line_family_gaps(
            binary_image=binary_image,
            merged_lines=[first_line, second_line],
            family_angle_degrees=90.0,
            family_name="vertical",
            config=ExperimentConfig(),
            minimum_dimension=100,
        )

        self.assertEqual(len(bridges), 1)
        self.assertEqual(len(merged_lines), 1)
        self.assertEqual(merged_lines[0].segment_count, 3)
        self.assertEqual(merged_lines[0].support_intervals, ((10.0, 90.0),))

    def test_resolve_last_touch_endpoint_connections_should_snap_mutual_endpoints(
        self,
    ) -> None:
        horizontal_line = build_merged_line(
            "horizontal",
            0.0,
            [build_detected_line_segment((10, 20), (50, 20))],
        )
        left_vertical_line = build_merged_line(
            "vertical",
            90.0,
            [build_detected_line_segment((12, 18), (12, 60))],
        )
        right_vertical_line = build_merged_line(
            "vertical",
            90.0,
            [build_detected_line_segment((48, 18), (48, 60))],
        )

        (
            horizontal_aligned_vertices,
            vertical_aligned_vertices,
            endpoint_connections,
        ) = resolve_last_touch_endpoint_connections(
            horizontal_lines=[horizontal_line],
            vertical_lines=[left_vertical_line, right_vertical_line],
            touch_tolerance_px=4.0,
        )

        self.assertEqual(len(endpoint_connections), 2)
        self.assertEqual(
            horizontal_aligned_vertices,
            (((12, 20), (48, 20)),),
        )
        self.assertEqual(vertical_aligned_vertices[0][0], (12, 20))
        self.assertEqual(vertical_aligned_vertices[1][0], (48, 20))
        self.assertEqual(endpoint_connections[0].horizontal_line_index, 0)
        self.assertEqual(endpoint_connections[0].vertical_line_index, 0)
        self.assertEqual(endpoint_connections[0].horizontal_vertex_index, 0)
        self.assertEqual(endpoint_connections[0].vertical_vertex_index, 0)
        self.assertEqual(endpoint_connections[1].horizontal_line_index, 0)
        self.assertEqual(endpoint_connections[1].vertical_line_index, 1)
        self.assertEqual(endpoint_connections[1].horizontal_vertex_index, 1)
        self.assertEqual(endpoint_connections[1].vertical_vertex_index, 0)


if __name__ == "__main__":
    unittest.main()
