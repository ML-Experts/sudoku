import type { RecognizedGrid } from "../../uc05a/domain/recognizedGrid";
import type { ChangedSolveCell } from "../domain/diffRecognizedGridChanges";
import type { TerminalSolveProgressEventType } from "../domain/isSolveProgressEventTerminal";
import type {
  SolveProgressEventType,
  SolveProgressStatus,
} from "../domain/solveProgressEvent";

export type SolveLiveConnectionState =
  | "disconnected"
  | "connecting"
  | "connected"
  | "reconnecting"
  | "completed"
  | "failed";

export type SolveLiveErrorKind =
  | "connection"
  | "contract"
  | "invariant"
  | "storage"
  | "recovery";

export type SolveLiveError = {
  kind: SolveLiveErrorKind;
  message: string;
};

export type LastAcceptedSolveEventMeta = {
  eventType: SolveProgressEventType;
  status: SolveProgressStatus;
  sequence: number;
};

export type PersistedLiveSolveContext = {
  solveSessionId: string;
  progressChannelUrl: string;
  startedGridSignature: string | null;
  inputGrid: RecognizedGrid;
};

export type SolveLiveState = {
  activeSolveSessionId: string | null;
  progressChannelUrl: string | null;
  inputGrid: RecognizedGrid | null;
  visibleGrid: RecognizedGrid | null;
  lastAcceptedSequence: number;
  changedCells: ChangedSolveCell[];
  connectionState: SolveLiveConnectionState;
  terminalEventType: TerminalSolveProgressEventType | null;
  lastEvent: LastAcceptedSolveEventMeta | null;
  error: SolveLiveError | null;
  degradedReason: string | null;
  hasPersistedContext: boolean;
};

export type SolveLiveAction =
  | {
      type: "persistedContextDetected";
      hasPersistedContext: boolean;
    }
  | {
      type: "monitoringPrepared";
      solveSessionId: string;
      progressChannelUrl: string;
      inputGrid: RecognizedGrid;
      visibleGrid: RecognizedGrid;
    }
  | {
      type: "connectRequested";
    }
  | {
      type: "connectSucceeded";
    }
  | {
      type: "reconnecting";
    }
  | {
      type: "reconnected";
    }
  | {
      type: "connectionClosed";
    }
  | {
      type: "eventAccepted";
      event: LastAcceptedSolveEventMeta;
      visibleGrid: RecognizedGrid;
      changedCells: ChangedSolveCell[];
      terminalEventType: TerminalSolveProgressEventType | null;
    }
  | {
      type: "monitoringFailed";
      error: SolveLiveError;
      connectionState: SolveLiveConnectionState;
    }
  | {
      type: "degradedModeEntered";
      solveSessionId: string | null;
      progressChannelUrl: string | null;
      reason: string;
    }
  | {
      type: "liveStateReset";
      preserveVisibleGrid?: boolean;
    };

export const defaultSolveLiveState: SolveLiveState = {
  activeSolveSessionId: null,
  progressChannelUrl: null,
  inputGrid: null,
  visibleGrid: null,
  lastAcceptedSequence: -1,
  changedCells: [],
  connectionState: "disconnected",
  terminalEventType: null,
  lastEvent: null,
  error: null,
  degradedReason: null,
  hasPersistedContext: false,
};
