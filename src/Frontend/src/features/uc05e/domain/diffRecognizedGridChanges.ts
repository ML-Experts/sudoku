import type { GridCoordinates } from "../../uc05a/domain/gridCoordinates";
import type { RecognizedGrid } from "../../uc05a/domain/recognizedGrid";

export type ChangedSolveCell = GridCoordinates & {
  previousDigit: number | null;
  nextDigit: number | null;
  changeType: "placed" | "removed" | "updated";
};

export function diffRecognizedGridChanges(
  previousGrid: RecognizedGrid | null,
  nextGrid: RecognizedGrid,
): ChangedSolveCell[] {
  if (!previousGrid) {
    return [];
  }

  const changedCells: ChangedSolveCell[] = [];

  for (const row of nextGrid) {
    for (const cell of row) {
      const previousCell = previousGrid[cell.rowIndex]?.[cell.columnIndex];

      if (!previousCell || previousCell.digit === cell.digit) {
        continue;
      }

      let changeType: ChangedSolveCell["changeType"] = "updated";
      if (previousCell.digit === null && cell.digit !== null) {
        changeType = "placed";
      } else if (previousCell.digit !== null && cell.digit === null) {
        changeType = "removed";
      }

      changedCells.push({
        rowIndex: cell.rowIndex,
        columnIndex: cell.columnIndex,
        previousDigit: previousCell.digit,
        nextDigit: cell.digit,
        changeType,
      });
    }
  }

  return changedCells;
}
