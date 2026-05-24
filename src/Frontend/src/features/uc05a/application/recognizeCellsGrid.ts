import type {
  CellsGridApiResponse,
  DigitInferenceApiResponse,
  SudokuCellInferenceParametersApiEntry,
} from "../../../types/api";
import { putSudokuCellInference } from "../../../api/sudokuCellsInference";
import type { GridCoordinates } from "../domain/gridCoordinates";
import { GRID_SIZE } from "../domain/gridCoordinates";
import { runPromisePool } from "../infrastructure/runPromisePool";

export class CellsGridShapeError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "CellsGridShapeError";
  }
}

export class CellRecognitionTaskError extends Error {
  readonly coordinates: GridCoordinates;
  readonly cause: unknown;

  constructor(message: string, coordinates: GridCoordinates, cause: unknown) {
    super(message);
    this.name = "CellRecognitionTaskError";
    this.coordinates = coordinates;
    this.cause = cause;
  }
}

type RecognizeCellsGridOptions = {
  apiBaseUrl: string;
  cellsGrid: CellsGridApiResponse;
  inferenceParameters?: SudokuCellInferenceParametersApiEntry | null;
  signal: AbortSignal;
  concurrency: number;
  onCellRecognized: (
    coordinates: GridCoordinates,
    result: DigitInferenceApiResponse,
  ) => void;
};

export function assertCellsGridShape(cellsGrid: CellsGridApiResponse): void {
  if (cellsGrid.cells.length !== GRID_SIZE) {
    throw new CellsGridShapeError("CellsGridApiResponse musi zawierac dokladnie 9 wierszy.");
  }

  for (const row of cellsGrid.cells) {
    if (row.length !== GRID_SIZE) {
      throw new CellsGridShapeError(
        "CellsGridApiResponse musi zawierac dokladnie 9 komorek w kazdym wierszu.",
      );
    }
  }
}

export async function recognizeCellsGrid({
  apiBaseUrl,
  cellsGrid,
  inferenceParameters,
  signal,
  concurrency,
  onCellRecognized,
}: RecognizeCellsGridOptions): Promise<void> {
  assertCellsGridShape(cellsGrid);

  const tasks = cellsGrid.cells.flatMap((row, rowIndex) =>
    row.map((cell, columnIndex) => {
      const coordinates = { rowIndex, columnIndex };

      return async () => {
        try {
          const response = await putSudokuCellInference(
            apiBaseUrl,
            cell,
            inferenceParameters,
            signal,
          );
          onCellRecognized(coordinates, response);
          return response;
        } catch (error) {
          throw new CellRecognitionTaskError(
            `Nie udalo sie rozpoznac komorki ${rowIndex + 1}-${columnIndex + 1}.`,
            coordinates,
            error,
          );
        }
      };
    }),
  );

  await runPromisePool({
    tasks,
    concurrency,
  });
}
