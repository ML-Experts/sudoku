import { fetchJson, JsonApiError } from "./shared/fetchJson";
import type {
  DigitInferenceApiResponse,
  ImageApiEntry,
} from "../types/api";

export class SudokuCellInferenceApiError extends JsonApiError {
  constructor(message: string, status: number, errorType?: string) {
    super(message, status, errorType);
    this.name = "SudokuCellInferenceApiError";
  }
}

function isDigitInferenceApiResponse(
  value: unknown,
): value is DigitInferenceApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;

  return (
    record.digit === null ||
    (typeof record.digit === "number" &&
      Number.isInteger(record.digit) &&
      record.digit >= 1 &&
      record.digit <= 9)
  );
}

export async function putSudokuCellInference(
  apiBaseUrl: string,
  entry: ImageApiEntry,
  signal?: AbortSignal,
): Promise<DigitInferenceApiResponse> {
  return fetchJson({
    url: `${apiBaseUrl}/sudoku/cells/inference`,
    init: {
      method: "PUT",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(entry),
      signal,
    },
    expectedStatus: 200,
    validateResponse: isDigitInferenceApiResponse,
    invalidResponseMessage:
      "Backend zwrocil niepoprawny ksztalt DigitInferenceApiResponse.",
    errorFactory: (message, status, errorType) =>
      new SudokuCellInferenceApiError(message, status, errorType),
  });
}
