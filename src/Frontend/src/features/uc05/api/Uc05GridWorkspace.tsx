import { RecognizedGridView } from "../../uc05a/api/RecognizedGridView";
import type { RecognizedGrid } from "../../uc05a/domain/recognizedGrid";
import type { SolveLiveState } from "../../uc05e/application/solveLiveTypes";
import type { ChangedSolveCell } from "../../uc05e/domain/diffRecognizedGridChanges";

type Uc05GridWorkspaceProps = {
  visibleGrid: RecognizedGrid | null;
  changedCells: ChangedSolveCell[];
  liveState: SolveLiveState;
};

function getWorkspaceBadge(
  liveState: SolveLiveState,
): { label: string; tone: "neutral" | "running" | "success" | "warning" | "error" } {
  if (liveState.terminalEventType === "completed") {
    return {
      label: "solve zakonczony sukcesem",
      tone: "success",
    };
  }

  if (liveState.terminalEventType === "failed") {
    return {
      label: "solve zakonczony bledem",
      tone: "error",
    };
  }

  if (liveState.terminalEventType === "cancelled") {
    return {
      label: "solve anulowany",
      tone: "warning",
    };
  }

  if (liveState.connectionState === "connected") {
    return {
      label: "live solve aktywny",
      tone: "running",
    };
  }

  if (liveState.connectionState === "reconnecting") {
    return {
      label: "reconnect live solve",
      tone: "warning",
    };
  }

  return {
    label: "grid roboczy UC-05",
    tone: "neutral",
  };
}

export function Uc05GridWorkspace({
  visibleGrid,
  changedCells,
  liveState,
}: Uc05GridWorkspaceProps) {
  const statusBadge = getWorkspaceBadge(liveState);

  return (
    <section className="result-card uc05-grid-workspace">
      <p className="eyebrow">UC-05C / UC-05E — Wspolny grid roboczy</p>
      <h2>Jeden widoczny grid dla rozpoznania i live solve</h2>
      <p className="muted-copy">
        Ten panel pokazuje ten sam `RecognizedGrid` w calym workflow: po `UC-05A`
        jako wynik rozpoznania, a po starcie solve jako kolejne snapshoty
        `currentGrid` z `SignalR`.
      </p>

      <div className="uc05-grid-workspace-meta">
        <div className="uc05-grid-workspace-chip">
          <span>SignalR</span>
          <strong>{liveState.connectionState}</strong>
        </div>
        <div className="uc05-grid-workspace-chip">
          <span>lastAcceptedSequence</span>
          <strong>{liveState.lastAcceptedSequence >= 0 ? liveState.lastAcceptedSequence : "-"}</strong>
        </div>
        <div className="uc05-grid-workspace-chip">
          <span>zmienione pola</span>
          <strong>{changedCells.length}</strong>
        </div>
      </div>

      <RecognizedGridView
        recognizedGrid={visibleGrid}
        title="Grid roboczy 9x9"
        mode="live-solve"
        highlightedCells={changedCells}
        statusBadge={statusBadge}
      />

      {liveState.lastEvent ? (
        <p className="muted-copy">
          Ostatni event: <code>{liveState.lastEvent.eventType}</code>, status:{" "}
          <code>{liveState.lastEvent.status}</code>, sequence:{" "}
          <code>{liveState.lastEvent.sequence}</code>.
        </p>
      ) : null}
    </section>
  );
}
