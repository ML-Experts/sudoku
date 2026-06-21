import { useCallback, useEffect, useMemo, useReducer, useRef } from "react";

import type {
  CellsGridApiResponse,
  SudokuCellInferenceParametersApiEntry,
} from "../../../types/api";
import {
  SudokuCellInferenceApiError,
} from "../../../api/sudokuCellsInference";
import { applyRecognitionResult } from "../domain/applyRecognitionResult";
import { createEmptyRecognizedGrid } from "../domain/createEmptyRecognizedGrid";
import { calculateRecognitionProgress } from "../domain/recognitionProgress";
import { isRecognizedDigit } from "../domain/recognizedGrid";
import {
  recognizeCellsGrid,
  CellRecognitionTaskError,
  CellsGridShapeError,
} from "./recognizeCellsGrid";
import { recognitionSessionReducer } from "./recognitionSessionReducer";
import {
  defaultRecognitionSessionState,
  type RecognitionSessionError,
} from "./recognitionSessionTypes";

const DEFAULT_RECOGNITION_CONCURRENCY = 4;

function toRecognitionSessionError(error: unknown): RecognitionSessionError {
  if (error instanceof SudokuCellInferenceApiError) {
    const messageByStatus: Record<number, string> = {
      400: "Backend odrzucil obraz komorki jako niepoprawny.",
      409: "Brak aktywnego modelu inferencyjnego albo model jest niespojny.",
      422: "Wybrana komorka nie nadaje sie do przetworzenia.",
      500: "Backend zakonczyl rozpoznanie bledem technicznym.",
      502: "Backend otrzymal niepoprawna odpowiedz od ML.",
      503: "Backend nie moze teraz skorzystac z uslugi ML.",
      504: "Rozpoznanie komorki przekroczylo limit czasu.",
    };

    return {
      message: messageByStatus[error.status] ?? error.message,
      errorType: error.errorType ?? null,
      httpStatus: error.status,
      isRetriable:
        error.status >= 500 || error.status === 409 || error.status === 422,
    };
  }

  if (error instanceof CellsGridShapeError) {
    return {
      message: error.message,
      errorType: "invalid_cells_grid_shape",
      httpStatus: null,
      isRetriable: false,
    };
  }

  if (error instanceof Error) {
    return {
      message: error.message,
      errorType: null,
      httpStatus: null,
      isRetriable: true,
    };
  }

  return {
    message: "Nie udalo sie rozpoznac siatki komorek.",
    errorType: null,
    httpStatus: null,
    isRetriable: true,
  };
}

type UseUc05aRecognitionOptions = {
  apiBaseUrl: string;
  cellsGrid: CellsGridApiResponse | null;
  inferenceParameters?: SudokuCellInferenceParametersApiEntry | null;
  isInferenceParametersValid?: boolean;
};

export function useUc05aRecognition({
  apiBaseUrl,
  cellsGrid,
  inferenceParameters = null,
  isInferenceParametersValid = true,
}: UseUc05aRecognitionOptions) {
  const [state, dispatch] = useReducer(
    recognitionSessionReducer,
    defaultRecognitionSessionState,
  );
  const sessionIdSequenceRef = useRef(0);
  const activeSessionIdRef = useRef<number | null>(null);
  const activeControllerRef = useRef<AbortController | null>(null);

  const cancelRecognition = useCallback(() => {
    const sessionId = activeSessionIdRef.current;

    if (activeControllerRef.current) {
      console.info("[UC-05A] Anulowano sesje rozpoznania.");
      activeControllerRef.current.abort();
      activeControllerRef.current = null;
    }

    activeSessionIdRef.current = null;
    dispatch({
      type: "sessionCancelled",
      sessionId,
    });
  }, []);

  const resetRecognition = useCallback(() => {
    activeControllerRef.current?.abort();
    activeControllerRef.current = null;
    activeSessionIdRef.current = null;
    dispatch({ type: "sessionReset" });
  }, []);

  const startRecognition = useCallback(async () => {
    if (!cellsGrid || !isInferenceParametersValid) {
      return;
    }

    activeControllerRef.current?.abort();

    const recognizedGrid = createEmptyRecognizedGrid();
    const sessionId = sessionIdSequenceRef.current + 1;
    sessionIdSequenceRef.current = sessionId;
    activeSessionIdRef.current = sessionId;

    const controller = new AbortController();
    activeControllerRef.current = controller;

    dispatch({
      type: "sessionStarted",
      sessionId,
      recognizedGrid,
      totalCount: 81,
    });

    console.info("[UC-05A] Start sesji rozpoznania.");

    let latestGrid = recognizedGrid;

    try {
      await recognizeCellsGrid({
        apiBaseUrl,
        cellsGrid,
        inferenceParameters,
        signal: controller.signal,
        concurrency: DEFAULT_RECOGNITION_CONCURRENCY,
        onCellRecognized: (coordinates, result) => {
          if (activeSessionIdRef.current !== sessionId) {
            return;
          }

          latestGrid = applyRecognitionResult(latestGrid, coordinates, {
            digit:
              result.digit === null
                ? null
                : isRecognizedDigit(result.digit)
                  ? result.digit
                  : null,
          });

          const progress = calculateRecognitionProgress(latestGrid);

          dispatch({
            type: "cellRecognized",
            sessionId,
            recognizedGrid: latestGrid,
            completedCount: progress.completedCount,
          });
        },
      });

      if (activeSessionIdRef.current !== sessionId) {
        return;
      }

      activeControllerRef.current = null;
      activeSessionIdRef.current = null;
      console.info("[UC-05A] Sesja rozpoznania zakonczona sukcesem.");
      dispatch({
        type: "sessionCompleted",
        sessionId,
      });
    } catch (error) {
      if (controller.signal.aborted) {
        dispatch({
          type: "sessionCancelled",
          sessionId,
        });
        return;
      }

      if (activeSessionIdRef.current !== sessionId) {
        return;
      }

      activeControllerRef.current?.abort();
      activeControllerRef.current = null;
      activeSessionIdRef.current = null;

      const failedCell =
        error instanceof CellRecognitionTaskError ? error.coordinates : null;
      const rootCause =
        error instanceof CellRecognitionTaskError ? error.cause : error;
      const mappedError = toRecognitionSessionError(rootCause);
      const failedGrid =
        failedCell === null
          ? latestGrid
          : applyRecognitionResult(latestGrid, failedCell, {
              digit: null,
              source: "error",
            });

      if (mappedError.httpStatus === 409 || mappedError.httpStatus === 422) {
        console.warn("[UC-05A] Sesja rozpoznania zakonczona bledem kontraktowym.");
      } else if (
        mappedError.httpStatus !== null &&
        mappedError.httpStatus >= 500
      ) {
        console.error("[UC-05A] Sesja rozpoznania zakonczona bledem backendu.");
      }

      dispatch({
        type: "sessionFailed",
        sessionId,
        recognizedGrid: failedGrid,
        error: mappedError,
        failedCell,
      });
    }
  }, [apiBaseUrl, cellsGrid, inferenceParameters, isInferenceParametersValid]);

  const retryRecognition = useCallback(async () => {
    await startRecognition();
  }, [startRecognition]);

  useEffect(() => {
    return () => {
      activeControllerRef.current?.abort();
    };
  }, []);

  useEffect(() => {
    resetRecognition();
  }, [cellsGrid, resetRecognition]);

  const progress = useMemo(
    () => calculateRecognitionProgress(state.recognizedGrid),
    [state.recognizedGrid],
  );

  return {
    state,
    progress,
    startRecognition,
    cancelRecognition,
    retryRecognition,
    resetRecognition,
    canStartRecognition:
      cellsGrid !== null &&
      isInferenceParametersValid &&
      state.status !== "running",
    canRetryRecognition:
      cellsGrid !== null &&
      isInferenceParametersValid &&
      state.status !== "running" &&
      (state.status === "failed" || state.status === "cancelled"),
    canCancelRecognition: state.status === "running",
  };
}
