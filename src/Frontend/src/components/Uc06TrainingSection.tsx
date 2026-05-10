import {
  HubConnectionBuilder,
  HubConnectionState,
  LogLevel,
  type HubConnection,
} from "@microsoft/signalr";
import { useCallback, useEffect, useRef, useState } from "react";

import {
  getActiveTrainingRun,
  getRegistryModels,
  postCancelTrainingRun,
  postCreateTrainingRun,
  TrainingsApiError,
} from "../api/trainings";
import { getProcessedDatasets } from "../api/datasets";
import type {
  CancelTrainingRunApiResponse,
  ProcessedDatasetListItemApiResponse,
  RegistryModelListItemApiResponse,
  TrainingRunApiResponse,
  TrainingRunSocketEventApiResponse,
} from "../types/api";

type Uc06TrainingSectionProps = {
  apiBaseUrl: string;
  accessToken?: string | null;
  onUnauthorized?: () => void;
};

type RemoteDataState<T> =
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

type RequestState<T> =
  | {
      kind: "idle";
      response: T | null;
      error: null;
      errorType: null;
      httpStatus: null;
    }
  | {
      kind: "loading";
      response: T | null;
      error: null;
      errorType: null;
      httpStatus: null;
    }
  | {
      kind: "success";
      response: T;
      error: null;
      errorType: null;
      httpStatus: number;
    }
  | {
      kind: "error";
      response: T | null;
      error: string;
      errorType: string | null;
      httpStatus: number | null;
    };

type SocketState =
  | "disconnected"
  | "connecting"
  | "connected"
  | "reconnecting"
  | "completed";

const defaultModelsState: RemoteDataState<RegistryModelListItemApiResponse[]> = {
  kind: "idle",
  data: null,
  error: null,
  errorType: null,
  httpStatus: null,
};

const defaultDatasetsState: RemoteDataState<ProcessedDatasetListItemApiResponse[]> = {
  kind: "idle",
  data: null,
  error: null,
  errorType: null,
  httpStatus: null,
};

const defaultActiveRunState: RemoteDataState<TrainingRunApiResponse | null> = {
  kind: "idle",
  data: null,
  error: null,
  errorType: null,
  httpStatus: null,
};

const defaultStartState: RequestState<TrainingRunApiResponse> = {
  kind: "idle",
  response: null,
  error: null,
  errorType: null,
  httpStatus: null,
};

const defaultCancelState: RequestState<CancelTrainingRunApiResponse> = {
  kind: "idle",
  response: null,
  error: null,
  errorType: null,
  httpStatus: null,
};

const activeStatuses = ["queued", "starting", "running", "cancelling"];
const terminalStatuses = ["succeeded", "failed", "cancelled"];

function isTerminalStatus(status: string): boolean {
  return terminalStatuses.includes(status);
}

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

function formatProgressPercent(value: number | null | undefined): string {
  if (typeof value !== "number") {
    return "-";
  }

  const clamped = Math.max(0, Math.min(100, value));
  return `${clamped.toFixed(1)}%`;
}

function buildHubUrl(progressChannelUrl: string, apiBaseUrl: string): string {
  if (progressChannelUrl.startsWith("http://") || progressChannelUrl.startsWith("https://")) {
    return progressChannelUrl;
  }

  if (apiBaseUrl.startsWith("http://") || apiBaseUrl.startsWith("https://")) {
    return new URL(progressChannelUrl, apiBaseUrl).toString();
  }

  return progressChannelUrl.startsWith("/")
    ? progressChannelUrl
    : `/${progressChannelUrl}`;
}

function toSyntheticStage(status: string): string {
  if (status === "queued" || status === "starting") {
    return "queued";
  }

  if (status === "succeeded" || status === "cancelled") {
    return "finished";
  }

  if (status === "failed") {
    return "evaluation";
  }

  return "training";
}

function normalizeSocketEvent(
  payload: unknown,
): TrainingRunSocketEventApiResponse | null {
  if (!payload || typeof payload !== "object") {
    return null;
  }

  const record = payload as Record<string, unknown>;
  if (
    typeof record.eventType === "string" &&
    typeof record.sequence === "number" &&
    typeof record.runName === "string" &&
    typeof record.status === "string" &&
    typeof record.stage === "string" &&
    typeof record.occurredAtUtc === "string" &&
    (typeof record.message === "string" || record.message === null) &&
    (typeof record.progress === "object" || record.progress === null) &&
    Array.isArray(record.warnings) &&
    (typeof record.result === "object" || record.result === null) &&
    (typeof record.failure === "object" || record.failure === null)
  ) {
    return record as unknown as TrainingRunSocketEventApiResponse;
  }

  const isLegacyPayload =
    typeof record.messageKind === "string" &&
    typeof record.runName === "string" &&
    typeof record.status === "string" &&
    typeof record.createdAtUtc === "string";
  if (!isLegacyPayload) {
    return null;
  }

  const status = String(record.status);
  const eventType =
    record.messageKind === "snapshot"
      ? "snapshot"
      : typeof record.lastEventType === "string"
        ? record.lastEventType
        : "statusChanged";
  const sequence =
    typeof record.lastAcceptedSequence === "number"
      ? record.lastAcceptedSequence
      : 0;
  const occurredAtUtc =
    typeof record.updatedAtUtc === "string"
      ? record.updatedAtUtc
      : String(record.createdAtUtc);
  const legacyProgress =
    record.progress && typeof record.progress === "object"
      ? (record.progress as Record<string, unknown>)
      : null;
  const warnings: string[] = [];
  if (Array.isArray(record.warnings)) {
    for (const warning of record.warnings) {
      if (typeof warning === "string") {
        warnings.push(warning);
      }
    }
  }
  if (Array.isArray(record.cleanupWarnings)) {
    for (const warning of record.cleanupWarnings) {
      if (typeof warning === "string") {
        warnings.push(warning);
      }
    }
  }

  const result =
    status === "succeeded"
      ? {
          producedModelName:
            typeof record.producedModelName === "string"
              ? record.producedModelName
              : String(record.runName),
          reportStatus:
            typeof record.reportStatus === "string" ? record.reportStatus : "ready",
          canUseProducedModelForInference: true,
          primaryArtifactRelativePath:
            typeof record.reportRelativePath === "string"
              ? record.reportRelativePath
              : "artifacts/model.keras",
          summaryRelativePath:
            typeof record.reportRelativePath === "string"
              ? record.reportRelativePath
              : null,
          metricsRelativePath: null,
          confusionMatrixRelativePath: null,
        }
      : null;
  const failure =
    status === "failed"
      ? {
          errorType: "training_run_failed",
          message:
            typeof record.failureReason === "string" && record.failureReason.trim()
              ? record.failureReason
              : "Run treningowy zakonczyl sie bledem technicznym.",
          canUseProducedModelForInference: false,
        }
      : null;

  return {
    eventType,
    sequence,
    runName: String(record.runName),
    status,
    stage: toSyntheticStage(status),
    occurredAtUtc,
    message: null,
    progress: legacyProgress
      ? {
          percent:
            typeof legacyProgress.percent === "number"
              ? legacyProgress.percent
              : null,
          epochCurrent:
            typeof legacyProgress.epoch === "number" ? legacyProgress.epoch : null,
          epochTotal:
            typeof legacyProgress.totalEpochs === "number"
              ? legacyProgress.totalEpochs
              : null,
          etaSeconds: null,
        }
      : null,
    warnings,
    result,
    failure,
  };
}

function toStartErrorHint(status: number | null): string | null {
  if (status === null) {
    return null;
  }

  const hints: Record<number, string> = {
    400: "Sprawdz wybor modelu i datasetu.",
    401: "Sesja administracyjna wygasla. Zaloguj sie ponownie.",
    404: "Model bazowy albo dataset zostal usuniety.",
    409: "Aktywny run juz istnieje. Interfejs powinien przelaczyc sie do monitoringu.",
    422: "Wybrany model lub dataset nie przechodzi walidacji treningu.",
    500: "Blad techniczny backendu. Zachowaj wybor i sproboj ponownie.",
    503: "Integracja backendu z ML jest chwilowo niedostepna.",
    504: "Start runu przekroczyl limit czasu.",
  };

  return hints[status] ?? null;
}

function toCancelDispositionHint(response: CancelTrainingRunApiResponse): string {
  const dispositionCopy: Record<string, string> = {
    cancellationRequested: "Zadanie anulowania zostalo przyjete.",
    alreadyCancelling: "Run byl juz w trakcie anulowania.",
    noopAlreadyFinished: "Run byl juz zakonczony - cancel nie zmienil stanu.",
    noopNoMatchingRun: "Nie znaleziono dopasowanego runu - cancel potraktowano jako no-op.",
  };

  return dispositionCopy[response.requestDisposition] ?? "Backend przyjal zadanie cancel.";
}

export function Uc06TrainingSection({
  apiBaseUrl,
  accessToken,
  onUnauthorized,
}: Uc06TrainingSectionProps) {
  const [modelsState, setModelsState] = useState(defaultModelsState);
  const [datasetsState, setDatasetsState] = useState(defaultDatasetsState);
  const [activeRunState, setActiveRunState] = useState(defaultActiveRunState);
  const [startState, setStartState] = useState(defaultStartState);
  const [cancelState, setCancelState] = useState(defaultCancelState);
  const [selectedModelName, setSelectedModelName] = useState("");
  const [selectedDatasetName, setSelectedDatasetName] = useState("");
  const [activeRun, setActiveRun] = useState<TrainingRunApiResponse | null>(null);
  const [connectionState, setConnectionState] = useState<SocketState>("disconnected");
  const [socketEvents, setSocketEvents] = useState<TrainingRunSocketEventApiResponse[]>([]);
  const connectionRef = useRef<HubConnection | null>(null);
  const latestSequenceRef = useRef<number>(-1);

  const disconnectRealtime = useCallback(async () => {
    const connection = connectionRef.current;
    connectionRef.current = null;

    if (!connection || connection.state === HubConnectionState.Disconnected) {
      setConnectionState("disconnected");
      return;
    }

    await connection.stop().catch(() => undefined);
    setConnectionState("disconnected");
  }, []);

  const handleUnauthorizedIfNeeded = useCallback(
    (error: TrainingsApiError) => {
      if (error.status === 401) {
        onUnauthorized?.();
        return true;
      }

      return false;
    },
    [onUnauthorized],
  );

  const loadSelectionData = useCallback(async () => {
    if (!accessToken) {
      setModelsState(defaultModelsState);
      setDatasetsState(defaultDatasetsState);
      return;
    }

    setModelsState((previous) => ({
      kind: "loading",
      data: previous.data,
      error: null,
      errorType: null,
      httpStatus: null,
    }));
    setDatasetsState((previous) => ({
      kind: "loading",
      data: previous.data,
      error: null,
      errorType: null,
      httpStatus: null,
    }));

    try {
      const [modelsResponse, datasetsResponse] = await Promise.all([
        getRegistryModels(apiBaseUrl, accessToken),
        getProcessedDatasets(apiBaseUrl, accessToken),
      ]);
      setModelsState({
        kind: "success",
        data: modelsResponse.items,
        error: null,
        errorType: null,
        httpStatus: 200,
      });
      setDatasetsState({
        kind: "success",
        data: datasetsResponse.items,
        error: null,
        errorType: null,
        httpStatus: 200,
      });

      if (!selectedModelName && modelsResponse.items.length > 0) {
        const firstTrainable =
          modelsResponse.items.find((item) => item.canStartTraining) ?? null;
        if (firstTrainable) {
          setSelectedModelName(firstTrainable.name);
        }
      }
      if (!selectedDatasetName && datasetsResponse.items.length > 0) {
        setSelectedDatasetName(datasetsResponse.items[0].name);
      }
    } catch (error) {
      if (error instanceof TrainingsApiError && handleUnauthorizedIfNeeded(error)) {
        return;
      }

      const message =
        error instanceof Error
          ? error.message
          : "Nie udalo sie pobrac list modeli i datasetow.";
      const httpStatus = error instanceof TrainingsApiError ? error.status : null;
      const errorType =
        error instanceof TrainingsApiError ? error.errorType ?? null : null;

      setModelsState({
        kind: "error",
        data: null,
        error: message,
        errorType,
        httpStatus,
      });
      setDatasetsState({
        kind: "error",
        data: null,
        error: message,
        errorType,
        httpStatus,
      });
    }
  }, [
    accessToken,
    apiBaseUrl,
    handleUnauthorizedIfNeeded,
    selectedDatasetName,
    selectedModelName,
  ]);

  const ingestSocketPayload = useCallback((payload: unknown) => {
    const event = normalizeSocketEvent(payload);
    if (!event) {
      return;
    }

    if (event.sequence < latestSequenceRef.current) {
      return;
    }
    latestSequenceRef.current = event.sequence;

    setSocketEvents((previous) => [event, ...previous.slice(0, 49)]);
    if (terminalStatuses.includes(event.status)) {
      setConnectionState("completed");
    } else {
      setConnectionState("connected");
    }
    setActiveRun((previous) => {
      if (!previous || previous.runName !== event.runName) {
        return previous;
      }

      return {
        ...previous,
        status: event.status,
      };
    });
  }, []);

  const connectRealtime = useCallback(
    async (run: TrainingRunApiResponse) => {
      if (!accessToken) {
        return;
      }

      await disconnectRealtime();
      latestSequenceRef.current = -1;
      setSocketEvents([]);
      setConnectionState("connecting");

      const connection = new HubConnectionBuilder()
        .withUrl(buildHubUrl(run.progressChannelUrl, apiBaseUrl), {
          accessTokenFactory: () => accessToken ?? "",
        })
        .configureLogging(LogLevel.Information)
        .withAutomaticReconnect()
        .build();

      connection.on(
        "trainingSnapshot",
        (message: unknown) => {
          ingestSocketPayload(message);
        }
      );
      connection.on(
        "trainingEvent",
        (message: unknown) => {
          ingestSocketPayload(message);
        }
      );
      connection.onreconnecting(() => setConnectionState("reconnecting"));
      connection.onreconnected(() => setConnectionState("connected"));
      connection.onclose(() => setConnectionState("disconnected"));

      connectionRef.current = connection;
      try {
        await connection.start();
        setConnectionState("connected");
      } catch {
        setConnectionState("disconnected");
      }
    },
    [accessToken, apiBaseUrl, disconnectRealtime, ingestSocketPayload],
  );

  const recoverFromActiveRun = useCallback(async () => {
    if (!accessToken) {
      setActiveRunState(defaultActiveRunState);
      setActiveRun(null);
      return;
    }

    setActiveRunState((previous) => ({
      kind: "loading",
      data: previous.data,
      error: null,
      errorType: null,
      httpStatus: null,
    }));

    try {
      const run = await getActiveTrainingRun(apiBaseUrl, accessToken);
      setActiveRun(run);
      setActiveRunState({
        kind: "success",
        data: run,
        error: null,
        errorType: null,
        httpStatus: run ? 200 : 204,
      });

      if (!run) {
        await disconnectRealtime();
        await loadSelectionData();
        return;
      }

      if (run.status === "starting") {
        for (let attempt = 0; attempt < 6; attempt += 1) {
          await new Promise((resolve) => {
            window.setTimeout(resolve, 1200);
          });
          const polledRun = await getActiveTrainingRun(apiBaseUrl, accessToken);
          if (!polledRun || polledRun.status !== "starting") {
            setActiveRun(polledRun);
            setActiveRunState({
              kind: "success",
              data: polledRun,
              error: null,
              errorType: null,
              httpStatus: polledRun ? 200 : 204,
            });
            if (!polledRun) {
              await disconnectRealtime();
              await loadSelectionData();
              return;
            }

            await connectRealtime(polledRun);
            return;
          }
        }
      } else {
        await connectRealtime(run);
      }
    } catch (error) {
      if (error instanceof TrainingsApiError && handleUnauthorizedIfNeeded(error)) {
        return;
      }

      setActiveRunState({
        kind: "error",
        data: null,
        error:
          error instanceof Error
            ? error.message
            : "Nie udalo sie odzyskac aktywnego runu treningowego.",
        errorType: error instanceof TrainingsApiError ? error.errorType ?? null : null,
        httpStatus: error instanceof TrainingsApiError ? error.status : null,
      });
    }
  }, [
    accessToken,
    apiBaseUrl,
    connectRealtime,
    disconnectRealtime,
    handleUnauthorizedIfNeeded,
    loadSelectionData,
  ]);

  const startTraining = useCallback(async () => {
    if (!accessToken) {
      onUnauthorized?.();
      return;
    }
    if (!selectedModelName || !selectedDatasetName) {
      setStartState({
        kind: "error",
        response: null,
        error: "Wybierz model bazowy i dataset processed.",
        errorType: null,
        httpStatus: null,
      });
      return;
    }

    setStartState((previous) => ({
      kind: "loading",
      response: previous.response,
      error: null,
      errorType: null,
      httpStatus: null,
    }));

    try {
      const response = await postCreateTrainingRun(
        apiBaseUrl,
        {
          baseModelName: selectedModelName,
          processedDatasetName: selectedDatasetName,
        },
        accessToken,
      );
      setStartState({
        kind: "success",
        response,
        error: null,
        errorType: null,
        httpStatus: 202,
      });
      setCancelState(defaultCancelState);
      setActiveRun(response);
      setActiveRunState({
        kind: "success",
        data: response,
        error: null,
        errorType: null,
        httpStatus: 200,
      });
      await connectRealtime(response);
    } catch (error) {
      if (error instanceof TrainingsApiError) {
        if (handleUnauthorizedIfNeeded(error)) {
          return;
        }
        if (error.status === 409 && error.errorType === "training_run_already_active") {
          setStartState({
            kind: "error",
            response: null,
            error:
              "Inny run treningowy jest juz aktywny. Przelaczam widok do monitoringu.",
            errorType: error.errorType,
            httpStatus: error.status,
          });
          await recoverFromActiveRun();
          return;
        }
      }

      setStartState((previous) => ({
        kind: "error",
        response: previous.response,
        error:
          error instanceof Error
            ? error.message
            : "Nie udalo sie uruchomic treningu.",
        errorType: error instanceof TrainingsApiError ? error.errorType ?? null : null,
        httpStatus: error instanceof TrainingsApiError ? error.status : null,
      }));
    }
  }, [
    accessToken,
    apiBaseUrl,
    connectRealtime,
    handleUnauthorizedIfNeeded,
    onUnauthorized,
    recoverFromActiveRun,
    selectedDatasetName,
    selectedModelName,
  ]);

  const cancelTraining = useCallback(async () => {
    if (!accessToken) {
      onUnauthorized?.();
      return;
    }

    const run = activeRun;
    if (!run) {
      return;
    }

    setCancelState((previous) => ({
      kind: "loading",
      response: previous.response,
      error: null,
      errorType: null,
      httpStatus: null,
    }));

    try {
      const response = await postCancelTrainingRun(
        apiBaseUrl,
        run.runName,
        accessToken,
      );
      setCancelState({
        kind: "success",
        response,
        error: null,
        errorType: null,
        httpStatus: 202,
      });
      if (response.requestDisposition !== "noopNoMatchingRun" && response.status) {
        setActiveRun((previous) =>
          previous
            ? {
                ...previous,
                status: response.status ?? previous.status,
              }
            : previous,
        );
      }
      if (connectionRef.current?.state !== HubConnectionState.Connected) {
        await connectRealtime(run);
      }
    } catch (error) {
      if (error instanceof TrainingsApiError && handleUnauthorizedIfNeeded(error)) {
        return;
      }

      setCancelState((previous) => ({
        kind: "error",
        response: previous.response,
        error:
          error instanceof Error
            ? error.message
            : "Nie udalo sie anulowac treningu.",
        errorType: error instanceof TrainingsApiError ? error.errorType ?? null : null,
        httpStatus: error instanceof TrainingsApiError ? error.status : null,
      }));
    }
  }, [
    accessToken,
    activeRun,
    apiBaseUrl,
    connectRealtime,
    handleUnauthorizedIfNeeded,
    onUnauthorized,
  ]);

  useEffect(() => {
    if (!accessToken) {
      setActiveRun(null);
      setSocketEvents([]);
      setStartState(defaultStartState);
      setCancelState(defaultCancelState);
      void disconnectRealtime();
      return;
    }

    void recoverFromActiveRun();
  }, [accessToken, disconnectRealtime, recoverFromActiveRun]);

  useEffect(() => {
    return () => {
      const connection = connectionRef.current;
      if (connection) {
        void connection.stop();
      }
    };
  }, []);

  const latestEvent = socketEvents[0] ?? null;
  const latestStatus = latestEvent?.status ?? activeRun?.status ?? null;
  const isActiveRunPresent = latestStatus ? activeStatuses.includes(latestStatus) : false;
  const canCancel =
    Boolean(activeRun) &&
    latestStatus !== null &&
    !isTerminalStatus(latestStatus) &&
    latestStatus !== "cancelling";
  const trainableModels = (modelsState.data ?? []).filter((model) => model.canStartTraining);
  const availableDatasets = datasetsState.data ?? [];
  const startErrorHint =
    startState.kind === "error" ? toStartErrorHint(startState.httpStatus) : null;

  return (
    <section className="hero-card uc06-section">
      <p className="eyebrow">UC-06 — Start treningu i monitoring postepu</p>
      <h2>Run treningowy oparty o model i dataset</h2>
      <p className="hero-copy">
        Ekran odzyskuje aktywny run przez <code>GET /api/trainings/active</code>,
        uruchamia nowy trening przez <code>POST /api/trainings</code> i monitoruje
        postep przez <code>/ws/trainings/{"{runName}"}</code>.
      </p>
      {accessToken ? (
        <div className="examples-row-actions">
          <button
            className="secondary-button"
            type="button"
            onClick={() => void recoverFromActiveRun()}
            disabled={activeRunState.kind === "loading"}
          >
            {activeRunState.kind === "loading"
              ? "Odswiezanie stanu..."
              : "Odswiez stan treningu"}
          </button>
        </div>
      ) : null}

      {!accessToken ? (
        <p className="status-banner status-loading">
          UC-06 wymaga sesji administracyjnej. Zaloguj sie, aby kontynuowac.
        </p>
      ) : null}

      {activeRunState.kind === "loading" ? (
        <p className="status-banner status-loading">
          Odczytywanie aktywnego runu treningowego...
        </p>
      ) : null}

      {activeRunState.kind === "error" ? (
        <p className="status-banner status-error">{activeRunState.error}</p>
      ) : null}

      {accessToken && activeRun === null ? (
        <article className="uc12-panel">
          <h3>Formularz startu runu</h3>
          <p className="muted-copy">
            Wybierz dokladnie jeden model bazowy i jeden dataset processed.
          </p>

          <div className="examples-row-actions">
            <button
              className="secondary-button"
              type="button"
              onClick={() => void loadSelectionData()}
              disabled={modelsState.kind === "loading" || datasetsState.kind === "loading"}
            >
              {modelsState.kind === "loading" || datasetsState.kind === "loading"
                ? "Odswiezanie..."
                : "Odswiez listy"}
            </button>
          </div>

          {modelsState.kind === "error" ? (
            <p className="status-banner status-error">{modelsState.error}</p>
          ) : null}
          {datasetsState.kind === "error" ? (
            <p className="status-banner status-error">{datasetsState.error}</p>
          ) : null}
          {modelsState.kind === "success" && trainableModels.length === 0 ? (
            <p className="status-banner status-loading">
              Brak modeli bazowych gotowych do treningu w rejestrze (
              <code>/api/models/registry</code> zwrocil pusta liste albo modele z{" "}
              <code>canStartTraining=false</code>).
            </p>
          ) : null}
          {datasetsState.kind === "success" && availableDatasets.length === 0 ? (
            <p className="status-banner status-loading">
              Brak datasetow processed w systemie (
              <code>/api/datasets/processed</code> zwrocil pusta liste).
            </p>
          ) : null}

          <label className="uc12-field">
            <span>Model bazowy z rejestru</span>
            <select
              value={selectedModelName}
              onChange={(event) => setSelectedModelName(event.target.value)}
              disabled={trainableModels.length === 0}
            >
              <option value="">-- wybierz model --</option>
              {trainableModels.map((model) => (
                <option key={model.name} value={model.name}>
                  {model.displayName} ({model.name}) | input: {model.inputProfile}
                </option>
              ))}
            </select>
          </label>

          <label className="uc12-field">
            <span>Dataset processed (.npz)</span>
            <select
              value={selectedDatasetName}
              onChange={(event) => setSelectedDatasetName(event.target.value)}
              disabled={availableDatasets.length === 0}
            >
              <option value="">-- wybierz dataset --</option>
              {availableDatasets.map((dataset) => (
                <option key={dataset.name} value={dataset.name}>
                  {dataset.fileName} | profile: {dataset.preprocessingProfile}
                </option>
              ))}
            </select>
          </label>

          <button
            className="primary-button"
            type="button"
            disabled={
              startState.kind === "loading" ||
              !selectedModelName ||
              !selectedDatasetName
            }
            onClick={() => void startTraining()}
          >
            {startState.kind === "loading" ? "Uruchamianie..." : "Start treningu"}
          </button>
        </article>
      ) : null}

      {startState.kind === "error" ? (
        <>
          <p className="status-banner status-error">{startState.error}</p>
          {startErrorHint ? <p className="muted-copy">{startErrorHint}</p> : null}
        </>
      ) : null}

      {cancelState.kind === "error" ? (
        <>
          <p className="status-banner status-error">{cancelState.error}</p>
          <p className="muted-copy">
            Cancel HTTP: {cancelState.httpStatus ?? "-"}, typ:{" "}
            {cancelState.errorType ?? "-"}
          </p>
        </>
      ) : null}

      {cancelState.kind === "success" ? (
        <p className="status-banner status-loading">
          {toCancelDispositionHint(cancelState.response)} Disposition:{" "}
          {cancelState.response.requestDisposition}. Status:{" "}
          {cancelState.response.status ?? "-"}.
        </p>
      ) : null}

      {activeRun ? (
        <div className="uc12-panel">
          <h3>Monitoring aktywnego runu</h3>
          <dl className="result-grid">
            <div>
              <dt>Run</dt>
              <dd>{activeRun.runName}</dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd>{latestStatus ?? activeRun.status}</dd>
            </div>
            <div>
              <dt>Model wynikowy</dt>
              <dd>{activeRun.producedModelName}</dd>
            </div>
            <div>
              <dt>SignalR kanal</dt>
              <dd>{connectionState}</dd>
            </div>
            <div>
              <dt>Dataset</dt>
              <dd>{activeRun.processedDatasetName}</dd>
            </div>
            <div>
              <dt>Utworzono (UTC)</dt>
              <dd>{formatTimestamp(activeRun.createdAtUtc)}</dd>
            </div>
          </dl>
          <div className="examples-row-actions">
            <button
              className="secondary-button"
              type="button"
              onClick={() => void recoverFromActiveRun()}
              disabled={activeRunState.kind === "loading"}
            >
              Sprawdz czy run jest nadal aktywny
            </button>
            <button
              className="secondary-button"
              type="button"
              onClick={() => void disconnectRealtime()}
            >
              Rozlacz SignalR
            </button>
            <button
              className="secondary-button"
              type="button"
              disabled={!canCancel || cancelState.kind === "loading"}
              onClick={() => void cancelTraining()}
            >
              {cancelState.kind === "loading" ? "Anulowanie..." : "Anuluj run"}
            </button>
          </div>
        </div>
      ) : null}

      {latestEvent ? (
        <p
          className={`status-banner ${
            latestEvent.status === "succeeded"
              ? "status-success"
              : latestEvent.status === "failed" || latestEvent.status === "cancelled"
                ? "status-error"
                : "status-loading"
          }`}
        >
          Aktualny status: {latestEvent.status} (event: {latestEvent.eventType}). Postep:{" "}
          {formatProgressPercent(latestEvent.progress?.percent)}.
          {latestEvent.status === "succeeded"
            ? " Trening zakonczony sukcesem."
            : latestEvent.status === "cancelled"
              ? " Trening anulowany."
              : latestEvent.status === "failed"
                ? " Trening zakonczony bledem."
                : ""}
        </p>
      ) : null}

      {latestEvent?.result && latestEvent.result.reportStatus !== "ready" ? (
        <p className="status-banner status-loading">
          Raport koncowy ma status <code>{latestEvent.result.reportStatus}</code>, ale model
          moze byc nadal uzywalny do inferencji.
        </p>
      ) : null}

      {socketEvents.length > 0 ? (
        <div className="uc12-panel">
          <h3>Odebrane komunikaty SignalR</h3>
          <ul className="uc06-events-list">
            {socketEvents.map((event) => (
              <li key={`${event.eventType}-${event.sequence}`}>
                <strong>
                  {event.eventType} / {event.status}
                </strong>
                <span>
                  seq: {event.sequence}, stage: {event.stage}, czas:{" "}
                  {formatTimestamp(event.occurredAtUtc)}
                </span>
                <span>
                  epoch: {event.progress?.epochCurrent ?? "-"} /{" "}
                  {event.progress?.epochTotal ?? "-"}, ETA: {event.progress?.etaSeconds ?? "-"} s
                </span>
                {event.result ? (
                  <span>model: {event.result.producedModelName}</span>
                ) : null}
                {event.failure ? (
                  <span>
                    failure: {event.failure.errorType} - {event.failure.message}
                  </span>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p className="muted-copy">Brak odebranych komunikatow SignalR.</p>
      )}

      {isActiveRunPresent && connectionState === "disconnected" ? (
        <p className="status-banner status-loading">
          Polaczenie SignalR zostalo utracone. Run trwa po stronie backendu - odswiez aktywny run.
        </p>
      ) : null}
    </section>
  );
}
