from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

from sudoku_board_threshold_notebook_report_models import LineDebugArtifacts

if TYPE_CHECKING:
    from sudoku_board_threshold_notebook_bootstrap import ThresholdNotebookApi


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
            (
                "Horizontal family angle: "
                f"{_format_angle(line_family_result.horizontal_angle_degrees)}"
            ),
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


def _bridge_diagnostic_sort_key(bridge_diagnostic) -> tuple[float, float, int, int]:
    projection_ratio = float("inf")
    if bridge_diagnostic.projection_tolerance_px > 1e-6:
        projection_ratio = (
            bridge_diagnostic.projection_distance_px
            / bridge_diagnostic.projection_tolerance_px
        )
    gap_ratio = float("inf")
    if bridge_diagnostic.gap_px is not None and bridge_diagnostic.max_gap_px > 1e-6:
        gap_ratio = bridge_diagnostic.gap_px / bridge_diagnostic.max_gap_px
    return (
        gap_ratio,
        projection_ratio,
        bridge_diagnostic.first_line_index,
        bridge_diagnostic.second_line_index,
    )


def _describe_bridge_diagnostics(
    line_family_result,
    family_name: str,
    family_label: str,
    family_prefix: str,
    *,
    max_entries: int = 12,
) -> list[str]:
    bridge_diagnostics = getattr(
        line_family_result,
        f"{family_name}_bridge_diagnostics",
        [],
    )
    if not bridge_diagnostics:
        return []

    rejected_diagnostics = [
        bridge_diagnostic
        for bridge_diagnostic in bridge_diagnostics
        if not bridge_diagnostic.accepted
    ]
    accepted_count = len(bridge_diagnostics) - len(rejected_diagnostics)
    rejected_reason_counts = Counter(
        bridge_diagnostic.reject_reason for bridge_diagnostic in rejected_diagnostics
    )

    lines = [
        "",
        f"{family_label} same-family bridge diagnostics after refresh:",
        (
            f"  accepted={accepted_count}, rejected={len(rejected_diagnostics)}, "
            f"pairs={len(bridge_diagnostics)}"
        ),
    ]
    if rejected_reason_counts:
        lines.append(
            "  rejected_by_reason="
            + ", ".join(
                f"{reason}:{count}"
                for reason, count in sorted(rejected_reason_counts.items())
            )
        )

    if not rejected_diagnostics:
        lines.append("  all pairs already pass current bridge checks")
        return lines

    lines.append("  closest rejected pairs:")
    for bridge_diagnostic in sorted(
        rejected_diagnostics,
        key=_bridge_diagnostic_sort_key,
    )[:max_entries]:
        gap_label = (
            "n/a"
            if bridge_diagnostic.gap_px is None
            else f"{bridge_diagnostic.gap_px:.1f}/{bridge_diagnostic.max_gap_px:.1f}"
        )
        candidate_label = (
            "-"
            if bridge_diagnostic.selected_candidate_rank is None
            else (
                f"{bridge_diagnostic.selected_candidate_rank}/"
                f"{bridge_diagnostic.candidate_count}"
            )
        )
        lines.append(
            f"  {family_prefix}{bridge_diagnostic.first_line_index} <-> "
            f"{family_prefix}{bridge_diagnostic.second_line_index}: "
            f"reason={bridge_diagnostic.reject_reason}, "
            f"proj={bridge_diagnostic.projection_distance_px:.1f}/"
            f"{bridge_diagnostic.projection_tolerance_px:.1f}, "
            f"gap={gap_label}, candidates={candidate_label}"
        )
        if bridge_diagnostic.reject_reason == "discontinuous_projection":
            coverage_start = bridge_diagnostic.projection_coverage_start_px
            coverage_end = bridge_diagnostic.projection_coverage_end_px
            coverage_label = "n/a"
            if coverage_start is not None and coverage_end is not None:
                coverage_label = f"{coverage_start:.1f}->{coverage_end:.1f}"
            max_hole_label = (
                "n/a"
                if bridge_diagnostic.projection_max_hole_px is None
                else str(bridge_diagnostic.projection_max_hole_px)
            )
            lines.append(
                f"    projection_coverage={coverage_label}, "
                f"max_hole_px={max_hole_label}"
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
    lines.extend(
        _describe_bridge_diagnostics(
            line_family_result,
            "horizontal",
            "Horizontal",
            "H",
        )
    )
    lines.extend(
        _describe_bridge_diagnostics(
            line_family_result,
            "vertical",
            "Vertical",
            "V",
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


__all__ = [
    "describe_endpoint_connections",
    "describe_line_debug_artifacts",
]
