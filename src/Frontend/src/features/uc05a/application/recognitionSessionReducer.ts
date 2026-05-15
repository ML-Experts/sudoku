import type {
  RecognitionSessionAction,
  RecognitionSessionState,
} from "./recognitionSessionTypes";
import { defaultRecognitionSessionState } from "./recognitionSessionTypes";

export function recognitionSessionReducer(
  state: RecognitionSessionState,
  action: RecognitionSessionAction,
): RecognitionSessionState {
  switch (action.type) {
    case "sessionStarted":
      return {
        status: "running",
        sessionId: action.sessionId,
        recognizedGrid: action.recognizedGrid,
        completedCount: 0,
        totalCount: action.totalCount,
        error: null,
        failedCell: null,
      };

    case "cellRecognized":
      if (state.sessionId !== action.sessionId) {
        return state;
      }

      return {
        ...state,
        recognizedGrid: action.recognizedGrid,
        completedCount: action.completedCount,
      };

    case "sessionFailed":
      if (state.sessionId !== action.sessionId) {
        return state;
      }

      return {
        ...state,
        status: "failed",
        recognizedGrid: action.recognizedGrid ?? state.recognizedGrid,
        error: action.error,
        failedCell: action.failedCell,
      };

    case "sessionCompleted":
      if (state.sessionId !== action.sessionId) {
        return state;
      }

      return {
        ...state,
        status: "completed",
        error: null,
        failedCell: null,
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
      return defaultRecognitionSessionState;

    default:
      return state;
  }
}
