from __future__ import annotations

import importlib

import numpy as np

import sudoku_board_threshold_cells as _cells
import sudoku_board_threshold_notebook_report_models as _report_models

_cells = importlib.reload(_cells)
_report_models = importlib.reload(_report_models)

CellDebugArtifacts = _report_models.CellDebugArtifacts
WarpDebugArtifacts = _report_models.WarpDebugArtifacts


def _count_non_empty_cells(cells_grid) -> int:
    if cells_grid is None:
        return 0
    return sum(
        1
        for row in cells_grid
        for cell_image in row
        if cell_image is not None and int(np.max(cell_image)) > 0
    )


def run_cells_debug_analysis(
    warp_debug: WarpDebugArtifacts,
    config,
) -> CellDebugArtifacts:
    if warp_debug.aligned_warp is None:
        return CellDebugArtifacts(
            selected_frame=warp_debug.selected_frame,
            board_gray=None,
            board_contrast=None,
            board_binary=None,
            raw_cells=None,
            cleaned_cells=None,
            raw_contact_sheet=None,
            cleaned_contact_sheet=None,
        )

    cell_artifacts = _cells.extract_cells_from_warped_board(
        warp_debug.aligned_warp,
        grid_size=config.cell_grid_size,
        inner_margin_ratio=config.cell_inner_margin_ratio,
        output_size=config.cell_output_size,
        contrast_clip_limit=config.cell_contrast_clip_limit,
        contrast_tile_grid_size=config.cell_contrast_tile_grid_size,
        adaptive_block_size=config.cell_threshold_block_size,
        adaptive_c=config.cell_threshold_c,
        border_clearance_px=config.cell_border_clearance_px,
        min_component_area_ratio=config.cell_min_component_area_ratio,
        contact_sheet_gap_px=config.cell_contact_sheet_gap_px,
    )
    return CellDebugArtifacts(
        selected_frame=warp_debug.selected_frame,
        board_gray=cell_artifacts.board_gray,
        board_contrast=cell_artifacts.board_contrast,
        board_binary=cell_artifacts.board_binary,
        raw_cells=cell_artifacts.raw_cells,
        cleaned_cells=cell_artifacts.cleaned_cells,
        raw_contact_sheet=cell_artifacts.raw_contact_sheet,
        cleaned_contact_sheet=cell_artifacts.cleaned_contact_sheet,
    )


def describe_cells_debug_artifacts(
    cell_debug: CellDebugArtifacts,
    config,
) -> list[str]:
    lines = [
        "",
        "Podzial warpa na siatke komorek i czyszczenie cyfr:",
    ]
    if cell_debug.board_binary is None:
        lines.append("No aligned warp, so cell extraction was skipped.")
        return lines

    raw_non_empty = _count_non_empty_cells(cell_debug.raw_cells)
    cleaned_non_empty = _count_non_empty_cells(cell_debug.cleaned_cells)
    lines.extend(
        [
            (
                f"Grid: {config.cell_grid_size}x{config.cell_grid_size}, "
                f"cell_size={config.cell_output_size}px"
            ),
            (
                "Split cells (UC-04 style): "
                f"inner_margin={config.cell_inner_margin_ratio:.3f}"
            ),
            (
                "Board preview contrast: "
                f"clahe_clip={config.cell_contrast_clip_limit}, "
                f"tile_grid={config.cell_contrast_tile_grid_size}"
            ),
            (
                "ML foreground mask: "
                f"inner_margin={config.cell_inner_margin_ratio:.3f}, "
                f"adaptive_block={config.cell_threshold_block_size}, "
                f"adaptive_c={config.cell_threshold_c}"
            ),
            (
                "Cell cleanup: "
                f"border_clearance={config.cell_border_clearance_px}px, "
                f"min_component_area_ratio={config.cell_min_component_area_ratio:.4f}"
            ),
            (
                f"Non-empty cells: raw={raw_non_empty}, "
                f"cleaned={cleaned_non_empty}"
            ),
        ]
    )
    return lines


def build_cells_debug_plot_items(
    warp_debug: WarpDebugArtifacts,
    cell_debug: CellDebugArtifacts,
) -> list[tuple[str, object, bool]]:
    plot_items: list[tuple[str, object, bool]] = []
    if cell_debug.board_gray is not None:
        plot_items.append(
            (
                "warp grayscale before cell preprocessing",
                cell_debug.board_gray,
                False,
            )
        )
    elif warp_debug.aligned_warp is not None:
        plot_items.append(
            (
                "warp to square from frame corners",
                warp_debug.aligned_warp,
                True,
            )
        )
    if cell_debug.board_contrast is not None:
        plot_items.append(
            (
                "warp grayscale with contrast boost",
                cell_debug.board_contrast,
                False,
            )
        )
    if cell_debug.board_binary is not None:
        plot_items.append(
            (
                "board binary inverted before split into 9x9",
                cell_debug.board_binary,
                False,
            )
        )
    if cell_debug.raw_contact_sheet is not None:
        plot_items.append(
            (
                "uc-04 split 9x9 grayscale cells",
                cell_debug.raw_contact_sheet,
                False,
            )
        )
    if cell_debug.cleaned_contact_sheet is not None:
        plot_items.append(
            (
                "ml foreground-mask cells (binary inv + centered)",
                cell_debug.cleaned_contact_sheet,
                False,
            )
        )
    return plot_items


__all__ = [
    "build_cells_debug_plot_items",
    "describe_cells_debug_artifacts",
    "run_cells_debug_analysis",
]
