import type {
  CreateProcessedDatasetApiEntry,
  ProcessedDatasetApiResponse,
  ProcessedDatasetListItemApiResponse,
  ProcessedDatasetsListApiResponse,
  RawDatasetCandidateApiResponse,
  SelectedPreparedDatasetSourceApiEntry,
  SplitSampleCountsApiResponse,
} from "../types/api";
import { fetchJson, JsonApiError } from "./shared/fetchJson";

export class DatasetsApiError extends JsonApiError {}

function buildAuthHeaders(accessToken?: string | null): HeadersInit {
  if (!accessToken) {
    return {};
  }

  return {
    Authorization: `Bearer ${accessToken}`,
  };
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

function isSelectedPreparedDatasetSourceApiEntry(
  value: unknown
): value is SelectedPreparedDatasetSourceApiEntry {
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

  if (
    !record.sources.every((item) => isSelectedPreparedDatasetSourceApiEntry(item))
  ) {
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

export async function getRawDatasetCandidates(
  apiBaseUrl: string,
  accessToken?: string | null,
  signal?: AbortSignal
): Promise<RawDatasetCandidateApiResponse[]> {
  return fetchJson<RawDatasetCandidateApiResponse[], DatasetsApiError>({
    url: `${apiBaseUrl}/datasets/raw-candidates`,
    init: {
      method: "GET",
      headers: {
        Accept: "application/json",
        ...buildAuthHeaders(accessToken),
      },
      signal,
    },
    expectedStatus: 200,
    validateResponse: (value): value is RawDatasetCandidateApiResponse[] =>
      Array.isArray(value) && value.every(isRawDatasetCandidateApiResponse),
    invalidResponseMessage:
      "Backend zwrocil niepoprawny ksztalt RawDatasetCandidateApiResponse[].",
    errorFactory: (message, status, errorType) =>
      new DatasetsApiError(message, status, errorType),
  });
}

export async function getProcessedDatasets(
  apiBaseUrl: string,
  accessToken?: string | null,
  signal?: AbortSignal
): Promise<ProcessedDatasetsListApiResponse> {
  return fetchJson<ProcessedDatasetsListApiResponse, DatasetsApiError>({
    url: `${apiBaseUrl}/datasets/processed`,
    init: {
      method: "GET",
      headers: {
        Accept: "application/json",
        ...buildAuthHeaders(accessToken),
      },
      signal,
    },
    expectedStatus: 200,
    validateResponse: isProcessedDatasetsListApiResponse,
    invalidResponseMessage:
      "Backend zwrocil niepoprawny ksztalt ProcessedDatasetsListApiResponse.",
    errorFactory: (message, status, errorType) =>
      new DatasetsApiError(message, status, errorType),
  });
}

export async function postCreateProcessedDataset(
  apiBaseUrl: string,
  entry: CreateProcessedDatasetApiEntry,
  accessToken?: string | null,
  signal?: AbortSignal
): Promise<ProcessedDatasetApiResponse> {
  return fetchJson<ProcessedDatasetApiResponse, DatasetsApiError>({
    url: `${apiBaseUrl}/datasets/processed`,
    init: {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        ...buildAuthHeaders(accessToken),
      },
      body: JSON.stringify(entry),
      signal,
    },
    expectedStatus: 201,
    validateResponse: isProcessedDatasetApiResponse,
    invalidResponseMessage:
      "Backend zwrocil niepoprawny ksztalt ProcessedDatasetApiResponse.",
    errorFactory: (message, status, errorType) =>
      new DatasetsApiError(message, status, errorType),
  });
}
