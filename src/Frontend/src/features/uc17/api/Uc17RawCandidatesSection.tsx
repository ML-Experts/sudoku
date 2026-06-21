import { useMemo, useState } from "react";

import { getDatasetPreparationStatusPresentation } from "../../../shared/datasets/getDatasetPreparationStatusPresentation";
import { groupRawCandidatesByType } from "../domain/groupRawCandidatesByType";
import {
  MAX_PREPARATION_NAME_LENGTH,
  validatePreparationRequest,
} from "../domain/validatePreparationRequest";
import { useUc17DatasetPreparations } from "../application/useUc17DatasetPreparations";
import { useUc17RawCandidates } from "../application/useUc17RawCandidates";
import { Uc17RawCandidatesList } from "./Uc17RawCandidatesList";

type Uc17RawCandidatesSectionProps = {
  apiBaseUrl: string;
  accessToken?: string | null;
  onUnauthorized?: () => void;
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

export function Uc17RawCandidatesSection({
  apiBaseUrl,
  accessToken,
  onUnauthorized,
}: Uc17RawCandidatesSectionProps) {
  const [preparationName, setPreparationName] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const rawCandidates = useUc17RawCandidates({
    apiBaseUrl,
    accessToken,
    onUnauthorized,
  });
  const datasetPreparations = useUc17DatasetPreparations({
    apiBaseUrl,
    accessToken,
    onUnauthorized,
  });

  const groupedCandidates = useMemo(
    () => groupRawCandidatesByType(rawCandidates.candidates),
    [rawCandidates.candidates]
  );
  const requestPreview = useMemo(
    () =>
      JSON.stringify(
        {
          preparationName: preparationName.trim(),
          sources: rawCandidates.sourceDrafts,
        },
        null,
        2
      ),
    [preparationName, rawCandidates.sourceDrafts]
  );
  const selectedPreparationStatusPresentation = datasetPreparations.detailsState.data
    ? getDatasetPreparationStatusPresentation(datasetPreparations.detailsState.data.status)
    : null;

  async function handleCreatePreparation() {
    const validationError = validatePreparationRequest({
      preparationName,
      selectedCount: rawCandidates.selectedCount,
    });

    if (validationError) {
      setFormError(validationError);
      return;
    }

    setFormError(null);

    const wasCreated = await datasetPreparations.createPreparationRequest({
      preparationName: preparationName.trim(),
      sources: rawCandidates.sourceDrafts,
    });

    if (wasCreated) {
      setPreparationName("");
    }
  }

  return (
    <section className="hero-card uc17-section">
      <p className="eyebrow">UC-17 - Przygotowanie datasetu</p>
      <h2>Wybierz zrodla raw i uruchom przygotowanie</h2>
      <p className="hero-copy">
        Ten krok pobiera kandydatow z backendu, buduje draft <code>name + type</code>{" "}
        i pozwala rozpoczac trwale przygotowanie przed pozniejszym czyszczeniem oraz
        buildem <code>.npz</code>.
      </p>

      <article className="uc17-panel">
        <div className="uc17-panel-header">
          <div>
            <h3>Krok 1 - Kandydaci raw</h3>
            <p className="muted-copy">
              Backend pozostaje jedynym zrodlem prawdy dla listy kandydatow i ich
              typu `board` albo `digit`.
            </p>
          </div>
          <button
            className="secondary-button"
            type="button"
            onClick={() => void rawCandidates.retryLoadRawCandidates()}
            disabled={rawCandidates.status === "loading"}
          >
            {rawCandidates.status === "loading" ? "Odswiezanie..." : "Odswiez liste"}
          </button>
        </div>

        <div className="uc17-stats">
          <span className="uc17-stat-chip">Lacznie: {groupedCandidates.counts.total}</span>
          <span className="uc17-stat-chip">Board: {groupedCandidates.counts.board}</span>
          <span className="uc17-stat-chip">Digit: {groupedCandidates.counts.digit}</span>
          <span className="uc17-stat-chip">
            Zaznaczone: {rawCandidates.selectedCount}
          </span>
        </div>

        {rawCandidates.status === "loading" ? (
          <p className="status-banner status-loading">
            Pobieranie kandydatow raw z backendu...
          </p>
        ) : null}

        {rawCandidates.status === "error" ? (
          <>
            <p className="status-banner status-error">{rawCandidates.error}</p>
            {rawCandidates.httpStatus === 401 ? (
              <p className="muted-copy">
                Sesja administracyjna zostala wyczyszczona. Zaloguj sie ponownie.
              </p>
            ) : null}
          </>
        ) : null}

        {rawCandidates.unknownTypeCount > 0 ? (
          <p className="muted-copy">
            Odrzucono rekordy z nieznanym typem: {rawCandidates.unknownTypeCount}.
          </p>
        ) : null}

        {rawCandidates.status === "success" && groupedCandidates.counts.total === 0 ? (
          <p className="status-banner status-loading">
            Backend nie zwrocil jeszcze zadnych kandydatow raw.
          </p>
        ) : null}

        <div className="uc17-groups">
          <Uc17RawCandidatesList
            title="Plansze sudoku (`board`)"
            candidates={groupedCandidates.boardCandidates}
            selectedKeys={rawCandidates.selectedKeys}
            onToggle={rawCandidates.toggleRawCandidateSelection}
          />
          <Uc17RawCandidatesList
            title="Zbiory cyfr (`digit`)"
            candidates={groupedCandidates.digitCandidates}
            selectedKeys={rawCandidates.selectedKeys}
            onToggle={rawCandidates.toggleRawCandidateSelection}
          />
        </div>
      </article>

      <article className="uc17-panel">
        <h3>Krok 2 - Draft requestu i start przygotowania</h3>
        <label className="uc12-field">
          <span>Nazwa przygotowania</span>
          <input
            value={preparationName}
            onChange={(event) => {
              setPreparationName(event.target.value);
              if (formError) {
                setFormError(null);
              }
            }}
            placeholder="np. preparation-001"
            maxLength={MAX_PREPARATION_NAME_LENGTH}
          />
        </label>

        <div className="uc17-draft">
          <div className="uc17-draft-header">
            <strong>Draft requestu do `POST /api/datasets/preparations`</strong>
            <span className="muted-copy">{rawCandidates.sourceDrafts.length} rekordow</span>
          </div>
          <pre className="uc06-json-preview">{requestPreview}</pre>
          {rawCandidates.sourceDrafts.length === 0 ? (
            <p className="muted-copy">
              Zaznacz zrodla w kroku 1, aby zbudowac payload <code>name + type</code>.
            </p>
          ) : (
            <ul className="uc17-draft-list">
              {rawCandidates.sourceDrafts.map((source) => (
                <li key={`${source.type}:${source.name}`}>
                  <code>{source.name}</code> <span>({source.type})</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {formError ? <p className="status-banner status-error">{formError}</p> : null}

        {datasetPreparations.createState.kind === "error" ? (
          <>
            <p className="status-banner status-error">
              {datasetPreparations.createState.error}
            </p>
            {datasetPreparations.createStatusHint ? (
              <p className="muted-copy">{datasetPreparations.createStatusHint}</p>
            ) : null}
          </>
        ) : null}

        {datasetPreparations.createState.kind === "success" ? (
          <p className="status-banner status-success">
            Przygotowanie <code>
              {datasetPreparations.createState.response.preparationName}
            </code>{" "}
            zostalo przyjete przez backend ze statusem{" "}
            <code>{datasetPreparations.createState.response.status}</code>.
          </p>
        ) : null}

        <button
          className="primary-button"
          type="button"
          onClick={() => void handleCreatePreparation()}
          disabled={
            datasetPreparations.createState.kind === "loading" ||
            rawCandidates.status === "loading"
          }
        >
          {datasetPreparations.createState.kind === "loading"
            ? "Uruchamianie przygotowania..."
            : "Rozpocznij przygotowanie"}
        </button>
      </article>

      <article className="uc17-panel">
        <div className="uc17-panel-header">
          <div>
            <h3>Krok 3 - Istniejace przygotowania</h3>
            <p className="muted-copy">
              Widok pozwala sprawdzic liste przygotowan i podejrzec status wybranego
              rekordu.
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
                      Zrodla board: {item.boardSourcesCount}, digit:{" "}
                      {item.digitSourcesCount}
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
                        void datasetPreparations.loadPreparationDetails(
                          item.preparationName
                        )
                      }
                      disabled={isRefreshingActiveDetails}
                    >
                      {isRefreshingActiveDetails
                        ? "Odswiezanie..."
                        : isActive
                          ? "Odswiez szczegoly"
                          : "Pokaz szczegoly"}
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
            <h3>Krok 4 - Szczegoly wybranego przygotowania</h3>
            <p className="muted-copy">
              Szczegoly pokazuja aktualny status, zrodla oraz liczbe przygotowanych
              elementow per zrodlo.
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
            Wybierz rekord z listy przygotowan, aby zobaczyc jego szczegoly.
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

            {datasetPreparations.detailsState.data.warnings.length > 0 ? (
              <>
                <h4>Ostrzezenia</h4>
                <ul className="uc12-warnings-list">
                  {datasetPreparations.detailsState.data.warnings.map((warning, index) => (
                    <li key={`uc17-warning-${index}`}>{warning}</li>
                  ))}
                </ul>
              </>
            ) : (
              <p className="muted-copy">Brak ostrzezen dla tego przygotowania.</p>
            )}
          </div>
        ) : null}
      </article>
    </section>
  );
}
