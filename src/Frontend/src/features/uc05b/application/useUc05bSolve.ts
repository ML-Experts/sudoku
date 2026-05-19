import { useCallback, useEffect, useMemo, useReducer } from "react";

import {
  getActiveSudokuSolveSession,
  postCancelSudokuSolve,
  postStartSudokuSolve,
  SudokuSolveApiError,
} from "../../../api/sudokuSolve";
import type { SolveSessionApiResponse } from "../../../types/api";
import type { RecognitionSessionStatus } from "../../uc05a/application/recognitionSessionTypes";
import type { RecognizedGrid } from "../../uc05a/domain/recognizedGrid";
import { clearPersistedLiveSolveContext } from "../../uc05e/infrastructure/solveLiveSessionStorage";
import { createGridSignature } from "../domain/createGridSignature";
import {
  GridNotReadyForSolveError,
  isRecognizedGridReadyForSolve,
  prepareRecognizedGridForSolve,
} from "../domain/prepareRecognizedGridForSolve";
import {
  isActiveSolveSessionStatus,
  isSolveSessionStatus,
  type SolveSessionStatus,
} from "../domain/solveSessionStatus";
import { toSolveSudokuApiEntry } from "../domain/toSolveSudokuApiEntry";
import { solveSessionReducer } from "./solveSessionReducer";
import {
  defaultSolveSessionState,
  type SolveSessionError,
  type SolveSessionOperation,
} from "./solveSessionTypes";

const DEFAULT_SOLVER_STEP_DELAY_MS = 50;

type UseUc05bSolveOptions = {
  apiBaseUrl: string;
  recognizedGrid: RecognizedGrid | null;
  recognitionStatus: RecognitionSessionStatus;
};

type GridSolveReadiness = {
  isReady: boolean;
  message: string;
};

function mapSessionFromApi(response: SolveSessionApiResponse) {
  return {
    solveSessionId: response.solveSessionId,
    status: response.status as SolveSessionStatus,
    progressChannelUrl: response.progressChannelUrl,
  };
}

function toSolveSessionError(
  error: unknown,
  operation: SolveSessionOperation,
): SolveSessionError {
  if (error instanceof GridNotReadyForSolveError) {
    return {
      message: error.message,
      errorType: "grid_not_ready_for_solve",
      httpStatus: null,
      isRetriable: false,
      operation,
    };
  }

  if (error instanceof SudokuSolveApiError) {
    const statusMessagesByOperation: Record<
      SolveSessionOperation,
      Partial<Record<number, string>>
    > = {
      start: {
        400: "Backend odrzucil payload solve jako niepoprawny.",
        409: "Aktywna sesja solve juz istnieje.",
        422: "Rozpoznany grid lamie reguly sudoku i nie moze zostac rozwiazany.",
        500: "Backend zakonczyl start solve bledem technicznym.",
      },
      recover: {
        401: "Publiczny recovery aktywnej sesji nieoczekiwanie wymaga autoryzacji.",
        403: "Publiczny recovery aktywnej sesji zostal zabroniony po stronie backendu.",
        500: "Backend zakonczyl recovery aktywnej sesji bledem technicznym.",
      },
      cancel: {
        400: "Backend odrzucil zadanie anulowania jako niepoprawne.",
        404: "Backend nie znalazl wskazanej sesji solve do anulowania.",
        500: "Backend zakonczyl anulowanie sesji bledem technicznym.",
      },
    };

    return {
      message:
        statusMessagesByOperation[operation][error.status] ?? error.message,
      errorType: error.errorType ?? null,
      httpStatus: error.status,
      isRetriable:
        error.status >= 500 ||
        error.status === 409 ||
        (operation === "cancel" && error.status === 404),
      operation,
    };
  }

  if (error instanceof Error) {
    return {
      message: error.message,
      errorType: null,
      httpStatus: null,
      isRetriable: true,
      operation,
    };
  }

  return {
    message: "Nie udalo sie obsluzyc sesji rozwiazywania sudoku.",
    errorType: null,
    httpStatus: null,
    isRetriable: true,
    operation,
  };
}

function getGridSolveReadiness(
  recognizedGrid: RecognizedGrid | null,
  recognitionStatus: RecognitionSessionStatus,
): GridSolveReadiness {
  if (!recognizedGrid) {
    return {
      isReady: false,
      message: "Najpierw zakoncz `UC-05A`, aby zbudowac recognizedGrid.",
    };
  }

  if (recognitionStatus === "idle") {
    return {
      isReady: false,
      message: "Uruchom rozpoznanie komorek, zanim wystartujesz solver.",
    };
  }

  if (recognitionStatus === "running") {
    return {
      isReady: false,
      message: "Poczekaj na zakonczenie rozpoznawania wszystkich komorek.",
    };
  }

  if (recognitionStatus === "failed") {
    return {
      isReady: false,
      message: "UC-05A zakonczyl sie bledem. Napraw grid albo wykonaj retry.",
    };
  }

  if (recognitionStatus === "cancelled") {
    return {
      isReady: false,
      message: "Rozpoznanie zostalo anulowane. Wznow je, aby przygotowac grid do solve.",
    };
  }

  if (!isRecognizedGridReadyForSolve(recognizedGrid)) {
    return {
      isReady: false,
      message:
        "Grid nie jest gotowy do solve, bo zawiera komorki oczekujace albo bledne.",
    };
  }

  return {
    isReady: true,
    message:
      "Grid jest gotowy do solve. Solver uzyje tego samego recognizedGrid z UC-05A.",
  };
}

export function useUc05bSolve({
  apiBaseUrl,
  recognizedGrid,
  recognitionStatus,
}: UseUc05bSolveOptions) {
  const [state, dispatch] = useReducer(
    solveSessionReducer,
    defaultSolveSessionState,
  );

  const gridReadiness = useMemo(
    () => getGridSolveReadiness(recognizedGrid, recognitionStatus),
    [recognitionStatus, recognizedGrid],
  );

  const recoverActiveSolveDetailed = useCallback(
    async (): Promise<
      | (ReturnType<typeof mapSessionFromApi> & {
          startedGridSignature: string | null;
          isSessionStaleForCurrentGrid: boolean;
        })
      | null
    > => {
    dispatch({ type: "recoverRequested" });

    try {
      const recoveredSession = await getActiveSudokuSolveSession(apiBaseUrl);

      if (!recoveredSession) {
          console.warn("[UC-05B] Recovery nie znalazl aktywnej sesji solve.");
          clearPersistedLiveSolveContext();
        dispatch({ type: "sessionCleared" });
          return null;
        }

        const mappedSession = mapSessionFromApi(recoveredSession);

        if (!isActiveSolveSessionStatus(mappedSession.status)) {
          console.warn("[UC-05B] Recovery zwrocil sesje w stanie terminalnym.", {
            solveSessionId: mappedSession.solveSessionId,
            status: mappedSession.status,
          });
          clearPersistedLiveSolveContext();
        } else {
          console.info("[UC-05B] Odzyskano aktywna sesje solve.", {
            solveSessionId: mappedSession.solveSessionId,
            status: mappedSession.status,
          });
        }

        dispatch({
          type: "recoverSucceeded",
          session: mappedSession,
        });

        return {
          ...mappedSession,
          startedGridSignature: null,
          isSessionStaleForCurrentGrid: false,
        };
      } catch (error) {
        if (
          error instanceof SudokuSolveApiError &&
          (error.status === 401 || error.status === 403)
        ) {
          console.error(
            "[UC-05B] Publiczny recovery aktywnej sesji zostal odrzucony.",
          );
        } else if (
          error instanceof SudokuSolveApiError &&
          error.status >= 500
        ) {
          console.error(
            "[UC-05B] Recovery aktywnej sesji zakonczyl sie bledem backendu.",
          );
        }

        dispatch({
          type: "requestFailed",
          error: toSolveSessionError(error, "recover"),
        });
        throw error;
      }
    },
    [apiBaseUrl],
  );

  const recoverActiveSolve = useCallback(async () => {
    await recoverActiveSolveDetailed();
  }, [recoverActiveSolveDetailed]);

  const startSolve = useCallback(async () => {
    if (!recognizedGrid) {
      dispatch({
        type: "requestFailed",
        error: toSolveSessionError(
          new GridNotReadyForSolveError(
            "Brakuje recognizedGrid do uruchomienia solve.",
          ),
          "start",
        ),
      });
      return;
    }

    dispatch({ type: "startRequested" });

    try {
      const solveReadyGrid = prepareRecognizedGridForSolve(recognizedGrid);
      const request = toSolveSudokuApiEntry(
        solveReadyGrid,
        DEFAULT_SOLVER_STEP_DELAY_MS,
      );
      const startedGridSignature = createGridSignature(solveReadyGrid);
      const session = await postStartSudokuSolve(apiBaseUrl, request);

      console.info("[UC-05B] Backend przyjal start solve.", {
        solveSessionId: session.solveSessionId,
        status: session.status,
        solverStepDelayMs: DEFAULT_SOLVER_STEP_DELAY_MS,
      });

      dispatch({
        type: "startAccepted",
        session: mapSessionFromApi(session),
        startedGridSignature,
      });
    } catch (error) {
      if (error instanceof SudokuSolveApiError && error.status === 409) {
        console.warn("[UC-05B] Wykryto konflikt aktywnej sesji. Uruchamiam recovery.");

        try {
          const recoveredSession = await recoverActiveSolveDetailed();

          if (recoveredSession) {
            console.info("[UC-05B] Recovery po 409 zakonczony sukcesem.", {
              solveSessionId: recoveredSession.solveSessionId,
              status: recoveredSession.status,
            });
            return;
          }

          console.error("[UC-05B] Recovery po 409 nie znalazl aktywnej sesji.");
          dispatch({
            type: "requestFailed",
            error: {
              message:
                "Backend zglosil konflikt aktywnej sesji, ale recovery nie znalazl sesji.",
              errorType: "solve_session_conflict_without_active_session",
              httpStatus: 409,
              isRetriable: true,
              operation: "start",
            },
          });
          return;
        } catch (recoveryError) {
          console.error("[UC-05B] Recovery po 409 zakonczyl sie bledem.");
          dispatch({
            type: "requestFailed",
            error: toSolveSessionError(recoveryError, "recover"),
          });
          return;
        }
      }

      if (error instanceof SudokuSolveApiError && error.status === 422) {
        console.warn("[UC-05B] Backend odrzucil grid biznesowo jako niepoprawny.");
      } else if (
        error instanceof SudokuSolveApiError &&
        (error.status === 401 || error.status === 403)
      ) {
        console.error("[UC-05B] Publiczny start solve nieoczekiwanie wymaga autoryzacji.");
      } else if (
        error instanceof SudokuSolveApiError &&
        error.status >= 500
      ) {
        console.error("[UC-05B] Start solve zakonczyl sie bledem backendu.");
      }

      dispatch({
        type: "requestFailed",
        error: toSolveSessionError(error, "start"),
      });
    }
  }, [apiBaseUrl, recognizedGrid]);

  const cancelSolve = useCallback(async () => {
    if (!state.session) {
      return;
    }

    dispatch({ type: "cancelRequested" });

    try {
      const response = await postCancelSudokuSolve(
        apiBaseUrl,
        state.session.solveSessionId,
      );

      console.info("[UC-05B] Backend przyjal zadanie anulowania solve.", {
        solveSessionId: state.session.solveSessionId,
        requestDisposition: response.requestDisposition,
        status: response.status,
      });

      if (response.status === null) {
        console.warn("[UC-05B] Cancel zwrocil accepted no-op dla niedostepnej sesji.", {
          solveSessionId: state.session.solveSessionId,
          requestDisposition: response.requestDisposition,
        });
        clearPersistedLiveSolveContext();
        dispatch({
          type: "sessionCleared",
          requestDisposition: response.requestDisposition,
        });
        return;
      }

      if (!isSolveSessionStatus(response.status)) {
        throw new Error("Backend zwrocil niepoprawny status cancel sesji solve.");
      }

      dispatch({
        type: "cancelAccepted",
        status: response.status,
        requestDisposition: response.requestDisposition,
      });
    } catch (error) {
      if (error instanceof SudokuSolveApiError && error.status === 404) {
        console.warn("[UC-05B] Backend zwrocil 404 dla cancel mimo kontraktu always-202.");
      } else if (
        error instanceof SudokuSolveApiError &&
        (error.status === 401 || error.status === 403)
      ) {
        console.error("[UC-05B] Publiczny cancel solve nieoczekiwanie wymaga autoryzacji.");
      } else if (
        error instanceof SudokuSolveApiError &&
        error.status >= 500
      ) {
        console.error("[UC-05B] Cancel solve zakonczyl sie bledem backendu.");
      }

      dispatch({
        type: "requestFailed",
        error: toSolveSessionError(error, "cancel"),
      });
    }
  }, [apiBaseUrl, state.session]);

  const acceptTerminalLiveEvent = useCallback((status: SolveSessionStatus) => {
    if (!isSolveSessionStatus(status)) {
      return;
    }

    dispatch({
      type: "terminalEventObserved",
      status,
    });
  }, []);

  useEffect(() => {
    if (!state.session || !state.session.startedGridSignature || !recognizedGrid) {
      return;
    }

    const currentGridSignature = createGridSignature(recognizedGrid);
    const isStale = currentGridSignature !== state.session.startedGridSignature;

    if (state.session.isSessionStaleForCurrentGrid === isStale) {
      return;
    }

    if (isStale) {
      console.warn("[UC-05B] Aktywna sesja solve jest stala wobec aktualnego gridu.");
    }

    dispatch({
      type: "sessionMarkedStale",
      isStale,
    });
  }, [recognizedGrid, state.session]);

  const isBusy =
    state.phase === "starting" ||
    state.phase === "recovering" ||
    state.phase === "cancelling";
  const hasKnownActiveSession =
    state.session !== null && isActiveSolveSessionStatus(state.session.status);

  return {
    state,
    gridReadiness,
    startSolve,
    recoverActiveSolve,
    recoverActiveSolveDetailed,
    cancelSolve,
    acceptTerminalLiveEvent,
    canStartSolve: gridReadiness.isReady && !isBusy && !hasKnownActiveSession,
    canRecoverActiveSolve: !isBusy,
    canCancelSolve: hasKnownActiveSession && state.phase !== "cancelling",
  };
}
