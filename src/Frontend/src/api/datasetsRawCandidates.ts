import type {
  RawDatasetCandidateApiResponse,
} from "../types/api";
import {
  fetchJson,
  JsonApiError,
} from "./shared/fetchJson";

export class RawDatasetCandidatesApiError extends JsonApiError {}

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

export async function getRawDatasetCandidates(
  apiBaseUrl: string,
  accessToken?: string | null,
  signal?: AbortSignal
): Promise<RawDatasetCandidateApiResponse[]> {
  return fetchJson<
    RawDatasetCandidateApiResponse[],
    RawDatasetCandidatesApiError
  >({
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
    validateResponse: (
      value
    ): value is RawDatasetCandidateApiResponse[] =>
      Array.isArray(value) && value.every(isRawDatasetCandidateApiResponse),
    invalidResponseMessage:
      "Backend zwrócił niepoprawny kształt RawDatasetCandidateApiResponse[].",
    errorFactory: (message, status, errorType) =>
      new RawDatasetCandidatesApiError(message, status, errorType),
  });
}
