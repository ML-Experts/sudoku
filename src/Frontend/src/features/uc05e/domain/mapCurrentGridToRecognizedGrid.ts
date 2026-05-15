import { GRID_SIZE } from "../../uc05a/domain/gridCoordinates";
import type {
  RecognizedCell,
  RecognizedDigit,
  RecognizedGrid,
} from "../../uc05a/domain/recognizedGrid";

export function mapCurrentGridToRecognizedGrid(
  inputGrid: RecognizedGrid,
  currentGrid: (number | null)[][],
): RecognizedGrid {
  return Array.from({ length: GRID_SIZE }, (_, rowIndex) =>
    Array.from({ length: GRID_SIZE }, (_, columnIndex) => {
      const inputCell = inputGrid[rowIndex][columnIndex];
      const currentDigit = currentGrid[rowIndex][columnIndex] as RecognizedDigit | null;
      const isLocked = inputCell.digit !== null;

      const cell: RecognizedCell = {
        rowIndex,
        columnIndex,
        digit: currentDigit,
        source: "recognized",
        isLocked,
        isEditable: !isLocked,
      };

      return cell;
    }),
  );
}
