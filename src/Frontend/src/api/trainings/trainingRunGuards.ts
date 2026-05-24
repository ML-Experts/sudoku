import type {
  TrainingDatasetSampleCountsApiResponse,
  TrainingMetricsSummaryApiResponse,
  TrainingRunApiResponse,
  TrainingRunConfigurationApiResponse,
  TrainingRunDatasetDetailsApiResponse,
  TrainingRunDetailsApiResponse,
  TrainingRunListItemApiResponse,
  TrainingRunProgressApiResponse,
  TrainingRunsListApiResponse,
} from "../../types/api";
import { isTrainingRunModelReferenceApiResponse } from "./modelGuards";
import { isTrainingRunReportApiResponse } from "./reportGuards";

export function isTrainingRunEffectiveParametersApiResponse(
  value: unknown,
): value is TrainingRunApiResponse["effectiveParameters"] {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    typeof record.epochs === "number" &&
    typeof record.learningRate === "number" &&
    typeof record.batchSize === "number" &&
    typeof record.earlyStoppingPatience === "number" &&
    typeof record.lrSchedulerPatience === "number" &&
    typeof record.lrSchedulerFactor === "number" &&
    typeof record.fineTuningPolicy === "string"
  );
}

export function isTrainingRunProgressApiResponse(
  value: unknown,
): value is TrainingRunProgressApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    (typeof record.percent === "number" || record.percent === null) &&
    (typeof record.epochCurrent === "number" || record.epochCurrent === null) &&
    (typeof record.epochTotal === "number" || record.epochTotal === null) &&
    (typeof record.etaSeconds === "number" || record.etaSeconds === null) &&
    (typeof record.trainLoss === "number" ||
      record.trainLoss === null ||
      record.trainLoss === undefined) &&
    (typeof record.validationLoss === "number" ||
      record.validationLoss === null ||
      record.validationLoss === undefined) &&
    (typeof record.trainAccuracy === "number" ||
      record.trainAccuracy === null ||
      record.trainAccuracy === undefined) &&
    (typeof record.validationAccuracy === "number" ||
      record.validationAccuracy === null ||
      record.validationAccuracy === undefined)
  );
}

export function isTrainingMetricsSummaryApiResponse(
  value: unknown,
): value is TrainingMetricsSummaryApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    (typeof record.accuracy === "number" || record.accuracy === null) &&
    (typeof record.macroF1 === "number" || record.macroF1 === null)
  );
}

export function isTrainingRunApiResponse(
  value: unknown,
): value is TrainingRunApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    typeof record.runName === "string" &&
    typeof record.status === "string" &&
    typeof record.createdAtUtc === "string" &&
    typeof record.baseModelName === "string" &&
    typeof record.producedModelName === "string" &&
    typeof record.processedDatasetName === "string" &&
    typeof record.trainingMode === "string" &&
    typeof record.trainingProfileName === "string" &&
    typeof record.augmentationProfileName === "string" &&
    typeof record.benchmarkName === "string" &&
    typeof record.seed === "number" &&
    (record.effectiveParameters === null ||
      record.effectiveParameters === undefined ||
      isTrainingRunEffectiveParametersApiResponse(record.effectiveParameters)) &&
    typeof record.progressChannelUrl === "string"
  );
}

export function isTrainingRunListItemApiResponse(
  value: unknown,
): value is TrainingRunListItemApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    typeof record.runName === "string" &&
    typeof record.status === "string" &&
    typeof record.createdAtUtc === "string" &&
    (typeof record.updatedAtUtc === "string" || record.updatedAtUtc === null) &&
    (typeof record.startedAtUtc === "string" || record.startedAtUtc === null) &&
    (typeof record.finishedAtUtc === "string" || record.finishedAtUtc === null) &&
    typeof record.baseModelName === "string" &&
    typeof record.producedModelName === "string" &&
    typeof record.processedDatasetName === "string" &&
    typeof record.trainingMode === "string" &&
    typeof record.trainingProfileName === "string" &&
    typeof record.augmentationProfileName === "string" &&
    typeof record.benchmarkName === "string" &&
    (record.effectiveParameters === null ||
      record.effectiveParameters === undefined ||
      isTrainingRunEffectiveParametersApiResponse(record.effectiveParameters)) &&
    (typeof record.reportStatus === "string" || record.reportStatus === null) &&
    (record.progress === null || isTrainingRunProgressApiResponse(record.progress)) &&
    (record.metricsSummary === null ||
      isTrainingMetricsSummaryApiResponse(record.metricsSummary)) &&
    Array.isArray(record.warnings) &&
    record.warnings.every((warning) => typeof warning === "string")
  );
}

export function isTrainingDatasetSampleCountsApiResponse(
  value: unknown,
): value is TrainingDatasetSampleCountsApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    typeof record.train === "number" &&
    typeof record.val === "number" &&
    typeof record.test === "number"
  );
}

export function isTrainingRunDatasetDetailsApiResponse(
  value: unknown,
): value is TrainingRunDatasetDetailsApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    typeof record.processedDatasetName === "string" &&
    (typeof record.preprocessingProfile === "string" ||
      record.preprocessingProfile === null) &&
    (record.sampleCounts === null ||
      isTrainingDatasetSampleCountsApiResponse(record.sampleCounts))
  );
}

export function isTrainingRunConfigurationApiResponse(
  value: unknown,
): value is TrainingRunConfigurationApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    typeof record.trainingMode === "string" &&
    typeof record.trainingProfileName === "string" &&
    typeof record.augmentationProfileName === "string" &&
    typeof record.benchmarkName === "string" &&
    typeof record.seed === "number" &&
    (record.effectiveParameters === null ||
      record.effectiveParameters === undefined ||
      isTrainingRunEffectiveParametersApiResponse(record.effectiveParameters)) &&
    (typeof record.sourceRevision === "string" || record.sourceRevision === null)
  );
}

export function isTrainingRunDetailsApiResponse(
  value: unknown,
): value is TrainingRunDetailsApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    typeof record.runName === "string" &&
    typeof record.status === "string" &&
    (typeof record.stage === "string" || record.stage === null) &&
    typeof record.createdAtUtc === "string" &&
    (typeof record.startedAtUtc === "string" || record.startedAtUtc === null) &&
    (typeof record.finishedAtUtc === "string" || record.finishedAtUtc === null) &&
    isTrainingRunModelReferenceApiResponse(record.baseModel) &&
    (record.producedModel === null ||
      isTrainingRunModelReferenceApiResponse(record.producedModel)) &&
    isTrainingRunDatasetDetailsApiResponse(record.dataset) &&
    isTrainingRunConfigurationApiResponse(record.configuration) &&
    (record.progress === null || isTrainingRunProgressApiResponse(record.progress)) &&
    isTrainingRunReportApiResponse(record.report) &&
    Array.isArray(record.warnings) &&
    record.warnings.every((warning) => typeof warning === "string")
  );
}

export function isTrainingRunsListApiResponse(
  value: unknown,
): value is TrainingRunsListApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    Array.isArray(record.items) &&
    record.items.every((item) => isTrainingRunListItemApiResponse(item)) &&
    typeof record.totalCount === "number"
  );
}
