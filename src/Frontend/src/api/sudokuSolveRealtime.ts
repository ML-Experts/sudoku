import {
  HubConnectionBuilder,
  HubConnectionState,
  LogLevel,
  type HubConnection,
} from "@microsoft/signalr";

import type { SolveProgressEventApiResponse } from "../types/api";
import { buildHubUrl } from "../shared/realtime/buildHubUrl";

const GRID_SIZE = 9;

function isGridDigit(value: unknown): value is number {
  return (
    typeof value === "number" &&
    Number.isInteger(value) &&
    value >= 1 &&
    value <= 9
  );
}

function isCurrentGrid(value: unknown): value is (number | null)[][] {
  if (!Array.isArray(value) || value.length !== GRID_SIZE) {
    return false;
  }

  return value.every(
    (row) =>
      Array.isArray(row) &&
      row.length === GRID_SIZE &&
      row.every((cell) => cell === null || isGridDigit(cell)),
  );
}

export function isSolveProgressEventApiResponse(
  value: unknown,
): value is SolveProgressEventApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;

  return (
    typeof record.eventType === "string" &&
    typeof record.solveSessionId === "string" &&
    typeof record.status === "string" &&
    typeof record.sequence === "number" &&
    Number.isInteger(record.sequence) &&
    record.sequence >= 0 &&
    isCurrentGrid(record.currentGrid) &&
    (typeof record.errorType === "string" || record.errorType === null) &&
    (typeof record.message === "string" || record.message === null)
  );
}

export class SudokuSolveRealtimeContractError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "SudokuSolveRealtimeContractError";
  }
}

export type SolveRealtimeConnection = {
  disconnect: () => Promise<void>;
  getState: () => HubConnectionState;
};

type ConnectSudokuSolveRealtimeOptions = {
  apiBaseUrl: string;
  solveSessionId: string;
  progressChannelUrl: string;
  onSnapshot: (event: SolveProgressEventApiResponse) => void;
  onEvent: (event: SolveProgressEventApiResponse) => void;
  onReconnecting?: (error?: Error) => void;
  onReconnected?: () => void;
  onClose?: (error?: Error) => void;
  onContractError?: (error: SudokuSolveRealtimeContractError) => void;
};

const SOLVE_SNAPSHOT_EVENT_NAME = "solveSnapshot";
const SOLVE_PROGRESS_EVENT_NAME = "solveProgress";
const LEGACY_SOLVE_EVENT_NAME = "solveEvent";

function createPayloadHandler(
  eventName: "solveSnapshot" | "solveProgress" | "solveEvent",
  handleEvent: (event: SolveProgressEventApiResponse) => void,
  handleContractError: ((error: SudokuSolveRealtimeContractError) => void) | undefined,
  connectionRef: { current: HubConnection | null },
) {
  return (payload: unknown) => {
    if (!isSolveProgressEventApiResponse(payload)) {
      const error = new SudokuSolveRealtimeContractError(
        `Backend zwrocil niepoprawny payload ${eventName}.`,
      );
      handleContractError?.(error);

      if (connectionRef.current) {
        void connectionRef.current.stop();
      }
      return;
    }

    handleEvent(payload);
  };
}

export async function connectSudokuSolveRealtime({
  apiBaseUrl,
  solveSessionId,
  progressChannelUrl,
  onSnapshot,
  onEvent,
  onReconnecting,
  onReconnected,
  onClose,
  onContractError,
}: ConnectSudokuSolveRealtimeOptions): Promise<SolveRealtimeConnection> {
  const connection = new HubConnectionBuilder()
    .withUrl(buildHubUrl(progressChannelUrl, apiBaseUrl))
    .configureLogging(LogLevel.Information)
    .withAutomaticReconnect()
    .build();

  const connectionRef: { current: HubConnection | null } = { current: connection };

  connection.on(
    SOLVE_SNAPSHOT_EVENT_NAME,
    createPayloadHandler(
      SOLVE_SNAPSHOT_EVENT_NAME,
      onSnapshot,
      onContractError,
      connectionRef,
    ),
  );

  // Accept both method names until FE/BE realtime contracts are fully aligned.
  connection.on(
    SOLVE_PROGRESS_EVENT_NAME,
    createPayloadHandler(
      SOLVE_PROGRESS_EVENT_NAME,
      onEvent,
      onContractError,
      connectionRef,
    ),
  );
  connection.on(
    LEGACY_SOLVE_EVENT_NAME,
    createPayloadHandler(
      LEGACY_SOLVE_EVENT_NAME,
      onEvent,
      onContractError,
      connectionRef,
    ),
  );
  connection.onreconnecting((error) => {
    onReconnecting?.(error ?? undefined);
  });
  connection.onreconnected(() => {
    onReconnected?.();
  });
  connection.onclose((error) => {
    onClose?.(error ?? undefined);
  });

  try {
    await connection.start();
  } catch (error) {
    connectionRef.current = null;

    if (error instanceof Error) {
      throw error;
    }

    throw new Error(
      `Nie udalo sie nawiazac polaczenia SignalR dla sesji ${solveSessionId}.`,
    );
  }

  return {
    disconnect: async () => {
      connectionRef.current = null;

      if (connection.state === HubConnectionState.Disconnected) {
        return;
      }

      await connection.stop();
    },
    getState: () => connection.state,
  };
}
