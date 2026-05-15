import type { SolveLiveState } from "../application/solveLiveTypes";

type Uc05eLiveSolvePanelProps = {
  state: SolveLiveState;
  canRetryMonitoring: boolean;
  onRetryMonitoring: () => void | Promise<void>;
};

function getConnectionCopy(connectionState: SolveLiveState["connectionState"]): string {
  switch (connectionState) {
    case "connecting":
      return "Trwa laczenie z kanalem SignalR.";
    case "connected":
      return "Kanal SignalR jest aktywny i przyjmuje snapshoty.";
    case "reconnecting":
      return "Polaczenie zostalo utracone i trwa reconnect.";
    case "completed":
      return "Monitoring zakonczyl sie terminalnym eventem.";
    case "failed":
      return "Monitoring zakonczyl sie bledem technicznym.";
    default:
      return "Monitoring live solve nie jest aktywny.";
  }
}

export function Uc05eLiveSolvePanel({
  state,
  canRetryMonitoring,
  onRetryMonitoring,
}: Uc05eLiveSolvePanelProps) {
  return (
    <section className="result-card uc05e-live-panel" aria-live="polite">
      <p className="eyebrow">UC-05E — Monitoring live solve</p>
      <h2>SignalR `/ws/sudoku/solving/{"{solveSessionId}"}`</h2>
      <p className="muted-copy">
        Panel pokazuje transport realtime dla snapshotow solvera, sequence,
        reconnect i stany terminalne `completed`, `failed`, `cancelled`.
      </p>

      <div className="uc05e-live-panel-grid">
        <div className="uc05e-live-card">
          <span>Stan polaczenia</span>
          <strong>{state.connectionState}</strong>
          <p className="muted-copy">{getConnectionCopy(state.connectionState)}</p>
        </div>
        <div className="uc05e-live-card">
          <span>Aktywna sesja</span>
          <strong>{state.activeSolveSessionId ?? "-"}</strong>
          <p className="muted-copy">Publiczny identyfikator sesji live solve.</p>
        </div>
        <div className="uc05e-live-card">
          <span>lastAcceptedSequence</span>
          <strong>{state.lastAcceptedSequence >= 0 ? state.lastAcceptedSequence : "-"}</strong>
          <p className="muted-copy">Eventy starsze albo zduplikowane sa ignorowane.</p>
        </div>
        <div className="uc05e-live-card">
          <span>Zmienione pola</span>
          <strong>{state.changedCells.length}</strong>
          <p className="muted-copy">Diff jest liczony lokalnie z pelnych snapshotow.</p>
        </div>
      </div>

      <div className="examples-row-actions">
        <button
          className="secondary-button"
          type="button"
          disabled={!canRetryMonitoring}
          onClick={() => void onRetryMonitoring()}
        >
          Wznow live monitoring
        </button>
      </div>

      {state.lastEvent ? (
        <p className="status-banner status-loading">
          Ostatni event: <code>{state.lastEvent.eventType}</code>, status:{" "}
          <code>{state.lastEvent.status}</code>, sequence:{" "}
          <code>{state.lastEvent.sequence}</code>.
        </p>
      ) : null}

      {state.degradedReason ? (
        <p className="status-banner status-warning">{state.degradedReason}</p>
      ) : null}

      {state.terminalEventType === "completed" ? (
        <p className="status-banner status-success">
          Solver zakonczyl live solve sukcesem.
        </p>
      ) : null}

      {state.terminalEventType === "cancelled" ? (
        <p className="status-banner status-warning">
          Sesja live solve zostala anulowana.
        </p>
      ) : null}

      {state.terminalEventType === "failed" ? (
        <p className="status-banner status-error">
          Sesja live solve zakonczona eventem `failed`.
        </p>
      ) : null}

      {state.error ? (
        <p className="status-banner status-error">{state.error.message}</p>
      ) : null}
    </section>
  );
}
