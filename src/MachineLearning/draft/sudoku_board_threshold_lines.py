from __future__ import annotations

from sudoku_board_threshold_line_bridge import bridge_line_family_gaps
from sudoku_board_threshold_line_detection import detect_line_families
from sudoku_board_threshold_line_families import (
    collect_line_family,
    get_dominant_angle_degrees,
    is_horizontal_like,
)
from sudoku_board_threshold_line_geometry import (
    angle_difference_degrees,
    build_line_segment,
    clamp_point_to_image,
    direction_vector_from_angle,
    interval_gap,
    normal_vector_from_angle,
    point_from_line_position,
    point_position_on_direction,
    resolve_merged_line_vertices,
    segment_interval_along_direction,
)
from sudoku_board_threshold_line_merge import (
    build_merged_line,
    connected_components,
    merge_line_family_segments,
    should_merge_line_segments,
)
from sudoku_board_threshold_line_touch import (
    annotate_cross_family_touches,
    drop_zero_touch_lines,
    filter_lines_by_min_cross_family_touch_points,
    intersection_point_for_merged_lines,
    iteratively_filter_lines_by_touch_points,
    line_vertex_name,
    merged_lines_touch,
    refresh_cross_family_touches,
    resolve_last_touch_endpoint_connections,
    touch_points_for_merged_lines,
)


__all__ = [
    "angle_difference_degrees",
    "annotate_cross_family_touches",
    "build_line_segment",
    "build_merged_line",
    "clamp_point_to_image",
    "collect_line_family",
    "connected_components",
    "detect_line_families",
    "direction_vector_from_angle",
    "drop_zero_touch_lines",
    "filter_lines_by_min_cross_family_touch_points",
    "get_dominant_angle_degrees",
    "intersection_point_for_merged_lines",
    "interval_gap",
    "iteratively_filter_lines_by_touch_points",
    "line_vertex_name",
    "is_horizontal_like",
    "bridge_line_family_gaps",
    "merge_line_family_segments",
    "merged_lines_touch",
    "normal_vector_from_angle",
    "point_from_line_position",
    "point_position_on_direction",
    "refresh_cross_family_touches",
    "resolve_last_touch_endpoint_connections",
    "resolve_merged_line_vertices",
    "segment_interval_along_direction",
    "should_merge_line_segments",
    "touch_points_for_merged_lines",
]
