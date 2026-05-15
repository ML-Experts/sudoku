import type { RecognizedGrid } from "../domain/recognizedGrid";

type GridHighlight = {
  rowIndex: number;
  columnIndex: number;
  changeType?: "placed" | "removed" | "updated";
};

type GridStatusBadge = {
  label: string;
  tone?: "neutral" | "running" | "success" | "warning" | "error";
};

type RecognizedGridViewProps = {
  recognizedGrid: RecognizedGrid | null;
  title?: string;
  mode?: "recognition" | "live-solve";
  highlightedCells?: GridHighlight[];
  statusBadge?: GridStatusBadge | null;
};

function renderCellValue(
  digit: number | null,
  source: "pending" | "recognized" | "error",
): string {
  if (source === "pending") {
    return "…";
  }

  if (source === "error") {
    return "!";
  }

  if (digit === null) {
    return "·";
  }

  return String(digit);
}

export function RecognizedGridView({
  recognizedGrid,
  title = "Rozpoznany grid 9x9",
  mode = "recognition",
  highlightedCells = [],
  statusBadge = null,
}: RecognizedGridViewProps) {
  const highlightedCellMap = new Map(
    highlightedCells.map((cell) => [
      `${cell.rowIndex}-${cell.columnIndex}`,
      cell.changeType ?? "updated",
    ]),
  );

  if (!recognizedGrid) {
    return (
      <article className="uc05a-panel">
        <h3>{title}</h3>
        <p className="muted-copy">
          Po starcie `UC-05A` tutaj pojawi sie lokalny `recognizedGrid`.
        </p>
      </article>
    );
  }

  return (
    <article className="uc05a-panel">
      <div className="uc05a-grid-header">
        <h3>{title}</h3>
        {statusBadge ? (
          <span
            className={`uc05a-grid-badge ${
              statusBadge.tone ? `is-${statusBadge.tone}` : ""
            }`}
          >
            {statusBadge.label}
          </span>
        ) : null}
      </div>
      <div className="uc05a-grid" role="grid" aria-label="Rozpoznany grid sudoku">
        {recognizedGrid.flatMap((row) =>
          row.map((cell) => {
            const highlightKey = `${cell.rowIndex}-${cell.columnIndex}`;
            const highlightType = highlightedCellMap.get(highlightKey);

            return (
              <div
                key={highlightKey}
                className={`uc05a-grid-cell is-${cell.source} ${
                  cell.isLocked ? "is-locked" : ""
                } ${cell.isEditable ? "is-editable" : ""} ${
                  highlightType ? "is-highlighted" : ""
                } ${highlightType ? `is-change-${highlightType}` : ""} ${
                  mode === "live-solve" ? "is-live-solve" : ""
                }`}
                role="gridcell"
                aria-label={`Komorka ${cell.rowIndex + 1}-${cell.columnIndex + 1}`}
              >
                <span>{renderCellValue(cell.digit, cell.source)}</span>
              </div>
            );
          }),
        )}
      </div>
      <div className="uc05a-grid-legend">
        <span>
          <strong>…</strong> oczekuje
        </span>
        <span>
          <strong>·</strong> pusta komorka
        </span>
        <span>
          <strong>!</strong> blad techniczny
        </span>
        <span>
          <strong>ciemne</strong> pole wejsciowe solvera
        </span>
        <span>
          <strong>jasne</strong> pole robocze solvera
        </span>
        {mode === "live-solve" ? (
          <>
            <span>
              <strong>blysk</strong> nowa cyfra solvera
            </span>
            <span>
              <strong>obrys</strong> cofniecie albo korekta solvera
            </span>
          </>
        ) : null}
      </div>
    </article>
  );
}
