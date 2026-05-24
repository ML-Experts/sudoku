import type { ErrorApiResponse } from "../../types/api";

export class JsonApiError extends Error {
  readonly status: number;
  readonly errorType: string | undefined;

  constructor(message: string, status: number, errorType?: string) {
    super(message);
    this.name = "JsonApiError";
    this.status = status;
    this.errorType = errorType;
  }
}

type FetchJsonOptions<TResponse, TError extends JsonApiError> = {
  url: string;
  init?: RequestInit;
  expectedStatus: number | number[];
  validateResponse: (value: unknown) => value is TResponse;
  invalidResponseMessage: string;
  errorFactory: (message: string, status: number, errorType?: string) => TError;
};

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

export function isErrorApiResponse(value: unknown): value is ErrorApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;

  return (
    typeof record.errorType === "string" && typeof record.message === "string"
  );
}

function isExpectedStatus(
  actualStatus: number,
  expectedStatus: number | number[],
): boolean {
  return Array.isArray(expectedStatus)
    ? expectedStatus.includes(actualStatus)
    : actualStatus === expectedStatus;
}

export async function fetchJson<TResponse, TError extends JsonApiError>({
  url,
  init,
  expectedStatus,
  validateResponse,
  invalidResponseMessage,
  errorFactory,
}: FetchJsonOptions<TResponse, TError>): Promise<TResponse> {
  const response = await fetch(url, init);
  const rawBody = await response.text();
  const parsedBody = tryParseJson(rawBody);

  if (isExpectedStatus(response.status, expectedStatus)) {
    if (!validateResponse(parsedBody)) {
      throw new Error(invalidResponseMessage);
    }

    return parsedBody;
  }

  if (isErrorApiResponse(parsedBody)) {
    throw errorFactory(
      parsedBody.message,
      response.status,
      parsedBody.errorType,
    );
  }

  throw errorFactory(
    rawBody.trim()
      ? `Backend zwrocil odpowiedz HTTP ${response.status}.`
      : `Backend zwrocil odpowiedz HTTP ${response.status} bez tresci.`,
    response.status,
  );
}
