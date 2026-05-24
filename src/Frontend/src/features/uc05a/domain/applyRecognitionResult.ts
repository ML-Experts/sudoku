import type { GridCoordinates } from "./gridCoordinates";
import { isGridCoordinateInBounds } from "./gridCoordinates";
import type {
  RecognizedCellSource,
  RecognizedDigit,
  RecognizedGrid,
} from "./recognizedGrid";
import { isRecognizedDigit } from "./recognizedGrid";

type RecognitionCellUpdate = {
  digit: RecognizedDigit | null;
  source?: Extract<RecognizedCellSource, "recognized" | "error">;
};

export function applyRecognitionResult(
  grid: RecognizedGrid,
  coordinates: GridCoordinates,
  update: RecognitionCellUpdate,
): RecognizedGrid {
  if (!isGridCoordinateInBounds(coordinates)) {
    throw new Error("Niepoprawne wspolrzedne komorki recognizedGrid.");
  }

  if (update.digit !== null && !isRecognizedDigit(update.digit)) {
    throw new Error("Niepoprawna cyfra rozpoznania w recognizedGrid.");
  }

  const nextSource = update.source ?? "recognized";

  return grid.map((row, rowIndex) =>
    row.map((cell, columnIndex) => {
      if (
        rowIndex !== coordinates.rowIndex ||
        columnIndex !== coordinates.columnIndex
      ) {
        return cell;
      }

      return {
        ...cell,
        digit: update.digit,
        source: nextSource,
      };
    }),
  );
}
