import type { SolveSessionState } from "../application/solveSessionTypes";
import type { SolveLiveState } from "../../uc05e/application/solveLiveTypes";

type SolveSessionStatusPanelProps = {
  state: SolveSessionState;
  gridReadinessMessage: string;
  liveState: SolveLiveState;
};

function getPhaseLabel(state: SolveSessionState): string {
  if (
    state.phase === "active" &&
    state.session &&
    (state.session.status === "completed" ||
      state.session.status === "failed" ||
      state.session.status === "cancelled")
  ) {
    return "Sesja solve jest juz w stanie terminalnym";
  }

  const { phase } = state;
  switch (phase) {
    case "idle":
      return "Brak aktywnej sesji solve";
    case "starting":
      return "Trwa uruchamianie sesji solve";
    case "recovering":
      return "Trwa odzyskiwanie aktywnej sesji solve";
    case "active":
      return "Aktywna sesja solve jest monitorowana";
    case "cancelling":
      return "Trwa anulowanie aktywnej sesji solve";
    case "error":
      return "Ostatnia operacja solve zakonczona bledem";
    default:
      return "Nieznany stan sesji solve";
  }
}

export function SolveSessionStatusPanel({
  state,
  gridReadinessMessage,
  liveState,
}: SolveSessionStatusPanelProps) {
  return (
    <article className="uc05a-panel uc05b-status-panel">
      <h3>Status sesji solve</h3>
      <p className="muted-copy">{getPhaseLabel(state)}</p>
      <p className="muted-copy">{gridReadinessMessage}</p>

      {state.session ? (
        <dl className="result-grid">
          <div>
            <dt>solveSessionId</dt>
            <dd>{state.session.solveSessionId}</dd>
          </div>
          <div>
            <dt>Status backendu</dt>
            <dd>{state.session.status}</dd>
          </div>
          <div>
            <dt>progressChannelUrl</dt>
            <dd>{state.session.progressChannelUrl}</dd>
          </div>
          <div>
            <dt>Stala wobec biezacego gridu</dt>
            <dd>{state.session.isSessionStaleForCurrentGrid ? "tak" : "nie"}</dd>
          </div>
          <div>
            <dt>Realtime</dt>
            <dd>{liveState.connectionState}</dd>
          </div>
          <div>
            <dt>lastAcceptedSequence</dt>
            <dd>{liveState.lastAcceptedSequence >= 0 ? liveState.lastAcceptedSequence : "-"}</dd>
          </div>
        </dl>
      ) : (
        <p className="muted-copy">
          Po starcie albo recovery tutaj pojawia sie publiczny identyfikator sesji.
        </p>
      )}

      {state.session?.isSessionStaleForCurrentGrid ? (
        <p className="status-banner status-warning">
          Aktywna sesja solve zostala uruchomiona dla starszego stanu planszy.
          Nie nadpisujemy nia cicho aktualnego `recognizedGrid`.
        </p>
      ) : null}

      {state.session &&
      (state.session.status === "completed" ||
        state.session.status === "failed" ||
        state.session.status === "cancelled") ? (
        <p className="status-banner status-warning">
          Ostatnia znana sesja solve ma stan <code>{state.session.status}</code>.
          Mozesz uruchomic nowa sesje dla aktualnego gridu.
        </p>
      ) : null}

      {state.cancelDisposition ? (
        <p className="status-banner status-loading">
          Ostatni wynik cancel: <code>{state.cancelDisposition}</code>.
        </p>
      ) : null}

      {liveState.degradedReason ? (
        <p className="status-banner status-warning">{liveState.degradedReason}</p>
      ) : null}

      {liveState.terminalEventType ? (
        <p
          className={`status-banner ${
            liveState.terminalEventType === "completed"
              ? "status-success"
              : liveState.terminalEventType === "cancelled"
                ? "status-warning"
                : "status-error"
          }`}
        >
          Ostatni terminalny event live solve: <code>{liveState.terminalEventType}</code>.
        </p>
      ) : null}

      {state.error ? (
        <>
          <p className="status-banner status-error">{state.error.message}</p>
          <p className="muted-copy">
            Operacja: {state.error.operation}, HTTP: {state.error.httpStatus ?? "-"},
            typ bledu: {state.error.errorType ?? "-"}.
          </p>
        </>
      ) : null}
    </article>
  );
}
