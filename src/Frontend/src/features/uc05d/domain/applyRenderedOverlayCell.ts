import { isGridCoordinateInBounds } from "../../uc05a/domain/gridCoordinates";
import type { OverlayRenderTarget } from "./overlayRenderTarget";

export function applyRenderedOverlayCell(
  renderedCells: string[][],
  target: OverlayRenderTarget,
  renderedCellUrl: string,
): string[][] {
  if (!isGridCoordinateInBounds(target)) {
    throw new Error("Niepoprawne wspolrzedne komorki overlay.");
  }

  return renderedCells.map((row, rowIndex) =>
    row.map((cellUrl, columnIndex) => {
      if (rowIndex !== target.rowIndex || columnIndex !== target.columnIndex) {
        return cellUrl;
      }

      return renderedCellUrl;
    }),
  );
}
