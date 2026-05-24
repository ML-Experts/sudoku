import type {
  TrainingClassMetricApiResponse,
  TrainingConfusionMatrixApiResponse,
  TrainingMetricHistoryPointApiResponse,
  TrainingReportSummaryApiResponse,
  TrainingRunReportApiResponse,
} from "../../types/api";

export function isTrainingReportSummaryApiResponse(
  value: unknown,
): value is TrainingReportSummaryApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    typeof record.accuracy === "number" &&
    typeof record.precisionMacro === "number" &&
    typeof record.recallMacro === "number" &&
    typeof record.f1Macro === "number" &&
    (typeof record.trainingDurationSeconds === "number" ||
      record.trainingDurationSeconds === null) &&
    (typeof record.averageInferenceTimeMs === "number" ||
      record.averageInferenceTimeMs === null)
  );
}

export function isTrainingClassMetricApiResponse(
  value: unknown,
): value is TrainingClassMetricApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    typeof record.label === "string" &&
    typeof record.precision === "number" &&
    typeof record.recall === "number" &&
    typeof record.f1 === "number" &&
    typeof record.support === "number"
  );
}

export function isTrainingMetricHistoryPointApiResponse(
  value: unknown,
): value is TrainingMetricHistoryPointApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    typeof record.epoch === "number" &&
    (typeof record.trainLoss === "number" || record.trainLoss === null) &&
    (typeof record.validationLoss === "number" || record.validationLoss === null) &&
    (typeof record.trainAccuracy === "number" || record.trainAccuracy === null) &&
    (typeof record.validationAccuracy === "number" ||
      record.validationAccuracy === null)
  );
}

export function isTrainingConfusionMatrixApiResponse(
  value: unknown,
): value is TrainingConfusionMatrixApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    Array.isArray(record.classNames) &&
    record.classNames.every((className) => typeof className === "string") &&
    Array.isArray(record.matrix) &&
    record.matrix.every(
      (row) =>
        Array.isArray(row) && row.every((cellValue) => typeof cellValue === "number"),
    )
  );
}

export function isTrainingRunReportApiResponse(
  value: unknown,
): value is TrainingRunReportApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    typeof record.status === "string" &&
    (record.summary === null || isTrainingReportSummaryApiResponse(record.summary)) &&
    Array.isArray(record.perClassMetrics) &&
    record.perClassMetrics.every((item) => isTrainingClassMetricApiResponse(item)) &&
    Array.isArray(record.history) &&
    record.history.every((item) => isTrainingMetricHistoryPointApiResponse(item)) &&
    (record.confusionMatrix === null ||
      isTrainingConfusionMatrixApiResponse(record.confusionMatrix))
  );
}
