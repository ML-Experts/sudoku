import type { CellsGridApiResponse } from "../../../types/api";
import { useUc05aRecognition } from "../application/useUc05aRecognition";
import { RecognitionProgressPanel } from "./RecognitionProgressPanel";
import { RecognizedGridView } from "./RecognizedGridView";

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
    <section className="result-card uc05a-section" aria-live="polite">
      <p className="eyebrow">UC-05A — Rozpoznanie pojedynczych komorek</p>
      <h2>Inferencja 81 komorek i budowa recognizedGrid</h2>
      <p className="muted-copy">
        Frontend buduje lokalny `recognizedGrid` na podstawie siatki z `UC-04`
        i wysyla pojedyncze komorki do <code>PUT /api/sudoku/cells/inference</code>.
      </p>

      {selectedProcessName ? (
        <p className="muted-copy">
          Aktywny przyklad: <code>{selectedProcessName}</code>
        </p>
      ) : null}

      {!cellsGrid ? (
        <p className="status-banner status-loading">
          Najpierw zakoncz `UC-04`, aby uzyskac siatke komorek 9x9.
        </p>
      ) : null}

      <div className="examples-row-actions">
        <button
          className="primary-button"
          type="button"
          disabled={!canStartRecognition}
          onClick={() => void startRecognition()}
        >
          {state.status === "running" ? "Trwa rozpoznawanie..." : "Start rozpoznania"}
        </button>
        <button
          className="secondary-button"
          type="button"
          disabled={!canRetryRecognition}
          onClick={() => void retryRecognition()}
        >
          Retry
        </button>
        <button
          className="secondary-button"
          type="button"
          disabled={!canCancelRecognition}
          onClick={cancelRecognition}
        >
          Anuluj
        </button>
      </div>

      <div className="uc05a-layout">
        <RecognitionProgressPanel state={state} progress={progress} />
        <RecognizedGridView recognizedGrid={state.recognizedGrid} />
      </div>
    </section>
  );
}
