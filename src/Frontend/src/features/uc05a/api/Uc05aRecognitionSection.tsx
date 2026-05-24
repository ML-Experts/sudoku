import type {
  CellsGridApiResponse,
  SudokuCellInferenceParametersApiEntry,
} from "../../../types/api";
import { useUc05aRecognition } from "../application/useUc05aRecognition";
import { Uc05aRecognitionPanel } from "./Uc05aRecognitionPanel";

type Uc05aRecognitionSectionProps = {
  apiBaseUrl: string;
  cellsGrid: CellsGridApiResponse | null;
  inferenceParameters?: SudokuCellInferenceParametersApiEntry | null;
  inferenceParametersValid?: boolean;
  inferenceParameterErrorCount?: number;
  inferenceParameterOverrideCount?: number;
  selectedProcessName: string | null;
};

export function Uc05aRecognitionSection({
  apiBaseUrl,
  cellsGrid,
  inferenceParameters = null,
  inferenceParametersValid = true,
  inferenceParameterErrorCount = 0,
  inferenceParameterOverrideCount = 0,
  selectedProcessName,
}: Uc05aRecognitionSectionProps) {
  const {
    state,
    progress,
    startRecognition,
    cancelRecognition,
    retryRecognition,
    canStartRecognition,
    canRetryRecognition,
    canCancelRecognition,
  } = useUc05aRecognition({
    apiBaseUrl,
    cellsGrid,
    inferenceParameters,
    isInferenceParametersValid: inferenceParametersValid,
  });

  return (
    <Uc05aRecognitionPanel
      selectedProcessName={selectedProcessName}
      cellsGridAvailable={cellsGrid !== null}
      parameterOverrideCount={inferenceParameterOverrideCount}
      parametersValid={inferenceParametersValid}
      parameterErrorCount={inferenceParameterErrorCount}
      state={state}
      progress={progress}
      canStartRecognition={canStartRecognition}
      canRetryRecognition={canRetryRecognition}
      canCancelRecognition={canCancelRecognition}
      onStartRecognition={startRecognition}
      onRetryRecognition={retryRecognition}
      onCancelRecognition={cancelRecognition}
    />
  );
}
