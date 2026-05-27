from __future__ import annotations

import numpy as np

from sudoku_board_threshold_models import DetectedLineSegment


def build_line_segment(raw_segment: np.ndarray) -> DetectedLineSegment:
    x1, y1, x2, y2 = (int(value) for value in raw_segment)
    delta_x = float(x2 - x1)
    delta_y = float(y2 - y1)
    return DetectedLineSegment(
        start=(x1, y1),
        end=(x2, y2),
        length=float(np.hypot(delta_x, delta_y)),
        angle_degrees=float(np.degrees(np.arctan2(delta_y, delta_x)) % 180.0),
    )


def build_detected_line_segment(
    start: tuple[int, int],
    end: tuple[int, int],
) -> DetectedLineSegment:
    delta_x = float(end[0] - start[0])
    delta_y = float(end[1] - start[1])
    return DetectedLineSegment(
        start=start,
        end=end,
        length=float(np.hypot(delta_x, delta_y)),
        angle_degrees=float(np.degrees(np.arctan2(delta_y, delta_x)) % 180.0),
    )


def angle_difference_degrees(first_angle: float, second_angle: float) -> float:
    raw_difference = abs(first_angle - second_angle) % 180.0
    return min(raw_difference, 180.0 - raw_difference)


def direction_vector_from_angle(angle_degrees: float) -> np.ndarray:
    angle_radians = np.deg2rad(angle_degrees)
    return np.array(
        [np.cos(angle_radians), np.sin(angle_radians)],
        dtype=np.float32,
    )


def normal_vector_from_angle(angle_degrees: float) -> np.ndarray:
    direction = direction_vector_from_angle(angle_degrees)
    return np.array([-direction[1], direction[0]], dtype=np.float32)


def point_array(point: tuple[int, int] | tuple[float, float]) -> np.ndarray:
    return np.array(point, dtype=np.float32)


def point_position_on_direction(
    point: tuple[int, int] | tuple[float, float],
    direction: np.ndarray,
) -> float:
    return float(np.dot(point_array(point), direction))


def point_from_line_position(
    projection: float,
    position: float,
    family_angle_degrees: float,
) -> tuple[int, int]:
    direction = direction_vector_from_angle(family_angle_degrees)
    normal = normal_vector_from_angle(family_angle_degrees)
    point = normal * projection + direction * position
    return int(round(float(point[0]))), int(round(float(point[1])))


def clamp_point_to_image(
    point: tuple[int, int],
    image_shape: tuple[int, ...],
) -> tuple[int, int]:
    height, width = image_shape[:2]
    return (
        int(np.clip(point[0], 0, width - 1)),
        int(np.clip(point[1], 0, height - 1)),
    )


def segment_interval_along_direction(
    line_segment: DetectedLineSegment,
    direction: np.ndarray,
) -> tuple[float, float]:
    start_position = point_position_on_direction(line_segment.start, direction)
    end_position = point_position_on_direction(line_segment.end, direction)
    return min(start_position, end_position), max(start_position, end_position)


def interval_gap(
    first_interval: tuple[float, float],
    second_interval: tuple[float, float],
) -> float:
    first_start, first_end = first_interval
    second_start, second_end = second_interval
    if first_end < second_start:
        return second_start - first_end
    if second_end < first_start:
        return first_start - second_end
    return 0.0


def merge_overlapping_intervals(
    intervals: list[tuple[float, float]],
    join_gap_px: float = 0.0,
) -> tuple[tuple[float, float], ...]:
    if not intervals:
        return ()

    sorted_intervals = sorted(intervals)
    merged_intervals: list[list[float]] = [
        [float(sorted_intervals[0][0]), float(sorted_intervals[0][1])]
    ]
    for start, end in sorted_intervals[1:]:
        last_interval = merged_intervals[-1]
        if float(start) <= last_interval[1] + join_gap_px:
            last_interval[1] = max(last_interval[1], float(end))
            continue
        merged_intervals.append([float(start), float(end)])
    return tuple((start, end) for start, end in merged_intervals)


def merged_interval_length(intervals: tuple[tuple[float, float], ...]) -> float:
    return float(
        sum(interval_end - interval_start for interval_start, interval_end in intervals)
    )


def point_is_within_intervals(
    position: float,
    intervals: tuple[tuple[float, float], ...],
    tolerance_px: float,
) -> bool:
    return any(
        interval_start - tolerance_px <= position <= interval_end + tolerance_px
        for interval_start, interval_end in intervals
    )


def cross_product_2d(first_vector: np.ndarray, second_vector: np.ndarray) -> float:
    return float(first_vector[0] * second_vector[1] - first_vector[1] * second_vector[0])


def intersection_point_for_segments(
    first_segment: DetectedLineSegment,
    second_segment: DetectedLineSegment,
    tolerance_px: float,
) -> np.ndarray | None:
    first_start = point_array(first_segment.start)
    first_direction = point_array(first_segment.end) - first_start
    second_start = point_array(second_segment.start)
    second_direction = point_array(second_segment.end) - second_start

    denominator = cross_product_2d(first_direction, second_direction)
    if abs(denominator) <= 1e-6:
        return None

    first_length = float(np.linalg.norm(first_direction))
    second_length = float(np.linalg.norm(second_direction))
    if first_length <= 1e-6 or second_length <= 1e-6:
        return None

    delta = second_start - first_start
    first_scale = cross_product_2d(delta, second_direction) / denominator
    second_scale = cross_product_2d(delta, first_direction) / denominator
    first_tolerance = tolerance_px / first_length
    second_tolerance = tolerance_px / second_length
    if not (-first_tolerance <= first_scale <= 1.0 + first_tolerance):
        return None
    if not (-second_tolerance <= second_scale <= 1.0 + second_tolerance):
        return None
    return first_start + first_direction * first_scale


def deduplicate_touch_points(
    touch_points: list[np.ndarray],
    tolerance_px: float,
) -> tuple[tuple[int, int], ...]:
    deduplicated_points: list[np.ndarray] = []
    for touch_point in touch_points:
        for point_index, existing_point in enumerate(deduplicated_points):
            if float(np.linalg.norm(touch_point - existing_point)) > tolerance_px:
                continue
            deduplicated_points[point_index] = (existing_point + touch_point) / 2.0
            break
        else:
            deduplicated_points.append(touch_point.astype(np.float32))

    return tuple(
        (
            int(round(float(touch_point[0]))),
            int(round(float(touch_point[1]))),
        )
        for touch_point in deduplicated_points
    )


def build_axis_aligned_box(
    center: tuple[int, int],
    radius_px: int,
    image_shape: tuple[int, ...],
) -> tuple[tuple[int, int], tuple[int, int]]:
    height, width = image_shape[:2]
    return (
        (
            int(np.clip(center[0] - radius_px, 0, width - 1)),
            int(np.clip(center[1] - radius_px, 0, height - 1)),
        ),
        (
            int(np.clip(center[0] + radius_px, 0, width - 1)),
            int(np.clip(center[1] + radius_px, 0, height - 1)),
        ),
    )


def build_corridor_polygon(
    start_point: tuple[int, int],
    end_point: tuple[int, int],
    half_width_px: float,
) -> tuple[tuple[int, int], ...]:
    start_vector = point_array(start_point)
    end_vector = point_array(end_point)
    segment_vector = end_vector - start_vector
    segment_length = float(np.linalg.norm(segment_vector))
    if segment_length <= 1e-6:
        return (
            start_point,
            start_point,
            end_point,
            end_point,
        )

    direction = segment_vector / segment_length
    normal = np.array([-direction[1], direction[0]], dtype=np.float32)
    offset = normal * float(half_width_px)
    polygon = (
        start_vector + offset,
        start_vector - offset,
        end_vector - offset,
        end_vector + offset,
    )
    return tuple(
        (
            int(round(float(point[0]))),
            int(round(float(point[1]))),
        )
        for point in polygon
    )


__all__ = [
    "angle_difference_degrees",
    "build_axis_aligned_box",
    "build_corridor_polygon",
    "build_detected_line_segment",
    "build_line_segment",
    "clamp_point_to_image",
    "cross_product_2d",
    "deduplicate_touch_points",
    "direction_vector_from_angle",
    "interval_gap",
    "intersection_point_for_segments",
    "merge_overlapping_intervals",
    "merged_interval_length",
    "normal_vector_from_angle",
    "point_array",
    "point_from_line_position",
    "point_is_within_intervals",
    "point_position_on_direction",
    "segment_interval_along_direction",
]
