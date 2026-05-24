import type { SolveLiveAction, SolveLiveState } from "./solveLiveTypes";
import { defaultSolveLiveState } from "./solveLiveTypes";

export function solveLiveReducer(
  state: SolveLiveState,
  action: SolveLiveAction,
): SolveLiveState {
  switch (action.type) {
    case "persistedContextDetected":
      return {
        ...state,
        hasPersistedContext: action.hasPersistedContext,
      };

    case "monitoringPrepared":
      return {
        ...state,
        activeSolveSessionId: action.solveSessionId,
        progressChannelUrl: action.progressChannelUrl,
        inputGrid: action.inputGrid,
        visibleGrid: action.visibleGrid,
        lastAcceptedSequence: -1,
        changedCells: [],
        connectionState: "disconnected",
        terminalEventType: null,
        lastEvent: null,
        error: null,
        degradedReason: null,
      };

    case "connectRequested":
      return {
        ...state,
        connectionState: "connecting",
        error: null,
      };

    case "connectSucceeded":
      return {
        ...state,
        connectionState: "connected",
        error: null,
      };

    case "reconnecting":
      return {
        ...state,
        connectionState: "reconnecting",
      };

    case "reconnected":
      return {
        ...state,
        connectionState: "connected",
      };

    case "connectionClosed":
      if (
        state.connectionState === "completed" ||
        state.connectionState === "failed"
      ) {
        return state;
      }

      return {
        ...state,
        connectionState: "disconnected",
      };

    case "eventAccepted":
      return {
        ...state,
        visibleGrid: action.visibleGrid,
        changedCells: action.changedCells,
        lastAcceptedSequence: action.event.sequence,
        lastEvent: action.event,
        terminalEventType: action.terminalEventType,
        connectionState:
          action.terminalEventType === null
            ? "connected"
            : action.terminalEventType === "failed"
              ? "failed"
              : "completed",
        error: null,
        degradedReason: null,
      };

    case "monitoringFailed":
      return {
        ...state,
        connectionState: action.connectionState,
        error: action.error,
      };

    case "degradedModeEntered":
      return {
        ...state,
        activeSolveSessionId: action.solveSessionId,
        progressChannelUrl: action.progressChannelUrl,
        connectionState: "disconnected",
        error: null,
        degradedReason: action.reason,
      };

    case "liveStateReset":
      return action.preserveVisibleGrid
        ? {
            ...defaultSolveLiveState,
            hasPersistedContext: state.hasPersistedContext,
            visibleGrid: state.visibleGrid,
          }
        : {
            ...defaultSolveLiveState,
            hasPersistedContext: state.hasPersistedContext,
          };

    default:
      return state;
  }
}
