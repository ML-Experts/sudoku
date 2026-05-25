import type { OverlayRenderTarget } from "../domain/overlayRenderTarget";

export type OverlaySessionStatus =
  | "idle"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export type OverlaySessionErrorKind =
  | "contract"
  | "business"
  | "technical"
  | "invariant"
  | "canvas";

export type OverlaySessionError = {
  kind: OverlaySessionErrorKind;
  message: string;
  errorType: string | null;
  httpStatus: number | null;
  isRetriable: boolean;
};

export type OverlaySessionState = {
  status: OverlaySessionStatus;
  sessionId: number | null;
  renderedCells: string[][] | null;
  completedCount: number;
  targetCount: number;
  previewUrl: string | null;
  error: OverlaySessionError | null;
  failedTarget: OverlayRenderTarget | null;
};

export type OverlaySessionAction =
  | {
      type: "sessionStarted";
      sessionId: number;
      renderedCells: string[][];
      targetCount: number;
    }
  | {
      type: "cellRendered";
      sessionId: number;
      renderedCells: string[][];
      previewUrl: string;
      completedCount: number;
    }
  | {
      type: "sessionCompleted";
      sessionId: number;
      previewUrl: string;
    }
  | {
      type: "sessionFailed";
      sessionId: number;
      error: OverlaySessionError;
      renderedCells: string[][] | null;
      previewUrl: string | null;
      failedTarget: OverlayRenderTarget | null;
    }
  | {
      type: "sessionCancelled";
      sessionId: number | null;
    }
  | {
      type: "sessionReset";
    };

export const defaultOverlaySessionState: OverlaySessionState = {
  status: "idle",
  sessionId: null,
  renderedCells: null,
  completedCount: 0,
  targetCount: 0,
  previewUrl: null,
  error: null,
  failedTarget: null,
};
