import { useCallback, useEffect, useMemo, useReducer, useRef } from "react";

import { SudokuOverlayCellApiError } from "../../../api/sudokuOverlayCells";
import { toImageDataUrl } from "../../../shared/images/toImageDataUrl";
import type { CellsGridApiResponse } from "../../../types/api";
import type { RecognizedGrid } from "../../uc05a/domain/recognizedGrid";
import type { TerminalSolveProgressEventType } from "../../uc05e/domain/isSolveProgressEventTerminal";
import { buildOverlayRenderPlan } from "../domain/buildOverlayRenderPlan";
import { calculateOverlayProgress } from "../domain/overlayProgress";
import type { OverlayRenderTarget } from "../domain/overlayRenderTarget";
import { overlaySessionReducer } from "./overlaySessionReducer";
import {
  OverlayCellRenderTaskError,
  OverlayCellsGridShapeError,
  renderSolvedOverlay,
} from "./renderSolvedOverlay";
import {
  defaultOverlaySessionState,
  type OverlaySessionError,
} from "./overlaySessionTypes";
import { OverlayGridConsistencyError } from "../domain/assertOverlayGridConsistency";

type UseUc05dOverlayOptions = {
  apiBaseUrl: string;
  cellsGrid: CellsGridApiResponse | null;
  inputGrid: RecognizedGrid | null;
  solvedGrid: RecognizedGrid | null;
  terminalEventType: TerminalSolveProgressEventType | null;
  degradedReason: string | null;
};

export type Uc05dOverlayAvailability = {
  canGenerate: boolean;
  tone: "success" | "warning" | "loading" | "error";
  message: string;
  targetCount: number | null;
  renderPlan: OverlayRenderTarget[] | null;
};

function createOverlayBaseCellsGrid(cellsGrid: CellsGridApiResponse): string[][] {
  return cellsGrid.cells.map((row) => row.map((cell) => toImageDataUrl(cell)));
}

function toOverlaySessionError(error: unknown): OverlaySessionError {
  if (error instanceof SudokuOverlayCellApiError) {
    const messageByStatus: Record<number, string> = {
      400: "Backend odrzucil payload overlay komorki jako niepoprawny.",
      422: "Backend nie moze wyrenderowac wskazanej komorki albo cyfry.",
      500: "Backend zakonczyl render overlay bledem technicznym.",
      502: "Backend zwrocil niepoprawna odpowiedz z warstwy renderera overlay.",
      503: "Backend nie moze teraz skorzystac z renderera overlay.",
      504: "Render overlay komorki przekroczyl limit czasu.",
    };

    return {
      kind:
        error.status === 400
          ? "contract"
          : error.status === 422
            ? "business"
            : "technical",
      message: messageByStatus[error.status] ?? error.message,
      errorType: error.errorType ?? null,
      httpStatus: error.status,
      isRetriable: error.status >= 500,
    };
  }

  if (
    error instanceof OverlayGridConsistencyError ||
    error instanceof OverlayCellsGridShapeError
  ) {
    return {
      kind: "invariant",
      message: error.message,
      errorType: "overlay_invariant_violation",
      httpStatus: null,
      isRetriable: false,
    };
  }

  if (error instanceof Error) {
    return {
      kind: "canvas",
      message: error.message,
      errorType: null,
      httpStatus: null,
      isRetriable: true,
    };
  }

  return {
    kind: "technical",
    message: "Nie udalo sie wygenerowac overlay rozwiazania sudoku.",
    errorType: null,
    httpStatus: null,
    isRetriable: true,
  };
}

function getOverlayAvailability({
  cellsGrid,
  inputGrid,
  solvedGrid,
  terminalEventType,
  degradedReason,
}: Omit<UseUc05dOverlayOptions, "apiBaseUrl">): Uc05dOverlayAvailability {
  if (terminalEventType !== "completed") {
    if (degradedReason) {
      return {
        canGenerate: false,
        tone: "warning",
        message: degradedReason,
        targetCount: null,
        renderPlan: null,
      };
    }

    return {
      canGenerate: false,
      tone: "loading",
      message:
        "Overlay jest dostepny dopiero po terminalnym `completed` z `UC-05E`.",
      targetCount: null,
      renderPlan: null,
    };
  }

  if (!cellsGrid) {
    return {
      canGenerate: false,
      tone: "warning",
      message:
        "Brakuje zrodlowych obrazow komorek z `UC-04`, dlatego overlay nie moze zostac wygenerowany.",
      targetCount: null,
      renderPlan: null,
    };
  }

  if (!inputGrid || !solvedGrid) {
    return {
      canGenerate: false,
      tone: "warning",
      message:
        "Brakuje `inputGrid` albo finalnego `visibleGrid`, dlatego overlay pozostaje zablokowany.",
      targetCount: null,
      renderPlan: null,
    };
  }

  try {
    const renderPlan = buildOverlayRenderPlan(inputGrid, solvedGrid);

    return {
      canGenerate: true,
      tone: "success",
      message:
        renderPlan.length === 0
          ? "Solve nie dodal nowych cyfr. FE zlozy finalna plansze bez requestow overlay."
          : `Overlay jest gotowy do uruchomienia dla ${renderPlan.length} nowych komorek.`,
      targetCount: renderPlan.length,
      renderPlan,
    };
  } catch (error) {
    const message =
      error instanceof Error
        ? error.message
        : "Wykryto niespojnosc miedzy inputGrid i solvedGrid dla overlay.";

    return {
      canGenerate: false,
      tone: "error",
      message,
      targetCount: null,
      renderPlan: null,
    };
  }
}

export function useUc05dOverlay({
  apiBaseUrl,
  cellsGrid,
  inputGrid,
  solvedGrid,
  terminalEventType,
  degradedReason,
}: UseUc05dOverlayOptions) {
  const [state, dispatch] = useReducer(
    overlaySessionReducer,
    defaultOverlaySessionState,
  );
  const sessionIdSequenceRef = useRef(0);
  const activeSessionIdRef = useRef<number | null>(null);
  const activeControllerRef = useRef<AbortController | null>(null);
  const didMountRef = useRef(false);

  const availability = useMemo(
    () =>
      getOverlayAvailability({
        cellsGrid,
        inputGrid,
        solvedGrid,
        terminalEventType,
        degradedReason,
      }),
    [cellsGrid, degradedReason, inputGrid, solvedGrid, terminalEventType],
  );

  const cancelOverlayRender = useCallback(() => {
    const sessionId = activeSessionIdRef.current;

    if (activeControllerRef.current) {
      console.warn("[UC-05D] Sesja overlay zostala anulowana.", {
        sessionId,
      });
      activeControllerRef.current.abort();
      activeControllerRef.current = null;
    }

    activeSessionIdRef.current = null;
    dispatch({
      type: "sessionCancelled",
      sessionId,
    });
  }, []);

  const resetOverlay = useCallback(() => {
    activeControllerRef.current?.abort();
    activeControllerRef.current = null;
    activeSessionIdRef.current = null;
    dispatch({ type: "sessionReset" });
  }, []);

  const startOverlayRender = useCallback(async () => {
    if (
      !availability.canGenerate ||
      !availability.renderPlan ||
      !cellsGrid ||
      !inputGrid ||
      !solvedGrid
    ) {
      return;
    }

    activeControllerRef.current?.abort();

    const sessionId = sessionIdSequenceRef.current + 1;
    sessionIdSequenceRef.current = sessionId;
    activeSessionIdRef.current = sessionId;

    const controller = new AbortController();
    activeControllerRef.current = controller;

    const baseRenderedCells = createOverlayBaseCellsGrid(cellsGrid);
    let latestRenderedCells = baseRenderedCells;
    let latestPreviewUrl: string | null = null;

    dispatch({
      type: "sessionStarted",
      sessionId,
      renderedCells: baseRenderedCells,
      targetCount: availability.renderPlan.length,
    });

    console.info("[UC-05D] Start sesji overlay.", {
      sessionId,
      targetCount: availability.renderPlan.length,
    });

    try {
      const result = await renderSolvedOverlay({
        apiBaseUrl,
        cellsGrid,
        initialRenderedCells: baseRenderedCells,
        targets: availability.renderPlan,
        signal: controller.signal,
        onCellRendered: (update) => {
          if (activeSessionIdRef.current !== sessionId) {
            return;
          }

          latestRenderedCells = update.renderedCells;
          latestPreviewUrl = update.previewUrl;

          dispatch({
            type: "cellRendered",
            sessionId,
            renderedCells: update.renderedCells,
            previewUrl: update.previewUrl,
            completedCount: update.completedCount,
          });
        },
      });

      if (activeSessionIdRef.current !== sessionId) {
        return;
      }

      activeControllerRef.current = null;
      activeSessionIdRef.current = null;

      if (availability.renderPlan.length === 0) {
        console.info(
          "[UC-05D] Brak targetow overlay. Zlozono plansze z oryginalnych komorek.",
          {
            sessionId,
          },
        );
      } else {
        console.info("[UC-05D] Sesja overlay zakonczona sukcesem.", {
          sessionId,
          completedCount: availability.renderPlan.length,
          targetCount: availability.renderPlan.length,
        });
      }

      dispatch({
        type: "sessionCompleted",
        sessionId,
        previewUrl: result.previewUrl,
      });
    } catch (error) {
      if (controller.signal.aborted) {
        dispatch({
          type: "sessionCancelled",
          sessionId,
        });

        if (activeSessionIdRef.current === sessionId) {
          activeSessionIdRef.current = null;
          activeControllerRef.current = null;
        }
        return;
      }

      const failedTarget =
        error instanceof OverlayCellRenderTaskError ? error.target : null;
      const rootCause =
        error instanceof OverlayCellRenderTaskError ? error.cause : error;
      const mappedError = toOverlaySessionError(rootCause);

      if (mappedError.httpStatus === 422) {
        console.warn("[UC-05D] Backend odrzucil render pojedynczej komorki.", {
          sessionId,
          rowIndex: failedTarget?.rowIndex ?? null,
          columnIndex: failedTarget?.columnIndex ?? null,
          httpStatus: mappedError.httpStatus,
          errorType: mappedError.errorType,
        });
      } else if (mappedError.kind === "invariant") {
        console.error("[UC-05D] Wykryto naruszenie niezmiennikow overlay.", {
          sessionId,
          errorType: mappedError.errorType,
        });
      } else if (
        mappedError.httpStatus !== null &&
        mappedError.httpStatus >= 500
      ) {
        console.error("[UC-05D] Sesja overlay zakonczona bledem backendu.", {
          sessionId,
          rowIndex: failedTarget?.rowIndex ?? null,
          columnIndex: failedTarget?.columnIndex ?? null,
          httpStatus: mappedError.httpStatus,
          errorType: mappedError.errorType,
        });
      } else {
        console.error("[UC-05D] Nie udalo sie zlozyc preview overlay.", {
          sessionId,
          errorType: mappedError.errorType,
        });
      }

      if (activeSessionIdRef.current === sessionId) {
        activeSessionIdRef.current = null;
        activeControllerRef.current = null;
      }

      dispatch({
        type: "sessionFailed",
        sessionId,
        error: mappedError,
        renderedCells: latestRenderedCells,
        previewUrl: latestPreviewUrl,
        failedTarget,
      });
    }
  }, [apiBaseUrl, availability, cellsGrid, inputGrid, solvedGrid]);

  const retryOverlayRender = useCallback(async () => {
    await startOverlayRender();
  }, [startOverlayRender]);

  useEffect(() => {
    if (!didMountRef.current) {
      didMountRef.current = true;
      return;
    }

    if (activeControllerRef.current) {
      console.warn("[UC-05D] Zmieniono dane wejsciowe overlay. Reset lokalnej sesji.", {
        sessionId: activeSessionIdRef.current,
      });
    }

    resetOverlay();
  }, [cellsGrid, inputGrid, solvedGrid, terminalEventType, resetOverlay]);

  useEffect(() => {
    return () => {
      activeControllerRef.current?.abort();
    };
  }, []);

  const progress = useMemo(
    () => calculateOverlayProgress(state.targetCount, state.completedCount),
    [state.completedCount, state.targetCount],
  );

  return {
    state,
    progress,
    availability,
    startOverlayRender,
    retryOverlayRender,
    cancelOverlayRender,
    canStartOverlay:
      availability.canGenerate &&
      state.status !== "running" &&
      state.status === "idle",
    canRetryOverlay:
      availability.canGenerate &&
      state.status !== "running" &&
      (state.status === "failed" ||
        state.status === "cancelled" ||
        state.status === "completed"),
    canCancelOverlay: state.status === "running",
  };
}
