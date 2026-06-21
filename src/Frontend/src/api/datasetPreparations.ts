import type {
  DeleteDatasetPreparationBoardFileApiResponse,
  DatasetPreparationBoardFileListItemApiResponse,
  DatasetPreparationBoardFilesApiResponse,
  CreateDatasetPreparationApiEntry,
  DatasetPreparationApiResponse,
  DatasetPreparationFoldersApiResponse,
  DatasetPreparationListItemApiResponse,
  DatasetPreparationsListApiResponse,
  ImageApiResponse,
  DatasetPreparationSourceApiResponse,
} from "../types/api";
import {
  fetchJson,
  JsonApiError,
} from "./shared/fetchJson";
import { isImageApiResponse } from "./shared/isImageApiResponse";
import { resolveUc18BoardImageRequestUrl } from "../features/uc18/domain/resolveUc18BoardImageRequestUrl";

export class DatasetPreparationsApiError extends JsonApiError {}

export type DatasetPreparationFolderType = "board" | "digit";

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

function isDatasetPreparationFoldersApiResponse(
  value: unknown
): value is DatasetPreparationFoldersApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;

  return (
    typeof record.preparationName === "string" &&
    typeof record.type === "string" &&
    Array.isArray(record.items) &&
    record.items.every((item) => typeof item === "string") &&
    typeof record.totalCount === "number"
  );
}

export function isDatasetPreparationBoardFileListItemApiResponse(
  value: unknown
): value is DatasetPreparationBoardFileListItemApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;

  return (
    typeof record.boardFolderName === "string" &&
    typeof record.imageEndpoint === "string"
  );
}

export function isDatasetPreparationBoardFilesApiResponse(
  value: unknown
): value is DatasetPreparationBoardFilesApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;

  return (
    typeof record.preparationName === "string" &&
    typeof record.sourceName === "string" &&
    Array.isArray(record.items) &&
    record.items.every(isDatasetPreparationBoardFileListItemApiResponse) &&
    typeof record.page === "number" &&
    typeof record.pageSize === "number" &&
    typeof record.totalCount === "number"
  );
}

export function isDeleteDatasetPreparationBoardFileApiResponse(
  value: unknown
): value is DeleteDatasetPreparationBoardFileApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;

  return (
    typeof record.preparationName === "string" &&
    typeof record.sourceName === "string" &&
    typeof record.boardFolderName === "string" &&
    typeof record.deleted === "boolean" &&
    typeof record.remainingItemsCount === "number"
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
      "Backend zwrocil niepoprawny ksztalt DatasetPreparationApiResponse.",
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
      "Backend zwrocil niepoprawny ksztalt DatasetPreparationsListApiResponse.",
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
      "Backend zwrocil niepoprawny ksztalt DatasetPreparationApiResponse.",
    errorFactory: (message, status, errorType) =>
      new DatasetPreparationsApiError(message, status, errorType),
  });
}

export async function getDatasetPreparationFolders(
  apiBaseUrl: string,
  preparationName: string,
  folderType: DatasetPreparationFolderType,
  accessToken?: string | null,
  signal?: AbortSignal
): Promise<DatasetPreparationFoldersApiResponse> {
  const encodedPreparationName = encodeURIComponent(preparationName);

  return fetchJson<
    DatasetPreparationFoldersApiResponse,
    DatasetPreparationsApiError
  >({
    url: `${apiBaseUrl}/datasets/preparations/${encodedPreparationName}/${folderType}/folders`,
    init: {
      method: "GET",
      headers: {
        Accept: "application/json",
        ...buildAuthHeaders(accessToken),
      },
      signal,
    },
    expectedStatus: 200,
    validateResponse: isDatasetPreparationFoldersApiResponse,
    invalidResponseMessage:
      "Backend zwrocil niepoprawny ksztalt DatasetPreparationFoldersApiResponse.",
    errorFactory: (message, status, errorType) =>
      new DatasetPreparationsApiError(message, status, errorType),
  });
}

export async function getDatasetPreparationBoardFiles(
  apiBaseUrl: string,
  params: {
    preparationName: string;
    sourceName: string;
    page: number;
    pageSize: number;
  },
  accessToken?: string | null,
  signal?: AbortSignal
): Promise<DatasetPreparationBoardFilesApiResponse> {
  const encodedPreparationName = encodeURIComponent(params.preparationName);
  const encodedSourceName = encodeURIComponent(params.sourceName);
  const query = new URLSearchParams({
    page: String(params.page),
    pageSize: String(params.pageSize),
  });

  return fetchJson<
    DatasetPreparationBoardFilesApiResponse,
    DatasetPreparationsApiError
  >({
    url: `${apiBaseUrl}/datasets/preparations/${encodedPreparationName}/board/${encodedSourceName}/files?${query.toString()}`,
    init: {
      method: "GET",
      headers: {
        Accept: "application/json",
        ...buildAuthHeaders(accessToken),
      },
      signal,
    },
    expectedStatus: 200,
    validateResponse: isDatasetPreparationBoardFilesApiResponse,
    invalidResponseMessage:
      "Backend zwrocil niepoprawny ksztalt DatasetPreparationBoardFilesApiResponse.",
    errorFactory: (message, status, errorType) =>
      new DatasetPreparationsApiError(message, status, errorType),
  });
}

export async function getDatasetPreparationBoardImageByEndpoint(
  apiBaseUrl: string,
  imageEndpoint: string,
  accessToken?: string | null,
  signal?: AbortSignal
): Promise<ImageApiResponse> {
  const url = resolveUc18BoardImageRequestUrl(apiBaseUrl, imageEndpoint);

  return fetchJson<ImageApiResponse, DatasetPreparationsApiError>({
    url,
    init: {
      method: "GET",
      headers: {
        Accept: "application/json",
        ...buildAuthHeaders(accessToken),
      },
      signal,
    },
    expectedStatus: 200,
    validateResponse: isImageApiResponse,
    invalidResponseMessage:
      "Backend zwrocil niepoprawny ksztalt ImageApiResponse dla preview planszy.",
    errorFactory: (message, status, errorType) =>
      new DatasetPreparationsApiError(message, status, errorType),
  });
}

export async function deleteDatasetPreparationBoardFile(
  apiBaseUrl: string,
  params: {
    preparationName: string;
    sourceName: string;
    boardFolderName: string;
  },
  accessToken?: string | null,
  signal?: AbortSignal
): Promise<DeleteDatasetPreparationBoardFileApiResponse> {
  const encodedPreparationName = encodeURIComponent(params.preparationName);
  const encodedSourceName = encodeURIComponent(params.sourceName);
  const encodedBoardFolderName = encodeURIComponent(params.boardFolderName);

  return fetchJson<
    DeleteDatasetPreparationBoardFileApiResponse,
    DatasetPreparationsApiError
  >({
    url: `${apiBaseUrl}/datasets/preparations/${encodedPreparationName}/board/${encodedSourceName}/files/${encodedBoardFolderName}`,
    init: {
      method: "DELETE",
      headers: {
        Accept: "application/json",
        ...buildAuthHeaders(accessToken),
      },
      signal,
    },
    expectedStatus: 200,
    validateResponse: isDeleteDatasetPreparationBoardFileApiResponse,
    invalidResponseMessage:
      "Backend zwrocil niepoprawny ksztalt DeleteDatasetPreparationBoardFileApiResponse.",
    errorFactory: (message, status, errorType) =>
      new DatasetPreparationsApiError(message, status, errorType),
  });
}
