import { useEffect } from "react";

import { useUc19BoardFoldersSelection } from "../application/useUc19BoardFoldersSelection";
import { useUc19DigitFoldersSelection } from "../application/useUc19DigitFoldersSelection";
import { useUc19PreparationSelection } from "../application/useUc19PreparationSelection";
import { useUc19ProcessedDatasetBuild } from "../application/useUc19ProcessedDatasetBuild";
import { useUc19ProcessedDatasetsList } from "../application/useUc19ProcessedDatasetsList";
import { Uc19BoardFoldersSelectionSection } from "./Uc19BoardFoldersSelectionSection";
import { Uc19DigitFoldersSelectionSection } from "./Uc19DigitFoldersSelectionSection";
import { Uc19ProcessedDatasetBuildSection } from "./Uc19ProcessedDatasetBuildSection";
import { Uc19ProcessedDatasetsListSection } from "./Uc19ProcessedDatasetsListSection";

type Uc19PreparationSelectionSectionProps = {
  apiBaseUrl: string;
  accessToken?: string | null;
  onUnauthorized?: () => void;
  onSelectedPreparationNameChange?: (preparationName: string | null) => void;
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

export function Uc19PreparationSelectionSection({
  apiBaseUrl,
  accessToken,
  onUnauthorized,
  onSelectedPreparationNameChange,
  preferredPreparationName,
}: Uc19PreparationSelectionSectionProps) {
  const preparationSelection = useUc19PreparationSelection({
    apiBaseUrl,
    accessToken,
    onUnauthorized,
    preferredPreparationName,
  });

  useEffect(() => {
    onSelectedPreparationNameChange?.(preparationSelection.selectedPreparationName);
  }, [onSelectedPreparationNameChange, preparationSelection.selectedPreparationName]);

  const boardFolders = useUc19BoardFoldersSelection({
    apiBaseUrl,
    accessToken,
    onUnauthorized,
    preparationName: preparationSelection.canContinueToSources
      ? preparationSelection.selectedPreparationName
      : null,
  });

  const digitFolders = useUc19DigitFoldersSelection({
    apiBaseUrl,
    accessToken,
    onUnauthorized,
    preparationName: preparationSelection.canContinueToSources
      ? preparationSelection.selectedPreparationName
      : null,
  });

  const processedDatasetBuild = useUc19ProcessedDatasetBuild({
    apiBaseUrl,
    accessToken,
    onUnauthorized,
    preparationName: preparationSelection.selectedPreparationName,
    canContinueToSources: preparationSelection.canContinueToSources,
    boardSelectedDrafts: boardFolders.selectedDrafts,
    digitSelectedDrafts: digitFolders.selectedDrafts,
  });
  const processedDatasetsList = useUc19ProcessedDatasetsList({
    apiBaseUrl,
    accessToken,
    onUnauthorized,
    typedDatasetName: processedDatasetBuild.datasetName,
  });

  async function handleProcessedDatasetBuildSubmit() {
    const response = await processedDatasetBuild.handleSubmitProcessedDatasetBuild();

    if (!response) {
      return null;
    }

    await processedDatasetsList.syncProcessedDatasetsAfterCreate(response.name);
    return response;
  }

  return (
    <section className="hero-card uc19-section">
      <p className="eyebrow">UC-19 - Budowa finalnego datasetu</p>
      <h2>Wybierz przygotowanie datasetu do budowy pliku `.npz`</h2>
      <p className="hero-copy">
        Ten krok korzysta z listy przygotowan z backendu i pozwala wybrac rekord,
        ktory odblokuje dalsza konfiguracje zrodel plansz i cyfr przed
        utworzeniem finalnego datasetu.
      </p>

      <article className="uc17-panel">
        <div className="uc17-panel-header">
          <div>
            <h3>Krok 1 - Lista przygotowan</h3>
            <p className="muted-copy">
              Backend pozostaje zrodlem prawdy dla kolejnosci rekordow, statusow i
              licznikow zrodel.
            </p>
          </div>
          <button
            className="secondary-button"
            type="button"
            onClick={() => void preparationSelection.refreshPreparations()}
            disabled={preparationSelection.preparationsState.kind === "loading"}
          >
            {preparationSelection.preparationsState.kind === "loading"
              ? "Odswiezanie..."
              : "Odswiez przygotowania"}
          </button>
        </div>

        {preparationSelection.preparationsState.kind === "loading" ? (
          <p className="status-banner status-loading">
            Pobieranie listy przygotowan datasetu...
          </p>
        ) : null}

        {preparationSelection.preparationsState.kind === "error" ? (
          <>
            <p className="status-banner status-error">
              {preparationSelection.preparationsState.error}
            </p>
            {preparationSelection.preparationsState.httpStatus === 401 ? (
              <p className="muted-copy">
                Sesja administracyjna zostala wyczyszczona. Zaloguj sie ponownie.
              </p>
            ) : null}
          </>
        ) : null}

        {preparationSelection.preparationItems.length > 0 ? (
          <ul className="uc17-preparations-list">
            {preparationSelection.preparationItems.map((item) => {
              const isActive =
                preparationSelection.selectedPreparationName === item.preparationName;
              const isRefreshingActiveDetails =
                isActive && preparationSelection.detailsState.kind === "loading";

              return (
                <li
                  key={`${item.preparationName}-${item.createdAtUtc}`}
                  className={`uc19-preparation-card ${isActive ? "is-active" : ""} ${
                    item.readiness.canContinue ? "is-ready" : "is-blocked"
                  }`}
                >
                  <div className="uc19-preparation-copy">
                    <strong>{item.preparationName}</strong>
                    <p className="muted-copy">
                      Utworzono: {formatTimestamp(item.createdAtUtc)}
                    </p>
                    <p className="muted-copy">
                      Zrodla board: {item.boardSourcesCount}, digit:{" "}
                      {item.digitSourcesCount}
                    </p>
                    {item.statusPresentation.description ? (
                      <p className="muted-copy">{item.statusPresentation.description}</p>
                    ) : null}
                  </div>
                  <div className="uc17-preparation-actions">
                    <span
                      className={`uc17-status-badge ${item.statusPresentation.className}`}
                    >
                      {item.statusPresentation.label}
                    </span>
                    <span
                      className={`uc19-readiness-badge ${
                        item.readiness.canContinue ? "is-ready" : "is-blocked"
                      }`}
                    >
                      {item.readiness.canContinue
                        ? "Odblokowuje kolejny krok"
                        : "Blokuje kolejny krok"}
                    </span>
                    <button
                      className="secondary-button"
                      type="button"
                      onClick={() =>
                        void preparationSelection.handlePreparationSelect(
                          item.preparationName
                        )
                      }
                      disabled={isRefreshingActiveDetails}
                    >
                      {isRefreshingActiveDetails
                        ? "Odswiezanie..."
                        : isActive
                          ? "Odswiez wybor"
                          : "Wybierz przygotowanie"}
                    </button>
                  </div>
                </li>
              );
            })}
          </ul>
        ) : preparationSelection.preparationsState.kind === "success" ? (
          <p className="muted-copy">
            Brak zapisanych przygotowan. Najpierw utworz przygotowanie w `UC-17`.
          </p>
        ) : null}
      </article>

      <article className="uc17-panel">
        <div className="uc17-panel-header">
          <div>
            <h3>Krok 2 - Walidacja wybranego przygotowania</h3>
            <p className="muted-copy">
              Tylko rekord gotowy po stronie backendu powinien odblokowac dalsze
              pobieranie zrodel plansz i cyfr.
            </p>
          </div>
          <button
            className="secondary-button"
            type="button"
            onClick={() => void preparationSelection.refreshSelectedPreparation()}
            disabled={
              !preparationSelection.selectedPreparationName ||
              preparationSelection.detailsState.kind === "loading"
            }
          >
            {preparationSelection.detailsState.kind === "loading"
              ? "Odswiezanie..."
              : "Odswiez szczegoly"}
          </button>
        </div>

        {!preparationSelection.selectedPreparation ? (
          <p className="muted-copy">
            Wybierz rekord z listy, aby sprawdzic czy moze byc uzyty jako zrodlo
            budowy pliku `.npz`.
          </p>
        ) : null}

        {preparationSelection.selectionWarning ? (
          <p
            className={`status-banner ${
              preparationSelection.selectionWarning.severity === "warning"
                ? "status-error"
                : "status-loading"
            }`}
          >
            {preparationSelection.selectionWarning.message}
          </p>
        ) : null}

        {preparationSelection.selectedPreparation ? (
          <div className="uc19-selection-summary">
            <div className="uc17-details-header">
              <div>
                <strong>{preparationSelection.selectedPreparation.preparationName}</strong>
                <p className="muted-copy">
                  Utworzono:{" "}
                  {formatTimestamp(
                    preparationSelection.selectedPreparation.createdAtUtc
                  )}
                </p>
                {preparationSelection.selectedPreparationDetails?.statusPresentation
                  .description ? (
                  <p className="muted-copy">
                    {
                      preparationSelection.selectedPreparationDetails.statusPresentation
                        .description
                    }
                  </p>
                ) : null}
              </div>
              <span
                className={`uc17-status-badge ${
                  (
                    preparationSelection.selectedPreparationDetails?.statusPresentation ??
                    preparationSelection.selectedPreparation.statusPresentation
                  ).className
                }`}
              >
                {
                  (
                    preparationSelection.selectedPreparationDetails?.statusPresentation ??
                    preparationSelection.selectedPreparation.statusPresentation
                  ).label
                }
              </span>
            </div>

            <div className="uc18-summary">
              <span className="uc17-stat-chip">
                Zrodla plansz: {preparationSelection.selectedPreparation.boardSourcesCount}
              </span>
              <span className="uc17-stat-chip">
                Zrodla cyfr: {preparationSelection.selectedPreparation.digitSourcesCount}
              </span>
              <span className="uc17-stat-chip">
                Dalszy krok:{" "}
                {preparationSelection.canContinueToSources ? "odblokowany" : "zablokowany"}
              </span>
            </div>

            {preparationSelection.detailsState.kind === "loading" ? (
              <p className="status-banner status-loading">
                Pobieranie szczegolow wybranego przygotowania...
              </p>
            ) : null}

            {preparationSelection.detailsState.kind === "error" ? (
              <>
                <p className="status-banner status-error">
                  {preparationSelection.detailsState.error}
                </p>
                {preparationSelection.detailsState.httpStatus === 401 ? (
                  <p className="muted-copy">
                    Sesja administracyjna zostala wyczyszczona. Zaloguj sie ponownie.
                  </p>
                ) : null}
              </>
            ) : null}

            {preparationSelection.selectedPreparationDetails ? (
              <>
                <ul className="uc17-draft-list">
                  {preparationSelection.selectedPreparationDetails.sources.map((source) => (
                    <li key={`${source.type}:${source.name}`}>
                      <code>{source.name}</code> <span>({source.type})</span>
                      <span> przygotowane: {source.preparedItemsCount}</span>
                    </li>
                  ))}
                </ul>

                {preparationSelection.selectedPreparationDetails.warnings.length > 0 ? (
                  <>
                    <h4>Ostrzezenia</h4>
                    <ul className="uc12-warnings-list">
                      {preparationSelection.selectedPreparationDetails.warnings.map(
                        (warning, index) => (
                          <li key={`uc19-warning-${index}`}>{warning}</li>
                        )
                      )}
                    </ul>
                  </>
                ) : (
                  <p className="muted-copy">Brak ostrzezen dla tego przygotowania.</p>
                )}
              </>
            ) : preparationSelection.selectedPreparationName ? (
              <p className="muted-copy">
                Szczegoly tego przygotowania pojawia sie tutaj po poprawnym
                pobraniu endpointu walidacyjnego.
              </p>
            ) : null}

            {preparationSelection.canContinueToSources ? (
              <p className="status-banner status-success">
                Wybrane przygotowanie odblokowalo konfiguracje zrodel plansz i cyfr
                w kolejnych krokach ponizej.
              </p>
            ) : null}
          </div>
        ) : null}
      </article>

      <Uc19BoardFoldersSelectionSection
        selectedPreparationName={preparationSelection.selectedPreparationName}
        canLoadBoardFolders={preparationSelection.canContinueToSources}
        boardFolders={boardFolders}
      />
      <Uc19DigitFoldersSelectionSection
        selectedPreparationName={preparationSelection.selectedPreparationName}
        canLoadDigitFolders={preparationSelection.canContinueToSources}
        digitFolders={digitFolders}
      />
      <Uc19ProcessedDatasetBuildSection
        selectedPreparationName={preparationSelection.selectedPreparationName}
        canContinueToSources={preparationSelection.canContinueToSources}
        datasetName={processedDatasetBuild.datasetName}
        onDatasetNameChange={processedDatasetBuild.setDatasetName}
        selectedBoardCount={boardFolders.selectedCount}
        selectedDigitCount={digitFolders.selectedCount}
        requestPreview={processedDatasetBuild.requestPreview}
        formError={processedDatasetBuild.formError}
        createState={processedDatasetBuild.createState}
        createStatusHint={processedDatasetBuild.createStatusHint}
        onSubmit={handleProcessedDatasetBuildSubmit}
      />
      <Uc19ProcessedDatasetsListSection
        status={processedDatasetsList.status}
        items={processedDatasetsList.highlightedItems}
        totalCount={processedDatasetsList.totalCount}
        error={processedDatasetsList.error}
        httpStatus={processedDatasetsList.httpStatus}
        typedDatasetName={processedDatasetBuild.datasetName}
        collisionItem={processedDatasetsList.collisionItem}
        syncWarning={processedDatasetsList.syncWarning}
        onRefresh={processedDatasetsList.refreshProcessedDatasets}
      />
    </section>
  );
}
