import type { GridCoordinates } from "../domain/gridCoordinates";
import type { RecognizedGrid } from "../domain/recognizedGrid";

export type RecognitionSessionStatus =
  | "idle"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export type RecognitionSessionError = {
  message: string;
  errorType: string | null;
  httpStatus: number | null;
  isRetriable: boolean;
};

export type RecognitionSessionState = {
  status: RecognitionSessionStatus;
  sessionId: number | null;
  recognizedGrid: RecognizedGrid | null;
  completedCount: number;
  totalCount: number;
  error: RecognitionSessionError | null;
  failedCell: GridCoordinates | null;
};

export type RecognitionSessionAction =
  | {
      type: "sessionStarted";
      sessionId: number;
      recognizedGrid: RecognizedGrid;
      totalCount: number;
    }
  | {
      type: "cellRecognized";
      sessionId: number;
      recognizedGrid: RecognizedGrid;
      completedCount: number;
    }
  | {
      type: "sessionFailed";
      sessionId: number;
      recognizedGrid: RecognizedGrid | null;
      error: RecognitionSessionError;
      failedCell: GridCoordinates | null;
    }
  | {
      type: "sessionCompleted";
      sessionId: number;
    }
  | {
      type: "sessionCancelled";
      sessionId: number | null;
    }
  | {
      type: "sessionReset";
    };

export const defaultRecognitionSessionState: RecognitionSessionState = {
  status: "idle",
  sessionId: null,
  recognizedGrid: null,
  completedCount: 0,
  totalCount: 0,
  error: null,
  failedCell: null,
};
