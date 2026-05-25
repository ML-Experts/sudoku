import type { OverlaySessionState } from "../application/overlaySessionTypes";
import type { OverlayProgress } from "../domain/overlayProgress";

type OverlayProgressPanelProps = {
  state: OverlaySessionState;
  progress: OverlayProgress;
};

export function OverlayProgressPanel({
  state,
  progress,
}: OverlayProgressPanelProps) {
  const isZeroTargetCompleted =
    state.status === "completed" && progress.targetCount === 0;

  return (
    <section className="uc05d-progress-panel" aria-live="polite">
      <div className="uc05d-progress-header">
        <div>
          <h3>Postep renderowania overlay</h3>
          <p className="muted-copy">
            Sekwencyjny render per-komorka aktualizuje preview planszy po kazdej
            odpowiedzi.
          </p>
        </div>
        <span className="uc05d-progress-badge">
          {state.status === "running"
            ? "sesja aktywna"
            : state.status === "completed"
              ? "sesja zakonczona"
              : state.status === "failed"
                ? "sesja z bledem"
                : state.status === "cancelled"
                  ? "sesja anulowana"
                  : "oczekiwanie"}
        </span>
      </div>

      <div className="uc05d-progress-bar" aria-hidden="true">
        <span
          className="uc05d-progress-bar-fill"
          style={{
            width: `${isZeroTargetCompleted ? 100 : progress.percent}%`,
          }}
        />
      </div>

      <dl className="uc05d-progress-stats">
        <div>
          <dt>completedCount</dt>
          <dd>{progress.completedCount}</dd>
        </div>
        <div>
          <dt>targetCount</dt>
          <dd>{progress.targetCount}</dd>
        </div>
        <div>
          <dt>remainingCount</dt>
          <dd>{progress.remainingCount}</dd>
        </div>
        <div>
          <dt>Procent</dt>
          <dd>{isZeroTargetCompleted ? 100 : progress.percent}%</dd>
        </div>
      </dl>
    </section>
  );
}
