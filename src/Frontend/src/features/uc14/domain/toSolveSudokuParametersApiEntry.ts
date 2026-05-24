import type { SolveSudokuParametersApiEntry } from "../../../types/api";
import type { SolveLiveContextState } from "./solveLiveParameterDefinitions";
import { Uc14LocalParametersValidationError } from "./toSudokuCellInferenceParametersApiEntry";
import { validateUc14ContextState } from "./validateUc14ContextState";

export function toSolveSudokuParametersApiEntry(
  contextState: SolveLiveContextState,
): SolveSudokuParametersApiEntry {
  const validation = validateUc14ContextState(contextState);
  if (!validation.isValid) {
    throw new Uc14LocalParametersValidationError(
      "Parametry live solve zawieraja bledy walidacji lokalnej.",
    );
  }

  const solverStepDelayField = contextState.solverStepDelayMs;
  if (solverStepDelayField.parsedValue === null) {
    throw new Uc14LocalParametersValidationError(
      "Brakuje poprawnej wartosci solverStepDelayMs.",
    );
  }

  return {
    solverStepDelayMs: solverStepDelayField.parsedValue,
  };
}
