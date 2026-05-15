import type { SolveSudokuApiEntry } from "../../../types/api";
import type { RecognizedGrid } from "../../uc05a/domain/recognizedGrid";

export function toSolveSudokuApiEntry(
  recognizedGrid: RecognizedGrid,
): SolveSudokuApiEntry {
  return {
    grid: recognizedGrid.map((row) => row.map((cell) => cell.digit)),
  };
}
