import type { UseUc18DigitFoldersResult } from "../application/uc18DigitFoldersTypes";
import { Uc18PreparationFoldersList } from "./Uc18PreparationFoldersList";

type Uc18DigitFoldersPanelProps = {
  preparationName: string | null;
  digitFolders: UseUc18DigitFoldersResult;
};

export function Uc18DigitFoldersPanel({
  preparationName,
  digitFolders,
}: Uc18DigitFoldersPanelProps) {
  return (
    <article className="uc17-panel">
      <div className="uc17-panel-header">
        <div>
          <h3>Krok 5 - Zrodla `digit`</h3>
          <p className="muted-copy">
            Ten panel ma charakter informacyjny. Backend zwraca liste logicznych zrodel
            `digit`, ale ten krok nie prowadzi do osobnego preview ani usuwania probek.
          </p>
        </div>
        <button
          className="secondary-button"
          type="button"
          onClick={() => void digitFolders.retryLoadDigitFolders()}
          disabled={!preparationName || digitFolders.status === "loading"}
        >
          {digitFolders.status === "loading"
            ? "Odswiezanie..."
            : "Odswiez liste digit"}
        </button>
      </div>

      {!preparationName ? (
        <p className="muted-copy">
          Najpierw wybierz preparation. Lista zrodel `digit` nie jest pobierana bez
          poprawnego <code>preparationName</code>.
        </p>
      ) : null}

      {digitFolders.status === "loading" ? (
        <p className="status-banner status-loading">
          Pobieranie zrodel `digit` dla preparation <code>{preparationName}</code>...
        </p>
      ) : null}

      {digitFolders.status === "error" ? (
        <>
          <p className="status-banner status-error">{digitFolders.error}</p>
          {digitFolders.httpStatus === 401 ? (
            <p className="muted-copy">
              Sesja administracyjna zostala wyczyszczona. Zaloguj sie ponownie.
            </p>
          ) : null}
          {digitFolders.httpStatus === 404 ? (
            <p className="muted-copy">
              Wybrane preparation nie jest juz dostepne. Wybierz inny rekord z listy.
            </p>
          ) : null}
        </>
      ) : null}

      {digitFolders.preparationName ? (
        <div className="uc18-summary">
          <span className="uc17-stat-chip">
            Preparation: <code>{digitFolders.preparationName}</code>
          </span>
          <span className="uc17-stat-chip">Liczba zrodel digit: {digitFolders.totalCount}</span>
          <span className="uc17-stat-chip">Tryb: tylko odczyt</span>
        </div>
      ) : null}

      {digitFolders.status === "success" && digitFolders.totalCount === 0 ? (
        <p className="status-banner status-loading">
          To preparation nie ma jeszcze zadnych zrodel `digit`.
        </p>
      ) : null}

      {(digitFolders.status === "success" ||
        digitFolders.status === "loading" ||
        digitFolders.status === "error") &&
      digitFolders.folders.length > 0 ? (
        <Uc18PreparationFoldersList
          mode="readonly"
          folders={digitFolders.folders}
          emptyMessage="Brak zrodel `digit` dla wybranego preparation."
          itemHint="Zrodlo digit nalezace do wybranego preparation."
        />
      ) : null}
    </article>
  );
}
