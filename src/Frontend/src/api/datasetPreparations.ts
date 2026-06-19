import type {
  CreateDatasetPreparationApiEntry,
  DatasetPreparationApiResponse,
  DatasetPreparationListItemApiResponse,
  DatasetPreparationsListApiResponse,
  DatasetPreparationSourceApiResponse,
} from "../types/api";
import {
  fetchJson,
  JsonApiError,
} from "./shared/fetchJson";

export class DatasetPreparationsApiError extends JsonApiError {}

function buildAuthHeaders(accessToken?: string | null): HeadersInit {
  if (!accessToken) {
    return {};
  }

  return {
    Authorization: `Bearer ${accessToken}`,
  };
}

function isDatasetPreparationSourceApiResponse(
  value: unknown
): value is DatasetPreparationSourceApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;

  return (
    typeof record.name === "string" &&
    typeof record.type === "string" &&
    typeof record.preparedItemsCount === "number"
  );
}

function isDatasetPreparationApiResponse(
  value: unknown
): value is DatasetPreparationApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;

  return (
    typeof record.preparationName === "string" &&
    typeof record.createdAtUtc === "string" &&
    typeof record.status === "string" &&
    Array.isArray(record.sources) &&
    record.sources.every(isDatasetPreparationSourceApiResponse) &&
    Array.isArray(record.warnings) &&
    record.warnings.every((warning) => typeof warning === "string")
  );
}

function isDatasetPreparationListItemApiResponse(
  value: unknown
): value is DatasetPreparationListItemApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;

  return (
    typeof record.preparationName === "string" &&
    typeof record.createdAtUtc === "string" &&
    typeof record.status === "string" &&
    typeof record.boardSourcesCount === "number" &&
    typeof record.digitSourcesCount === "number"
  );
}

function isDatasetPreparationsListApiResponse(
  value: unknown
): value is DatasetPreparationsListApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;

  return (
    Array.isArray(record.items) &&
    record.items.every(isDatasetPreparationListItemApiResponse) &&
    typeof record.totalCount === "number"
  );
}

export async function createDatasetPreparation(
  apiBaseUrl: string,
  entry: CreateDatasetPreparationApiEntry,
  accessToken?: string | null,
  signal?: AbortSignal
): Promise<DatasetPreparationApiResponse> {
  return fetchJson<DatasetPreparationApiResponse, DatasetPreparationsApiError>({
    url: `${apiBaseUrl}/datasets/preparations`,
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
    expectedStatus: 202,
    validateResponse: isDatasetPreparationApiResponse,
    invalidResponseMessage:
      "Backend zwrócił niepoprawny kształt DatasetPreparationApiResponse.",
    errorFactory: (message, status, errorType) =>
      new DatasetPreparationsApiError(message, status, errorType),
  });
}

export async function getDatasetPreparations(
  apiBaseUrl: string,
  accessToken?: string | null,
  signal?: AbortSignal
): Promise<DatasetPreparationsListApiResponse> {
  return fetchJson<
    DatasetPreparationsListApiResponse,
    DatasetPreparationsApiError
  >({
    url: `${apiBaseUrl}/datasets/preparations`,
    init: {
      method: "GET",
      headers: {
        Accept: "application/json",
        ...buildAuthHeaders(accessToken),
      },
      signal,
    },
    expectedStatus: 200,
    validateResponse: isDatasetPreparationsListApiResponse,
    invalidResponseMessage:
      "Backend zwrócił niepoprawny kształt DatasetPreparationsListApiResponse.",
    errorFactory: (message, status, errorType) =>
      new DatasetPreparationsApiError(message, status, errorType),
  });
}

export async function getDatasetPreparationDetails(
  apiBaseUrl: string,
  preparationName: string,
  accessToken?: string | null,
  signal?: AbortSignal
): Promise<DatasetPreparationApiResponse> {
  const encodedPreparationName = encodeURIComponent(preparationName);

  return fetchJson<DatasetPreparationApiResponse, DatasetPreparationsApiError>({
    url: `${apiBaseUrl}/datasets/preparations/${encodedPreparationName}`,
    init: {
      method: "GET",
      headers: {
        Accept: "application/json",
        ...buildAuthHeaders(accessToken),
      },
      signal,
    },
    expectedStatus: 200,
    validateResponse: isDatasetPreparationApiResponse,
    invalidResponseMessage:
      "Backend zwrócił niepoprawny kształt DatasetPreparationApiResponse.",
    errorFactory: (message, status, errorType) =>
      new DatasetPreparationsApiError(message, status, errorType),
  });
}
