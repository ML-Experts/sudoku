import type {
  ErrorApiResponse,
  RawDatasetCandidateApiResponse,
} from "../types/api";

export class RawDatasetCandidatesApiError extends Error {
  readonly status: number;
  readonly errorType: string | undefined;

  constructor(message: string, status: number, errorType?: string) {
    super(message);
    this.name = "RawDatasetCandidatesApiError";
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

function buildErrorFromResponse(
  rawBody: string,
  status: number
): RawDatasetCandidatesApiError {
  const parsed = tryParseJson(rawBody);

  if (isErrorApiResponse(parsed)) {
    return new RawDatasetCandidatesApiError(
      parsed.message,
      status,
      parsed.errorType
    );
  }

  return new RawDatasetCandidatesApiError(
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
