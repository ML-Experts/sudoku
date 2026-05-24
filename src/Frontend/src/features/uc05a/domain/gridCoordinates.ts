export const GRID_SIZE = 9;

export type GridCoordinates = {
  rowIndex: number;
  columnIndex: number;
};

export function isGridCoordinateInBounds({
  rowIndex,
  columnIndex,
}: GridCoordinates): boolean {
  return (
    Number.isInteger(rowIndex) &&
    Number.isInteger(columnIndex) &&
    rowIndex >= 0 &&
    rowIndex < GRID_SIZE &&
    columnIndex >= 0 &&
    columnIndex < GRID_SIZE
  );
}
