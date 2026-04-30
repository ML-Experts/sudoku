import type {
  CancelTrainingRunApiResponse,
  CreateTrainingRunApiEntry,
  ErrorApiResponse,
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
    typeof record.message === "string" &&
    (typeof record.progressChannelUrl === "string" ||
      record.progressChannelUrl === null)
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
      throw new Error(
        "Backend zwrocil niepoprawny ksztalt CancelTrainingRunApiResponse.",
      );
    }

    return parsed;
  }

  throw buildErrorFromResponse(rawBody, response.status);
}
