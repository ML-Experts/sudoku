import { GRID_SIZE } from "../../uc05a/domain/gridCoordinates";
import type { RecognizedGrid } from "../../uc05a/domain/recognizedGrid";

export class GridNotReadyForSolveError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "GridNotReadyForSolveError";
  }
}

export function isRecognizedGridReadyForSolve(
  recognizedGrid: RecognizedGrid | null,
): recognizedGrid is RecognizedGrid {
  if (!recognizedGrid || recognizedGrid.length !== GRID_SIZE) {
    return false;
  }

  return recognizedGrid.every(
    (row) =>
      row.length === GRID_SIZE &&
      row.every((cell) => cell.source === "recognized"),
  );
}

export function prepareRecognizedGridForSolve(
  recognizedGrid: RecognizedGrid,
): RecognizedGrid {
  if (!isRecognizedGridReadyForSolve(recognizedGrid)) {
    throw new GridNotReadyForSolveError(
      "RecognizedGrid nie jest gotowy do uruchomienia solve.",
    );
  }

  return recognizedGrid.map((row) =>
    row.map((cell) => ({
      ...cell,
      isLocked: cell.digit !== null,
      isEditable: cell.digit === null,
    })),
  );
}
