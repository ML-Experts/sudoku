import { fetchJson, JsonApiError } from "./shared/fetchJson";
import type {
  DigitInferenceApiEntry,
  DigitInferenceApiResponse,
  ImageApiEntry,
  SudokuCellInferenceParametersApiEntry,
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

const DEFAULT_DIGIT_INFERENCE_ENTRY: Omit<DigitInferenceApiEntry, "image"> = {
  emptyCellDarkPixelRatioThreshold: 0.02,
  emptyCellInnerMarginRatio: 0.12,
  centerAreaRatio: 0.5,
  minComponentAreaRatio: 0.055,
  lineArtifactMinSpanRatio: 0.4,
  lineArtifactMaxThicknessRatio: 0.08,
  emptyCellMinSegmentLengthPx: 8,
  emptyCellFilteredSegmentCountThreshold: 2,
};

export async function putSudokuCellInference(
  apiBaseUrl: string,
  entry: ImageApiEntry,
  parameters?: SudokuCellInferenceParametersApiEntry | null,
  signal?: AbortSignal,
): Promise<DigitInferenceApiResponse> {
  const request: DigitInferenceApiEntry = {
    image: entry,
    ...DEFAULT_DIGIT_INFERENCE_ENTRY,
    ...parameters,
  };

  return fetchJson({
    url: `${apiBaseUrl}/sudoku/cells/inference`,
    init: {
      method: "PUT",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
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
