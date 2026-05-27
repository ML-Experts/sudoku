from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from sudoku_board_threshold_warp import (
    aligned_frame_corners,
    build_corner_overlay,
    warp_image_from_corners,
)

if TYPE_CHECKING:
    from sudoku_board_threshold_notebook_bootstrap import ThresholdNotebookApi


@dataclass(frozen=True)
class LineDebugArtifacts:
    line_family_result: object
    selected_repaired_binary: np.ndarray
    binary_family_overlay: np.ndarray
    source_family_overlay: np.ndarray
    binary_logical_overlay: np.ndarray
    source_logical_overlay: np.ndarray
    binary_merged_overlay: np.ndarray
    source_merged_overlay: np.ndarray
    binary_vertex_overlay: np.ndarray
    source_vertex_overlay: np.ndarray


@dataclass(frozen=True)
class FrameDebugArtifacts:
    frame_detection_result: object
    selected_frames: list[object]
    binary_frame_overlay: np.ndarray
    source_frame_overlay: np.ndarray


@dataclass(frozen=True)
class WarpDebugArtifacts:
    selected_frame: object | None
    aligned_corners: (
        tuple[
            tuple[float, float],
            tuple[float, float],
            tuple[float, float],
            tuple[float, float],
        ]
        | None
    )
    aligned_corner_overlay: np.ndarray | None
    aligned_warp: np.ndarray | None


def run_line_debug_analysis(
    display_bgr: np.ndarray,
    selected_repaired_binary: np.ndarray,
    config,
    notebook_api: "ThresholdNotebookApi",
) -> LineDebugArtifacts:
    line_family_result = notebook_api.detect_line_families(
        selected_repaired_binary,
        config,
    )
    binary_family_overlay, source_family_overlay = (
        notebook_api.build_line_family_overlays(
            display_bgr,
            selected_repaired_binary,
            line_family_result,
            config,
        )
    )
    binary_logical_overlay, source_logical_overlay = (
        notebook_api.build_bridged_line_family_overlays(
            display_bgr,
            selected_repaired_binary,
            line_family_result,
            config,
        )
    )
    binary_merged_overlay, source_merged_overlay = (
        notebook_api.build_merged_line_overlays(
            display_bgr,
            selected_repaired_binary,
            line_family_result,
            config,
        )
    )
    binary_vertex_overlay, source_vertex_overlay = (
        notebook_api.build_merged_line_vertex_overlays(
            display_bgr,
            selected_repaired_binary,
            line_family_result,
            config,
        )
    )
    return LineDebugArtifacts(
        line_family_result=line_family_result,
        selected_repaired_binary=selected_repaired_binary,
        binary_family_overlay=binary_family_overlay,
        source_family_overlay=source_family_overlay,
        binary_logical_overlay=binary_logical_overlay,
        source_logical_overlay=source_logical_overlay,
        binary_merged_overlay=binary_merged_overlay,
        source_merged_overlay=source_merged_overlay,
        binary_vertex_overlay=binary_vertex_overlay,
        source_vertex_overlay=source_vertex_overlay,
    )


def _format_angle(angle_degrees: float | None) -> str:
    if angle_degrees is None:
        return "n/a"
    return f"{angle_degrees:.1f} deg"


def _resolve_display_vertices(
    line_family_result,
    merged_line,
    line_index: int,
    notebook_api: "ThresholdNotebookApi",
) -> tuple[tuple[int, int], tuple[int, int]]:
    if merged_line.family_name == "horizontal":
        aligned_vertices = line_family_result.horizontal_aligned_vertices
    else:
        aligned_vertices = line_family_result.vertical_aligned_vertices

    if line_index < len(aligned_vertices):
        return aligned_vertices[line_index]
    return notebook_api.resolve_merged_line_vertices(merged_line)


def _describe_overview(
    line_family_result,
    config,
    *,
    include_endpoint_summary: bool,
) -> list[str]:
    horizontal_pre_filter_count = len(
        line_family_result.horizontal_pre_filter_merged_lines
    )
    vertical_pre_filter_count = len(line_family_result.vertical_pre_filter_merged_lines)
    horizontal_kept_count = len(line_family_result.horizontal_merged_lines)
    vertical_kept_count = len(line_family_result.vertical_merged_lines)
    is_success = (
        horizontal_kept_count == config.expected_horizontal_line_count
        and vertical_kept_count == config.expected_vertical_line_count
    )

    lines = [
        "",
        "Line families from selected repair:",
        f"Raw Hough segments: {line_family_result.raw_segment_count}",
        f"Raw min line length px: {line_family_result.raw_min_line_length_px}",
        f"Raw max line gap px: {line_family_result.raw_max_line_gap_px}",
        (
            "Merge projection distance px: "
            f"{line_family_result.merge_projection_distance_px:.1f}"
        ),
        f"Merge endpoint gap px: {line_family_result.merge_endpoint_gap_px:.1f}",
        (
            "Bridge projection tolerance px: "
            f"{line_family_result.bridge_projection_tolerance_px:.1f}"
        ),
        f"Bridge max gap px: {line_family_result.bridge_max_gap_px:.1f}",
        (
            "Bridge endpoint tolerance px: "
            f"{line_family_result.bridge_endpoint_tolerance_px:.1f}"
        ),
        (
            "Cross-family touch tolerance px: "
            f"{line_family_result.cross_family_touch_tolerance_px:.1f}"
        ),
        f"Horizontal repaired bridges: {len(line_family_result.horizontal_bridges)}",
        f"Vertical repaired bridges: {len(line_family_result.vertical_bridges)}",
    ]
    if include_endpoint_summary:
        lines.append(
            "Mutual last-touch endpoint pairs: "
            f"{len(line_family_result.endpoint_connections)}"
        )
    lines.extend(
        [
            (
                "Min cross-family touch points to keep per iteration: "
                f"{config.min_cross_family_touches_to_keep}"
            ),
            (
                "Expected kept lines: "
                f"H={config.expected_horizontal_line_count}, "
                f"V={config.expected_vertical_line_count}"
            ),
            f"Horizontal family angle: {_format_angle(line_family_result.horizontal_angle_degrees)}",
            f"Vertical family angle: {_format_angle(line_family_result.vertical_angle_degrees)}",
            f"Horizontal raw segments: {len(line_family_result.horizontal_segments)}",
            f"Vertical raw segments: {len(line_family_result.vertical_segments)}",
            (
                "Horizontal logical groups before touch filter: "
                f"{horizontal_pre_filter_count}"
            ),
            (
                "Vertical logical groups before touch filter: "
                f"{vertical_pre_filter_count}"
            ),
            (
                "Horizontal kept logical groups (after refresh): "
                f"{horizontal_kept_count}"
            ),
            (
                "Vertical kept logical groups (after refresh): "
                f"{vertical_kept_count}"
            ),
            "",
        ]
    )
    if is_success:
        lines.append(
            "SUCCESS: detected exactly "
            f"{config.expected_horizontal_line_count} horizontal and "
            f"{config.expected_vertical_line_count} vertical logical lines."
        )
    else:
        lines.append(
            "NOT YET: expected exactly "
            f"{config.expected_horizontal_line_count} horizontal and "
            f"{config.expected_vertical_line_count} vertical logical lines."
        )
    return lines


def _describe_lines_without_vertices(
    line_family_result,
    family_name: str,
    family_label: str,
    touching_axis_label: str,
) -> list[str]:
    merged_lines = getattr(line_family_result, f"{family_name}_merged_lines")
    lines = ["", f"{family_label} kept logical groups:"]
    for line_index, merged_line in enumerate(merged_lines):
        lines.append(
            f"  {family_label[0]}{line_index}: span={merged_line.span_length:.1f}px, "
            f"covered={merged_line.covered_length:.1f}px, "
            f"segments={merged_line.segment_count}, "
            f"raw_len={merged_line.total_segment_length:.1f}px, "
            f"touch_lines={merged_line.touching_line_count}, "
            f"touch_points={merged_line.touching_point_count}, "
            f"{touching_axis_label}_ids={list(merged_line.touching_line_indices)}, "
            f"points={list(merged_line.touching_points)}"
        )
    return lines


def _describe_lines_with_vertices(
    line_family_result,
    family_name: str,
    heading_label: str,
    family_prefix: str,
    touching_axis_label: str,
    notebook_api: "ThresholdNotebookApi",
) -> list[str]:
    merged_lines = getattr(line_family_result, f"{family_name}_merged_lines")
    lines = ["", f"{heading_label} kept logical groups with vertices:"]
    for line_index, merged_line in enumerate(merged_lines):
        raw_first_vertex, raw_second_vertex = notebook_api.resolve_merged_line_vertices(
            merged_line
        )
        aligned_first_vertex, aligned_second_vertex = _resolve_display_vertices(
            line_family_result,
            merged_line,
            line_index,
            notebook_api,
        )
        first_name = notebook_api.line_vertex_name(merged_line.family_name, 0)
        second_name = notebook_api.line_vertex_name(merged_line.family_name, 1)
        lines.append(
            f"  {family_prefix}{line_index}: span={merged_line.span_length:.1f}px, "
            f"covered={merged_line.covered_length:.1f}px, "
            f"segments={merged_line.segment_count}, "
            f"raw_len={merged_line.total_segment_length:.1f}px, "
            f"touch_lines={merged_line.touching_line_count}, "
            f"touch_points={merged_line.touching_point_count}, "
            f"{first_name}_raw={raw_first_vertex}, "
            f"{first_name}_aligned={aligned_first_vertex}, "
            f"{second_name}_raw={raw_second_vertex}, "
            f"{second_name}_aligned={aligned_second_vertex}, "
            f"{touching_axis_label}_ids={list(merged_line.touching_line_indices)}, "
            f"points={list(merged_line.touching_points)}"
        )
    return lines


def describe_line_debug_artifacts(
    line_debug: LineDebugArtifacts,
    config,
    notebook_api: "ThresholdNotebookApi",
    *,
    include_vertices: bool = False,
) -> list[str]:
    line_family_result = line_debug.line_family_result
    lines = _describe_overview(
        line_family_result,
        config,
        include_endpoint_summary=include_vertices,
    )

    if include_vertices:
        lines.extend(
            _describe_lines_with_vertices(
                line_family_result,
                "horizontal",
                "Horizontal",
                "H",
                "vertical",
                notebook_api,
            )
        )
        lines.extend(
            _describe_lines_with_vertices(
                line_family_result,
                "vertical",
                "Vertical",
                "V",
                "horizontal",
                notebook_api,
            )
        )
        lines.extend(describe_endpoint_connections(line_family_result, notebook_api))
    else:
        lines.extend(
            _describe_lines_without_vertices(
                line_family_result,
                "horizontal",
                "Horizontal",
                "vertical",
            )
        )
        lines.extend(
            _describe_lines_without_vertices(
                line_family_result,
                "vertical",
                "Vertical",
                "horizontal",
            )
        )

    return lines


def describe_endpoint_connections(
    line_family_result,
    notebook_api: "ThresholdNotebookApi",
) -> list[str]:
    lines = ["", "Mutual last-touch line pairs:"]
    seen_pairs: set[str] = set()
    for endpoint_connection in line_family_result.endpoint_connections:
        pair_label = (
            f"H{endpoint_connection.horizontal_line_index} <-> "
            f"V{endpoint_connection.vertical_line_index}"
        )
        if pair_label in seen_pairs:
            continue
        seen_pairs.add(pair_label)
        lines.append(f"  {pair_label}")
    if not seen_pairs:
        lines.append("  -")

    lines.extend(("", "Mutual last-touch endpoint connections:"))
    for endpoint_connection in line_family_result.endpoint_connections:
        horizontal_vertex_name = notebook_api.line_vertex_name(
            "horizontal",
            endpoint_connection.horizontal_vertex_index,
        )
        vertical_vertex_name = notebook_api.line_vertex_name(
            "vertical",
            endpoint_connection.vertical_vertex_index,
        )
        lines.append(
            f"  H{endpoint_connection.horizontal_line_index}.{horizontal_vertex_name} "
            f"<-> V{endpoint_connection.vertical_line_index}.{vertical_vertex_name}: "
            f"H_raw={endpoint_connection.horizontal_vertex}, "
            f"V_raw={endpoint_connection.vertical_vertex}, "
            f"touch={endpoint_connection.touch_point}, "
            f"aligned={endpoint_connection.aligned_point}"
        )
    if not line_family_result.endpoint_connections:
        lines.append("  -")

    return lines


def build_line_debug_plot_items(
    line_debug: LineDebugArtifacts,
    selected_repair_name: str,
    *,
    include_vertices: bool,
) -> list[tuple[str, np.ndarray, bool]]:
    plot_items = [
        (
            f"selected_repair: {selected_repair_name}",
            line_debug.selected_repaired_binary,
            False,
        ),
        ("raw line families on repaired binary", line_debug.binary_family_overlay, True),
        (
            "logical lines + bridge repair before touch filter on repaired binary",
            line_debug.binary_logical_overlay,
            True,
        ),
        (
            "kept logical groups after refresh on repaired binary",
            line_debug.binary_merged_overlay,
            True,
        ),
    ]
    if include_vertices:
        plot_items.append(
            (
                "logical lines + aligned vertices on repaired binary",
                line_debug.binary_vertex_overlay,
                True,
            )
        )
    plot_items.extend(
        [
            ("raw line families on source", line_debug.source_family_overlay, True),
            (
                "logical lines + bridge repair before touch filter on source",
                line_debug.source_logical_overlay,
                True,
            ),
            (
                "kept logical groups after refresh on source",
                line_debug.source_merged_overlay,
                True,
            ),
        ]
    )
    if include_vertices:
        plot_items.append(
            (
                "logical lines + aligned vertices on source",
                line_debug.source_vertex_overlay,
                True,
            )
        )
    return plot_items


def run_frame_debug_analysis(
    display_bgr: np.ndarray,
    selected_repaired_binary: np.ndarray,
    line_debug: LineDebugArtifacts,
    config,
    notebook_api: "ThresholdNotebookApi",
) -> FrameDebugArtifacts:
    frame_detection_result = notebook_api.find_line_frames(
        line_debug.line_family_result,
        config,
    )
    selected_frames = frame_detection_result.selected_frames
    binary_frame_overlay, source_frame_overlay = notebook_api.build_line_frame_overlays(
        display_bgr,
        selected_repaired_binary,
        selected_frames,
        config,
    )
    return FrameDebugArtifacts(
        frame_detection_result=frame_detection_result,
        selected_frames=selected_frames,
        binary_frame_overlay=binary_frame_overlay,
        source_frame_overlay=source_frame_overlay,
    )


def describe_frame_debug_artifacts(frame_debug: FrameDebugArtifacts) -> list[str]:
    lines = [
        "",
        (
            "Detected frame candidates: "
            f"all={len(frame_debug.frame_detection_result.all_frames)}, "
            f"selected={len(frame_debug.selected_frames)}"
        ),
        "",
        "Selected frames built from mutual endpoint corners:",
    ]
    for frame_index, frame in enumerate(frame_debug.selected_frames):
        lines.append(
            f"  F{frame_index}: H{frame.top_line_index}-H{frame.bottom_line_index} x "
            f"V{frame.left_line_index}-V{frame.right_line_index}, "
            f"area={frame.area_px:.1f}px, perimeter={frame.perimeter_px:.1f}px, "
            f"H_count={frame.horizontal_line_count}, V_count={frame.vertical_line_count}, "
            f"inner_H={frame.inner_horizontal_line_count}, "
            f"inner_V={frame.inner_vertical_line_count}, "
            f"priority={frame.priority_score:.1f}"
        )
        lines.append(
            "    TL: "
            f"H{frame.top_line_index} <-> V{frame.left_line_index} = "
            f"{frame.top_left_connection.aligned_point}"
        )
        lines.append(
            "    TR: "
            f"H{frame.top_line_index} <-> V{frame.right_line_index} = "
            f"{frame.top_right_connection.aligned_point}"
        )
        lines.append(
            "    BR: "
            f"H{frame.bottom_line_index} <-> V{frame.right_line_index} = "
            f"{frame.bottom_right_connection.aligned_point}"
        )
        lines.append(
            "    BL: "
            f"H{frame.bottom_line_index} <-> V{frame.left_line_index} = "
            f"{frame.bottom_left_connection.aligned_point}"
        )
    if not frame_debug.selected_frames:
        lines.append("  -")
    return lines


def build_frame_debug_plot_items(
    frame_debug: FrameDebugArtifacts,
    line_debug: LineDebugArtifacts,
) -> list[tuple[str, np.ndarray, bool]]:
    return [
        (
            "kept logical groups after refresh on repaired binary",
            line_debug.binary_merged_overlay,
            True,
        ),
        (
            "selected frames from mutual endpoint corners on repaired binary",
            frame_debug.binary_frame_overlay,
            True,
        ),
        (
            "kept logical groups after refresh on source",
            line_debug.source_merged_overlay,
            True,
        ),
        (
            "selected frames from mutual endpoint corners on source",
            frame_debug.source_frame_overlay,
            True,
        ),
    ]


def run_warp_debug_analysis(
    display_bgr: np.ndarray,
    frame_debug: FrameDebugArtifacts,
    config,
) -> WarpDebugArtifacts:
    if not frame_debug.selected_frames:
        return WarpDebugArtifacts(
            selected_frame=None,
            aligned_corners=None,
            aligned_corner_overlay=None,
            aligned_warp=None,
        )

    selected_frame = frame_debug.selected_frames[0]
    aligned_corners = aligned_frame_corners(selected_frame)
    aligned_corner_overlay = build_corner_overlay(
        display_bgr,
        aligned_corners,
        color_bgr=(0, 200, 0),
        label_prefix="A",
        thickness=max(config.line_overlay_thickness, 2),
    )
    aligned_warp = warp_image_from_corners(
        display_bgr,
        aligned_corners,
        config.warp_output_size,
        config.warp_output_padding_pixels,
    )

    return WarpDebugArtifacts(
        selected_frame=selected_frame,
        aligned_corners=aligned_corners,
        aligned_corner_overlay=aligned_corner_overlay,
        aligned_warp=aligned_warp,
    )


def _format_corner(
    point: tuple[float, float],
) -> str:
    return f"({point[0]:.1f}, {point[1]:.1f})"


def _describe_corner_set(
    label: str,
    corners: tuple[
        tuple[float, float],
        tuple[float, float],
        tuple[float, float],
        tuple[float, float],
    ],
) -> list[str]:
    corner_labels = ("TL", "TR", "BR", "BL")
    lines = [f"{label} corners:"]
    for corner_label, point in zip(corner_labels, corners):
        lines.append(f"  {corner_label}: {_format_corner(point)}")
    return lines


def describe_warp_debug_artifacts(
    warp_debug: WarpDebugArtifacts,
    config,
) -> list[str]:
    lines = [
        "",
        "Warp from the highest-priority selected frame:",
    ]
    if warp_debug.selected_frame is None or warp_debug.aligned_corners is None:
        lines.append("No selected frame, so warp was skipped.")
        return lines

    lines.append(
        "Warp output: "
        f"{config.warp_output_size}x{config.warp_output_size}px, "
        f"padding={config.warp_output_padding_pixels}px"
    )
    lines.extend(("", *_describe_corner_set("Frame corners used for warp", warp_debug.aligned_corners)))
    return lines


def build_warp_debug_plot_items(
    frame_debug: FrameDebugArtifacts,
    warp_debug: WarpDebugArtifacts,
) -> list[tuple[str, np.ndarray, bool]]:
    plot_items = [
        (
            "selected frame from mutual endpoint corners on source",
            frame_debug.source_frame_overlay,
            True,
        )
    ]
    if warp_debug.aligned_corner_overlay is not None:
        plot_items.append(
            (
                "frame corners used for warp on source",
                warp_debug.aligned_corner_overlay,
                True,
            )
        )
    if warp_debug.aligned_warp is not None:
        plot_items.append(
            (
                "warp to square from frame corners",
                warp_debug.aligned_warp,
                True,
            )
        )
    return plot_items


__all__ = [
    "FrameDebugArtifacts",
    "LineDebugArtifacts",
    "WarpDebugArtifacts",
    "build_frame_debug_plot_items",
    "build_line_debug_plot_items",
    "build_warp_debug_plot_items",
    "describe_endpoint_connections",
    "describe_frame_debug_artifacts",
    "describe_line_debug_artifacts",
    "describe_warp_debug_artifacts",
    "run_frame_debug_analysis",
    "run_line_debug_analysis",
    "run_warp_debug_analysis",
]
