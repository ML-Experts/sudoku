import type { RecognizedGrid } from "./recognizedGrid";

export type RecognitionProgress = {
  totalCount: number;
  completedCount: number;
  pendingCount: number;
  recognizedCount: number;
  emptyCount: number;
  errorCount: number;
  percent: number;
};

export function calculateRecognitionProgress(
  recognizedGrid: RecognizedGrid | null,
): RecognitionProgress {
  if (!recognizedGrid) {
    return {
      totalCount: 0,
      completedCount: 0,
      pendingCount: 0,
      recognizedCount: 0,
      emptyCount: 0,
      errorCount: 0,
      percent: 0,
    };
  }

  let completedCount = 0;
  let pendingCount = 0;
  let recognizedCount = 0;
  let emptyCount = 0;
  let errorCount = 0;

  for (const row of recognizedGrid) {
    for (const cell of row) {
      if (cell.source === "pending") {
        pendingCount += 1;
        continue;
      }

      completedCount += 1;

      if (cell.source === "error") {
        errorCount += 1;
        continue;
      }

      if (cell.digit === null) {
        emptyCount += 1;
      } else {
        recognizedCount += 1;
      }
    }
  }

  const totalCount = recognizedGrid.length * (recognizedGrid[0]?.length ?? 0);
  const percent =
    totalCount === 0 ? 0 : Math.round((completedCount / totalCount) * 100);

  return {
    totalCount,
    completedCount,
    pendingCount,
    recognizedCount,
    emptyCount,
    errorCount,
    percent,
  };
}
