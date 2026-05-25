import { postSudokuOverlayCell } from "../../../api/sudokuOverlayCells";
import { composeImageGrid } from "../../../shared/images/composeImageGrid";
import { toImageDataUrl } from "../../../shared/images/toImageDataUrl";
import type { CellsGridApiResponse } from "../../../types/api";
import { GRID_SIZE } from "../../uc05a/domain/gridCoordinates";
import { applyRenderedOverlayCell } from "../domain/applyRenderedOverlayCell";
import type { OverlayRenderTarget } from "../domain/overlayRenderTarget";

export class OverlayCellsGridShapeError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "OverlayCellsGridShapeError";
  }
}

export class OverlayCellRenderTaskError extends Error {
  readonly target: OverlayRenderTarget;
  readonly cause: unknown;

  constructor(message: string, target: OverlayRenderTarget, cause: unknown) {
    super(message);
    this.name = "OverlayCellRenderTaskError";
    this.target = target;
    this.cause = cause;
  }
}

type RenderSolvedOverlayOptions = {
  apiBaseUrl: string;
  cellsGrid: CellsGridApiResponse;
  initialRenderedCells: string[][];
  targets: OverlayRenderTarget[];
  signal: AbortSignal;
  onCellRendered: (update: {
    renderedCells: string[][];
    previewUrl: string;
    completedCount: number;
  }) => void;
};

type RenderSolvedOverlayResult = {
  renderedCells: string[][];
  previewUrl: string;
};

function assertOverlayCellsGridShape(cellsGrid: CellsGridApiResponse): void {
  if (cellsGrid.cells.length !== GRID_SIZE) {
    throw new OverlayCellsGridShapeError(
      "CellsGridApiResponse dla overlay musi zawierac dokladnie 9 wierszy.",
    );
  }

  for (const row of cellsGrid.cells) {
    if (row.length !== GRID_SIZE) {
      throw new OverlayCellsGridShapeError(
        "CellsGridApiResponse dla overlay musi zawierac dokladnie 9 komorek w kazdym wierszu.",
      );
    }
  }
}

export async function renderSolvedOverlay({
  apiBaseUrl,
  cellsGrid,
  initialRenderedCells,
  targets,
  signal,
  onCellRendered,
}: RenderSolvedOverlayOptions): Promise<RenderSolvedOverlayResult> {
  assertOverlayCellsGridShape(cellsGrid);

  let renderedCells = initialRenderedCells;

  if (targets.length === 0) {
    return {
      renderedCells,
      previewUrl: await composeImageGrid(renderedCells, signal),
    };
  }

  for (let index = 0; index < targets.length; index += 1) {
    const target = targets[index];

    try {
      const response = await postSudokuOverlayCell(
        apiBaseUrl,
        {
          cellImage: cellsGrid.cells[target.rowIndex][target.columnIndex],
          digit: target.digit,
          rowIndex: target.rowIndex,
          columnIndex: target.columnIndex,
        },
        signal,
      );

      renderedCells = applyRenderedOverlayCell(
        renderedCells,
        target,
        toImageDataUrl(response),
      );

      const previewUrl = await composeImageGrid(renderedCells, signal);
      onCellRendered({
        renderedCells,
        previewUrl,
        completedCount: index + 1,
      });
    } catch (error) {
      if (signal.aborted) {
        throw error;
      }

      throw new OverlayCellRenderTaskError(
        `Nie udalo sie wyrenderowac komorki ${target.rowIndex + 1}-${target.columnIndex + 1}.`,
        target,
        error,
      );
    }
  }

  return {
    renderedCells,
    previewUrl: await composeImageGrid(renderedCells, signal),
  };
}
