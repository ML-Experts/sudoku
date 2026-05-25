import type {
  OverlaySessionAction,
  OverlaySessionState,
} from "./overlaySessionTypes";
import { defaultOverlaySessionState } from "./overlaySessionTypes";

export function overlaySessionReducer(
  state: OverlaySessionState,
  action: OverlaySessionAction,
): OverlaySessionState {
  switch (action.type) {
    case "sessionStarted":
      return {
        status: "running",
        sessionId: action.sessionId,
        renderedCells: action.renderedCells,
        completedCount: 0,
        targetCount: action.targetCount,
        previewUrl: null,
        error: null,
        failedTarget: null,
      };

    case "cellRendered":
      if (state.sessionId !== action.sessionId) {
        return state;
      }

      return {
        ...state,
        renderedCells: action.renderedCells,
        previewUrl: action.previewUrl,
        completedCount: action.completedCount,
      };

    case "sessionCompleted":
      if (state.sessionId !== action.sessionId) {
        return state;
      }

      return {
        ...state,
        status: "completed",
        previewUrl: action.previewUrl,
        error: null,
        failedTarget: null,
      };

    case "sessionFailed":
      if (state.sessionId !== action.sessionId) {
        return state;
      }

      return {
        ...state,
        status: "failed",
        renderedCells: action.renderedCells ?? state.renderedCells,
        previewUrl: action.previewUrl ?? state.previewUrl,
        error: action.error,
        failedTarget: action.failedTarget,
      };

    case "sessionCancelled":
      if (
        action.sessionId !== null &&
        state.sessionId !== null &&
        state.sessionId !== action.sessionId
      ) {
        return state;
      }

      return {
        ...state,
        status: "cancelled",
        error: null,
      };

    case "sessionReset":
      return defaultOverlaySessionState;

    default:
      return state;
  }
}
