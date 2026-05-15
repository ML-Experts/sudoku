import { useEffect } from "react";

import type { CellsGridApiResponse } from "../../../types/api";
import { Uc05GridWorkspace } from "./Uc05GridWorkspace";
import { Uc05aRecognitionPanel } from "../../uc05a/api";
import { useUc05aRecognition } from "../../uc05a/application/useUc05aRecognition";
import { Uc05bSolveSection } from "../../uc05b/api/Uc05bSolveSection";
import { useUc05bSolve } from "../../uc05b/application/useUc05bSolve";
import { Uc05eLiveSolvePanel } from "../../uc05e/api/Uc05eLiveSolvePanel";
import { useUc05eLiveSolve } from "../../uc05e/application/useUc05eLiveSolve";

type Uc05WorkflowSectionProps = {
  apiBaseUrl: string;
  cellsGrid: CellsGridApiResponse | null;
  selectedProcessName: string | null;
};

export function Uc05WorkflowSection({
  apiBaseUrl,
  cellsGrid,
  selectedProcessName,
}: Uc05WorkflowSectionProps) {
  const recognition = useUc05aRecognition({
    apiBaseUrl,
    cellsGrid,
  });
  const solve = useUc05bSolve({
    apiBaseUrl,
    recognizedGrid: recognition.state.recognizedGrid,
    recognitionStatus: recognition.state.status,
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

      <Uc05bSolveSection
        state={solve.state}
        gridReadiness={solve.gridReadiness}
        canStartSolve={solve.canStartSolve}
        canRecoverActiveSolve={solve.canRecoverActiveSolve}
        canCancelSolve={solve.canCancelSolve}
        canResumeLiveMonitoring={liveSolve.hasLiveSessionToResume}
        onStartSolve={solve.startSolve}
        onRecoverActiveSolve={solve.recoverActiveSolve}
        onCancelSolve={solve.cancelSolve}
        onResumeLiveMonitoring={liveSolve.retryMonitoring}
        liveState={liveSolve.state}
      />

      <Uc05eLiveSolvePanel
        state={liveSolve.state}
        canRetryMonitoring={liveSolve.hasLiveSessionToResume}
        onRetryMonitoring={liveSolve.retryMonitoring}
      />
    </section>
  );
}
