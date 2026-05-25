import { fetchJson, JsonApiError } from "./shared/fetchJson";
import type {
  ImageApiResponse,
  RenderSudokuOverlayCellApiEntry,
} from "../types/api";

export class SudokuOverlayCellApiError extends JsonApiError {
  constructor(message: string, status: number, errorType?: string) {
    super(message, status, errorType);
    this.name = "SudokuOverlayCellApiError";
  }
}

function isImageApiResponse(value: unknown): value is ImageApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;

  return (
    typeof record.mimeType === "string" && typeof record.base64 === "string"
  );
}

export async function postSudokuOverlayCell(
  apiBaseUrl: string,
  entry: RenderSudokuOverlayCellApiEntry,
  signal?: AbortSignal,
): Promise<ImageApiResponse> {
  return fetchJson({
    url: `${apiBaseUrl}/sudoku/overlay/cells`,
    init: {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(entry),
      signal,
    },
    expectedStatus: 200,
    validateResponse: isImageApiResponse,
    invalidResponseMessage:
      "Backend zwrocil niepoprawny ksztalt ImageApiResponse dla overlay komorki.",
    errorFactory: (message, status, errorType) =>
      new SudokuOverlayCellApiError(message, status, errorType),
  });
}
