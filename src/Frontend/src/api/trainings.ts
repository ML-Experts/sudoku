import type {
  CancelTrainingRunApiResponse,
  CreateTrainingRunApiEntry,
  ErrorApiResponse,
  RegistryModelListItemApiResponse,
  RegistryModelsListApiResponse,
  TrainingClassMetricApiResponse,
  TrainingConfusionMatrixApiResponse,
  TrainingDatasetSampleCountsApiResponse,
  TrainingMetricsSummaryApiResponse,
  TrainingMetricHistoryPointApiResponse,
  TrainingRunApiResponse,
  TrainingRunConfigurationApiResponse,
  TrainingRunDatasetDetailsApiResponse,
  TrainingRunDetailsApiResponse,
  TrainingRunListItemApiResponse,
  TrainingRunModelReferenceApiResponse,
  TrainingRunProgressApiResponse,
  TrainingRunReportApiResponse,
  TrainingReportSummaryApiResponse,
  TrainingRunsListApiResponse,
} from "../types/api";

export class TrainingsApiError extends Error {
  readonly status: number;
  readonly errorType: string | undefined;

  constructor(message: string, status: number, errorType?: string) {
    super(message);
    this.name = "TrainingsApiError";
    this.status = status;
    this.errorType = errorType;
  }
}

function tryParseJson(raw: string): unknown {
  if (!raw.trim()) {
    return null;
  }

  try {
    return JSON.parse(raw) as unknown;
  } catch {
    return null;
  }
}

function buildAuthHeaders(accessToken?: string | null): HeadersInit {
  if (!accessToken) {
    return {};
  }

  return {
    Authorization: `Bearer ${accessToken}`,
  };
}

function isErrorApiResponse(value: unknown): value is ErrorApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    typeof record.message === "string" && typeof record.errorType === "string"
  );
}

function isTrainingRunApiResponse(
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
    typeof record.progressChannelUrl === "string"
  );
}

function isTrainingRunProgressApiResponse(
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

function isTrainingMetricsSummaryApiResponse(
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

function isTrainingRunListItemApiResponse(
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
    (typeof record.reportStatus === "string" || record.reportStatus === null) &&
    (record.progress === null || isTrainingRunProgressApiResponse(record.progress)) &&
    (record.metricsSummary === null ||
      isTrainingMetricsSummaryApiResponse(record.metricsSummary)) &&
    Array.isArray(record.warnings) &&
    record.warnings.every((warning) => typeof warning === "string")
  );
}

function isTrainingRunModelReferenceApiResponse(
  value: unknown,
): value is TrainingRunModelReferenceApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    typeof record.name === "string" &&
    typeof record.displayName === "string" &&
    typeof record.sourceType === "string" &&
    (typeof record.sourceRunName === "string" || record.sourceRunName === null) &&
    (typeof record.parentModelName === "string" || record.parentModelName === null) &&
    typeof record.inputProfile === "string" &&
    typeof record.canUseForInference === "boolean" &&
    typeof record.canStartTraining === "boolean"
  );
}

function isTrainingDatasetSampleCountsApiResponse(
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

function isTrainingRunDatasetDetailsApiResponse(
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

function isTrainingRunConfigurationApiResponse(
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
    (typeof record.sourceRevision === "string" || record.sourceRevision === null)
  );
}

function isTrainingReportSummaryApiResponse(
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

function isTrainingClassMetricApiResponse(
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

function isTrainingMetricHistoryPointApiResponse(
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

function isTrainingConfusionMatrixApiResponse(
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

function isTrainingRunReportApiResponse(
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

function isTrainingRunDetailsApiResponse(
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

function isTrainingRunsListApiResponse(
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

function isRegistryModelListItemApiResponse(
  value: unknown,
): value is RegistryModelListItemApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    typeof record.name === "string" &&
    typeof record.displayName === "string" &&
    typeof record.sourceType === "string" &&
    (typeof record.sourceRunName === "string" || record.sourceRunName === null) &&
    (typeof record.parentModelName === "string" || record.parentModelName === null) &&
    typeof record.trainingMode === "string" &&
    typeof record.inputProfile === "string" &&
    (typeof record.trainingProfileName === "string" ||
      record.trainingProfileName === null) &&
    (typeof record.augmentationProfileName === "string" ||
      record.augmentationProfileName === null) &&
    (typeof record.createdAtUtc === "string" || record.createdAtUtc === null) &&
    typeof record.canStartTraining === "boolean" &&
    typeof record.canUseForInference === "boolean" &&
    Array.isArray(record.warnings) &&
    record.warnings.every((warning) => typeof warning === "string")
  );
}

function isRegistryModelsListApiResponse(
  value: unknown,
): value is RegistryModelsListApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    Array.isArray(record.items) &&
    record.items.every((item) => isRegistryModelListItemApiResponse(item)) &&
    typeof record.totalCount === "number"
  );
}

function isCancelTrainingRunApiResponse(
  value: unknown,
): value is CancelTrainingRunApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    typeof record.runName === "string" &&
    (typeof record.status === "string" || record.status === null) &&
    typeof record.requestDisposition === "string" &&
    (typeof record.cancellationRequestedAtUtc === "string" ||
      record.cancellationRequestedAtUtc === null)
  );
}

function isLegacyCancelTrainingRunApiResponse(
  value: unknown,
): value is {
  runName: string;
  status: string | null;
  requestDisposition: string;
} {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    typeof record.runName === "string" &&
    (typeof record.status === "string" || record.status === null) &&
    typeof record.requestDisposition === "string"
  );
}

function buildErrorFromResponse(rawBody: string, status: number): TrainingsApiError {
  const parsed = tryParseJson(rawBody);

  if (isErrorApiResponse(parsed)) {
    return new TrainingsApiError(parsed.message, status, parsed.errorType);
  }

  return new TrainingsApiError(
    rawBody.trim()
      ? `Backend zwrocil odpowiedz HTTP ${status}.`
      : `Backend zwrocil odpowiedz HTTP ${status} bez tresci.`,
    status,
  );
}

export async function postCreateTrainingRun(
  apiBaseUrl: string,
  entry: CreateTrainingRunApiEntry,
  accessToken?: string | null,
  signal?: AbortSignal,
): Promise<TrainingRunApiResponse> {
  const response = await fetch(`${apiBaseUrl}/trainings`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...buildAuthHeaders(accessToken),
    },
    body: JSON.stringify(entry),
    signal,
  });

  const rawBody = await response.text();
  const parsed = tryParseJson(rawBody);

  if (response.status === 202) {
    if (!isTrainingRunApiResponse(parsed)) {
      throw new Error(
        "Backend zwrocil niepoprawny ksztalt TrainingRunApiResponse.",
      );
    }

    return parsed;
  }

  throw buildErrorFromResponse(rawBody, response.status);
}

export async function getActiveTrainingRun(
  apiBaseUrl: string,
  accessToken?: string | null,
  signal?: AbortSignal,
): Promise<TrainingRunApiResponse | null> {
  const response = await fetch(`${apiBaseUrl}/trainings/active`, {
    method: "GET",
    headers: {
      Accept: "application/json",
      ...buildAuthHeaders(accessToken),
    },
    signal,
  });

  if (response.status === 204) {
    return null;
  }

  const rawBody = await response.text();
  const parsed = tryParseJson(rawBody);

  if (response.status === 200) {
    if (!isTrainingRunApiResponse(parsed)) {
      throw new Error(
        "Backend zwrocil niepoprawny ksztalt TrainingRunApiResponse.",
      );
    }

    return parsed;
  }

  throw buildErrorFromResponse(rawBody, response.status);
}

export async function getTrainingRuns(
  apiBaseUrl: string,
  accessToken?: string | null,
  signal?: AbortSignal,
): Promise<TrainingRunsListApiResponse> {
  const response = await fetch(`${apiBaseUrl}/trainings`, {
    method: "GET",
    headers: {
      Accept: "application/json",
      ...buildAuthHeaders(accessToken),
    },
    signal,
  });

  const rawBody = await response.text();
  const parsed = tryParseJson(rawBody);

  if (response.status === 200) {
    if (!isTrainingRunsListApiResponse(parsed)) {
      throw new Error(
        "Backend zwrocil niepoprawny ksztalt TrainingRunsListApiResponse.",
      );
    }

    return parsed;
  }

  throw buildErrorFromResponse(rawBody, response.status);
}

export async function getTrainingRunDetails(
  apiBaseUrl: string,
  runName: string,
  accessToken?: string | null,
  signal?: AbortSignal,
): Promise<TrainingRunDetailsApiResponse> {
  const response = await fetch(
    `${apiBaseUrl}/trainings/${encodeURIComponent(runName)}`,
    {
      method: "GET",
      headers: {
        Accept: "application/json",
        ...buildAuthHeaders(accessToken),
      },
      signal,
    },
  );

  const rawBody = await response.text();
  const parsed = tryParseJson(rawBody);

  if (response.status === 200) {
    if (!isTrainingRunDetailsApiResponse(parsed)) {
      throw new Error(
        "Backend zwrocil niepoprawny ksztalt TrainingRunDetailsApiResponse.",
      );
    }

    return parsed;
  }

  throw buildErrorFromResponse(rawBody, response.status);
}

export async function getRegistryModels(
  apiBaseUrl: string,
  accessToken?: string | null,
  signal?: AbortSignal,
): Promise<RegistryModelsListApiResponse> {
  const response = await fetch(`${apiBaseUrl}/models/registry`, {
    method: "GET",
    headers: {
      Accept: "application/json",
      ...buildAuthHeaders(accessToken),
    },
    signal,
  });

  const rawBody = await response.text();
  const parsed = tryParseJson(rawBody);

  if (response.status === 200) {
    if (!isRegistryModelsListApiResponse(parsed)) {
      throw new Error(
        "Backend zwrocil niepoprawny ksztalt RegistryModelsListApiResponse.",
      );
    }

    return parsed;
  }

  throw buildErrorFromResponse(rawBody, response.status);
}

export async function postCancelTrainingRun(
  apiBaseUrl: string,
  runName: string,
  accessToken?: string | null,
  signal?: AbortSignal,
): Promise<CancelTrainingRunApiResponse> {
  const response = await fetch(
    `${apiBaseUrl}/trainings/${encodeURIComponent(runName)}/cancel`,
    {
      method: "POST",
      headers: {
        Accept: "application/json",
        ...buildAuthHeaders(accessToken),
      },
      signal,
    },
  );

  const rawBody = await response.text();
  const parsed = tryParseJson(rawBody);

  if (response.status === 202) {
    if (!isCancelTrainingRunApiResponse(parsed)) {
      if (isLegacyCancelTrainingRunApiResponse(parsed)) {
        return {
          runName: parsed.runName,
          status: parsed.status,
          requestDisposition: parsed.requestDisposition,
          cancellationRequestedAtUtc: null,
        };
      }

      throw new Error(
        "Backend zwrocil niepoprawny ksztalt CancelTrainingRunApiResponse.",
      );
    }

    return parsed;
  }

  throw buildErrorFromResponse(rawBody, response.status);
}
