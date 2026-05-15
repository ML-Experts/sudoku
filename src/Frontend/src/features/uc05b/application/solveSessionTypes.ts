import type { SolveSessionStatus } from "../domain/solveSessionStatus";

export type SolveSessionRequestPhase =
  | "idle"
  | "starting"
  | "recovering"
  | "active"
  | "cancelling"
  | "error";

export type SolveSessionOperation = "start" | "recover" | "cancel";

export type SolveSessionError = {
  message: string;
  errorType: string | null;
  httpStatus: number | null;
  isRetriable: boolean;
  operation: SolveSessionOperation;
};

export type SolveSessionViewModel = {
  solveSessionId: string;
  status: SolveSessionStatus;
  progressChannelUrl: string;
  startedGridSignature: string | null;
  isSessionStaleForCurrentGrid: boolean;
};

export type SolveSessionState = {
  phase: SolveSessionRequestPhase;
  session: SolveSessionViewModel | null;
  error: SolveSessionError | null;
  cancelDisposition: string | null;
};

export type SolveSessionAction =
  | {
      type: "startRequested";
    }
  | {
      type: "startAccepted";
      session: Omit<
        SolveSessionViewModel,
        "startedGridSignature" | "isSessionStaleForCurrentGrid"
      >;
      startedGridSignature: string;
    }
  | {
      type: "recoverRequested";
    }
  | {
      type: "recoverSucceeded";
      session: Omit<
        SolveSessionViewModel,
        "startedGridSignature" | "isSessionStaleForCurrentGrid"
      >;
    }
  | {
      type: "cancelRequested";
    }
  | {
      type: "cancelAccepted";
      status: SolveSessionStatus;
      requestDisposition: string;
    }
  | {
      type: "sessionCleared";
      requestDisposition?: string | null;
    }
  | {
      type: "sessionMarkedStale";
      isStale: boolean;
    }
  | {
      type: "terminalEventObserved";
      status: SolveSessionStatus;
    }
  | {
      type: "requestFailed";
      error: SolveSessionError;
    };

export const defaultSolveSessionState: SolveSessionState = {
  phase: "idle",
  session: null,
  error: null,
  cancelDisposition: null,
};
