import type { RecognitionSessionState } from "../application/recognitionSessionTypes";
import type { RecognitionProgress } from "../domain/recognitionProgress";
import { RecognitionProgressPanel } from "./RecognitionProgressPanel";

type Uc05aRecognitionPanelProps = {
  selectedProcessName: string | null;
  cellsGridAvailable: boolean;
  parameterOverrideCount: number;
  parametersValid: boolean;
  parameterErrorCount: number;
  state: RecognitionSessionState;
  progress: RecognitionProgress;
  canStartRecognition: boolean;
  canRetryRecognition: boolean;
  canCancelRecognition: boolean;
  onStartRecognition: () => void | Promise<void>;
  onRetryRecognition: () => void | Promise<void>;
  onCancelRecognition: () => void;
};

export function Uc05aRecognitionPanel({
  selectedProcessName,
  cellsGridAvailable,
  parameterOverrideCount,
  parametersValid,
  parameterErrorCount,
  state,
  progress,
  canStartRecognition,
  canRetryRecognition,
  canCancelRecognition,
  onStartRecognition,
  onRetryRecognition,
  onCancelRecognition,
}: Uc05aRecognitionPanelProps) {
  const startButtonLabel =
    state.status === "running"
      ? "Trwa rozpoznawanie..."
      : state.status === "completed" ||
          state.status === "failed" ||
          state.status === "cancelled"
        ? "Start od nowa"
        : "Start rozpoznania";

  return (
    <section className="result-card uc05a-section" aria-live="polite">
      <p className="eyebrow">UC-05A — Rozpoznanie pojedynczych komorek</p>
      <h2>Inferencja 81 komorek i budowa recognizedGrid</h2>
      <p className="muted-copy">
        Frontend buduje lokalny `recognizedGrid` na podstawie siatki z `UC-04`
        i wysyla pojedyncze komorki do <code>PUT /api/sudoku/cells/inference</code>.
      </p>

      <p className="muted-copy">
        {parameterOverrideCount > 0
          ? `Biezace rozpoznanie wysle ${parameterOverrideCount} aktywne override'y z panelu UC-14.`
          : "Biezace rozpoznanie wysle domyslny snapshot parametrow UC-14."}
      </p>

      {selectedProcessName ? (
        <p className="muted-copy">
          Aktywny przyklad: <code>{selectedProcessName}</code>
        </p>
      ) : null}

      {!cellsGridAvailable ? (
        <p className="status-banner status-loading">
          Najpierw zakoncz `UC-04`, aby uzyskac siatke komorek 9x9.
        </p>
      ) : null}

      {!parametersValid ? (
        <p className="status-banner status-error">
          Panel parametrow zawiera {parameterErrorCount} bledy. Popraw je, zanim
          uruchomisz rozpoznanie.
        </p>
      ) : null}

      <div className="examples-row-actions">
        <button
          className="primary-button"
          type="button"
          disabled={!canStartRecognition}
          onClick={() => void onStartRecognition()}
        >
          {startButtonLabel}
        </button>
        <button
          className="secondary-button"
          type="button"
          disabled={!canRetryRecognition}
          onClick={() => void onRetryRecognition()}
        >
          Retry
        </button>
        <button
          className="secondary-button"
          type="button"
          disabled={!canCancelRecognition}
          onClick={onCancelRecognition}
        >
          Anuluj
        </button>
      </div>

      <RecognitionProgressPanel state={state} progress={progress} />
    </section>
  );
}
