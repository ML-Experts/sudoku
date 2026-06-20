import { useEffect, useRef } from "react";

import { getDatasetPreparationStatusPresentation } from "../../../shared/datasets/getDatasetPreparationStatusPresentation";
import { useUc17DatasetPreparations } from "../../uc17/application/useUc17DatasetPreparations";
import { useUc18BoardFiles } from "../application/useUc18BoardFiles";
import { useUc18BoardFolders } from "../application/useUc18BoardFolders";
import { useUc18DigitFolders } from "../application/useUc18DigitFolders";
import { Uc18BoardFilesPanel } from "./Uc18BoardFilesPanel";
import { Uc18DigitFoldersPanel } from "./Uc18DigitFoldersPanel";
import { Uc18PreparationFoldersList } from "./Uc18PreparationFoldersList";

type Uc18BoardFoldersSectionProps = {
  apiBaseUrl: string;
  accessToken?: string | null;
  onUnauthorized?: () => void;
  preferredPreparationName?: string | null;
};

function formatTimestamp(timestampUtc: string): string {
  const parsedDate = new Date(timestampUtc);

  if (Number.isNaN(parsedDate.getTime())) {
    return timestampUtc;
  }

  return new Intl.DateTimeFormat("pl-PL", {
    dateStyle: "medium",
    timeStyle: "medium",
    timeZone: "UTC",
  }).format(parsedDate);
}

export function Uc18BoardFoldersSection({
  apiBaseUrl,
  accessToken,
  onUnauthorized,
  preferredPreparationName,
}: Uc18BoardFoldersSectionProps) {
  const datasetPreparations = useUc17DatasetPreparations({
    apiBaseUrl,
    accessToken,
    onUnauthorized,
  });
  const preferredSelectionRef = useRef<string | null>(null);
  const boardFolders = useUc18BoardFolders({
    apiBaseUrl,
    accessToken,
    onUnauthorized,
    preparationName: datasetPreparations.selectedPreparationName,
  });
  const digitFolders = useUc18DigitFolders({
    apiBaseUrl,
    accessToken,
    onUnauthorized,
    preparationName: datasetPreparations.selectedPreparationName,
  });
  const selectedBoardSourceName =
    boardFolders.preparationName === datasetPreparations.selectedPreparationName
      ? boardFolders.selectedSourceName
      : null;
  const boardFiles = useUc18BoardFiles({
    apiBaseUrl,
    accessToken,
    onUnauthorized,
    preparationName: datasetPreparations.selectedPreparationName,
    sourceName: selectedBoardSourceName,
  });
  const selectedPreparationStatusPresentation = datasetPreparations.detailsState.data
    ? getDatasetPreparationStatusPresentation(datasetPreparations.detailsState.data.status)
    : null;

  useEffect(() => {
    if (!preferredPreparationName) {
      preferredSelectionRef.current = null;
      return;
    }

    if (datasetPreparations.selectedPreparationName === preferredPreparationName) {
      preferredSelectionRef.current = preferredPreparationName;
      return;
    }

    const preferredPreparationExists = datasetPreparations.preparationsState.data?.some(
      (item) => item.preparationName === preferredPreparationName
    );

    if (!preferredPreparationExists) {
      return;
    }

    if (preferredSelectionRef.current === preferredPreparationName) {
      return;
    }

    preferredSelectionRef.current = preferredPreparationName;
    void datasetPreparations.loadPreparationDetails(preferredPreparationName);
  }, [
    datasetPreparations.loadPreparationDetails,
    datasetPreparations.preparationsState.data,
    datasetPreparations.selectedPreparationName,
    preferredPreparationName,
  ]);

  return (
    <section className="hero-card uc18-section">
      <p className="eyebrow">UC-18 - Przeglad zrodel przygotowania</p>
      <h2>Wybierz preparation i przejrzyj zrodla</h2>
      <p className="hero-copy">
        Ten krok pobiera z backendu istniejace preparation oraz listy zrodel{" "}
        <code>board</code> i <code>digit</code> dla wybranego rekordu, a po wyborze
        konkretnego zrodla `board` doladowuje paginowana liste plansz. Preview obrazu{" "}
        <code>corrected-board.png</code> pozostaje jeszcze placeholderem.
      </p>

      <article className="uc17-panel">
        <div className="uc17-panel-header">
          <div>
            <h3>Krok 1 - Wybierz preparation</h3>
            <p className="muted-copy">
              Lista preparation pochodzi z backendu i jest punktem wejsciowym do dalszego
              przegladu `board/folders` i `digit/folders`.
            </p>
          </div>
          <button
            className="secondary-button"
            type="button"
            onClick={() => void datasetPreparations.refreshPreparations()}
            disabled={datasetPreparations.preparationsState.kind === "loading"}
          >
            {datasetPreparations.preparationsState.kind === "loading"
              ? "Odswiezanie..."
              : "Odswiez przygotowania"}
          </button>
        </div>

        {datasetPreparations.preparationsState.kind === "loading" ? (
          <p className="status-banner status-loading">
            Pobieranie listy przygotowan datasetu...
          </p>
        ) : null}

        {datasetPreparations.preparationsState.kind === "error" ? (
          <>
            <p className="status-banner status-error">
              {datasetPreparations.preparationsState.error}
            </p>
            {datasetPreparations.preparationsState.httpStatus === 401 ? (
              <p className="muted-copy">
                Sesja administracyjna zostala wyczyszczona. Zaloguj sie ponownie.
              </p>
            ) : null}
          </>
        ) : null}

        {datasetPreparations.preparationsState.data?.length ? (
          <ul className="uc17-preparations-list">
            {datasetPreparations.preparationsState.data.map((item) => {
              const isActive =
                datasetPreparations.selectedPreparationName === item.preparationName;
              const isRefreshingActiveDetails =
                isActive && datasetPreparations.detailsState.kind === "loading";
              const statusPresentation = getDatasetPreparationStatusPresentation(
                item.status
              );

              return (
                <li
                  key={`${item.preparationName}-${item.createdAtUtc}`}
                  className={isActive ? "is-active" : ""}
                >
                  <div>
                    <strong>{item.preparationName}</strong>
                    <p className="muted-copy">
                      Utworzono: {formatTimestamp(item.createdAtUtc)}
                    </p>
                    <p className="muted-copy">
                      Zrodla board: {item.boardSourcesCount}, digit: {item.digitSourcesCount}
                    </p>
                  </div>
                  <div className="uc17-preparation-actions">
                    <span
                      className={`uc17-status-badge ${statusPresentation.className}`}
                    >
                      {statusPresentation.label}
                    </span>
                    <button
                      className="secondary-button"
                      type="button"
                      onClick={() =>
                        void datasetPreparations.loadPreparationDetails(item.preparationName)
                      }
                      disabled={isRefreshingActiveDetails}
                    >
                      {isRefreshingActiveDetails
                        ? "Odswiezanie..."
                        : isActive
                          ? "Odswiez szczegoly"
                          : "Wybierz preparation"}
                    </button>
                  </div>
                </li>
              );
            })}
          </ul>
        ) : datasetPreparations.preparationsState.kind === "success" ? (
          <p className="muted-copy">Brak zapisanych przygotowan datasetu.</p>
        ) : null}
      </article>

      <article className="uc17-panel">
        <div className="uc17-panel-header">
          <div>
            <h3>Krok 2 - Kontekst wybranego preparation</h3>
            <p className="muted-copy">
              Szczegoly pomagaja potwierdzic, z ktorego rekordu pobierasz listy zrodel
              `board` i `digit`.
            </p>
          </div>
          <button
            className="secondary-button"
            type="button"
            onClick={() => void datasetPreparations.refreshSelectedPreparation()}
            disabled={
              !datasetPreparations.selectedPreparationName ||
              datasetPreparations.detailsState.kind === "loading"
            }
          >
            {datasetPreparations.detailsState.kind === "loading"
              ? "Odswiezanie..."
              : "Odswiez szczegoly"}
          </button>
        </div>

        {!datasetPreparations.selectedPreparationName ? (
          <p className="muted-copy">
            Wybierz rekord z listy przygotowan, aby pobrac jego zrodla `board` i `digit`.
          </p>
        ) : null}

        {datasetPreparations.detailsState.kind === "loading" ? (
          <p className="status-banner status-loading">
            Pobieranie szczegolow przygotowania...
          </p>
        ) : null}

        {datasetPreparations.detailsState.kind === "error" ? (
          <>
            <p className="status-banner status-error">
              {datasetPreparations.detailsState.error}
            </p>
            {datasetPreparations.detailsState.httpStatus === 401 ? (
              <p className="muted-copy">
                Sesja administracyjna zostala wyczyszczona. Zaloguj sie ponownie.
              </p>
            ) : null}
          </>
        ) : null}

        {datasetPreparations.detailsState.data ? (
          <div className="uc17-details">
            <div className="uc17-details-header">
              <div>
                <strong>{datasetPreparations.detailsState.data.preparationName}</strong>
                <p className="muted-copy">
                  Utworzono:{" "}
                  {formatTimestamp(datasetPreparations.detailsState.data.createdAtUtc)}
                </p>
              </div>
              <span
                className={`uc17-status-badge ${selectedPreparationStatusPresentation?.className ?? "is-unknown"}`}
              >
                {selectedPreparationStatusPresentation?.label ??
                  datasetPreparations.detailsState.data.status}
              </span>
            </div>

            <ul className="uc17-draft-list">
              {datasetPreparations.detailsState.data.sources.map((source) => (
                <li key={`${source.type}:${source.name}`}>
                  <code>{source.name}</code> <span>({source.type})</span>
                  <span> przygotowane: {source.preparedItemsCount}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </article>

      <article className="uc17-panel">
        <div className="uc17-panel-header">
          <div>
            <h3>Krok 3 - Zrodla `board`</h3>
            <p className="muted-copy">
              Backend zwraca tylko nazwy logicznych zrodel. Wybor przygotowuje nastepny
              krok listowania plansz.
            </p>
          </div>
          <button
            className="secondary-button"
            type="button"
            onClick={() => void boardFolders.retryLoadBoardFolders()}
            disabled={
              !datasetPreparations.selectedPreparationName || boardFolders.status === "loading"
            }
          >
            {boardFolders.status === "loading" ? "Odswiezanie..." : "Odswiez liste zrodel"}
          </button>
        </div>

        {!datasetPreparations.selectedPreparationName ? (
          <p className="muted-copy">
            Najpierw wybierz preparation. Lista zrodel `board` nie jest pobierana bez
            poprawnego <code>preparationName</code>.
          </p>
        ) : null}

        {boardFolders.status === "loading" ? (
          <p className="status-banner status-loading">
            Pobieranie zrodel `board` dla preparation{" "}
            <code>{datasetPreparations.selectedPreparationName}</code>...
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
                Wybrane preparation nie jest juz dostepne. Wybierz inny rekord z listy.
              </p>
            ) : null}
          </>
        ) : null}

        {boardFolders.preparationName ? (
          <div className="uc18-summary">
            <span className="uc17-stat-chip">
              Preparation: <code>{boardFolders.preparationName}</code>
            </span>
            <span className="uc17-stat-chip">Liczba zrodel board: {boardFolders.totalCount}</span>
            <span className="uc17-stat-chip">
              Aktywne zrodlo:{" "}
              {boardFolders.selectedSourceName ? (
                <code>{boardFolders.selectedSourceName}</code>
              ) : (
                "brak"
              )}
            </span>
          </div>
        ) : null}

        {boardFolders.status === "success" && boardFolders.totalCount === 0 ? (
          <p className="status-banner status-loading">
            To preparation nie ma jeszcze zadnych zrodel `board`.
          </p>
        ) : null}

        {(boardFolders.status === "success" ||
          boardFolders.status === "loading" ||
          boardFolders.status === "error") &&
        boardFolders.folders.length > 0 ? (
          <Uc18PreparationFoldersList
            mode="selectable"
            folders={boardFolders.folders}
            selectedSourceName={boardFolders.selectedSourceName}
            onSelect={boardFolders.selectBoardSource}
            emptyMessage="Brak zrodel `board` dla wybranego preparation."
            disabled={boardFolders.status === "loading"}
          />
        ) : null}

        {boardFolders.selectedFolder ? (
          <p className="muted-copy">
            Wybrane zrodlo <code>{boardFolders.selectedFolder.folderName}</code> jest gotowe
            do dalszego listowania plansz w kolejnym kroku `UC-18`.
          </p>
        ) : null}
      </article>

      <Uc18BoardFilesPanel
        apiBaseUrl={apiBaseUrl}
        preparationName={datasetPreparations.selectedPreparationName}
        selectedSourceName={selectedBoardSourceName}
        boardFiles={boardFiles}
        accessToken={accessToken}
        onUnauthorized={onUnauthorized}
      />

      <Uc18DigitFoldersPanel
        preparationName={datasetPreparations.selectedPreparationName}
        digitFolders={digitFolders}
      />
    </section>
  );
}
