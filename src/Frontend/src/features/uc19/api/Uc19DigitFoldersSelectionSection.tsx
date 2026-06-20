import type { UseUc19DigitFoldersSelectionResult } from "../application/uc19DigitFoldersSelectionTypes";
import { Uc19DigitSourceSplitList } from "./Uc19DigitSourceSplitList";

type Uc19DigitFoldersSelectionSectionProps = {
  selectedPreparationName: string | null;
  canLoadDigitFolders: boolean;
  digitFolders: UseUc19DigitFoldersSelectionResult;
};

export function Uc19DigitFoldersSelectionSection({
  selectedPreparationName,
  canLoadDigitFolders,
  digitFolders,
}: Uc19DigitFoldersSelectionSectionProps) {
  return (
    <article className="uc17-panel">
      <div className="uc17-panel-header">
        <div>
          <h3>Krok 4 - Zrodla `digit` do builda</h3>
          <p className="muted-copy">
            Ten krok pobiera tylko logiczne nazwy folderow `digit` i pozwala
            przypisac im lokalne splity do finalnego builda `.npz`.
          </p>
        </div>
        <button
          className="secondary-button"
          type="button"
          onClick={() => void digitFolders.retryLoadDigitFolders()}
          disabled={!canLoadDigitFolders || digitFolders.status === "loading"}
        >
          {digitFolders.status === "loading" ? "Odswiezanie..." : "Odswiez liste digit"}
        </button>
      </div>

      {!selectedPreparationName ? (
        <p className="muted-copy">
          Najpierw wybierz preparation, aby odblokowac konfiguracje zrodel `digit`.
        </p>
      ) : null}

      {selectedPreparationName && !canLoadDigitFolders ? (
        <p className="status-banner status-loading">
          Krok `digit/folders` pozostaje zablokowany, dopoki wybrane preparation nie
          przejdzie walidacji w kroku 2.
        </p>
      ) : null}

      {digitFolders.status === "loading" ? (
        <p className="status-banner status-loading">
          Pobieranie zrodel `digit` dla preparation{" "}
          <code>{digitFolders.preparationName ?? selectedPreparationName}</code>...
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
              Wybrane preparation nie jest juz dostepne. Odswiez liste i wybierz inny
              rekord.
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
          <span className="uc17-stat-chip">Wybrane zrodla: {digitFolders.selectedCount}</span>
          <span className="uc17-stat-chip">
            Niepoprawne wybory: {digitFolders.invalidSelectedCount}
          </span>
        </div>
      ) : null}

      {digitFolders.selectedCount > 0 && digitFolders.invalidSelectedCount > 0 ? (
        <p className="status-banner status-error">
          Co najmniej jedno aktywne zrodlo `digit` ma niepoprawna konfiguracje splitow.
        </p>
      ) : null}

      {digitFolders.status === "success" && digitFolders.totalCount === 0 ? (
        <p className="status-banner status-loading">
          To preparation nie ma jeszcze zadnych zrodel `digit`.
        </p>
      ) : null}

      {(digitFolders.status === "success" ||
        digitFolders.status === "loading" ||
        digitFolders.status === "error") &&
      digitFolders.drafts.length > 0 ? (
        <Uc19DigitSourceSplitList
          drafts={digitFolders.drafts}
          validationByKey={digitFolders.validationByKey}
          disabled={digitFolders.status === "loading"}
          onToggleEnabled={digitFolders.toggleDigitSourceEnabled}
          onToggleSplit={digitFolders.toggleDigitSourceSplit}
        />
      ) : null}

      {digitFolders.selectedCount === 0 && digitFolders.drafts.length > 0 ? (
        <p className="muted-copy">
          Zaznacz wybrane foldery `digit`, aby przygotowac ich mapowanie do
          <code> sources[].name</code> i lokalnych splitow.
        </p>
      ) : null}
    </article>
  );
}
