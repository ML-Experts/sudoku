import type { RecognizedGrid } from "../domain/recognizedGrid";

type RecognizedGridViewProps = {
  recognizedGrid: RecognizedGrid | null;
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
}: RecognizedGridViewProps) {
  if (!recognizedGrid) {
    return (
      <article className="uc05a-panel">
        <h3>Rozpoznany grid 9x9</h3>
        <p className="muted-copy">
          Po starcie `UC-05A` tutaj pojawi sie lokalny `recognizedGrid`.
        </p>
      </article>
    );
  }

  return (
    <article className="uc05a-panel">
      <h3>Rozpoznany grid 9x9</h3>
      <div className="uc05a-grid" role="grid" aria-label="Rozpoznany grid sudoku">
        {recognizedGrid.flatMap((row) =>
          row.map((cell) => (
            <div
              key={`${cell.rowIndex}-${cell.columnIndex}`}
              className={`uc05a-grid-cell is-${cell.source}`}
              role="gridcell"
              aria-label={`Komorka ${cell.rowIndex + 1}-${cell.columnIndex + 1}`}
            >
              <span>{renderCellValue(cell.digit, cell.source)}</span>
            </div>
          )),
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
      </div>
    </article>
  );
}
