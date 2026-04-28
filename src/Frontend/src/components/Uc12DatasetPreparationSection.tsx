import { useCallback, useEffect, useMemo, useState } from "react";

import {
  DatasetsApiError,
  getProcessedDatasets,
  getRawDatasetCandidates,
  postCreateProcessedDataset,
} from "../api/datasets";
import type {
  ProcessedDatasetApiResponse,
  ProcessedDatasetListItemApiResponse,
  RawDatasetCandidateApiResponse,
} from "../types/api";

type LoadableState<T> =
  | {
      kind: "idle";
      data: T | null;
      error: null;
      errorType: null;
      httpStatus: null;
    }
  | {
      kind: "loading";
      data: T | null;
      error: null;
      errorType: null;
      httpStatus: null;
    }
  | {
      kind: "success";
      data: T;
      error: null;
      errorType: null;
      httpStatus: number;
    }
  | {
      kind: "error";
      data: T | null;
      error: string;
      errorType: string | null;
      httpStatus: number | null;
    };

type RequestState =
  | {
      kind: "idle";
      response: ProcessedDatasetApiResponse | null;
      error: null;
      errorType: null;
      httpStatus: null;
    }
  | {
      kind: "loading";
      response: ProcessedDatasetApiResponse | null;
      error: null;
      errorType: null;
      httpStatus: null;
    }
  | {
      kind: "success";
      response: ProcessedDatasetApiResponse;
      error: null;
      errorType: null;
      httpStatus: number;
    }
  | {
      kind: "error";
      response: ProcessedDatasetApiResponse | null;
      error: string;
      errorType: string | null;
      httpStatus: number | null;
    };

type SelectedSource = {
  candidate: RawDatasetCandidateApiResponse;
  splits: string[];
};

type Uc12DatasetPreparationSectionProps = {
  apiBaseUrl: string;
};

const defaultCandidatesState: LoadableState<RawDatasetCandidateApiResponse[]> = {
  kind: "idle",
  data: null,
  error: null,
  errorType: null,
  httpStatus: null,
};

const defaultProcessedDatasetsState: LoadableState<
  ProcessedDatasetListItemApiResponse[]
> = {
  kind: "idle",
  data: null,
  error: null,
  errorType: null,
  httpStatus: null,
};

const defaultCreateState: RequestState = {
  kind: "idle",
  response: null,
  error: null,
  errorType: null,
  httpStatus: null,
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

function clearAdminSession(): void {
  const sessionKeys = [
    "sudokuAdminAccessToken",
    "sudokuAdminToken",
    "adminAccessToken",
    "accessToken",
  ];

  for (const key of sessionKeys) {
    window.sessionStorage.removeItem(key);
    window.localStorage.removeItem(key);
  }
}

function normalizeSplitSelection(previousSplits: string[], split: string): string[] {
  if (split === "mix") {
    return previousSplits.includes("mix") ? [] : ["mix"];
  }

  const withoutMix = previousSplits.filter((item) => item !== "mix");
  if (withoutMix.includes(split)) {
    return withoutMix.filter((item) => item !== split);
  }

  return [...withoutMix, split];
}

function toStatusCopy(status: number | null): string | null {
  if (status === null) {
    return null;
  }

  const map: Record<number, string> = {
    400: "Sprawdz formularz: nazwa oraz wybory splitow.",
    401: "Sesja administracyjna wygasla. Zaloguj sie ponownie.",
    404: "Jedno ze zrodel nie jest juz dostepne.",
    409: "Dataset o tej nazwie juz istnieje.",
    422: "Dane zrodlowe nie przechodza walidacji technicznej.",
    503: "Serwis ML jest chwilowo niedostepny.",
    504: "Przygotowanie datasetu przekroczylo limit czasu.",
  };

  return map[status] ?? null;
}

export function Uc12DatasetPreparationSection({
  apiBaseUrl,
}: Uc12DatasetPreparationSectionProps) {
  const tokenFromEnv = import.meta.env.VITE_ADMIN_TOKEN?.trim() ?? "";
  const adminToken = tokenFromEnv || null;

  const [datasetName, setDatasetName] = useState("");
  const [selectedSources, setSelectedSources] = useState<Record<string, SelectedSource>>(
    {}
  );
  const [candidatesState, setCandidatesState] = useState(defaultCandidatesState);
  const [processedDatasetsState, setProcessedDatasetsState] = useState(
    defaultProcessedDatasetsState
  );
  const [createState, setCreateState] = useState(defaultCreateState);
  const [formError, setFormError] = useState<string | null>(null);

  const loadCandidates = useCallback(async () => {
    setCandidatesState((previous) => ({
      kind: "loading",
      data: previous.data,
      error: null,
      errorType: null,
      httpStatus: null,
    }));

    try {
      const candidates = await getRawDatasetCandidates(apiBaseUrl, adminToken);
      setCandidatesState({
        kind: "success",
        data: candidates,
        error: null,
        errorType: null,
        httpStatus: 200,
      });
    } catch (error) {
      if (error instanceof DatasetsApiError && error.status === 401) {
        clearAdminSession();
      }

      setCandidatesState({
        kind: "error",
        data: null,
        error:
          error instanceof Error
            ? error.message
            : "Nie udalo sie pobrac kandydatow datasetowych.",
        errorType: error instanceof DatasetsApiError ? error.errorType ?? null : null,
        httpStatus: error instanceof DatasetsApiError ? error.status : null,
      });
    }
  }, [adminToken, apiBaseUrl]);

  const loadProcessedDatasets = useCallback(async () => {
    setProcessedDatasetsState((previous) => ({
      kind: "loading",
      data: previous.data,
      error: null,
      errorType: null,
      httpStatus: null,
    }));

    try {
      const response = await getProcessedDatasets(apiBaseUrl, adminToken);
      setProcessedDatasetsState({
        kind: "success",
        data: response.items,
        error: null,
        errorType: null,
        httpStatus: 200,
      });
    } catch (error) {
      if (error instanceof DatasetsApiError && error.status === 401) {
        clearAdminSession();
      }

      setProcessedDatasetsState({
        kind: "error",
        data: null,
        error:
          error instanceof Error
            ? error.message
            : "Nie udalo sie pobrac listy przygotowanych datasetow.",
        errorType: error instanceof DatasetsApiError ? error.errorType ?? null : null,
        httpStatus: error instanceof DatasetsApiError ? error.status : null,
      });
    }
  }, [adminToken, apiBaseUrl]);

  useEffect(() => {
    void Promise.all([loadCandidates(), loadProcessedDatasets()]);
  }, [loadCandidates, loadProcessedDatasets]);

  const candidates = candidatesState.data ?? [];
  const selectedSourcesArray = useMemo(
    () => Object.values(selectedSources),
    [selectedSources]
  );

  const toggleSourceSelection = useCallback(
    (candidate: RawDatasetCandidateApiResponse) => {
      setSelectedSources((previous) => {
        const key = `${candidate.type}:${candidate.name}`;
        if (previous[key]) {
          const next = { ...previous };
          delete next[key];
          return next;
        }

        return {
          ...previous,
          [key]: {
            candidate,
            splits: ["mix"],
          },
        };
      });
    },
    []
  );

  const toggleSplit = useCallback((candidateKey: string, split: string) => {
    setSelectedSources((previous) => {
      const existing = previous[candidateKey];
      if (!existing) {
        return previous;
      }

      const normalizedSplits = normalizeSplitSelection(existing.splits, split);
      return {
        ...previous,
        [candidateKey]: {
          ...existing,
          splits: normalizedSplits,
        },
      };
    });
  }, []);

  const validateForm = useCallback((): string | null => {
    if (!datasetName.trim()) {
      return "Podaj nazwe datasetu.";
    }

    if (selectedSourcesArray.length === 0) {
      return "Wybierz przynajmniej jedno zrodlo.";
    }

    for (const source of selectedSourcesArray) {
      if (source.splits.length === 0) {
        return `Wybierz split dla zrodla ${source.candidate.name}.`;
      }

      if (source.splits.includes("mix") && source.splits.length > 1) {
        return `Zrodlo ${source.candidate.name} ma niepoprawna kombinacje splitow.`;
      }
    }

    return null;
  }, [datasetName, selectedSourcesArray]);

  const handleCreateDataset = useCallback(async () => {
    setFormError(null);
    const validationError = validateForm();
    if (validationError) {
      setFormError(validationError);
      return;
    }

    setCreateState((previous) => ({
      kind: "loading",
      response: previous.response,
      error: null,
      errorType: null,
      httpStatus: null,
    }));

    try {
      const response = await postCreateProcessedDataset(
        apiBaseUrl,
        {
          name: datasetName.trim(),
          sources: selectedSourcesArray.map((source) => ({
            name: source.candidate.name,
            type: source.candidate.type,
            splits: source.splits,
          })),
        },
        adminToken
      );

      setCreateState({
        kind: "success",
        response,
        error: null,
        errorType: null,
        httpStatus: 201,
      });
      await loadProcessedDatasets();
    } catch (error) {
      if (error instanceof DatasetsApiError && error.status === 401) {
        clearAdminSession();
      }

      setCreateState((previous) => ({
        kind: "error",
        response: previous.response,
        error:
          error instanceof Error
            ? error.message
            : "Nie udalo sie utworzyc datasetu processed.",
        errorType: error instanceof DatasetsApiError ? error.errorType ?? null : null,
        httpStatus: error instanceof DatasetsApiError ? error.status : null,
      }));
    }
  }, [
    adminToken,
    apiBaseUrl,
    datasetName,
    loadProcessedDatasets,
    selectedSourcesArray,
    validateForm,
  ]);

  const statusHint =
    createState.kind === "error" ? toStatusCopy(createState.httpStatus) : null;

  return (
    <section className="hero-card uc12-section">
      <p className="eyebrow">UC-12 — Przygotowanie datasetu processed</p>
      <h2>Budowa datasetu .npz z kandydatow raw</h2>
      <p className="hero-copy">
        Wybierz zrodla, ustaw splity i utworz dataset gotowy pod trening.
      </p>

      <article className="uc12-panel">
        <h3>Krok 1 — Kandydaci z UC-11</h3>
        <div className="examples-row-actions">
          <button
            className="secondary-button"
            type="button"
            onClick={() => void loadCandidates()}
            disabled={candidatesState.kind === "loading"}
          >
            {candidatesState.kind === "loading"
              ? "Odswiezanie..."
              : "Odswiez kandydatow"}
          </button>
        </div>

        {candidatesState.kind === "error" ? (
          <p className="status-banner status-error">{candidatesState.error}</p>
        ) : null}

        {candidatesState.kind === "success" && candidates.length === 0 ? (
          <p className="status-banner status-loading">
            Brak kandydatow datasetowych. Dodaj dane zrodlowe po stronie backendu.
          </p>
        ) : null}

        <div className="uc12-candidates-list">
          {candidates.map((candidate) => {
            const key = `${candidate.type}:${candidate.name}`;
            const isSelected = Boolean(selectedSources[key]);
            return (
              <label key={key} className={`uc12-candidate ${isSelected ? "is-selected" : ""}`}>
                <input
                  type="checkbox"
                  checked={isSelected}
                  onChange={() => toggleSourceSelection(candidate)}
                />
                <span>
                  <strong>{candidate.name}</strong> (<code>{candidate.type}</code>)
                </span>
              </label>
            );
          })}
        </div>
      </article>

      <article className="uc12-panel">
        <h3>Krok 2 — Konfiguracja splitow i nazwa</h3>
        <label className="uc12-field">
          <span>Nazwa datasetu (bez .npz)</span>
          <input
            value={datasetName}
            onChange={(event) => setDatasetName(event.target.value)}
            placeholder="np. sudokuDigitsV2"
          />
        </label>

        {selectedSourcesArray.length === 0 ? (
          <p className="muted-copy">
            Wybierz zrodla w kroku 1, aby skonfigurowac splity.
          </p>
        ) : (
          <div className="uc12-source-config-list">
            {Object.entries(selectedSources).map(([key, source]) => (
              <div key={key} className="uc12-source-config">
                <p>
                  <strong>{source.candidate.name}</strong> ({source.candidate.type})
                </p>
                <div className="uc12-splits">
                  {["mix", "train", "val", "test"].map((split) => (
                    <label key={split}>
                      <input
                        type="checkbox"
                        checked={source.splits.includes(split)}
                        onChange={() => toggleSplit(key, split)}
                      />
                      <span>{split}</span>
                    </label>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {formError ? <p className="status-banner status-error">{formError}</p> : null}

        <button
          className="primary-button"
          type="button"
          onClick={() => void handleCreateDataset()}
          disabled={createState.kind === "loading"}
        >
          {createState.kind === "loading"
            ? "Tworzenie datasetu..."
            : "Utworz dataset processed"}
        </button>
      </article>

      {createState.kind === "error" ? (
        <article className="uc12-panel">
          <h3>Blad tworzenia</h3>
          <p className="status-banner status-error">{createState.error}</p>
          {statusHint ? <p className="muted-copy">{statusHint}</p> : null}
        </article>
      ) : null}

      {createState.kind === "success" ? (
        <article className="uc12-panel">
          <h3>Raport utworzonego datasetu</h3>
          <p className="status-banner status-success">
            Dataset <code>{createState.response.fileName}</code> zostal utworzony.
          </p>
          <p className="muted-copy">
            Profil: <code>{createState.response.preprocessingProfile}</code> | Utworzono:{" "}
            {formatTimestamp(createState.response.createdAtUtc)}
          </p>
          <p className="muted-copy">
            Sample counts: train {createState.response.sampleCounts.train}, val{" "}
            {createState.response.sampleCounts.val}, test{" "}
            {createState.response.sampleCounts.test}
          </p>

          <div className="uc12-source-config-list">
            {createState.response.sourceReports.map((report) => (
              <div key={`${report.type}-${report.name}`} className="uc12-source-config">
                <p>
                  <strong>{report.name}</strong> ({report.type})
                </p>
                <p className="muted-copy">
                  processed: {report.processedSampleCount}, included:{" "}
                  {report.includedSampleCount}, empty: {report.emptyCellCount}, rejected:{" "}
                  {report.rejectedSampleCount}
                </p>
                {report.warnings.length > 0 ? (
                  <ul className="uc12-warnings-list">
                    {report.warnings.map((warning, index) => (
                      <li key={`${report.name}-warning-${index}`}>{warning}</li>
                    ))}
                  </ul>
                ) : null}
              </div>
            ))}
          </div>

          {createState.response.warnings.length > 0 ? (
            <>
              <h4>Ostrzezenia globalne</h4>
              <ul className="uc12-warnings-list">
                {createState.response.warnings.map((warning, index) => (
                  <li key={`global-warning-${index}`}>{warning}</li>
                ))}
              </ul>
            </>
          ) : null}
        </article>
      ) : null}

      <article className="uc12-panel">
        <h3>Lista gotowych datasetow (UC-12 -&gt; UC-06)</h3>
        <div className="examples-row-actions">
          <button
            className="secondary-button"
            type="button"
            onClick={() => void loadProcessedDatasets()}
            disabled={processedDatasetsState.kind === "loading"}
          >
            {processedDatasetsState.kind === "loading"
              ? "Odswiezanie..."
              : "Odswiez liste"}
          </button>
        </div>

        {processedDatasetsState.kind === "error" ? (
          <p className="status-banner status-error">{processedDatasetsState.error}</p>
        ) : null}

        {processedDatasetsState.kind === "success" &&
        processedDatasetsState.data.length === 0 ? (
          <p className="muted-copy">Brak przygotowanych datasetow.</p>
        ) : null}

        {processedDatasetsState.kind === "success" &&
        processedDatasetsState.data.length > 0 ? (
          <ul className="uc12-processed-list">
            {processedDatasetsState.data.map((item) => (
              <li key={`${item.name}-${item.createdAtUtc}`}>
                <strong>{item.fileName}</strong>
                <span>
                  profile: {item.preprocessingProfile} | train {item.sampleCounts.train}, val{" "}
                  {item.sampleCounts.val}, test {item.sampleCounts.test}
                </span>
                <span>created: {formatTimestamp(item.createdAtUtc)}</span>
              </li>
            ))}
          </ul>
        ) : null}
      </article>
    </section>
  );
}
