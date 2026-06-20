import type { UseUc19BoardFoldersSelectionResult } from "../application/uc19BoardFoldersSelectionTypes";
import { Uc19BoardSourceSplitList } from "./Uc19BoardSourceSplitList";

type Uc19BoardFoldersSelectionSectionProps = {
  selectedPreparationName: string | null;
  canLoadBoardFolders: boolean;
  boardFolders: UseUc19BoardFoldersSelectionResult;
};

export function Uc19BoardFoldersSelectionSection({
  selectedPreparationName,
  canLoadBoardFolders,
  boardFolders,
}: Uc19BoardFoldersSelectionSectionProps) {
  return (
    <article className="uc17-panel">
      <div className="uc17-panel-header">
        <div>
          <h3>Krok 3 - Zrodla plansz do budowy datasetu</h3>
          <p className="muted-copy">
            Ten krok pobiera tylko logiczne nazwy folderow plansz, bez listowania
            plansz i bez przechodzenia do kroku przegladu oraz usuwania wadliwych
            danych z `UC-18`.
          </p>
        </div>
        <button
          className="secondary-button"
          type="button"
          onClick={() => void boardFolders.retryLoadBoardFolders()}
          disabled={!canLoadBoardFolders || boardFolders.status === "loading"}
        >
          {boardFolders.status === "loading"
            ? "Odswiezanie..."
            : "Odswiez liste zrodel plansz"}
        </button>
      </div>

      {!selectedPreparationName ? (
        <p className="muted-copy">
          Najpierw wybierz przygotowanie datasetu, aby odblokowac konfiguracje
          zrodel plansz.
        </p>
      ) : null}

      {selectedPreparationName && !canLoadBoardFolders ? (
        <p className="status-banner status-loading">
          Krok zrodel plansz pozostaje zablokowany, dopoki wybrane przygotowanie
          nie przejdzie walidacji w kroku 2.
        </p>
      ) : null}

      {boardFolders.status === "loading" ? (
        <p className="status-banner status-loading">
          Pobieranie zrodel plansz dla przygotowania{" "}
          <code>{boardFolders.preparationName ?? selectedPreparationName}</code>...
        </p>
      ) : null}

      {boardFolders.status === "error" ? (
        <>
          <p className="status-banner status-error">{boardFolders.error}</p>
          {boardFolders.httpStatus === 401 ? (
            <p className="muted-copy">
              Sesja administracyjna zostala wyczyszczona. Zaloguj sie ponownie.
            </p>
          ) : null}
          {boardFolders.httpStatus === 404 ? (
            <p className="muted-copy">
              Wybrane przygotowanie nie jest juz dostepne. Odswiez liste i wybierz
              inny rekord.
            </p>
          ) : null}
        </>
      ) : null}

      {boardFolders.preparationName ? (
        <div className="uc18-summary">
          <span className="uc17-stat-chip">
            Przygotowanie: <code>{boardFolders.preparationName}</code>
          </span>
          <span className="uc17-stat-chip">Liczba zrodel plansz: {boardFolders.totalCount}</span>
          <span className="uc17-stat-chip">Wybrane zrodla: {boardFolders.selectedCount}</span>
          <span className="uc17-stat-chip">
            Niepoprawne wybory: {boardFolders.invalidSelectedCount}
          </span>
        </div>
      ) : null}

      {boardFolders.selectedCount > 0 && boardFolders.invalidSelectedCount > 0 ? (
        <p className="status-banner status-error">
          Co najmniej jedno aktywne zrodlo plansz ma niepoprawna konfiguracje splitow.
        </p>
      ) : null}

      {boardFolders.status === "success" && boardFolders.totalCount === 0 ? (
        <p className="status-banner status-loading">
          To przygotowanie nie ma jeszcze zadnych zrodel plansz.
        </p>
      ) : null}

      {(boardFolders.status === "success" ||
        boardFolders.status === "loading" ||
        boardFolders.status === "error") &&
      boardFolders.drafts.length > 0 ? (
        <Uc19BoardSourceSplitList
          drafts={boardFolders.drafts}
          validationByKey={boardFolders.validationByKey}
          disabled={boardFolders.status === "loading"}
          onToggleEnabled={boardFolders.toggleBoardSourceEnabled}
          onToggleSplit={boardFolders.toggleBoardSourceSplit}
        />
      ) : null}

      {boardFolders.selectedCount === 0 && boardFolders.drafts.length > 0 ? (
        <p className="muted-copy">
          Zaznacz wybrane foldery plansz, aby przygotowac ich mapowanie do
          <code> sources[].name</code> i lokalnych splitow.
        </p>
      ) : null}
    </article>
  );
}
