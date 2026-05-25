import type { CellsGridApiResponse } from "../../../types/api";
import type { RecognizedGrid } from "../../uc05a/domain/recognizedGrid";
import type { TerminalSolveProgressEventType } from "../../uc05e/domain/isSolveProgressEventTerminal";
import { useUc05dOverlay } from "../application/useUc05dOverlay";
import { OverlayImagePreview } from "./OverlayImagePreview";
import { OverlayProgressPanel } from "./OverlayProgressPanel";

type Uc05dOverlaySectionProps = {
  apiBaseUrl: string;
  cellsGrid: CellsGridApiResponse | null;
  inputGrid: RecognizedGrid | null;
  solvedGrid: RecognizedGrid | null;
  terminalEventType: TerminalSolveProgressEventType | null;
  degradedReason: string | null;
};

function toStatusBannerClassName(
  tone: "success" | "warning" | "loading" | "error",
): string {
  switch (tone) {
    case "success":
      return "status-banner status-success";
    case "warning":
      return "status-banner status-warning";
    case "error":
      return "status-banner status-error";
    default:
      return "status-banner status-loading";
  }
}

export function Uc05dOverlaySection({
  apiBaseUrl,
  cellsGrid,
  inputGrid,
  solvedGrid,
  terminalEventType,
  degradedReason,
}: Uc05dOverlaySectionProps) {
  const overlay = useUc05dOverlay({
    apiBaseUrl,
    cellsGrid,
    inputGrid,
    solvedGrid,
    terminalEventType,
    degradedReason,
  });

  return (
    <section className="result-card uc05d-section" aria-live="polite">
      <p className="eyebrow">UC-05D — Graficzny overlay rozwiazania</p>
      <h2>Render per-komorka przez `POST /api/sudoku/overlay/cells`</h2>
      <p className="muted-copy">
        Panel reuse&apos;uje obrazy komorek z `UC-04` oraz `inputGrid` i finalny
        `visibleGrid` z `UC-05E`, a nastepnie sklada lokalnie finalna plansze 9x9.
      </p>

      <p className={toStatusBannerClassName(overlay.availability.tone)}>
        {overlay.availability.message}
      </p>

      {overlay.availability.targetCount !== null ? (
        <p className="muted-copy">
          Targety overlay: <code>{overlay.availability.targetCount}</code>.
        </p>
      ) : null}

      <div className="examples-row-actions">
        <button
          className="primary-button"
          type="button"
          disabled={!overlay.canStartOverlay}
          onClick={() => void overlay.startOverlayRender()}
        >
          {overlay.state.status === "running"
            ? "Trwa generowanie overlay..."
            : "Start overlay"}
        </button>
        <button
          className="secondary-button"
          type="button"
          disabled={!overlay.canRetryOverlay}
          onClick={() => void overlay.retryOverlayRender()}
        >
          Retry
        </button>
        <button
          className="secondary-button"
          type="button"
          disabled={!overlay.canCancelOverlay}
          onClick={overlay.cancelOverlayRender}
        >
          Anuluj
        </button>
      </div>

      {overlay.availability.canGenerate || overlay.state.status !== "idle" ? (
        <OverlayProgressPanel
          state={overlay.state}
          progress={overlay.progress}
        />
      ) : null}

      {overlay.state.status === "completed" ? (
        <p className="status-banner status-success">
          Overlay zostal wygenerowany i nie zastapil tekstowego wyniku solve jako
          zrodla prawdy.
        </p>
      ) : null}

      {overlay.state.error ? (
        <p className="status-banner status-error">{overlay.state.error.message}</p>
      ) : null}

      {overlay.state.failedTarget ? (
        <p className="muted-copy">
          Blad dotyczy komorki <code>{overlay.state.failedTarget.rowIndex + 1}</code>
          -
          <code>{overlay.state.failedTarget.columnIndex + 1}</code>.
        </p>
      ) : null}

      {overlay.availability.canGenerate || overlay.state.previewUrl !== null ? (
        <OverlayImagePreview
          previewUrl={overlay.state.previewUrl}
          status={overlay.state.status}
        />
      ) : null}
    </section>
  );
}
