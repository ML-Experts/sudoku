import { useCallback, useEffect, useMemo, useState } from "react";

import {
  getTrainingRunDetails,
  getRegistryModels,
  getTrainingRuns,
  TrainingsApiError,
} from "../api/trainings";
import type {
  RegistryModelListItemApiResponse,
  TrainingRunDetailsApiResponse,
  TrainingRunListItemApiResponse,
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

type Uc08CatalogSectionProps = {
  apiBaseUrl: string;
  accessToken?: string | null;
  onUnauthorized?: () => void;
};

const defaultRunsState: LoadableState<TrainingRunListItemApiResponse[]> = {
  kind: "idle",
  data: null,
  error: null,
  errorType: null,
  httpStatus: null,
};

const defaultModelsState: LoadableState<RegistryModelListItemApiResponse[]> = {
  kind: "idle",
  data: null,
  error: null,
  errorType: null,
  httpStatus: null,
};

const defaultDetailsState: LoadableState<TrainingRunDetailsApiResponse> = {
  kind: "idle",
  data: null,
  error: null,
  errorType: null,
  httpStatus: null,
};

function formatTimestamp(timestampUtc: string | null): string {
  if (!timestampUtc) {
    return "-";
  }

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

function formatMetric(value: number | null | undefined): string {
  if (typeof value !== "number") {
    return "-";
  }

  return value.toFixed(4);
}

export function Uc08CatalogSection({
  apiBaseUrl,
  accessToken,
  onUnauthorized,
}: Uc08CatalogSectionProps) {
  const [runsState, setRunsState] = useState(defaultRunsState);
  const [modelsState, setModelsState] = useState(defaultModelsState);
  const [selectedRunName, setSelectedRunName] = useState<string | null>(null);
  const [detailsState, setDetailsState] = useState(defaultDetailsState);

  const loadCatalog = useCallback(async () => {
    if (!accessToken) {
      setRunsState(defaultRunsState);
      setModelsState(defaultModelsState);
      return;
    }

    setRunsState((previous) => ({
      kind: "loading",
      data: previous.data,
      error: null,
      errorType: null,
      httpStatus: null,
    }));
    setModelsState((previous) => ({
      kind: "loading",
      data: previous.data,
      error: null,
      errorType: null,
      httpStatus: null,
    }));

    try {
      const [runsResponse, modelsResponse] = await Promise.all([
        getTrainingRuns(apiBaseUrl, accessToken),
        getRegistryModels(apiBaseUrl, accessToken),
      ]);

      setRunsState({
        kind: "success",
        data: runsResponse.items,
        error: null,
        errorType: null,
        httpStatus: 200,
      });
      setModelsState({
        kind: "success",
        data: modelsResponse.items,
        error: null,
        errorType: null,
        httpStatus: 200,
      });
    } catch (error) {
      if (error instanceof TrainingsApiError && error.status === 401) {
        onUnauthorized?.();
      }

      const message =
        error instanceof Error ? error.message : "Nie udalo sie odczytac katalogu.";
      const errorType = error instanceof TrainingsApiError ? error.errorType ?? null : null;
      const httpStatus = error instanceof TrainingsApiError ? error.status : null;

      setRunsState({
        kind: "error",
        data: null,
        error: message,
        errorType,
        httpStatus,
      });
      setModelsState({
        kind: "error",
        data: null,
        error: message,
        errorType,
        httpStatus,
      });
    }
  }, [accessToken, apiBaseUrl, onUnauthorized]);

  useEffect(() => {
    void loadCatalog();
  }, [loadCatalog]);

  const loadRunDetails = useCallback(
    async (runName: string) => {
      if (!accessToken) {
        setDetailsState(defaultDetailsState);
        return;
      }

      setSelectedRunName(runName);
      setDetailsState((previous) => ({
        kind: "loading",
        data: previous.data,
        error: null,
        errorType: null,
        httpStatus: null,
      }));

      try {
        const details = await getTrainingRunDetails(apiBaseUrl, runName, accessToken);
        setDetailsState({
          kind: "success",
          data: details,
          error: null,
          errorType: null,
          httpStatus: 200,
        });
      } catch (error) {
        if (error instanceof TrainingsApiError && error.status === 401) {
          onUnauthorized?.();
        }

        setDetailsState({
          kind: "error",
          data: null,
          error:
            error instanceof Error
              ? error.message
              : "Nie udalo sie odczytac szczegolow runu.",
          errorType: error instanceof TrainingsApiError ? error.errorType ?? null : null,
          httpStatus: error instanceof TrainingsApiError ? error.status : null,
        });
      }
    },
    [accessToken, apiBaseUrl, onUnauthorized],
  );

  const runs = runsState.data ?? [];
  const models = modelsState.data ?? [];
  const activeRunsCount = useMemo(
    () =>
      runs.filter((run) =>
        ["queued", "starting", "running", "cancelling"].includes(run.status),
      ).length,
    [runs],
  );
  const bootstrapModelsCount = useMemo(
    () => models.filter((model) => model.sourceType === "bootstrap").length,
    [models],
  );
  const trainingModelsCount = useMemo(
    () => models.filter((model) => model.sourceType !== "bootstrap").length,
    [models],
  );
  const modelNames = useMemo(() => new Set(models.map((model) => model.name)), [models]);
  const runNames = useMemo(() => new Set(runs.map((run) => run.runName)), [runs]);

  return (
    <section className="hero-card uc12-section">
      <p className="eyebrow">UC-08 — Katalog treningow i modeli</p>
      <h2>Lista runow i rejestr modeli</h2>
      <p className="hero-copy">
        Widok laczy dane katalogowe z <code>GET /api/trainings</code> i{" "}
        <code>GET /api/models/registry</code>.
      </p>

      <div className="examples-row-actions">
        <button
          className="secondary-button"
          type="button"
          disabled={runsState.kind === "loading" || modelsState.kind === "loading"}
          onClick={() => void loadCatalog()}
        >
          {runsState.kind === "loading" || modelsState.kind === "loading"
            ? "Odswiezanie..."
            : "Odswiez katalog"}
        </button>
      </div>

      {runsState.kind === "error" ? (
        <p className="status-banner status-error">{runsState.error}</p>
      ) : null}

      <article className="uc12-panel">
        <h3>Podsumowanie katalogu</h3>
        <dl className="result-grid">
          <div>
            <dt>Treningi lacznie</dt>
            <dd>{runs.length}</dd>
          </div>
          <div>
            <dt>Treningi aktywne</dt>
            <dd>{activeRunsCount}</dd>
          </div>
          <div>
            <dt>Modele bootstrap</dt>
            <dd>{bootstrapModelsCount}</dd>
          </div>
          <div>
            <dt>Modele z treningu</dt>
            <dd>{trainingModelsCount}</dd>
          </div>
        </dl>
      </article>

      <article className="uc12-panel">
        <h3>Runy treningowe</h3>
        {runs.length === 0 ? (
          <p className="muted-copy">Brak runow treningowych do wyswietlenia.</p>
        ) : (
          <ul className="uc12-processed-list">
            {runs.map((run) => {
              const hasProducedModel = modelNames.has(run.producedModelName);

              return (
                <li key={run.runName}>
                  <strong>
                    {run.runName} ({run.status})
                  </strong>
                  <span>
                    dataset: {run.processedDatasetName} | base: {run.baseModelName} | produced:{" "}
                    {run.producedModelName}
                  </span>
                  <span>
                    created: {formatTimestamp(run.createdAtUtc)} | updated:{" "}
                    {formatTimestamp(run.updatedAtUtc)}
                  </span>
                  <span>
                    accuracy: {formatMetric(run.metricsSummary?.accuracy)} | macroF1:{" "}
                    {formatMetric(run.metricsSummary?.macroF1)} | progress:{" "}
                    {run.progress?.percent ?? "-"}%
                  </span>
                  <span>
                    model registry link:{" "}
                    <code>{hasProducedModel ? "model_found" : "model_not_found"}</code>
                  </span>
                  <span className="examples-row-actions">
                    <button
                      type="button"
                      className="secondary-button"
                      onClick={() => void loadRunDetails(run.runName)}
                    >
                      Szczegoly runu (UC-09)
                    </button>
                  </span>
                </li>
              );
            })}
          </ul>
        )}
      </article>

      <article className="uc12-panel">
        <h3>Rejestr modeli</h3>
        {models.length === 0 ? (
          <p className="muted-copy">Brak modeli w rejestrze.</p>
        ) : (
          <ul className="uc12-processed-list">
            {models.map((model) => {
              const hasSourceRun = model.sourceRunName
                ? runNames.has(model.sourceRunName)
                : null;

              return (
                <li key={model.name}>
                  <strong>
                    {model.displayName} ({model.name})
                  </strong>
                  <span>
                    sourceType: {model.sourceType} | sourceRunName:{" "}
                    {model.sourceRunName ?? "-"} | parent: {model.parentModelName ?? "-"}
                  </span>
                  <span>
                    canStartTraining: {String(model.canStartTraining)} | canUseForInference:{" "}
                    {String(model.canUseForInference)}
                  </span>
                  <span>
                    run relation:{" "}
                    <code>
                      {hasSourceRun === null
                        ? "bootstrap_without_run"
                        : hasSourceRun
                          ? "run_found"
                          : "run_not_found"}
                    </code>
                  </span>
                </li>
              );
            })}
          </ul>
        )}
      </article>

      <article className="uc12-panel">
        <h3>UC-09 — Szczegoly wybranego runu</h3>
        {!selectedRunName ? (
          <p className="muted-copy">
            Wybierz run z listy "Runy treningowe", aby odczytac szczegoly.
          </p>
        ) : null}
        {selectedRunName ? (
          <p className="muted-copy">
            Wybrany run: <code>{selectedRunName}</code>
          </p>
        ) : null}

        {detailsState.kind === "loading" ? (
          <p className="status-banner status-loading">
            Pobieranie szczegolow runu treningowego...
          </p>
        ) : null}

        {detailsState.kind === "error" ? (
          <>
            <p className="status-banner status-error">{detailsState.error}</p>
            <p className="muted-copy">
              HTTP: {detailsState.httpStatus ?? "-"} | typ: {detailsState.errorType ?? "-"}
            </p>
          </>
        ) : null}

        {detailsState.kind === "success" ? (
          <>
            <dl className="result-grid">
              <div>
                <dt>Status</dt>
                <dd>{detailsState.data.status}</dd>
              </div>
              <div>
                <dt>Stage</dt>
                <dd>{detailsState.data.stage ?? "-"}</dd>
              </div>
              <div>
                <dt>Created</dt>
                <dd>{formatTimestamp(detailsState.data.createdAtUtc)}</dd>
              </div>
              <div>
                <dt>Finished</dt>
                <dd>{formatTimestamp(detailsState.data.finishedAtUtc)}</dd>
              </div>
              <div>
                <dt>Base model</dt>
                <dd>{detailsState.data.baseModel.name}</dd>
              </div>
              <div>
                <dt>Produced model</dt>
                <dd>{detailsState.data.producedModel?.name ?? "-"}</dd>
              </div>
              <div>
                <dt>Dataset</dt>
                <dd>{detailsState.data.dataset.processedDatasetName}</dd>
              </div>
              <div>
                <dt>Benchmark</dt>
                <dd>{detailsState.data.configuration.benchmarkName}</dd>
              </div>
            </dl>

            <p className="muted-copy">
              reportStatus: <code>{detailsState.data.report.status}</code> | accuracy:{" "}
              {formatMetric(detailsState.data.report.summary?.accuracy)} | precisionMacro:{" "}
              {formatMetric(detailsState.data.report.summary?.precisionMacro)} | recallMacro:{" "}
              {formatMetric(detailsState.data.report.summary?.recallMacro)} | f1Macro:{" "}
              {formatMetric(detailsState.data.report.summary?.f1Macro)}
            </p>

            {detailsState.data.report.history.length > 0 ? (
              <div className="examples-table-wrap">
                <table className="examples-table">
                  <thead>
                    <tr>
                      <th scope="col">Epoch</th>
                      <th scope="col">Train loss</th>
                      <th scope="col">Validation loss</th>
                      <th scope="col">Train accuracy</th>
                      <th scope="col">Validation accuracy</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detailsState.data.report.history.map((point) => (
                      <tr key={`history-${point.epoch}`}>
                        <td>{point.epoch}</td>
                        <td>{formatMetric(point.trainLoss)}</td>
                        <td>{formatMetric(point.validationLoss)}</td>
                        <td>{formatMetric(point.trainAccuracy)}</td>
                        <td>{formatMetric(point.validationAccuracy)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="muted-copy">Brak historii metryk epoch dla tego runu.</p>
            )}

            {detailsState.data.report.confusionMatrix ? (
              <div className="examples-table-wrap">
                <table className="examples-table">
                  <thead>
                    <tr>
                      <th scope="col">actual/predicted</th>
                      {detailsState.data.report.confusionMatrix.classNames.map((className) => (
                        <th key={`cm-header-${className}`} scope="col">
                          {className}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {detailsState.data.report.confusionMatrix.matrix.map((row, rowIndex) => (
                      <tr key={`cm-row-${rowIndex}`}>
                        <td>{detailsState.data.report.confusionMatrix?.classNames[rowIndex] ?? rowIndex}</td>
                        {row.map((value, cellIndex) => (
                          <td key={`cm-cell-${rowIndex}-${cellIndex}`}>{value}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="muted-copy">
                Brak macierzy pomylek (report nie jest gotowy albo jest uszkodzony).
              </p>
            )}

            {detailsState.data.warnings.length > 0 ? (
              <ul className="uc12-warnings-list">
                {detailsState.data.warnings.map((warning, index) => (
                  <li key={`run-warning-${index}`}>{warning}</li>
                ))}
              </ul>
            ) : null}
          </>
        ) : null}
      </article>
    </section>
  );
}
