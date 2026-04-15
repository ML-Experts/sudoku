import type {
  CancelTrainingRunApiResponse,
  CreateTrainingRunApiEntry,
  ErrorApiResponse,
  ProcessedDatasetListItemApiResponse,
  ProcessedDatasetsListApiResponse,
  RegistryModelListItemApiResponse,
  RegistryModelsListApiResponse,
  TrainingRunApiResponse,
  TrainingRunFailureApiResponse,
  TrainingRunProgressApiResponse,
  TrainingRunResultApiResponse,
  TrainingRunSocketEventApiResponse,
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

function isTrainingRunApiResponse(value: unknown): value is TrainingRunApiResponse {
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

function isRegistryModelListItemApiResponse(
  value: unknown
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
    (typeof record.parentModelName === "string" ||
      record.parentModelName === null) &&
    typeof record.trainingMode === "string" &&
    typeof record.inputProfile === "string" &&
    typeof record.trainingProfileName === "string" &&
    typeof record.augmentationProfileName === "string" &&
    typeof record.createdAtUtc === "string" &&
    typeof record.canStartTraining === "boolean" &&
    typeof record.canUseForInference === "boolean"
  );
}

function isRegistryModelsListApiResponse(
  value: unknown
): value is RegistryModelsListApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  if (!Array.isArray(record.items) || typeof record.totalCount !== "number") {
    return false;
  }

  return record.items.every((item) => isRegistryModelListItemApiResponse(item));
}

function isProcessedDatasetListItemApiResponse(
  value: unknown
): value is ProcessedDatasetListItemApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  if (
    typeof record.name !== "string" ||
    typeof record.fileName !== "string" ||
    typeof record.preprocessingProfile !== "string" ||
    typeof record.createdAtUtc !== "string"
  ) {
    return false;
  }

  if (!record.sampleCounts || typeof record.sampleCounts !== "object") {
    return false;
  }

  const sampleCounts = record.sampleCounts as Record<string, unknown>;
  return (
    typeof sampleCounts.train === "number" &&
    typeof sampleCounts.val === "number" &&
    typeof sampleCounts.test === "number"
  );
}

function isProcessedDatasetsListApiResponse(
  value: unknown
): value is ProcessedDatasetsListApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  if (!Array.isArray(record.items) || typeof record.totalCount !== "number") {
    return false;
  }

  return record.items.every((item) =>
    isProcessedDatasetListItemApiResponse(item)
  );
}

function isCancelTrainingRunApiResponse(
  value: unknown
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

function isTrainingRunProgressApiResponse(
  value: unknown
): value is TrainingRunProgressApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    (typeof record.percent === "number" || record.percent === null) &&
    (typeof record.epochCurrent === "number" || record.epochCurrent === null) &&
    (typeof record.epochTotal === "number" || record.epochTotal === null) &&
    (typeof record.etaSeconds === "number" || record.etaSeconds === null)
  );
}

function isTrainingRunResultApiResponse(
  value: unknown
): value is TrainingRunResultApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    typeof record.producedModelName === "string" &&
    typeof record.reportStatus === "string" &&
    typeof record.canUseProducedModelForInference === "boolean" &&
    typeof record.primaryArtifactRelativePath === "string" &&
    (typeof record.summaryRelativePath === "string" ||
      record.summaryRelativePath === null) &&
    (typeof record.metricsRelativePath === "string" ||
      record.metricsRelativePath === null) &&
    (typeof record.confusionMatrixRelativePath === "string" ||
      record.confusionMatrixRelativePath === null)
  );
}

function isTrainingRunFailureApiResponse(
  value: unknown
): value is TrainingRunFailureApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    typeof record.errorType === "string" &&
    typeof record.message === "string" &&
    typeof record.canUseProducedModelForInference === "boolean"
  );
}

export function isTrainingRunSocketEventApiResponse(
  value: unknown
): value is TrainingRunSocketEventApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  if (
    typeof record.eventType !== "string" ||
    typeof record.sequence !== "number" ||
    typeof record.runName !== "string" ||
    typeof record.status !== "string" ||
    typeof record.stage !== "string" ||
    typeof record.occurredAtUtc !== "string" ||
    !(typeof record.message === "string" || record.message === null) ||
    !Array.isArray(record.warnings)
  ) {
    return false;
  }

  if (!record.warnings.every((item) => typeof item === "string")) {
    return false;
  }

  if (
    !(
      record.progress === null ||
      isTrainingRunProgressApiResponse(record.progress)
    ) ||
    !(record.result === null || isTrainingRunResultApiResponse(record.result)) ||
    !(record.failure === null || isTrainingRunFailureApiResponse(record.failure))
  ) {
    return false;
  }

  return true;
}

function buildErrorFromResponse(rawBody: string, status: number): TrainingsApiError {
  const parsed = tryParseJson(rawBody);

  if (isErrorApiResponse(parsed)) {
    return new TrainingsApiError(parsed.message, status, parsed.errorType);
  }

  return new TrainingsApiError(
    rawBody.trim()
      ? `Backend zwrócił odpowiedź HTTP ${status}.`
      : `Backend zwrócił odpowiedź HTTP ${status} bez treści.`,
    status
  );
}

export async function getActiveTrainingRun(
  apiBaseUrl: string,
  accessToken?: string | null,
  signal?: AbortSignal
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
        "Backend zwrócił niepoprawny kształt TrainingRunApiResponse."
      );
    }

    return parsed;
  }

  throw buildErrorFromResponse(rawBody, response.status);
}

export async function getRegistryModels(
  apiBaseUrl: string,
  accessToken?: string | null,
  signal?: AbortSignal
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
        "Backend zwrócił niepoprawny kształt RegistryModelsListApiResponse."
      );
    }

    return parsed;
  }

  throw buildErrorFromResponse(rawBody, response.status);
}

export async function getProcessedDatasets(
  apiBaseUrl: string,
  accessToken?: string | null,
  signal?: AbortSignal
): Promise<ProcessedDatasetsListApiResponse> {
  const response = await fetch(`${apiBaseUrl}/datasets/processed`, {
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
    if (!isProcessedDatasetsListApiResponse(parsed)) {
      throw new Error(
        "Backend zwrócił niepoprawny kształt ProcessedDatasetsListApiResponse."
      );
    }

    return parsed;
  }

  throw buildErrorFromResponse(rawBody, response.status);
}

export async function postCreateTrainingRun(
  apiBaseUrl: string,
  entry: CreateTrainingRunApiEntry,
  accessToken?: string | null,
  signal?: AbortSignal
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
        "Backend zwrócił niepoprawny kształt TrainingRunApiResponse."
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
  signal?: AbortSignal
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
    }
  );

  const rawBody = await response.text();
  const parsed = tryParseJson(rawBody);

  if (response.status === 202) {
    if (!isCancelTrainingRunApiResponse(parsed)) {
      throw new Error(
        "Backend zwrócił niepoprawny kształt CancelTrainingRunApiResponse."
      );
    }

    return parsed;
  }

  throw buildErrorFromResponse(rawBody, response.status);
}
