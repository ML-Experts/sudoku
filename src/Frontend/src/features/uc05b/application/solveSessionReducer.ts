import type { SolveSessionState, SolveSessionAction } from "./solveSessionTypes";

export function solveSessionReducer(
  state: SolveSessionState,
  action: SolveSessionAction,
): SolveSessionState {
  switch (action.type) {
    case "startRequested":
      return {
        ...state,
        phase: "starting",
        error: null,
        cancelDisposition: null,
      };

    case "startAccepted":
      return {
        phase: "active",
        session: {
          ...action.session,
          startedGridSignature: action.startedGridSignature,
          isSessionStaleForCurrentGrid: false,
        },
        error: null,
        cancelDisposition: null,
      };

    case "recoverRequested":
      return {
        ...state,
        phase: "recovering",
        error: null,
      };

    case "recoverSucceeded":
      return {
        phase: "active",
        session: {
          ...action.session,
          startedGridSignature: null,
          isSessionStaleForCurrentGrid: false,
        },
        error: null,
        cancelDisposition: null,
      };

    case "cancelRequested":
      return {
        ...state,
        phase: "cancelling",
        error: null,
      };

    case "cancelAccepted":
      if (!state.session) {
        return state;
      }

      return {
        phase: "active",
        session: {
          ...state.session,
          status: action.status,
        },
        error: null,
        cancelDisposition: action.requestDisposition,
      };

    case "sessionCleared":
      return {
        phase: "idle",
        session: null,
        error: null,
        cancelDisposition: action.requestDisposition ?? null,
      };

    case "sessionMarkedStale":
      if (!state.session) {
        return state;
      }

      return {
        ...state,
        session: {
          ...state.session,
          isSessionStaleForCurrentGrid: action.isStale,
        },
      };

    case "terminalEventObserved":
      if (!state.session) {
        return state;
      }

      return {
        ...state,
        phase: "active",
        session: {
          ...state.session,
          status: action.status,
        },
        error: null,
      };

    case "requestFailed":
      return {
        ...state,
        phase: "error",
        error: action.error,
      };

    default:
      return state;
  }
}
