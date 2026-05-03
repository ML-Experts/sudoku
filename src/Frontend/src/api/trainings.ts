import type {
  CancelTrainingRunApiResponse,
  CreateTrainingRunApiEntry,
  ErrorApiResponse,
  RegistryModelListItemApiResponse,
  RegistryModelsListApiResponse,
  TrainingRunApiResponse,
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
