import {
  HubConnectionBuilder,
  HubConnectionState,
  LogLevel,
  type HubConnection,
} from "@microsoft/signalr";
import { useCallback, useEffect, useRef, useState } from "react";

import {
  postCancelTrainingRun,
  postCreateTrainingRun,
  TrainingsApiError,
} from "../api/trainings";
import type {
  CancelTrainingRunApiResponse,
  TrainingRunApiResponse,
  TrainingRunRealtimeApiResponse,
} from "../types/api";

type Uc06TrainingSectionProps = {
  apiBaseUrl: string;
  accessToken?: string | null;
  onUnauthorized?: () => void;
};

type TrainingRequestState =
  | {
      kind: "idle";
      response: TrainingRunApiResponse | null;
      error: null;
      errorType: null;
      httpStatus: null;
    }
  | {
      kind: "loading";
      response: TrainingRunApiResponse | null;
      error: null;
      errorType: null;
      httpStatus: null;
    }
  | {
      kind: "success";
      response: TrainingRunApiResponse;
      error: null;
      errorType: null;
      httpStatus: number;
    }
  | {
      kind: "error";
      response: TrainingRunApiResponse | null;
      error: string;
      errorType: string | null;
      httpStatus: number | null;
    };

type CancelRequestState =
  | {
      kind: "idle";
      response: CancelTrainingRunApiResponse | null;
      error: null;
      errorType: null;
      httpStatus: null;
    }
  | {
      kind: "loading";
      response: CancelTrainingRunApiResponse | null;
      error: null;
      errorType: null;
      httpStatus: null;
    }
  | {
      kind: "success";
      response: CancelTrainingRunApiResponse;
      error: null;
      errorType: null;
      httpStatus: number;
    }
  | {
      kind: "error";
      response: CancelTrainingRunApiResponse | null;
      error: string;
      errorType: string | null;
      httpStatus: number | null;
    };

const defaultTrainingState: TrainingRequestState = {
  kind: "idle",
  response: null,
  error: null,
  errorType: null,
  httpStatus: null,
};

const defaultCancelState: CancelRequestState = {
  kind: "idle",
  response: null,
  error: null,
  errorType: null,
  httpStatus: null,
};

const trainingRequest = {
  baseModelName: "cnn-baseline",
  processedDatasetName: "uc12-dataset-v2",
};

function isTerminalStatus(status: string): boolean {
  return ["succeeded", "failed", "cancelled"].includes(status);
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

function formatPercent(value: number | null | undefined): string {
  return typeof value === "number" ? `${value.toFixed(1)}%` : "-";
}

function buildHubUrl(progressChannelUrl: string): string {
  if (progressChannelUrl.startsWith("http://") || progressChannelUrl.startsWith("https://")) {
    return progressChannelUrl;
  }

  return progressChannelUrl.startsWith("/")
    ? progressChannelUrl
    : `/${progressChannelUrl}`;
}

export function Uc06TrainingSection({
  apiBaseUrl,
  accessToken,
  onUnauthorized,
}: Uc06TrainingSectionProps) {
  const [trainingState, setTrainingState] = useState(defaultTrainingState);
  const [cancelState, setCancelState] = useState(defaultCancelState);
  const [connectionState, setConnectionState] = useState("disconnected");
  const [realtimeEvents, setRealtimeEvents] = useState<
    TrainingRunRealtimeApiResponse[]
  >([]);
  const connectionRef = useRef<HubConnection | null>(null);

  const disconnectRealtime = useCallback(async () => {
    const connection = connectionRef.current;
    connectionRef.current = null;

    if (!connection || connection.state === HubConnectionState.Disconnected) {
      setConnectionState("disconnected");
      return;
    }

    await connection.stop();
    setConnectionState("disconnected");
  }, []);

  const connectRealtime = useCallback(
    async (run: TrainingRunApiResponse) => {
      await disconnectRealtime();
      setRealtimeEvents([]);
      setConnectionState("connecting");

      const connection = new HubConnectionBuilder()
        .withUrl(buildHubUrl(run.progressChannelUrl), {
          accessTokenFactory: () => accessToken ?? "",
        })
        .configureLogging(LogLevel.Information)
        .withAutomaticReconnect()
        .build();

      connection.on(
        "trainingSnapshot",
        (message: TrainingRunRealtimeApiResponse) => {
          setRealtimeEvents((previous) => [message, ...previous]);
          setConnectionState(
            isTerminalStatus(message.status) ? "completed" : "connected",
          );
        },
      );
      connection.on(
        "trainingEvent",
        (message: TrainingRunRealtimeApiResponse) => {
          setRealtimeEvents((previous) => [message, ...previous]);
          setConnectionState(
            isTerminalStatus(message.status) ? "completed" : "connected",
          );
        },
      );
      connection.onreconnecting(() => setConnectionState("reconnecting"));
      connection.onreconnected(() => setConnectionState("connected"));
      connection.onclose(() => setConnectionState("disconnected"));

      connectionRef.current = connection;
      await connection.start();
      setConnectionState("connected");
    },
    [accessToken, disconnectRealtime],
  );

  const startTraining = useCallback(async () => {
    if (!accessToken) {
      onUnauthorized?.();
      return;
    }

    setTrainingState((previous) => ({
      kind: "loading",
      response: previous.response,
      error: null,
      errorType: null,
      httpStatus: null,
    }));

    try {
      const response = await postCreateTrainingRun(
        apiBaseUrl,
        trainingRequest,
        accessToken,
      );
      setTrainingState({
        kind: "success",
        response,
        error: null,
        errorType: null,
        httpStatus: 202,
      });
      setCancelState(defaultCancelState);
      await connectRealtime(response);
    } catch (error) {
      if (error instanceof TrainingsApiError && error.status === 401) {
        onUnauthorized?.();
      }

      setTrainingState((previous) => ({
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
  }, [accessToken, apiBaseUrl, connectRealtime, onUnauthorized]);

  const cancelTraining = useCallback(async () => {
    if (!accessToken) {
      onUnauthorized?.();
      return;
    }

    const run = trainingState.response;
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

      if (
        connectionRef.current?.state !== HubConnectionState.Connected &&
        response.progressChannelUrl
      ) {
        await connectRealtime(run);
      }
    } catch (error) {
      if (error instanceof TrainingsApiError && error.status === 401) {
        onUnauthorized?.();
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
    apiBaseUrl,
    connectRealtime,
    onUnauthorized,
    trainingState.response,
  ]);

  useEffect(() => {
    return () => {
      const connection = connectionRef.current;
      if (connection) {
        void connection.stop();
      }
    };
  }, []);

  const latestEvent = realtimeEvents[0] ?? null;
  const latestStatus = latestEvent?.status ?? trainingState.response?.status ?? null;
  const canCancel =
    Boolean(trainingState.response) &&
    latestStatus !== null &&
    !isTerminalStatus(latestStatus) &&
    latestStatus !== "cancelling";

  return (
    <section className="hero-card uc06-section">
      <p className="eyebrow">UC-06 — Start treningu i SignalR</p>
      <h2>Minimalny monitoring runu treningowego</h2>
      <p className="hero-copy">
        Ten widok wysyla testowy request do <code>POST /api/trainings</code> i
        nasluchuje eventow z <code>/ws/trainings/{"{runName}"}</code>.
      </p>

      <div className="uc12-panel">
        <h3>Request testowy</h3>
        <pre className="uc06-json-preview">
{JSON.stringify(trainingRequest, null, 2)}
        </pre>
        <div className="examples-row-actions">
          <button
            className="primary-button"
            type="button"
            disabled={trainingState.kind === "loading"}
            onClick={() => void startTraining()}
          >
            {trainingState.kind === "loading"
              ? "Uruchamianie..."
              : "Uruchom trening UC-06"}
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
            {cancelState.kind === "loading" ? "Anulowanie..." : "Anuluj trening"}
          </button>
        </div>
      </div>

      {trainingState.kind === "error" ? (
        <>
          <p className="status-banner status-error">{trainingState.error}</p>
          <p className="muted-copy">
            HTTP: {trainingState.httpStatus ?? "-"}, typ:{" "}
            {trainingState.errorType ?? "-"}
          </p>
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
          {cancelState.response.message} Disposition:{" "}
          {cancelState.response.requestDisposition}, status:{" "}
          {cancelState.response.status ?? "-"}.
        </p>
      ) : null}

      {trainingState.kind === "success" ? (
        <div className="uc12-panel">
          <h3>Odpowiedz BE</h3>
          <dl className="result-grid">
            <div>
              <dt>Run</dt>
              <dd>{trainingState.response.runName}</dd>
            </div>
            <div>
              <dt>Status startowy</dt>
              <dd>{trainingState.response.status}</dd>
            </div>
            <div>
              <dt>Model wynikowy</dt>
              <dd>{trainingState.response.producedModelName}</dd>
            </div>
            <div>
              <dt>SignalR</dt>
              <dd>{connectionState}</dd>
            </div>
          </dl>
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
          Aktualny status: {latestEvent.status}. Postep:{" "}
          {formatPercent(latestEvent.progress?.percent)}.
          {latestEvent.status === "succeeded"
            ? " Trening zakonczony sukcesem."
            : latestEvent.status === "cancelled"
              ? " Trening anulowany."
            : ""}
        </p>
      ) : null}

      {realtimeEvents.length > 0 ? (
        <div className="uc12-panel">
          <h3>Odebrane komunikaty SignalR</h3>
          <ul className="uc06-events-list">
            {realtimeEvents.map((event, index) => (
              <li key={`${event.messageKind}-${event.lastAcceptedSequence ?? index}`}>
                <strong>
                  {event.messageKind} / {event.status}
                </strong>
                <span>
                  seq: {event.lastAcceptedSequence ?? "-"}, event:{" "}
                  {event.lastEventType ?? "-"}, czas:{" "}
                  {formatTimestamp(event.updatedAtUtc ?? event.createdAtUtc)}
                </span>
                <span>
                  epoch: {event.progress?.epoch ?? "-"} /{" "}
                  {event.progress?.totalEpochs ?? "-"}, accuracy:{" "}
                  {event.metricsSummary?.accuracy ?? event.progress?.validationAccuracy ?? "-"}
                </span>
                {event.reportRelativePath ? (
                  <span>Raport: {event.reportRelativePath}</span>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p className="muted-copy">Brak odebranych komunikatow SignalR.</p>
      )}
    </section>
  );
}
