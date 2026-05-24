import type { ErrorApiResponse } from "../../types/api";

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

export function tryParseJson(raw: string): unknown {
  if (!raw.trim()) {
    return null;
  }

  try {
    return JSON.parse(raw) as unknown;
  } catch {
    return null;
  }
}

export function buildAuthHeaders(accessToken?: string | null): HeadersInit {
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

export function buildErrorFromResponse(
  rawBody: string,
  status: number,
): TrainingsApiError {
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
