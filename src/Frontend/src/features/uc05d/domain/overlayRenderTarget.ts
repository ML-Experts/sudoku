import type { RecognizedDigit } from "../../uc05a/domain/recognizedGrid";

export type OverlayRenderTarget = {
  rowIndex: number;
  columnIndex: number;
  digit: RecognizedDigit;
};
