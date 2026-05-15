import type { CellsGridApiResponse } from "../../../types/api";
import { useUc05aRecognition } from "../application/useUc05aRecognition";
import { Uc05aRecognitionPanel } from "./Uc05aRecognitionPanel";

type Uc05aRecognitionSectionProps = {
  apiBaseUrl: string;
  cellsGrid: CellsGridApiResponse | null;
  selectedProcessName: string | null;
};

export function Uc05aRecognitionSection({
  apiBaseUrl,
  cellsGrid,
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
  });

  return (
    <Uc05aRecognitionPanel
      selectedProcessName={selectedProcessName}
      cellsGridAvailable={cellsGrid !== null}
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
