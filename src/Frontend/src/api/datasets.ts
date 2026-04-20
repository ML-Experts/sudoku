import type {
  CreateProcessedDatasetApiEntry,
  ErrorApiResponse,
  ProcessedDatasetApiResponse,
  ProcessedDatasetListItemApiResponse,
  ProcessedDatasetsListApiResponse,
  RawDatasetCandidateApiResponse,
  SelectedRawDatasetSourceApiEntry,
  SplitSampleCountsApiResponse,
} from "../types/api";

export class DatasetsApiError extends Error {
  readonly status: number;
  readonly errorType: string | undefined;

  constructor(message: string, status: number, errorType?: string) {
    super(message);
    this.name = "DatasetsApiError";
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

function isRawDatasetCandidateApiResponse(
  value: unknown
): value is RawDatasetCandidateApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return typeof record.name === "string" && typeof record.type === "string";
}

function isSplitSampleCountsApiResponse(
  value: unknown
): value is SplitSampleCountsApiResponse {
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

function isSelectedRawDatasetSourceApiEntry(
  value: unknown
): value is SelectedRawDatasetSourceApiEntry {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  if (
    typeof record.name !== "string" ||
    typeof record.type !== "string" ||
    !Array.isArray(record.splits)
  ) {
    return false;
  }

  return record.splits.every((item) => typeof item === "string");
}

function isProcessedDatasetListItemApiResponse(
  value: unknown
): value is ProcessedDatasetListItemApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    typeof record.name === "string" &&
    typeof record.fileName === "string" &&
    typeof record.preprocessingProfile === "string" &&
    typeof record.createdAtUtc === "string" &&
    isSplitSampleCountsApiResponse(record.sampleCounts)
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

function isProcessedDatasetApiResponse(
  value: unknown
): value is ProcessedDatasetApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  if (
    typeof record.name !== "string" ||
    typeof record.fileName !== "string" ||
    typeof record.preprocessingProfile !== "string" ||
    typeof record.createdAtUtc !== "string" ||
    !Array.isArray(record.sources) ||
    !isSplitSampleCountsApiResponse(record.sampleCounts) ||
    !Array.isArray(record.sourceReports) ||
    !Array.isArray(record.warnings)
  ) {
    return false;
  }

  if (!record.sources.every((item) => isSelectedRawDatasetSourceApiEntry(item))) {
    return false;
  }

  if (
    !record.sourceReports.every((item) => {
      if (!item || typeof item !== "object") {
        return false;
      }

      const report = item as Record<string, unknown>;
      return (
        typeof report.name === "string" &&
        typeof report.type === "string" &&
        typeof report.processedSampleCount === "number" &&
        typeof report.includedSampleCount === "number" &&
        typeof report.emptyCellCount === "number" &&
        typeof report.rejectedSampleCount === "number" &&
        Array.isArray(report.warnings) &&
        report.warnings.every((warning) => typeof warning === "string")
      );
    })
  ) {
    return false;
  }

  return record.warnings.every((warning) => typeof warning === "string");
}

function buildErrorFromResponse(rawBody: string, status: number): DatasetsApiError {
  const parsed = tryParseJson(rawBody);

  if (isErrorApiResponse(parsed)) {
    return new DatasetsApiError(parsed.message, status, parsed.errorType);
  }

  return new DatasetsApiError(
    rawBody.trim()
      ? `Backend zwrócił odpowiedź HTTP ${status}.`
      : `Backend zwrócił odpowiedź HTTP ${status} bez treści.`,
    status
  );
}

export async function getRawDatasetCandidates(
  apiBaseUrl: string,
  accessToken?: string | null,
  signal?: AbortSignal
): Promise<RawDatasetCandidateApiResponse[]> {
  const response = await fetch(`${apiBaseUrl}/datasets/raw-candidates`, {
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
    if (!Array.isArray(parsed) || !parsed.every(isRawDatasetCandidateApiResponse)) {
      throw new Error(
        "Backend zwrócił niepoprawny kształt RawDatasetCandidateApiResponse[]."
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

export async function postCreateProcessedDataset(
  apiBaseUrl: string,
  entry: CreateProcessedDatasetApiEntry,
  accessToken?: string | null,
  signal?: AbortSignal
): Promise<ProcessedDatasetApiResponse> {
  const response = await fetch(`${apiBaseUrl}/datasets/processed`, {
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

  if (response.status === 201) {
    if (!isProcessedDatasetApiResponse(parsed)) {
      throw new Error(
        "Backend zwrócił niepoprawny kształt ProcessedDatasetApiResponse."
      );
    }

    return parsed;
  }

  throw buildErrorFromResponse(rawBody, response.status);
}
