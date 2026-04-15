import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  HubConnectionBuilder,
  HubConnectionState,
  LogLevel,
} from "@microsoft/signalr";

import {
  getActiveTrainingRun,
  getProcessedDatasets,
  getRegistryModels,
  isTrainingRunSocketEventApiResponse,
  postCancelTrainingRun,
  postCreateTrainingRun,
  TrainingsApiError,
} from "../api/trainings";
import type {
  ProcessedDatasetListItemApiResponse,
  RegistryModelListItemApiResponse,
  TrainingRunApiResponse,
  TrainingRunSocketEventApiResponse,
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
      message: null;
      errorType: null;
      httpStatus: null;
    }
  | {
      kind: "loading";
      message: null;
      errorType: null;
      httpStatus: null;
    }
  | {
      kind: "success";
      message: string;
      errorType: null;
      httpStatus: number;
    }
  | {
      kind: "error";
      message: string;
      errorType: string | null;
      httpStatus: number | null;
    };

type ToastState = {
  kind: "info" | "success" | "error";
  message: string;
} | null;

type SocketStatus =
  | "idle"
  | "connecting"
  | "connected"
  | "reconnecting"
  | "disconnected";

const defaultModelsState: LoadableState<RegistryModelListItemApiResponse[]> = {
  kind: "idle",
  data: null,
  error: null,
  errorType: null,
  httpStatus: null,
};

const defaultDatasetsState: LoadableState<ProcessedDatasetListItemApiResponse[]> = {
  kind: "idle",
  data: null,
  error: null,
  errorType: null,
  httpStatus: null,
};

const defaultActiveRunState: LoadableState<TrainingRunApiResponse | null> = {
  kind: "idle",
  data: null,
  error: null,
  errorType: null,
  httpStatus: null,
};

const defaultRequestState: RequestState = {
  kind: "idle",
  message: null,
  errorType: null,
  httpStatus: null,
};

const activeStatuses = new Set(["queued", "starting", "running", "cancelling"]);
const terminalStatuses = new Set(["succeeded", "failed", "cancelled"]);

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

function formatEtaSeconds(seconds: number | null): string {
  if (seconds === null || seconds < 0) {
    return "brak";
  }

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}m ${remainingSeconds}s`;
}

function resolveProgressChannelUrl(progressChannelUrl: string): string {
  if (/^https?:\/\//i.test(progressChannelUrl)) {
    return progressChannelUrl;
  }

  if (progressChannelUrl.startsWith("/")) {
    return `${window.location.origin}${progressChannelUrl}`;
  }

  return `${window.location.origin}/${progressChannelUrl}`;
}

function getStatusClassName(status: string | null): string {
  if (status === "succeeded") {
    return "status-success";
  }

  if (status === "failed" || status === "cancelled") {
    return "status-error";
  }

  return "status-loading";
}

function isRunActive(run: TrainingRunApiResponse | null): boolean {
  if (!run) {
    return false;
  }

  return activeStatuses.has(run.status);
}

function toSocketEvent(
  payload: unknown
): TrainingRunSocketEventApiResponse | null {
  if (isTrainingRunSocketEventApiResponse(payload)) {
    return payload;
  }

  if (!payload || typeof payload !== "object") {
    return null;
  }

  const record = payload as Record<string, unknown>;
  if (isTrainingRunSocketEventApiResponse(record.event)) {
    return record.event;
  }

  if (isTrainingRunSocketEventApiResponse(record.payload)) {
    return record.payload;
  }

  return null;
}

type Uc06TrainingSectionProps = {
  apiBaseUrl: string;
};

export function Uc06TrainingSection({ apiBaseUrl }: Uc06TrainingSectionProps) {
  const tokenFromEnv = import.meta.env.VITE_ADMIN_TOKEN?.trim() ?? "";
  const adminToken = tokenFromEnv || null;

  const [modelsState, setModelsState] = useState(defaultModelsState);
  const [datasetsState, setDatasetsState] = useState(defaultDatasetsState);
  const [activeRunState, setActiveRunState] = useState(defaultActiveRunState);
  const [startState, setStartState] = useState(defaultRequestState);
  const [cancelState, setCancelState] = useState(defaultRequestState);
  const [selectedModelName, setSelectedModelName] = useState<string | null>(null);
  const [selectedDatasetName, setSelectedDatasetName] = useState<string | null>(null);
  const [eventsFeed, setEventsFeed] = useState<TrainingRunSocketEventApiResponse[]>(
    []
  );
  const [latestEvent, setLatestEvent] =
    useState<TrainingRunSocketEventApiResponse | null>(null);
  const [socketStatus, setSocketStatus] = useState<SocketStatus>("idle");
  const [toast, setToast] = useState<ToastState>(null);

  const connectionRef = useRef<ReturnType<
    HubConnectionBuilder["build"]
  > | null>(null);
  const latestSequenceRef = useRef<number>(-1);

  const pushToast = useCallback((nextToast: ToastState) => {
    setToast(nextToast);
  }, []);

  useEffect(() => {
    if (!toast) {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      setToast(null);
    }, 5000);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [toast]);

  const loadModels = useCallback(async () => {
    setModelsState((previous) => ({
      kind: "loading",
      data: previous.data,
      error: null,
      errorType: null,
      httpStatus: null,
    }));

    try {
      const response = await getRegistryModels(apiBaseUrl, adminToken);
      setModelsState({
        kind: "success",
        data: response.items,
        error: null,
        errorType: null,
        httpStatus: 200,
      });
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Nie udało się pobrać listy modeli.";
      setModelsState({
        kind: "error",
        data: null,
        error: message,
        errorType: error instanceof TrainingsApiError ? error.errorType ?? null : null,
        httpStatus: error instanceof TrainingsApiError ? error.status : null,
      });
    }
  }, [adminToken, apiBaseUrl]);

  const loadDatasets = useCallback(async () => {
    setDatasetsState((previous) => ({
      kind: "loading",
      data: previous.data,
      error: null,
      errorType: null,
      httpStatus: null,
    }));

    try {
      const response = await getProcessedDatasets(apiBaseUrl, adminToken);
      setDatasetsState({
        kind: "success",
        data: response.items,
        error: null,
        errorType: null,
        httpStatus: 200,
      });
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : "Nie udało się pobrać listy datasetów.";
      setDatasetsState({
        kind: "error",
        data: null,
        error: message,
        errorType: error instanceof TrainingsApiError ? error.errorType ?? null : null,
        httpStatus: error instanceof TrainingsApiError ? error.status : null,
      });
    }
  }, [adminToken, apiBaseUrl]);

  const syncActiveRun = useCallback(
    async (silenceErrors?: boolean) => {
      setActiveRunState((previous) => ({
        kind: "loading",
        data: previous.data,
        error: null,
        errorType: null,
        httpStatus: null,
      }));

      try {
        const run = await getActiveTrainingRun(apiBaseUrl, adminToken);
        setActiveRunState({
          kind: "success",
          data: run,
          error: null,
          errorType: null,
          httpStatus: run ? 200 : 204,
        });

        if (!run) {
          setLatestEvent(null);
          setEventsFeed([]);
          latestSequenceRef.current = -1;
          setSocketStatus("idle");
        }
      } catch (error) {
        if (silenceErrors) {
          return;
        }

        setActiveRunState({
          kind: "error",
          data: null,
          error:
            error instanceof Error
              ? error.message
              : "Nie udało się pobrać aktywnego runu.",
          errorType: error instanceof TrainingsApiError ? error.errorType ?? null : null,
          httpStatus: error instanceof TrainingsApiError ? error.status : null,
        });
      }
    },
    [adminToken, apiBaseUrl]
  );

  useEffect(() => {
    void Promise.all([loadModels(), loadDatasets(), syncActiveRun()]);
  }, [loadDatasets, loadModels, syncActiveRun]);

  const activeRun = activeRunState.data;
  const hasActiveRun = isRunActive(activeRun);
  const displayStatus = latestEvent?.status ?? activeRun?.status ?? "idle";
  const displayStage = latestEvent?.stage ?? "queued";
  const displayProgress = latestEvent?.progress ?? null;
  const displayWarnings = latestEvent?.warnings ?? [];

  useEffect(() => {
    if (!activeRun || activeRun.status !== "starting") {
      return;
    }

    const intervalId = window.setInterval(() => {
      void syncActiveRun(true);
    }, 2000);

    return () => {
      window.clearInterval(intervalId);
    };
  }, [activeRun, syncActiveRun]);

  useEffect(() => {
    if (!activeRun?.runName) {
      return;
    }

    const hubUrl = resolveProgressChannelUrl(activeRun.progressChannelUrl);
    const connection = new HubConnectionBuilder()
      .withUrl(hubUrl, {
        accessTokenFactory: () => adminToken ?? "",
      })
      .withAutomaticReconnect([0, 2000, 5000, 10000])
      .configureLogging(LogLevel.Warning)
      .build();

    connectionRef.current = connection;
    setSocketStatus("connecting");

    const handleSocketEvent = (payload: unknown) => {
      const socketEvent = toSocketEvent(payload);
      if (!socketEvent || socketEvent.runName !== activeRun.runName) {
        return;
      }

      if (socketEvent.sequence < latestSequenceRef.current) {
        return;
      }

      latestSequenceRef.current = socketEvent.sequence;
      setLatestEvent(socketEvent);
      setEventsFeed((previous) =>
        [socketEvent, ...previous.filter((item) => item.sequence !== socketEvent.sequence)].slice(
          0,
          30
        )
      );

      setActiveRunState((previous) => {
        if (previous.kind !== "success" || !previous.data) {
          return previous;
        }

        return {
          kind: "success",
          data: {
            ...previous.data,
            status: socketEvent.status,
          },
          error: null,
          errorType: null,
          httpStatus: previous.httpStatus,
        };
      });

      if (terminalStatuses.has(socketEvent.status)) {
        if (socketEvent.status === "succeeded") {
          pushToast({ kind: "success", message: "Run zakończył się sukcesem." });
        } else if (socketEvent.status === "failed") {
          pushToast({ kind: "error", message: "Run zakończył się błędem." });
        } else if (socketEvent.status === "cancelled") {
          pushToast({ kind: "info", message: "Run został anulowany." });
        }
      }
    };

    const eventNames = [
      "snapshot",
      "statusChanged",
      "progress",
      "completed",
      "failed",
      "cancelled",
      "event",
      "trainingRunEvent",
    ];
    for (const eventName of eventNames) {
      connection.on(eventName, handleSocketEvent);
    }

    connection.onreconnecting(() => {
      setSocketStatus("reconnecting");
      pushToast({ kind: "info", message: "Utracono połączenie SignalR. Trwa reconnect..." });
    });

    connection.onreconnected(() => {
      setSocketStatus("connected");
      pushToast({ kind: "success", message: "Połączenie SignalR zostało odzyskane." });
    });

    connection.onclose(() => {
      setSocketStatus("disconnected");
    });

    let isDisposed = false;

    void connection
      .start()
      .then(() => {
        if (!isDisposed) {
          setSocketStatus("connected");
        }
      })
      .catch((error: unknown) => {
        if (!isDisposed) {
          setSocketStatus("disconnected");
          pushToast({
            kind: "error",
            message:
              error instanceof Error
                ? error.message
                : "Nie udało się połączyć z kanałem SignalR.",
          });
        }
      });

    return () => {
      isDisposed = true;
      for (const eventName of eventNames) {
        connection.off(eventName, handleSocketEvent);
      }
      void connection.stop();
      if (connectionRef.current === connection) {
        connectionRef.current = null;
      }
    };
  }, [activeRun?.progressChannelUrl, activeRun?.runName, adminToken, pushToast]);

  useEffect(() => {
    return () => {
      if (!connectionRef.current) {
        return;
      }

      if (connectionRef.current.state !== HubConnectionState.Disconnected) {
        void connectionRef.current.stop();
      }
    };
  }, []);

  const startDisabled =
    startState.kind === "loading" ||
    hasActiveRun ||
    !selectedModelName ||
    !selectedDatasetName;

  const handleStartTraining = useCallback(async () => {
    if (!selectedModelName || !selectedDatasetName) {
      return;
    }

    setStartState({
      kind: "loading",
      message: null,
      errorType: null,
      httpStatus: null,
    });

    try {
      const run = await postCreateTrainingRun(
        apiBaseUrl,
        {
          baseModelName: selectedModelName,
          processedDatasetName: selectedDatasetName,
        },
        adminToken
      );
      latestSequenceRef.current = -1;
      setLatestEvent(null);
      setEventsFeed([]);
      setActiveRunState({
        kind: "success",
        data: run,
        error: null,
        errorType: null,
        httpStatus: 202,
      });
      setStartState({
        kind: "success",
        message: "Start runu zaakceptowany.",
        errorType: null,
        httpStatus: 202,
      });
      pushToast({ kind: "success", message: "Start runu został zaakceptowany." });
    } catch (error) {
      if (
        error instanceof TrainingsApiError &&
        error.status === 409 &&
        error.errorType === "training_run_already_active"
      ) {
        await syncActiveRun(true);
        setStartState({
          kind: "error",
          message: error.message,
          errorType: error.errorType ?? null,
          httpStatus: error.status,
        });
        pushToast({
          kind: "info",
          message: "Aktywny run już istnieje. Przełączono na monitoring.",
        });
        return;
      }

      setStartState({
        kind: "error",
        message:
          error instanceof Error ? error.message : "Nie udało się uruchomić treningu.",
        errorType: error instanceof TrainingsApiError ? error.errorType ?? null : null,
        httpStatus: error instanceof TrainingsApiError ? error.status : null,
      });
      pushToast({ kind: "error", message: "Start runu nie powiódł się." });
    }
  }, [
    adminToken,
    apiBaseUrl,
    pushToast,
    selectedDatasetName,
    selectedModelName,
    syncActiveRun,
  ]);

  const handleCancelTraining = useCallback(async () => {
    if (!activeRun) {
      return;
    }

    setCancelState({
      kind: "loading",
      message: null,
      errorType: null,
      httpStatus: null,
    });

    try {
      const result = await postCancelTrainingRun(apiBaseUrl, activeRun.runName, adminToken);
      setCancelState({
        kind: "success",
        message: `Anulowanie przyjęte: ${result.requestDisposition}.`,
        errorType: null,
        httpStatus: 202,
      });

      if (result.status) {
        setActiveRunState((previous) => {
          if (previous.kind !== "success" || !previous.data) {
            return previous;
          }

          return {
            kind: "success",
            data: {
              ...previous.data,
              status: result.status ?? previous.data.status,
            },
            error: null,
            errorType: null,
            httpStatus: previous.httpStatus,
          };
        });
      }

      pushToast({ kind: "info", message: "Żądanie anulowania zostało przyjęte." });
    } catch (error) {
      setCancelState({
        kind: "error",
        message:
          error instanceof Error ? error.message : "Nie udało się anulować aktywnego runu.",
        errorType: error instanceof TrainingsApiError ? error.errorType ?? null : null,
        httpStatus: error instanceof TrainingsApiError ? error.status : null,
      });
      pushToast({ kind: "error", message: "Anulowanie runu nie powiodło się." });
    }
  }, [activeRun, adminToken, apiBaseUrl, pushToast]);

  const models = useMemo(() => modelsState.data ?? [], [modelsState.data]);
  const datasets = useMemo(() => datasetsState.data ?? [], [datasetsState.data]);
  const trainableModels = useMemo(
    () => models.filter((model) => model.canStartTraining),
    [models]
  );

  return (
    <section className="hero-card uc06-section">
      <p className="eyebrow">UC-06 — Orkiestracja treningu</p>
      <h2>Start i monitoring aktywnego runu</h2>
      <p className="hero-copy">
        Wybierz model bazowy i dataset, uruchom trening oraz monitoruj postęp przez
        kanał SignalR.
      </p>

      {toast ? (
        <p className={`status-banner ${toast.kind === "error" ? "status-error" : toast.kind === "success" ? "status-success" : "status-loading"}`}>
          {toast.message}
        </p>
      ) : null}

      <div className="uc06-layout">
        <div className="uc06-column">
          <article className="uc06-panel">
            <h3>Krok 1 — Wybierz model bazowy</h3>
            <button
              className="secondary-button"
              type="button"
              disabled={modelsState.kind === "loading"}
              onClick={() => void loadModels()}
            >
              {modelsState.kind === "loading" ? "Odświeżanie..." : "Odśwież modele"}
            </button>
            {modelsState.kind === "error" ? (
              <p className="status-banner status-error">{modelsState.error}</p>
            ) : null}
            {trainableModels.length === 0 && modelsState.kind === "success" ? (
              <p className="muted-copy">Brak modeli możliwych do treningu.</p>
            ) : null}
            <div className="uc06-card-list">
              {trainableModels.map((model) => (
                <button
                  key={model.name}
                  type="button"
                  className={`uc06-select-card ${selectedModelName === model.name ? "is-selected" : ""}`}
                  onClick={() => setSelectedModelName(model.name)}
                >
                  <strong>{model.displayName}</strong>
                  <span>
                    <code>{model.name}</code>
                  </span>
                  <span>Input profile: {model.inputProfile}</span>
                  <span>Utworzono: {formatTimestamp(model.createdAtUtc)}</span>
                </button>
              ))}
            </div>
          </article>

          <article className="uc06-panel">
            <h3>Krok 2 — Wybierz dataset</h3>
            <button
              className="secondary-button"
              type="button"
              disabled={datasetsState.kind === "loading"}
              onClick={() => void loadDatasets()}
            >
              {datasetsState.kind === "loading"
                ? "Odświeżanie..."
                : "Odśwież datasety"}
            </button>
            {datasetsState.kind === "error" ? (
              <p className="status-banner status-error">{datasetsState.error}</p>
            ) : null}
            {datasets.length === 0 && datasetsState.kind === "success" ? (
              <p className="muted-copy">Brak datasetów przetworzonych.</p>
            ) : null}
            <div className="uc06-card-list">
              {datasets.map((dataset) => (
                <button
                  key={dataset.name}
                  type="button"
                  className={`uc06-select-card ${selectedDatasetName === dataset.name ? "is-selected" : ""}`}
                  onClick={() => setSelectedDatasetName(dataset.name)}
                >
                  <strong>
                    <code>{dataset.name}</code>
                  </strong>
                  <span>{dataset.fileName}</span>
                  <span>Profil: {dataset.preprocessingProfile}</span>
                  <span>
                    Próbki: train {dataset.sampleCounts.train}, val {dataset.sampleCounts.val}
                    , test {dataset.sampleCounts.test}
                  </span>
                </button>
              ))}
            </div>
          </article>

          <article className="uc06-panel">
            <h3>Krok 3 — Start runu</h3>
            <button
              className="primary-button"
              type="button"
              disabled={startDisabled}
              onClick={() => void handleStartTraining()}
            >
              {startState.kind === "loading" ? "Uruchamianie..." : "Start treningu"}
            </button>
            {hasActiveRun ? (
              <p className="muted-copy">
                W systemie jest aktywny run. Start nowego runu jest zablokowany.
              </p>
            ) : null}
            {startState.kind === "error" ? (
              <p className="status-banner status-error">{startState.message}</p>
            ) : null}
            {startState.kind === "success" ? (
              <p className="status-banner status-success">{startState.message}</p>
            ) : null}
          </article>
        </div>

        <div className="uc06-column">
          <article className="uc06-panel uc06-sticky">
            <h3>Aktywny run</h3>
            <button
              className="secondary-button"
              type="button"
              disabled={activeRunState.kind === "loading"}
              onClick={() => void syncActiveRun()}
            >
              {activeRunState.kind === "loading"
                ? "Synchronizacja..."
                : "Odśwież aktywny run"}
            </button>

            {activeRunState.kind === "error" ? (
              <p className="status-banner status-error">{activeRunState.error}</p>
            ) : null}

            {!activeRun ? (
              <p className="muted-copy">Brak aktywnego runu.</p>
            ) : (
              <>
                <p className={`status-banner ${getStatusClassName(displayStatus)}`}>
                  Status: <strong>{displayStatus}</strong> | Stage:{" "}
                  <strong>{displayStage}</strong>
                </p>
                <p className="muted-copy">
                  Run: <code>{activeRun.runName}</code>
                </p>
                <p className="muted-copy">
                  Model: <code>{activeRun.baseModelName}</code>
                </p>
                <p className="muted-copy">
                  Dataset: <code>{activeRun.processedDatasetName}</code>
                </p>
                <p className="muted-copy">
                  Utworzono: {formatTimestamp(activeRun.createdAtUtc)}
                </p>
                <p className="muted-copy">
                  Połączenie SignalR: <strong>{socketStatus}</strong>
                </p>
                <div className="uc06-progress-grid">
                  <span>Postęp: {displayProgress?.percent ?? "brak"}%</span>
                  <span>
                    Epoki: {displayProgress?.epochCurrent ?? "-"} /{" "}
                    {displayProgress?.epochTotal ?? "-"}
                  </span>
                  <span>ETA: {formatEtaSeconds(displayProgress?.etaSeconds ?? null)}</span>
                </div>
                <div className="uc06-timeline">
                  {["queued", "training", "evaluation", "finished"].map((stage) => (
                    <span
                      key={stage}
                      className={`uc06-timeline-step ${displayStage === stage ? "is-active" : ""}`}
                    >
                      {stage}
                    </span>
                  ))}
                </div>

                {displayWarnings.length > 0 ? (
                  <ul className="examples-list">
                    {displayWarnings.map((warning) => (
                      <li key={warning}>Ostrzeżenie: {warning}</li>
                    ))}
                  </ul>
                ) : null}

                {activeRun && activeStatuses.has(displayStatus) ? (
                  <button
                    className="secondary-button"
                    type="button"
                    disabled={cancelState.kind === "loading"}
                    onClick={() => void handleCancelTraining()}
                  >
                    {cancelState.kind === "loading" ? "Anulowanie..." : "Anuluj run"}
                  </button>
                ) : null}
                {cancelState.kind === "error" ? (
                  <p className="status-banner status-error">{cancelState.message}</p>
                ) : null}
                {cancelState.kind === "success" ? (
                  <p className="status-banner status-success">{cancelState.message}</p>
                ) : null}
              </>
            )}
          </article>

          <article className="uc06-panel">
            <h3>Feed zdarzeń</h3>
            {eventsFeed.length === 0 ? (
              <p className="muted-copy">Brak zdarzeń. Feed pojawi się po snapshot/eventach.</p>
            ) : (
              <ul className="uc06-events-feed">
                {eventsFeed.map((eventItem) => (
                  <li key={`${eventItem.sequence}-${eventItem.eventType}`}>
                    <div>
                      <strong>{eventItem.eventType}</strong> ({eventItem.sequence})
                    </div>
                    <div>
                      status: {eventItem.status}, stage: {eventItem.stage}
                    </div>
                    {eventItem.message ? <div>{eventItem.message}</div> : null}
                    <div>{formatTimestamp(eventItem.occurredAtUtc)}</div>
                  </li>
                ))}
              </ul>
            )}
          </article>
        </div>
      </div>
    </section>
  );
}
