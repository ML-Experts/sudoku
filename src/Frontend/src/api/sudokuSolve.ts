import { fetchJson, isErrorApiResponse, JsonApiError } from "./shared/fetchJson";
import type {
  CancelSolveSessionApiResponse,
  SolveSessionApiResponse,
  SolveSudokuApiEntry,
} from "../types/api";

export class SudokuSolveApiError extends JsonApiError {
  constructor(message: string, status: number, errorType?: string) {
    super(message, status, errorType);
    this.name = "SudokuSolveApiError";
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

function isSolveSessionStatus(value: unknown): value is SolveSessionApiResponse["status"] {
  return (
    value === "queued" ||
    value === "running" ||
    value === "cancelling" ||
    value === "completed" ||
    value === "failed" ||
    value === "cancelled"
  );
}

function isSolveSessionApiResponse(value: unknown): value is SolveSessionApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;

  return (
    typeof record.solveSessionId === "string" &&
    isSolveSessionStatus(record.status) &&
    typeof record.progressChannelUrl === "string"
  );
}

function isCancelSolveSessionApiResponse(
  value: unknown,
): value is CancelSolveSessionApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;

  return (
    (record.status === null || isSolveSessionStatus(record.status)) &&
    typeof record.requestDisposition === "string"
  );
}

function buildError(rawBody: string, status: number): SudokuSolveApiError {
  const parsedBody = tryParseJson(rawBody);

  if (isErrorApiResponse(parsedBody)) {
    return new SudokuSolveApiError(
      parsedBody.message,
      status,
      parsedBody.errorType,
    );
  }

  return new SudokuSolveApiError(
    rawBody.trim()
      ? `Backend zwrocil odpowiedz HTTP ${status}.`
      : `Backend zwrocil odpowiedz HTTP ${status} bez tresci.`,
    status,
  );
}

export async function postStartSudokuSolve(
  apiBaseUrl: string,
  entry: SolveSudokuApiEntry,
  signal?: AbortSignal,
): Promise<SolveSessionApiResponse> {
  return fetchJson({
    url: `${apiBaseUrl}/sudoku/solve`,
    init: {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(entry),
      signal,
    },
    expectedStatus: 202,
    validateResponse: isSolveSessionApiResponse,
    invalidResponseMessage:
      "Backend zwrocil niepoprawny ksztalt SolveSessionApiResponse.",
    errorFactory: (message, status, errorType) =>
      new SudokuSolveApiError(message, status, errorType),
  });
}

export async function getActiveSudokuSolveSession(
  apiBaseUrl: string,
  signal?: AbortSignal,
): Promise<SolveSessionApiResponse | null> {
  const response = await fetch(`${apiBaseUrl}/sudoku/solve/active`, {
    method: "GET",
    headers: {
      Accept: "application/json",
    },
    signal,
  });

  if (response.status === 204) {
    return null;
  }

  const rawBody = await response.text();
  const parsedBody = tryParseJson(rawBody);

  if (response.status === 200) {
    if (!isSolveSessionApiResponse(parsedBody)) {
      throw new Error(
        "Backend zwrocil niepoprawny ksztalt SolveSessionApiResponse.",
      );
    }

    return parsedBody;
  }

  throw buildError(rawBody, response.status);
}

export async function postCancelSudokuSolve(
  apiBaseUrl: string,
  solveSessionId: string,
  signal?: AbortSignal,
): Promise<CancelSolveSessionApiResponse> {
  return fetchJson({
    url: `${apiBaseUrl}/sudoku/solve/${encodeURIComponent(solveSessionId)}/cancel`,
    init: {
      method: "POST",
      headers: {
        Accept: "application/json",
      },
      signal,
    },
    expectedStatus: 202,
    validateResponse: isCancelSolveSessionApiResponse,
    invalidResponseMessage:
      "Backend zwrocil niepoprawny ksztalt CancelSolveSessionApiResponse.",
    errorFactory: (message, status, errorType) =>
      new SudokuSolveApiError(message, status, errorType),
  });
}
