import { GRID_SIZE } from "../../uc05a/domain/gridCoordinates";
import type { RecognizedGrid } from "../../uc05a/domain/recognizedGrid";

export class InputCellsInvariantError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "InputCellsInvariantError";
  }
}

export function assertInputCellsInvariant(
  inputGrid: RecognizedGrid,
  currentGrid: (number | null)[][],
): void {
  for (let rowIndex = 0; rowIndex < GRID_SIZE; rowIndex += 1) {
    for (let columnIndex = 0; columnIndex < GRID_SIZE; columnIndex += 1) {
      const inputCell = inputGrid[rowIndex]?.[columnIndex];
      const currentDigit = currentGrid[rowIndex]?.[columnIndex];

      if (!inputCell) {
        throw new InputCellsInvariantError(
          "Brakuje komorki inputGrid podczas walidacji solve progress.",
        );
      }

      if (inputCell.digit !== null && inputCell.digit !== currentDigit) {
        throw new InputCellsInvariantError(
          `Event solve progress naruszyl pole wejsciowe ${rowIndex + 1}-${columnIndex + 1}.`,
        );
      }
    }
  }
}
