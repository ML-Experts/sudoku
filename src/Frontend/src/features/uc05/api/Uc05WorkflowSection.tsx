import { useEffect } from "react";

import type {
  CellsGridApiResponse,
  SolveSudokuParametersApiEntry,
  SudokuCellInferenceParametersApiEntry,
} from "../../../types/api";
import { Uc05GridWorkspace } from "./Uc05GridWorkspace";
import { Uc05aRecognitionPanel } from "../../uc05a/api";
import { useUc05aRecognition } from "../../uc05a/application/useUc05aRecognition";
import { Uc05bSolveSection } from "../../uc05b/api/Uc05bSolveSection";
import { useUc05bSolve } from "../../uc05b/application/useUc05bSolve";
import { Uc05eLiveSolvePanel } from "../../uc05e/api/Uc05eLiveSolvePanel";
import { useUc05eLiveSolve } from "../../uc05e/application/useUc05eLiveSolve";
import type { Uc14ActiveParameterContext } from "../../uc14/domain/uc14ParameterContext";

type Uc05WorkflowSectionProps = {
  apiBaseUrl: string;
  cellsGrid: CellsGridApiResponse | null;
  selectedProcessName: string | null;
  solveCellInferenceParameters: SudokuCellInferenceParametersApiEntry | null;
  solveCellInferenceParametersValid: boolean;
  solveCellInferenceParameterErrorCount: number;
  solveCellInferenceOverrideCount: number;
  solveLiveParameters: SolveSudokuParametersApiEntry | null;
  solveLiveParametersValid: boolean;
  solveLiveParameterErrorCount: number;
  solveLiveOverrideCount: number;
  onParameterContextChange?: (context: Uc14ActiveParameterContext) => void;
};

export function Uc05WorkflowSection({
  apiBaseUrl,
  cellsGrid,
  selectedProcessName,
  solveCellInferenceParameters,
  solveCellInferenceParametersValid,
  solveCellInferenceParameterErrorCount,
  solveCellInferenceOverrideCount,
  solveLiveParameters,
  solveLiveParametersValid,
  solveLiveParameterErrorCount,
  solveLiveOverrideCount,
  onParameterContextChange,
}: Uc05WorkflowSectionProps) {
  const recognition = useUc05aRecognition({
    apiBaseUrl,
    cellsGrid,
    inferenceParameters: solveCellInferenceParameters,
    isInferenceParametersValid: solveCellInferenceParametersValid,
  });
  const solve = useUc05bSolve({
    apiBaseUrl,
    recognizedGrid: recognition.state.recognizedGrid,
    recognitionStatus: recognition.state.status,
    solveParameters: solveLiveParameters,
    isSolveParametersValid: solveLiveParametersValid,
  });
  const liveSolve = useUc05eLiveSolve({
    apiBaseUrl,
    recognizedGrid: recognition.state.recognizedGrid,
    solveSession: solve.state.session,
    recoverActiveSolve: solve.recoverActiveSolveDetailed,
  });

  useEffect(() => {
    if (!liveSolve.state.terminalEventType) {
      return;
    }

    solve.acceptTerminalLiveEvent(liveSolve.state.terminalEventType);
  }, [liveSolve.state.terminalEventType, solve.acceptTerminalLiveEvent]);

  const activeParameterContext: Uc14ActiveParameterContext =
    solve.state.session !== null ||
    liveSolve.hasLiveSessionToResume ||
    recognition.state.status === "completed"
      ? "solveLive"
      : cellsGrid !== null
        ? "solveCellInference"
        : null;

  useEffect(() => {
    onParameterContextChange?.(activeParameterContext);
  }, [activeParameterContext, onParameterContextChange]);

  const shouldShowSolveSection =
    recognition.state.status === "completed" ||
    solve.state.session !== null ||
    liveSolve.hasLiveSessionToResume;
  const shouldShowLivePanel =
    solve.state.session !== null || liveSolve.hasLiveSessionToResume;

  return (
    <section className="uc05-workflow-section">
      <section className="hero-card uc05-workflow-header">
        <p className="eyebrow">UC-05 — Rozpoznaj i rozwiaz sudoku</p>
        <h2>Wspolny workflow `recognizedGrid` do sesji solve</h2>
        <p className="hero-copy">
          `UC-05A` buduje kanoniczny `recognizedGrid`, a `UC-05B` wykorzystuje go
          bez tworzenia drugiego modelu planszy ani drugiego widoku 9x9.
        </p>
      </section>

      <Uc05aRecognitionPanel
        selectedProcessName={selectedProcessName}
        cellsGridAvailable={cellsGrid !== null}
        parameterOverrideCount={solveCellInferenceOverrideCount}
        parametersValid={solveCellInferenceParametersValid}
        parameterErrorCount={solveCellInferenceParameterErrorCount}
        state={recognition.state}
        progress={recognition.progress}
        canStartRecognition={recognition.canStartRecognition}
        canRetryRecognition={recognition.canRetryRecognition}
        canCancelRecognition={recognition.canCancelRecognition}
        onStartRecognition={recognition.startRecognition}
        onRetryRecognition={recognition.retryRecognition}
        onCancelRecognition={recognition.cancelRecognition}
      />

      <Uc05GridWorkspace
        visibleGrid={liveSolve.visibleGrid}
        changedCells={liveSolve.state.changedCells}
        liveState={liveSolve.state}
      />

      {shouldShowSolveSection ? (
        <Uc05bSolveSection
          state={solve.state}
          gridReadiness={solve.gridReadiness}
          canStartSolve={solve.canStartSolve}
          canRecoverActiveSolve={solve.canRecoverActiveSolve}
          canCancelSolve={solve.canCancelSolve}
          canResumeLiveMonitoring={liveSolve.hasLiveSessionToResume}
          solveParameterOverrideCount={solveLiveOverrideCount}
          solveParametersValid={solveLiveParametersValid}
          solveParameterErrorCount={solveLiveParameterErrorCount}
          onStartSolve={solve.startSolve}
          onRecoverActiveSolve={solve.recoverActiveSolve}
          onCancelSolve={solve.cancelSolve}
          onResumeLiveMonitoring={liveSolve.retryMonitoring}
          liveState={liveSolve.state}
        />
      ) : null}

      {shouldShowLivePanel ? (
        <Uc05eLiveSolvePanel
          state={liveSolve.state}
          canRetryMonitoring={liveSolve.hasLiveSessionToResume}
          onRetryMonitoring={liveSolve.retryMonitoring}
        />
      ) : null}
    </section>
  );
}
