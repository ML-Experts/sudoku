import type { SolveSessionState } from "../application/solveSessionTypes";
import type { SolveLiveState } from "../../uc05e/application/solveLiveTypes";
import { SolveSessionStatusPanel } from "./SolveSessionStatusPanel";

type Uc05bSolveSectionProps = {
  state: SolveSessionState;
  gridReadiness: {
    isReady: boolean;
    message: string;
  };
  canStartSolve: boolean;
  canRecoverActiveSolve: boolean;
  canCancelSolve: boolean;
  canResumeLiveMonitoring: boolean;
  onStartSolve: () => void | Promise<void>;
  onRecoverActiveSolve: () => void | Promise<void>;
  onCancelSolve: () => void | Promise<void>;
  onResumeLiveMonitoring: () => void | Promise<void>;
  liveState: SolveLiveState;
};

export function Uc05bSolveSection({
  state,
  gridReadiness,
  canStartSolve,
  canRecoverActiveSolve,
  canCancelSolve,
  canResumeLiveMonitoring,
  onStartSolve,
  onRecoverActiveSolve,
  onCancelSolve,
  onResumeLiveMonitoring,
  liveState,
}: Uc05bSolveSectionProps) {
  return (
    <section className="result-card uc05b-section" aria-live="polite">
      <p className="eyebrow">UC-05B — Start i monitoring sesji solve</p>
      <h2>Backendowy workflow rozwiazywania sudoku</h2>
      <p className="muted-copy">
        Ten panel reuse'uje dokladnie ten sam `recognizedGrid` z `UC-05A` i
        komunikuje sie tylko z backendem przez:
        <code> POST /api/sudoku/solve</code>,
        <code> GET /api/sudoku/solve/active</code> oraz
        <code> POST /api/sudoku/solve/{"{solveSessionId}"}/cancel</code>.
      </p>

      <p
        className={`status-banner ${
          gridReadiness.isReady ? "status-success" : "status-loading"
        }`}
      >
        {gridReadiness.message}
      </p>

      <div className="examples-row-actions">
        <button
          className="primary-button"
          type="button"
          disabled={!canStartSolve}
          onClick={() => void onStartSolve()}
        >
          {state.phase === "starting" ? "Uruchamianie solve..." : "Start solve"}
        </button>
        <button
          className="secondary-button"
          type="button"
          disabled={!canRecoverActiveSolve}
          onClick={() => void onRecoverActiveSolve()}
        >
          {state.phase === "recovering"
            ? "Odzyskiwanie sesji..."
            : "Odzyskaj aktywna sesje"}
        </button>
        <button
          className="secondary-button"
          type="button"
          disabled={!canCancelSolve}
          onClick={() => void onCancelSolve()}
        >
          {state.phase === "cancelling" ? "Anulowanie..." : "Anuluj solve"}
        </button>
        <button
          className="secondary-button"
          type="button"
          disabled={!canResumeLiveMonitoring}
          onClick={() => void onResumeLiveMonitoring()}
        >
          Wznow live monitoring
        </button>
      </div>

      {state.phase === "cancelling" || state.session?.status === "cancelling" ? (
        <p className="muted-copy">
          HTTP <code>202 Accepted</code> potwierdza tylko przyjecie komendy cancel.
          Finalny stan <code>cancelled</code> powinien przyjsc asynchronicznie przez
          live monitoring.
        </p>
      ) : null}

      <SolveSessionStatusPanel
        state={state}
        gridReadinessMessage={gridReadiness.message}
        liveState={liveState}
      />
    </section>
  );
}
