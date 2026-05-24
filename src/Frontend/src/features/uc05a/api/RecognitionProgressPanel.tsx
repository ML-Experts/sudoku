import type {
  RecognitionSessionState,
} from "../application/recognitionSessionTypes";
import type { RecognitionProgress } from "../domain/recognitionProgress";

type RecognitionProgressPanelProps = {
  state: RecognitionSessionState;
  progress: RecognitionProgress;
};

function getStatusLabel(status: RecognitionSessionState["status"]): string {
  switch (status) {
    case "idle":
      return "Oczekiwanie na start rozpoznania";
    case "running":
      return "Trwa rozpoznawanie komorek";
    case "completed":
      return "Rozpoznanie zakonczone";
    case "failed":
      return "Rozpoznanie zakonczone bledem";
    case "cancelled":
      return "Rozpoznanie anulowane";
    default:
      return "Nieznany status";
  }
}

export function RecognitionProgressPanel({
  state,
  progress,
}: RecognitionProgressPanelProps) {
  return (
    <article className="uc05a-panel">
      <h3>Postep rozpoznania</h3>
      <p className="muted-copy">{getStatusLabel(state.status)}</p>

      <div className="uc05a-progress-bar" aria-hidden="true">
        <span
          className="uc05a-progress-bar-fill"
          style={{ width: `${progress.percent}%` }}
        />
      </div>

      <dl className="uc05a-progress-stats">
        <div>
          <dt>Ukonczone</dt>
          <dd>
            {progress.completedCount} / {progress.totalCount}
          </dd>
        </div>
        <div>
          <dt>Rozpoznane cyfry</dt>
          <dd>{progress.recognizedCount}</dd>
        </div>
        <div>
          <dt>Puste pola</dt>
          <dd>{progress.emptyCount}</dd>
        </div>
        <div>
          <dt>Oczekujace</dt>
          <dd>{progress.pendingCount}</dd>
        </div>
      </dl>

      {state.failedCell ? (
        <p className="muted-copy">
          Problem wystapil dla komorki {state.failedCell.rowIndex + 1}-
          {state.failedCell.columnIndex + 1}.
        </p>
      ) : null}

      {state.error ? (
        <>
          <p className="status-banner status-error">{state.error.message}</p>
          <p className="muted-copy">
            HTTP: {state.error.httpStatus ?? "-"}, typ bledu:{" "}
            {state.error.errorType ?? "-"}.
          </p>
        </>
      ) : null}

      {state.status === "completed" ? (
        <p className="status-banner status-success">
          Rozpoznanie zakonczone. Ten sam grid jest gotowy do dalszych krokow
          `UC-05`.
        </p>
      ) : null}
    </article>
  );
}
