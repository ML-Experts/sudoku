import { GRID_SIZE } from "../../uc05a/domain/gridCoordinates";
import type { RecognizedGrid } from "../../uc05a/domain/recognizedGrid";
import { assertOverlayGridConsistency } from "./assertOverlayGridConsistency";
import type { OverlayRenderTarget } from "./overlayRenderTarget";

export function buildOverlayRenderPlan(
  inputGrid: RecognizedGrid,
  solvedGrid: RecognizedGrid,
): OverlayRenderTarget[] {
  assertOverlayGridConsistency(inputGrid, solvedGrid);

  const targets: OverlayRenderTarget[] = [];

  for (let rowIndex = 0; rowIndex < GRID_SIZE; rowIndex += 1) {
    for (let columnIndex = 0; columnIndex < GRID_SIZE; columnIndex += 1) {
      const inputDigit = inputGrid[rowIndex][columnIndex].digit;
      const solvedDigit = solvedGrid[rowIndex][columnIndex].digit;

      if (inputDigit === null && solvedDigit !== null) {
        targets.push({
          rowIndex,
          columnIndex,
          digit: solvedDigit,
        });
      }
    }
  }

  return targets;
}
