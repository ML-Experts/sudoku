import type { RecognizedGrid } from "../../uc05a/domain/recognizedGrid";

export function createGridSignature(recognizedGrid: RecognizedGrid): string {
  return recognizedGrid
    .map((row) =>
      row
        .map((cell) => `${cell.source}:${cell.digit === null ? "_" : cell.digit}`)
        .join("|"),
    )
    .join("||");
}
