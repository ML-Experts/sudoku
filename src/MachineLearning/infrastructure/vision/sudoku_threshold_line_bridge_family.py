from __future__ import annotations

from infrastructure.vision.sudoku_threshold_line_bridge_inspection import (
    inspect_line_bridge_candidate,
    line_bridge_candidate,
)
from infrastructure.vision.sudoku_threshold_line_merge import (
    build_merged_line,
    connected_components,
)
from infrastructure.vision.sudoku_threshold_models import (
    LineBridge,
    LineBridgeDiagnostic,
    MergedLine,
    SudokuThresholdConfig,
)


def resolve_bridge_thresholds(
    config: SudokuThresholdConfig,
    minimum_dimension: int,
) -> tuple[float, float, float]:
    return (
        max(4.0, minimum_dimension * config.line_bridge_projection_distance_ratio),
        max(8.0, minimum_dimension * config.line_bridge_max_gap_ratio),
        max(6.0, minimum_dimension * config.line_bridge_endpoint_tolerance_ratio),
    )


def inspect_line_family_bridge_candidates(
    binary_image,
    merged_lines: list[MergedLine],
    family_angle_degrees: float | None,
    family_name: str,
    config: SudokuThresholdConfig,
    minimum_dimension: int,
) -> list[LineBridgeDiagnostic]:
    (
        bridge_projection_tolerance_px,
        bridge_max_gap_px,
        bridge_endpoint_tolerance_px,
    ) = resolve_bridge_thresholds(config, minimum_dimension)
    if family_angle_degrees is None or len(merged_lines) <= 1:
        return []

    bridge_diagnostics: list[LineBridgeDiagnostic] = []
    for first_index in range(len(merged_lines)):
        for second_index in range(first_index + 1, len(merged_lines)):
            _, line_bridge_diagnostic = inspect_line_bridge_candidate(
                binary_image=binary_image,
                first_line=merged_lines[first_index],
                second_line=merged_lines[second_index],
                family_angle_degrees=family_angle_degrees,
                family_name=family_name,
                first_line_index=first_index,
                second_line_index=second_index,
                projection_tolerance_px=bridge_projection_tolerance_px,
                max_gap_px=bridge_max_gap_px,
                endpoint_tolerance_px=bridge_endpoint_tolerance_px,
            )
            bridge_diagnostics.append(line_bridge_diagnostic)

    return bridge_diagnostics


def merge_lines_with_bridges(
    merged_lines: list[MergedLine],
    bridges: list[LineBridge],
    family_name: str,
    family_angle_degrees: float,
) -> list[MergedLine]:
    adjacency: list[list[int]] = [[] for _ in merged_lines]
    for line_bridge in bridges:
        adjacency[line_bridge.first_line_index].append(line_bridge.second_line_index)
        adjacency[line_bridge.second_line_index].append(line_bridge.first_line_index)

    bridged_lines = []
    for component in connected_components(adjacency):
        component_set = set(component)
        merged_segments = []
        for line_index in component:
            merged_segments.extend(merged_lines[line_index].segments)
        for line_bridge in bridges:
            if (
                line_bridge.first_line_index in component_set
                and line_bridge.second_line_index in component_set
            ):
                merged_segments.append(line_bridge.segment)
        bridged_lines.append(
            build_merged_line(
                family_name,
                family_angle_degrees,
                merged_segments,
            )
        )

    return sorted(bridged_lines, key=lambda merged_line: merged_line.projection)


def bridge_line_family_gaps(
    binary_image,
    merged_lines: list[MergedLine],
    family_angle_degrees: float | None,
    family_name: str,
    config: SudokuThresholdConfig,
    minimum_dimension: int,
) -> tuple[list[MergedLine], list[LineBridge], float, float, float]:
    (
        bridge_projection_tolerance_px,
        bridge_max_gap_px,
        bridge_endpoint_tolerance_px,
    ) = resolve_bridge_thresholds(config, minimum_dimension)
    if family_angle_degrees is None or len(merged_lines) <= 1:
        return (
            merged_lines,
            [],
            bridge_projection_tolerance_px,
            bridge_max_gap_px,
            bridge_endpoint_tolerance_px,
        )

    current_lines = list(merged_lines)
    all_bridges: list[LineBridge] = []
    while len(current_lines) > 1:
        iteration_bridges: list[LineBridge] = []
        for first_index in range(len(current_lines)):
            for second_index in range(first_index + 1, len(current_lines)):
                line_bridge = line_bridge_candidate(
                    binary_image=binary_image,
                    first_line=current_lines[first_index],
                    second_line=current_lines[second_index],
                    family_angle_degrees=family_angle_degrees,
                    family_name=family_name,
                    first_line_index=first_index,
                    second_line_index=second_index,
                    projection_tolerance_px=bridge_projection_tolerance_px,
                    max_gap_px=bridge_max_gap_px,
                    endpoint_tolerance_px=bridge_endpoint_tolerance_px,
                )
                if line_bridge is not None:
                    iteration_bridges.append(line_bridge)

        if not iteration_bridges:
            break

        current_lines = merge_lines_with_bridges(
            current_lines,
            iteration_bridges,
            family_name,
            family_angle_degrees,
        )
        all_bridges.extend(iteration_bridges)

    return (
        current_lines,
        all_bridges,
        bridge_projection_tolerance_px,
        bridge_max_gap_px,
        bridge_endpoint_tolerance_px,
    )
