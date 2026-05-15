import { GRID_SIZE } from "./gridCoordinates";

export type RecognizedDigit = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9;

export type RecognizedCellSource = "pending" | "recognized" | "error";

export type RecognizedCell = {
  rowIndex: number;
  columnIndex: number;
  digit: RecognizedDigit | null;
  source: RecognizedCellSource;
  isEditable: boolean;
  isLocked: boolean;
};

export type RecognizedGrid = RecognizedCell[][];

export function isRecognizedDigit(value: unknown): value is RecognizedDigit {
  return (
    typeof value === "number" &&
    Number.isInteger(value) &&
    value >= 1 &&
    value <= 9
  );
}

export function isRecognizedGrid(value: unknown): value is RecognizedGrid {
  if (!Array.isArray(value) || value.length !== GRID_SIZE) {
    return false;
  }

  return value.every((row, rowIndex) => {
    if (!Array.isArray(row) || row.length !== GRID_SIZE) {
      return false;
    }

    return row.every((cell, columnIndex) => {
      if (!cell || typeof cell !== "object") {
        return false;
      }

      const record = cell as Record<string, unknown>;

      return (
        record.rowIndex === rowIndex &&
        record.columnIndex === columnIndex &&
        (record.digit === null || isRecognizedDigit(record.digit)) &&
        (record.source === "pending" ||
          record.source === "recognized" ||
          record.source === "error") &&
        typeof record.isEditable === "boolean" &&
        typeof record.isLocked === "boolean"
      );
    });
  });
}
