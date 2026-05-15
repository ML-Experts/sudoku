import { GRID_SIZE } from "./gridCoordinates";
import type { RecognizedGrid } from "./recognizedGrid";

export function createEmptyRecognizedGrid(): RecognizedGrid {
  return Array.from({ length: GRID_SIZE }, (_, rowIndex) =>
    Array.from({ length: GRID_SIZE }, (_, columnIndex) => ({
      rowIndex,
      columnIndex,
      digit: null,
      source: "pending" as const,
      isEditable: false,
      isLocked: false,
    })),
  );
}
