import { GRID_SIZE } from "../../uc05a/domain/gridCoordinates";
import type { RecognizedGrid } from "../../uc05a/domain/recognizedGrid";
import { isRecognizedGrid } from "../../uc05a/domain/recognizedGrid";

export class OverlayGridConsistencyError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "OverlayGridConsistencyError";
  }
}

function assertRecognizedGridShape(
  grid: RecognizedGrid,
  gridLabel: "inputGrid" | "solvedGrid",
): void {
  if (!isRecognizedGrid(grid)) {
    throw new OverlayGridConsistencyError(
      `${gridLabel} musi miec poprawny ksztalt recognizedGrid 9x9.`,
    );
  }

  if (grid.length !== GRID_SIZE) {
    throw new OverlayGridConsistencyError(
      `${gridLabel} musi zawierac dokladnie ${GRID_SIZE} wierszy.`,
    );
  }
}

export function assertOverlayGridConsistency(
  inputGrid: RecognizedGrid,
  solvedGrid: RecognizedGrid,
): void {
  assertRecognizedGridShape(inputGrid, "inputGrid");
  assertRecognizedGridShape(solvedGrid, "solvedGrid");

  for (let rowIndex = 0; rowIndex < GRID_SIZE; rowIndex += 1) {
    for (let columnIndex = 0; columnIndex < GRID_SIZE; columnIndex += 1) {
      const inputDigit = inputGrid[rowIndex][columnIndex].digit;
      const solvedDigit = solvedGrid[rowIndex][columnIndex].digit;

      if (inputDigit !== null && solvedDigit !== inputDigit) {
        throw new OverlayGridConsistencyError(
          `Solve zmienil cyfre wejsciowa w polu ${rowIndex + 1}-${columnIndex + 1}.`,
        );
      }
    }
  }
}
