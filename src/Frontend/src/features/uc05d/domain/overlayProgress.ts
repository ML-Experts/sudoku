export type OverlayProgress = {
  targetCount: number;
  completedCount: number;
  remainingCount: number;
  percent: number;
};

export function calculateOverlayProgress(
  targetCount: number,
  completedCount: number,
): OverlayProgress {
  const normalizedTargetCount = Math.max(0, targetCount);
  const normalizedCompletedCount = Math.max(
    0,
    Math.min(completedCount, normalizedTargetCount),
  );
  const remainingCount = Math.max(
    0,
    normalizedTargetCount - normalizedCompletedCount,
  );

  return {
    targetCount: normalizedTargetCount,
    completedCount: normalizedCompletedCount,
    remainingCount,
    percent:
      normalizedTargetCount === 0
        ? 0
        : Math.round((normalizedCompletedCount / normalizedTargetCount) * 100),
  };
}
