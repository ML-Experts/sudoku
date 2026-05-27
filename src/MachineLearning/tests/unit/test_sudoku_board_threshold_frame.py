from dataclasses import replace
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DRAFT_DIR = PROJECT_ROOT / "draft"
if str(DRAFT_DIR) not in sys.path:
    sys.path.insert(0, str(DRAFT_DIR))

from sudoku_board_threshold_frame import (  # noqa: E402
    build_endpoint_connection_lookup,
    build_horizontal_connection_map,
    build_line_frame_candidate,
    build_vertical_connection_map,
    find_line_frames,
    is_dominated_by_larger_container,
)
from sudoku_board_threshold_line_geometry import build_detected_line_segment  # noqa: E402
from sudoku_board_threshold_line_merge import build_merged_line  # noqa: E402
from sudoku_board_threshold_line_touch import (  # noqa: E402
    annotate_cross_family_touches,
    resolve_last_touch_endpoint_connections,
)
from sudoku_board_threshold_models import ExperimentConfig, LineFamilyResult  # noqa: E402


def build_horizontal_line(
    y: int,
    x_start: int = 10,
    x_end: int = 50,
):
    return build_merged_line(
        "horizontal",
        0.0,
        [build_detected_line_segment((x_start, y), (x_end, y))],
    )


def build_vertical_line(
    x: int,
    y_start: int = 10,
    y_end: int = 50,
):
    return build_merged_line(
        "vertical",
        90.0,
        [build_detected_line_segment((x, y_start), (x, y_end))],
    )


def build_line_family_result(
    horizontal_lines,
    vertical_lines,
    touch_tolerance_px: float = 2.0,
) -> LineFamilyResult:
    annotated_horizontal, annotated_vertical = annotate_cross_family_touches(
        horizontal_lines,
        vertical_lines,
        touch_tolerance_px,
    )
    (
        horizontal_aligned_vertices,
        vertical_aligned_vertices,
        endpoint_connections,
    ) = resolve_last_touch_endpoint_connections(
        list(annotated_horizontal),
        list(annotated_vertical),
        touch_tolerance_px,
    )
    return LineFamilyResult(
        raw_segment_count=0,
        raw_min_line_length_px=0,
        raw_max_line_gap_px=0,
        horizontal_angle_degrees=0.0,
        vertical_angle_degrees=90.0,
        merge_projection_distance_px=0.0,
        merge_endpoint_gap_px=0.0,
        bridge_projection_tolerance_px=0.0,
        bridge_max_gap_px=0.0,
        bridge_endpoint_tolerance_px=0.0,
        cross_family_touch_tolerance_px=touch_tolerance_px,
        horizontal_segments=[],
        vertical_segments=[],
        horizontal_pre_filter_merged_lines=list(annotated_horizontal),
        vertical_pre_filter_merged_lines=list(annotated_vertical),
        horizontal_bridges=[],
        vertical_bridges=[],
        horizontal_merged_lines=list(annotated_horizontal),
        vertical_merged_lines=list(annotated_vertical),
        horizontal_aligned_vertices=horizontal_aligned_vertices,
        vertical_aligned_vertices=vertical_aligned_vertices,
        endpoint_connections=endpoint_connections,
    )


def build_candidate_frame(
    horizontal_lines,
    vertical_lines,
    top_line_index: int,
    bottom_line_index: int,
    left_line_index: int,
    right_line_index: int,
    touch_tolerance_px: float = 2.0,
    minimum_area_px: float = 1.0,
    reference_area_px: float = 1600.0,
):
    line_family_result = build_line_family_result(
        horizontal_lines,
        vertical_lines,
        touch_tolerance_px=touch_tolerance_px,
    )
    return build_line_frame_candidate(
        horizontal_lines=list(line_family_result.horizontal_merged_lines),
        vertical_lines=list(line_family_result.vertical_merged_lines),
        top_line_index=top_line_index,
        bottom_line_index=bottom_line_index,
        left_line_index=left_line_index,
        right_line_index=right_line_index,
        endpoint_connection_lookup=build_endpoint_connection_lookup(
            line_family_result.endpoint_connections
        ),
        horizontal_connection_map=build_horizontal_connection_map(
            line_family_result.endpoint_connections
        ),
        vertical_connection_map=build_vertical_connection_map(
            line_family_result.endpoint_connections
        ),
        minimum_area_px=minimum_area_px,
        reference_area_px=reference_area_px,
        config=ExperimentConfig(),
    )


class SudokuBoardThresholdFrameTests(unittest.TestCase):
    def test_build_line_frame_candidate_should_create_frame_with_complete_corners(
        self,
    ) -> None:
        candidate_frame = build_candidate_frame(
            horizontal_lines=[
                build_horizontal_line(10),
                build_horizontal_line(50),
            ],
            vertical_lines=[
                build_vertical_line(10),
                build_vertical_line(50),
            ],
            top_line_index=0,
            bottom_line_index=1,
            left_line_index=0,
            right_line_index=1,
        )

        self.assertIsNotNone(candidate_frame)
        self.assertEqual(
            candidate_frame.corners if candidate_frame is not None else (),
            ((10, 10), (50, 10), (50, 50), (10, 50)),
        )
        self.assertEqual(candidate_frame.horizontal_line_count, 2)
        self.assertEqual(candidate_frame.vertical_line_count, 2)

    def test_build_line_frame_candidate_should_reject_missing_corner_connection(
        self,
    ) -> None:
        candidate_frame = build_candidate_frame(
            horizontal_lines=[
                build_horizontal_line(10),
                build_horizontal_line(50),
            ],
            vertical_lines=[
                build_vertical_line(10),
                build_vertical_line(50, y_start=20, y_end=50),
            ],
            top_line_index=0,
            bottom_line_index=1,
            left_line_index=0,
            right_line_index=1,
        )

        self.assertIsNone(candidate_frame)

    def test_build_line_frame_candidate_should_reject_too_small_frame(
        self,
    ) -> None:
        candidate_frame = build_candidate_frame(
            horizontal_lines=[
                build_horizontal_line(10, x_start=10, x_end=16),
                build_horizontal_line(16, x_start=10, x_end=16),
            ],
            vertical_lines=[
                build_vertical_line(10, y_start=10, y_end=16),
                build_vertical_line(16, y_start=10, y_end=16),
            ],
            top_line_index=0,
            bottom_line_index=1,
            left_line_index=0,
            right_line_index=1,
            minimum_area_px=100.0,
            reference_area_px=36.0,
        )

        self.assertIsNone(candidate_frame)

    def test_find_line_frames_should_build_frame_from_unordered_corner_connections(
        self,
    ) -> None:
        horizontal_lines = [
            build_merged_line(
                "horizontal",
                0.0,
                [build_detected_line_segment((12, 10), (88, 10))],
            ),
            build_merged_line(
                "horizontal",
                0.0,
                [build_detected_line_segment((20, 50), (80, 50))],
            ),
            build_merged_line(
                "horizontal",
                0.0,
                [build_detected_line_segment((12, 90), (88, 90))],
            ),
        ]
        vertical_lines = [
            build_merged_line(
                "vertical",
                90.0,
                [build_detected_line_segment((12, 10), (12, 90))],
            ),
            build_merged_line(
                "vertical",
                90.0,
                [build_detected_line_segment((50, 20), (50, 80))],
            ),
            build_merged_line(
                "vertical",
                90.0,
                [build_detected_line_segment((88, 10), (88, 90))],
            ),
        ]
        line_family_result = build_line_family_result(
            horizontal_lines,
            vertical_lines,
            touch_tolerance_px=4.0,
        )
        line_family_result = replace(
            line_family_result,
            endpoint_connections=(
                line_family_result.endpoint_connections[0],
                line_family_result.endpoint_connections[2],
                line_family_result.endpoint_connections[1],
                line_family_result.endpoint_connections[4],
                line_family_result.endpoint_connections[3],
            ),
        )

        frame_detection_result = find_line_frames(
            line_family_result=line_family_result,
            config=ExperimentConfig(
                frame_min_area_ratio=0.0,
                frame_max_selected_count=4,
            ),
        )

        self.assertEqual(len(frame_detection_result.all_frames), 1)
        self.assertEqual(len(frame_detection_result.selected_frames), 1)

        frame = frame_detection_result.selected_frames[0]
        self.assertEqual(frame.top_line_index, 0)
        self.assertEqual(frame.bottom_line_index, 2)
        self.assertEqual(frame.left_line_index, 0)
        self.assertEqual(frame.right_line_index, 2)
        self.assertEqual(frame.corners, ((12, 10), (88, 10), (88, 90), (12, 90)))
        self.assertEqual(frame.inner_horizontal_line_count, 1)
        self.assertEqual(frame.inner_vertical_line_count, 1)

    def test_find_line_frames_should_prefer_outer_frame_with_more_inner_lines(
        self,
    ) -> None:
        line_family_result = build_line_family_result(
            [build_horizontal_line(y) for y in (10, 20, 30, 40, 50)],
            [build_vertical_line(x) for x in (10, 20, 30, 40, 50)],
        )

        frame_detection_result = find_line_frames(
            line_family_result,
            ExperimentConfig(
                expected_horizontal_line_count=5,
                expected_vertical_line_count=5,
                frame_min_area_ratio=0.02,
                frame_max_selected_count=10,
            ),
        )

        self.assertGreaterEqual(len(frame_detection_result.selected_frames), 1)
        self.assertEqual(
            (
                frame_detection_result.selected_frames[0].top_line_index,
                frame_detection_result.selected_frames[0].bottom_line_index,
                frame_detection_result.selected_frames[0].left_line_index,
                frame_detection_result.selected_frames[0].right_line_index,
            ),
            (0, 4, 0, 4),
        )

        selected_frame_indices = {
            (
                frame.top_line_index,
                frame.bottom_line_index,
                frame.left_line_index,
                frame.right_line_index,
            )
            for frame in frame_detection_result.selected_frames
        }
        self.assertNotIn((1, 3, 1, 3), selected_frame_indices)

    def test_nested_frames_should_prefer_larger_perimeter_over_priority(
        self,
    ) -> None:
        outer_frame = build_candidate_frame(
            horizontal_lines=[
                build_horizontal_line(10, x_start=10, x_end=40),
                build_horizontal_line(20, x_start=20, x_end=30),
                build_horizontal_line(30, x_start=20, x_end=30),
                build_horizontal_line(40, x_start=10, x_end=40),
            ],
            vertical_lines=[
                build_vertical_line(10, y_start=10, y_end=40),
                build_vertical_line(20, y_start=20, y_end=30),
                build_vertical_line(30, y_start=20, y_end=30),
                build_vertical_line(40, y_start=10, y_end=40),
            ],
            top_line_index=0,
            bottom_line_index=3,
            left_line_index=0,
            right_line_index=3,
            reference_area_px=900.0,
        )
        inner_frame = build_candidate_frame(
            horizontal_lines=[
                build_horizontal_line(10, x_start=10, x_end=40),
                build_horizontal_line(20, x_start=20, x_end=30),
                build_horizontal_line(30, x_start=20, x_end=30),
                build_horizontal_line(40, x_start=10, x_end=40),
            ],
            vertical_lines=[
                build_vertical_line(10, y_start=10, y_end=40),
                build_vertical_line(20, y_start=20, y_end=30),
                build_vertical_line(30, y_start=20, y_end=30),
                build_vertical_line(40, y_start=10, y_end=40),
            ],
            top_line_index=1,
            bottom_line_index=2,
            left_line_index=1,
            right_line_index=2,
            reference_area_px=900.0,
        )

        self.assertIsNotNone(outer_frame)
        self.assertIsNotNone(inner_frame)

        outer_frame = replace(outer_frame, priority_score=1.0)
        inner_frame = replace(inner_frame, priority_score=999.0)

        self.assertTrue(is_dominated_by_larger_container(inner_frame, outer_frame))
        self.assertFalse(is_dominated_by_larger_container(outer_frame, inner_frame))


if __name__ == "__main__":
    unittest.main()
