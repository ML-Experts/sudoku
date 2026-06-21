import type { SudokuCellInferenceParametersApiEntry } from "../../../types/api";
import type { SolveCellInferenceContextState } from "./solveCellInferenceParameterDefinitions";
import { validateUc14ContextState } from "./validateUc14ContextState";

export class Uc14LocalParametersValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "Uc14LocalParametersValidationError";
  }
}

export function toSudokuCellInferenceParametersApiEntry(
  contextState: SolveCellInferenceContextState,
): SudokuCellInferenceParametersApiEntry {
  const validation = validateUc14ContextState(contextState);
  if (!validation.isValid) {
    throw new Uc14LocalParametersValidationError(
      "Parametry inferencji komorki zawieraja bledy walidacji lokalnej.",
    );
  }

  const thresholdField = contextState.emptyCellDarkPixelRatioThreshold;
  const marginField = contextState.emptyCellInnerMarginRatio;
  const centerAreaField = contextState.centerAreaRatio;
  const minComponentAreaField = contextState.minComponentAreaRatio;
  const lineArtifactMinSpanField = contextState.lineArtifactMinSpanRatio;
  const lineArtifactMaxThicknessField = contextState.lineArtifactMaxThicknessRatio;
  const minSegmentLengthField = contextState.emptyCellMinSegmentLengthPx;
  const filteredSegmentCountThresholdField =
    contextState.emptyCellFilteredSegmentCountThreshold;

  if (thresholdField.parsedValue === null) {
    throw new Uc14LocalParametersValidationError(
      "Brakuje poprawnej wartosci emptyCellDarkPixelRatioThreshold.",
    );
  }

  if (marginField.parsedValue === null) {
    throw new Uc14LocalParametersValidationError(
      "Brakuje poprawnej wartosci emptyCellInnerMarginRatio.",
    );
  }

  if (centerAreaField.parsedValue === null) {
    throw new Uc14LocalParametersValidationError(
      "Brakuje poprawnej wartosci centerAreaRatio.",
    );
  }

  if (minComponentAreaField.parsedValue === null) {
    throw new Uc14LocalParametersValidationError(
      "Brakuje poprawnej wartosci minComponentAreaRatio.",
    );
  }

  if (lineArtifactMinSpanField.parsedValue === null) {
    throw new Uc14LocalParametersValidationError(
      "Brakuje poprawnej wartosci lineArtifactMinSpanRatio.",
    );
  }

  if (lineArtifactMaxThicknessField.parsedValue === null) {
    throw new Uc14LocalParametersValidationError(
      "Brakuje poprawnej wartosci lineArtifactMaxThicknessRatio.",
    );
  }

  if (minSegmentLengthField.parsedValue === null) {
    throw new Uc14LocalParametersValidationError(
      "Brakuje poprawnej wartosci emptyCellMinSegmentLengthPx.",
    );
  }

  if (filteredSegmentCountThresholdField.parsedValue === null) {
    throw new Uc14LocalParametersValidationError(
      "Brakuje poprawnej wartosci emptyCellFilteredSegmentCountThreshold.",
    );
  }

  return {
    emptyCellDarkPixelRatioThreshold: thresholdField.parsedValue,
    emptyCellInnerMarginRatio: marginField.parsedValue,
    centerAreaRatio: centerAreaField.parsedValue,
    minComponentAreaRatio: minComponentAreaField.parsedValue,
    lineArtifactMinSpanRatio: lineArtifactMinSpanField.parsedValue,
    lineArtifactMaxThicknessRatio: lineArtifactMaxThicknessField.parsedValue,
    emptyCellMinSegmentLengthPx: minSegmentLengthField.parsedValue,
    emptyCellFilteredSegmentCountThreshold:
      filteredSegmentCountThresholdField.parsedValue,
  };
}
