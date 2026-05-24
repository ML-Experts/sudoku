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
import { buildHubUrl } from "../shared/realtime/buildHubUrl";
import { getProcessedDatasets } from "../api/datasets";
import type {
  CancelTrainingRunApiResponse,
  CreateTrainingRunParametersApiEntry,
  ProcessedDatasetListItemApiResponse,
  RegistryModelListItemApiResponse,
  TrainingRunApiResponse,
  TrainingRunProgressApiResponse,
  TrainingRunSocketEventApiResponse,
} from "../types/api";

type Uc06TrainingSectionProps = {
  apiBaseUrl: string;
  accessToken?: string | null;
  onUnauthorized?: () => void;
  trainingParameters: CreateTrainingRunParametersApiEntry | null;
  trainingParametersValid: boolean;
  trainingParameterErrorCount: number;
  trainingParameterOverrideCount: number;
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
const activeRunRefreshIntervalMs = 10_000;
const degradedActiveRunRefreshIntervalMs = 4_000;

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

function formatMetric(value: number | null | undefined): string {
  if (typeof value !== "number") {
    return "-";
  }

  return value.toFixed(4);
}

function formatEtaSeconds(value: number | null | undefined): string {
  if (typeof value !== "number" || value < 0) {
    return "brak prognozy";
  }

  return `${value} s`;
}

function getSignalRMetricTooltip(kind: string): string {
  const tooltips: Record<string, string> = {
    epoch:
      "Numer aktualnej epoki. Epoka to jedno pelne przejscie modelu przez dane treningowe.",
    progress:
      "Przyblizony procent wykonania biezacego runu treningowego.",
    eta: "Szacowany czas do konca treningu, obliczony na podstawie dotychczasowego tempa.",
    trainLoss:
      "Blad modelu na danych treningowych. Zwykle im nizsza wartosc, tym lepiej model dopasowuje sie do danych, na ktorych sie uczy.",
    validationLoss:
      "Blad modelu na danych walidacyjnych, czyli na danych kontrolnych nieuzywanych bezposrednio do uczenia. Pomaga ocenic, czy model nie uczy sie 'na pamiec'.",
    trainAccuracy:
      "Skutecznosc modelu na danych treningowych. Pokazuje, jaki procent odpowiedzi na danych do nauki byl poprawny.",
    validationAccuracy:
      "Skutecznosc modelu na danych walidacyjnych. To bardziej praktyczny sygnal, jak model radzi sobie na nowych danych niz train accuracy.",
  };

  return tooltips[kind] ?? "";
}

function formatMetricPair(
  primary: number | null | undefined,
  secondary: number | null | undefined,
): string {
  const primaryText = formatMetric(primary);
  const secondaryText = formatMetric(secondary);

  if (primaryText === "-" && secondaryText === "-") {
    return "-";
  }

  if (primaryText !== "-" && secondaryText !== "-") {
    return `train: ${primaryText} | val: ${secondaryText}`;
  }

  if (primaryText !== "-") {
    return primaryText;
  }

  return secondaryText;
}

function toOptionalNumber(value: unknown): number | null | undefined {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }

  if (value === null || value === undefined) {
    return value;
  }

  return undefined;
}

function normalizeProgress(
  payload: unknown,
): TrainingRunProgressApiResponse | null {
  if (payload === null) {
    return null;
  }

  if (!payload || typeof payload !== "object") {
    return null;
  }

  const record = payload as Record<string, unknown>;
  const percent = toOptionalNumber(record.percent);
  const epochCurrent = toOptionalNumber(record.epochCurrent);
  const epochTotal = toOptionalNumber(record.epochTotal);
  const etaSeconds = toOptionalNumber(record.etaSeconds);
  const trainLoss = toOptionalNumber(record.trainLoss);
  const validationLoss = toOptionalNumber(record.validationLoss);
  const trainAccuracy = toOptionalNumber(record.trainAccuracy);
  const validationAccuracy = toOptionalNumber(record.validationAccuracy);
  const legacyLoss = toOptionalNumber(record.loss);
  const legacyAccuracy = toOptionalNumber(record.accuracy);

  if (
    percent === undefined ||
    epochCurrent === undefined ||
    epochTotal === undefined
  ) {
    return null;
  }

  return {
    percent,
    epochCurrent,
    epochTotal,
    etaSeconds: etaSeconds ?? null,
    trainLoss:
      trainLoss === undefined
        ? legacyLoss === undefined
          ? undefined
          : legacyLoss
        : trainLoss,
    validationLoss: validationLoss === undefined ? undefined : validationLoss,
    trainAccuracy:
      trainAccuracy === undefined
        ? legacyAccuracy === undefined
          ? undefined
          : legacyAccuracy
        : trainAccuracy,
    validationAccuracy:
      validationAccuracy === undefined ? undefined : validationAccuracy,
  };
}

function getHighestEpochProgressEvent(
  events: TrainingRunSocketEventApiResponse[],
): TrainingRunSocketEventApiResponse | null {
  let candidate: TrainingRunSocketEventApiResponse | null = null;

  for (const event of events) {
    if (event.progress?.epochCurrent === null || event.progress === null) {
      continue;
    }

    if (candidate === null || candidate.progress === null) {
      candidate = event;
      continue;
    }

    const currentEpoch = event.progress.epochCurrent ?? -1;
    const candidateEpoch = candidate.progress.epochCurrent ?? -1;
    if (currentEpoch > candidateEpoch) {
      candidate = event;
      continue;
    }

    if (currentEpoch === candidateEpoch && event.sequence > candidate.sequence) {
      candidate = event;
    }
  }

  return candidate;
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
  if (Array.isArray(payload)) {
    if (payload.length !== 1) {
      return null;
    }

    return normalizeSocketEvent(payload[0]);
  }

  if (!payload || typeof payload !== "object") {
    return null;
  }

  const record = payload as Record<string, unknown>;
  const normalizedProgress = normalizeProgress(record.progress);
  if (
    typeof record.eventType === "string" &&
    typeof record.sequence === "number" &&
    typeof record.runName === "string" &&
    typeof record.status === "string" &&
    typeof record.stage === "string" &&
    typeof record.occurredAtUtc === "string" &&
    (typeof record.message === "string" || record.message === null) &&
    (record.progress === null || normalizedProgress !== null) &&
    Array.isArray(record.warnings) &&
    (typeof record.result === "object" || record.result === null) &&
    (typeof record.failure === "object" || record.failure === null)
  ) {
    return {
      eventType: record.eventType,
      sequence: record.sequence,
      runName: record.runName,
      status: record.status,
      stage: record.stage,
      occurredAtUtc: record.occurredAtUtc,
      message: typeof record.message === "string" ? record.message : null,
      progress: normalizedProgress,
      warnings: record.warnings.filter(
        (warning): warning is string => typeof warning === "string",
      ),
      result:
        record.result && typeof record.result === "object"
          ? (record.result as TrainingRunSocketEventApiResponse["result"])
          : null,
      failure:
        record.failure && typeof record.failure === "object"
          ? (record.failure as TrainingRunSocketEventApiResponse["failure"])
          : null,
    };
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
    progress:
      legacyProgress
        ? normalizeProgress({
            percent: typeof legacyProgress.percent === "number" ? legacyProgress.percent : null,
            epochCurrent:
              typeof legacyProgress.epoch === "number" ? legacyProgress.epoch : null,
            epochTotal:
              typeof legacyProgress.totalEpochs === "number"
                ? legacyProgress.totalEpochs
                : null,
            etaSeconds:
              typeof legacyProgress.etaSeconds === "number"
                ? legacyProgress.etaSeconds
                : null,
            trainLoss:
              typeof legacyProgress.trainLoss === "number"
                ? legacyProgress.trainLoss
                : null,
            validationLoss:
              typeof legacyProgress.validationLoss === "number"
                ? legacyProgress.validationLoss
                : null,
            trainAccuracy:
              typeof legacyProgress.trainAccuracy === "number"
                ? legacyProgress.trainAccuracy
                : null,
            validationAccuracy:
              typeof legacyProgress.validationAccuracy === "number"
                ? legacyProgress.validationAccuracy
                : null,
            loss: typeof legacyProgress.loss === "number" ? legacyProgress.loss : null,
            accuracy:
              typeof legacyProgress.accuracy === "number"
                ? legacyProgress.accuracy
                : null,
          })
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

function toActiveRunBlockingCopy(status: string | null): string | null {
  if (status === null) {
    return null;
  }

  const copy: Record<string, string> = {
    queued: "Inny run jest zakolejkowany. Mozesz juz wybrac model i dataset, ale start kolejnego runu pozostanie zablokowany do zakonczenia biezacego.",
    starting: "Backend uruchamia run. Mozesz przygotowac kolejny wybor, ale start pozostanie zablokowany do czasu zejscia biezacego runu z aktywnego statusu.",
    running: "Run jest w trakcie treningu. Mozesz zmienic wybor modelu i datasetu, ale kolejny start bedzie mozliwy dopiero po zakonczeniu albo anulowaniu biezacego runu.",
    cancelling: "Run jest w trakcie anulowania. Mozesz juz ustawic model i dataset dla kolejnej proby, ale start odblokuje sie dopiero, gdy backend potwierdzi status terminalny.",
  };

  return copy[status] ?? null;
}

function getStaleActivityWarning(
  status: string | null,
  occurredAtUtc: string | null,
): string | null {
  if (status === null || occurredAtUtc === null) {
    return null;
  }

  const parsedTimestamp = new Date(occurredAtUtc);
  if (Number.isNaN(parsedTimestamp.getTime())) {
    return null;
  }

  if (Date.now() - parsedTimestamp.getTime() < 60_000) {
    return null;
  }

  if (status === "cancelling") {
    return "Brak swiezego eventu dla statusu cancelling. Run moze byc zablokowany po stronie backendu albo ML.";
  }

  if (status === "queued" || status === "starting" || status === "running") {
    return "Brak swiezych eventow SignalR dla aktywnego runu. Odswiez stan treningu, aby sprawdzic, czy backend nadal widzi go jako aktywny.";
  }

  return null;
}

export function Uc06TrainingSection({
  apiBaseUrl,
  accessToken,
  onUnauthorized,
  trainingParameters,
  trainingParametersValid,
  trainingParameterErrorCount,
  trainingParameterOverrideCount,
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
  const realtimeRunNameRef = useRef<string | null>(null);
  const hadActiveRunRef = useRef(false);
  const activeRunRefreshInFlightRef = useRef(false);

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

  const ingestSocketPayload = useCallback(
    (payload: unknown) => {
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
    },
    [],
  );

  const connectRealtime = useCallback(
    async (run: TrainingRunApiResponse) => {
      if (!accessToken) {
        return;
      }

      const sameRun = realtimeRunNameRef.current === run.runName;
      await disconnectRealtime();
      realtimeRunNameRef.current = run.runName;
      if (!sameRun) {
        latestSequenceRef.current = -1;
        setSocketEvents([]);
      }
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

  const recoverFromActiveRunSafely = useCallback(async () => {
    if (activeRunRefreshInFlightRef.current) {
      return;
    }

    activeRunRefreshInFlightRef.current = true;
    try {
      await recoverFromActiveRun();
    } finally {
      activeRunRefreshInFlightRef.current = false;
    }
  }, [recoverFromActiveRun]);

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
    if (!trainingParametersValid || trainingParameters === null) {
      setStartState({
        kind: "error",
        response: null,
        error:
          "Parametry treningu z panelu UC-14 zawieraja bledy. Popraw je przed startem runu.",
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
          trainingParameters,
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
    trainingParameters,
    trainingParametersValid,
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
      hadActiveRunRef.current = false;
      realtimeRunNameRef.current = null;
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
    if (!accessToken) {
      return;
    }

    void loadSelectionData();
  }, [accessToken, loadSelectionData]);

  useEffect(() => {
    return () => {
      const connection = connectionRef.current;
      if (connection) {
        void connection.stop();
      }
    };
  }, []);

  const latestEvent = socketEvents[0] ?? null;
  const highestEpochProgressEvent = getHighestEpochProgressEvent(socketEvents);
  const latestProgress = highestEpochProgressEvent?.progress ?? null;
  const latestStatus = latestEvent?.status ?? activeRun?.status ?? null;
  const isActiveRunPresent = latestStatus ? activeStatuses.includes(latestStatus) : false;
  const shouldShowStartForm = Boolean(accessToken);
  const canCancel =
    Boolean(activeRun) &&
    latestStatus !== null &&
    !isTerminalStatus(latestStatus);
  const trainableModels = (modelsState.data ?? []).filter((model) => model.canStartTraining);
  const availableDatasets = datasetsState.data ?? [];
  const startErrorHint =
    startState.kind === "error" ? toStartErrorHint(startState.httpStatus) : null;
  const activeRunBlockingCopy = toActiveRunBlockingCopy(latestStatus);
  const latestActivityAtUtc = latestEvent?.occurredAtUtc ?? activeRun?.createdAtUtc ?? null;
  const staleActivityWarning = getStaleActivityWarning(latestStatus, latestActivityAtUtc);

  useEffect(() => {
    if (!accessToken) {
      hadActiveRunRef.current = false;
      realtimeRunNameRef.current = null;
      return;
    }

    if (isActiveRunPresent) {
      hadActiveRunRef.current = true;
      return;
    }

    if (!hadActiveRunRef.current) {
      return;
    }

    hadActiveRunRef.current = false;
    void loadSelectionData();
  }, [accessToken, isActiveRunPresent, loadSelectionData]);

  useEffect(() => {
    if (!accessToken || !activeRun || latestStatus === null || isTerminalStatus(latestStatus)) {
      return;
    }

    const refreshDelay =
      connectionState === "disconnected" ||
      connectionState === "reconnecting" ||
      staleActivityWarning
        ? degradedActiveRunRefreshIntervalMs
        : activeRunRefreshIntervalMs;
    const timeoutId = window.setTimeout(() => {
      void recoverFromActiveRunSafely();
    }, refreshDelay);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [
    accessToken,
    activeRun,
    connectionState,
    latestStatus,
    recoverFromActiveRunSafely,
    staleActivityWarning,
  ]);

  useEffect(() => {
    if (
      cancelState.kind !== "success" ||
      !activeRun ||
      cancelState.response.runName !== activeRun.runName
    ) {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      void recoverFromActiveRunSafely();
    }, 1_500);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [activeRun, cancelState, recoverFromActiveRunSafely]);

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

      {shouldShowStartForm ? (
        <article className="uc12-panel">
          <h3>Formularz startu runu</h3>
          <p className="muted-copy">
            Wybierz dokladnie jeden model bazowy i jeden dataset processed.
          </p>
          {isActiveRunPresent && activeRunBlockingCopy ? (
            <p className="status-banner status-loading">{activeRunBlockingCopy}</p>
          ) : null}
          {isActiveRunPresent && staleActivityWarning ? (
            <p className="status-banner status-error">{staleActivityWarning}</p>
          ) : null}
          {activeRun && latestStatus && isTerminalStatus(latestStatus) ? (
            <p className="status-banner status-success">
              Poprzedni run ma status <code>{latestStatus}</code>. Mozesz od razu uruchomic
              kolejny trening.
            </p>
          ) : null}

          <div className="uc05b-parameter-summary">
            <span className="app-chip">
              Override&apos;y parametrow: {trainingParameterOverrideCount}
            </span>
            <span
              className={`app-chip ${
                trainingParametersValid ? "app-chip-muted" : "uc14-chip-error"
              }`}
            >
              {trainingParametersValid
                ? "Panel parametrow gotowy"
                : `Panel parametrow: ${trainingParameterErrorCount} bledy`}
            </span>
          </div>
          <p className="muted-copy">
            Parametry runu sa konfigurowane w panelu po prawej stronie i trafiaja do
            requestu jako <code>trainingParameters</code>.
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
              disabled={modelsState.kind === "loading" || trainableModels.length === 0}
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
              disabled={datasetsState.kind === "loading" || availableDatasets.length === 0}
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
              isActiveRunPresent ||
              !selectedModelName ||
              !selectedDatasetName ||
              !trainingParametersValid ||
              trainingParameters === null
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
            <div>
              <dt>Epoki</dt>
              <dd>{activeRun.effectiveParameters?.epochs ?? "-"}</dd>
            </div>
            <div>
              <dt>Postep</dt>
              <dd>{formatProgressPercent(latestProgress?.percent)}</dd>
            </div>
            <div>
              <dt>Biezaca epoka</dt>
              <dd>
                {latestProgress?.epochCurrent ?? "-"} / {latestProgress?.epochTotal ?? "-"}
              </dd>
            </div>
            <div>
              <dt>Loss</dt>
              <dd>
                {formatMetricPair(
                  latestProgress?.trainLoss,
                  latestProgress?.validationLoss,
                )}
              </dd>
            </div>
            <div>
              <dt>Accuracy</dt>
              <dd>
                {formatMetricPair(
                  latestProgress?.trainAccuracy,
                  latestProgress?.validationAccuracy,
                )}
              </dd>
            </div>
            <div>
              <dt>Szacowany czas do konca</dt>
              <dd>{formatEtaSeconds(latestProgress?.etaSeconds)}</dd>
            </div>
            <div>
              <dt>Learning rate</dt>
              <dd>{activeRun.effectiveParameters?.learningRate ?? "-"}</dd>
            </div>
            <div>
              <dt>Batch size</dt>
              <dd>{activeRun.effectiveParameters?.batchSize ?? "-"}</dd>
            </div>
            <div>
              <dt>Early stopping min delta</dt>
              <dd>{activeRun.effectiveParameters?.earlyStoppingMinDelta ?? "-"}</dd>
            </div>
            <div>
              <dt>Warmup epochs</dt>
              <dd>{activeRun.effectiveParameters?.warmupEpochs ?? "-"}</dd>
            </div>
            <div>
              <dt>Fine-tuning policy</dt>
              <dd>{activeRun.effectiveParameters?.fineTuningPolicy ?? "-"}</dd>
            </div>
            <div>
              <dt>Najlepszy checkpoint</dt>
              <dd>
                {typeof activeRun.effectiveParameters?.useBestCheckpoint === "boolean"
                  ? activeRun.effectiveParameters.useBestCheckpoint
                    ? "tak"
                    : "nie"
                  : "-"}
              </dd>
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
              {cancelState.kind === "loading"
                ? "Anulowanie..."
                : latestStatus === "cancelling"
                  ? "Ponow cancel"
                  : "Anuluj run"}
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
          {formatProgressPercent(latestProgress?.percent)}.
          {latestProgress?.trainLoss !== undefined ||
          latestProgress?.validationLoss !== undefined ? (
            <>
              {" "}
              Loss:{" "}
              {formatMetricPair(
                latestProgress?.trainLoss,
                latestProgress?.validationLoss,
              )}
              .
            </>
          ) : null}
          {latestProgress?.trainAccuracy !== undefined ||
          latestProgress?.validationAccuracy !== undefined ? (
            <>
              {" "}
              Accuracy:{" "}
              {formatMetricPair(
                latestProgress?.trainAccuracy,
                latestProgress?.validationAccuracy,
              )}
              .
            </>
          ) : null}
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
                <div className="uc06-event-chips">
                  <span
                    className="uc06-event-chip uc06-event-chip-progress"
                    title={getSignalRMetricTooltip("epoch")}
                  >
                    epoka: {event.progress?.epochCurrent ?? "-"} /{" "}
                    {event.progress?.epochTotal ?? "-"}
                  </span>
                  <span
                    className="uc06-event-chip uc06-event-chip-progress"
                    title={getSignalRMetricTooltip("progress")}
                  >
                    postep: {formatProgressPercent(event.progress?.percent)}
                  </span>
                  <span
                    className="uc06-event-chip uc06-event-chip-progress"
                    title={getSignalRMetricTooltip("eta")}
                  >
                    szacowany czas do konca: {formatEtaSeconds(event.progress?.etaSeconds)}
                  </span>
                </div>
                <div className="uc06-event-chips">
                  <span
                    className="uc06-event-chip uc06-event-chip-loss"
                    title={getSignalRMetricTooltip("trainLoss")}
                  >
                    train loss: {formatMetric(event.progress?.trainLoss)}
                  </span>
                  <span
                    className="uc06-event-chip uc06-event-chip-loss"
                    title={getSignalRMetricTooltip("validationLoss")}
                  >
                    validation loss: {formatMetric(event.progress?.validationLoss)}
                  </span>
                </div>
                <div className="uc06-event-chips">
                  <span
                    className="uc06-event-chip uc06-event-chip-accuracy"
                    title={getSignalRMetricTooltip("trainAccuracy")}
                  >
                    train accuracy: {formatMetric(event.progress?.trainAccuracy)}
                  </span>
                  <span
                    className="uc06-event-chip uc06-event-chip-accuracy"
                    title={getSignalRMetricTooltip("validationAccuracy")}
                  >
                    validation accuracy: {formatMetric(event.progress?.validationAccuracy)}
                  </span>
                </div>
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
      ) : activeRun ? (
        <p className="muted-copy">
          SignalR nie dostarczyl jeszcze zdarzenia do UI. Widoczny status runu pochodzi na razie
          z <code>GET /api/trainings/active</code>, a FE bedzie dalej probowal odzyskac stan.
        </p>
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
