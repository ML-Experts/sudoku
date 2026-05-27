import { useCallback, useEffect, useMemo, useReducer, useRef } from "react";

import {
  connectSudokuSolveRealtime,
} from "../../../api/sudokuSolveRealtime";
import type { SolveProgressEventApiResponse } from "../../../types/api";
import type { SolveSessionViewModel } from "../../uc05b/application/solveSessionTypes";
import { createGridSignature } from "../../uc05b/domain/createGridSignature";
import {
  isRecognizedGridReadyForSolve,
  prepareRecognizedGridForSolve,
} from "../../uc05b/domain/prepareRecognizedGridForSolve";
import { isTerminalSolveSessionStatus } from "../../uc05b/domain/solveSessionStatus";
import type { RecognizedGrid } from "../../uc05a/domain/recognizedGrid";
import { solveLiveReducer } from "./solveLiveReducer";
import {
  defaultSolveLiveState,
  type PersistedLiveSolveContext,
  type SolveLiveConnectionState,
  type SolveLiveError,
} from "./solveLiveTypes";
import { assertInputCellsInvariant, InputCellsInvariantError } from "../domain/assertInputCellsInvariant";
import {
  clearPersistedLiveSolveContext,
  loadPersistedLiveSolveContext,
  savePersistedLiveSolveContext,
} from "../infrastructure/solveLiveSessionStorage";
import { diffRecognizedGridChanges } from "../domain/diffRecognizedGridChanges";
import { isSolveProgressEventTerminal } from "../domain/isSolveProgressEventTerminal";
import { mapCurrentGridToRecognizedGrid } from "../domain/mapCurrentGridToRecognizedGrid";
import { shouldAcceptSolveProgressEvent } from "../domain/shouldAcceptSolveProgressEvent";
import { toSolveProgressEvent } from "../domain/solveProgressEvent";

type UseUc05eLiveSolveOptions = {
  apiBaseUrl: string;
  recognizedGrid: RecognizedGrid | null;
  solveSession: SolveSessionViewModel | null;
  recoverActiveSolve: () => Promise<SolveSessionViewModel | null>;
};

function toLiveError(
  kind: SolveLiveError["kind"],
  error: unknown,
  fallbackMessage: string,
): SolveLiveError {
  if (error instanceof Error && error.message.trim()) {
    return {
      kind,
      message: error.message,
    };
  }

  return {
    kind,
    message: fallbackMessage,
  };
}

export function useUc05eLiveSolve({
  apiBaseUrl,
  recognizedGrid,
  solveSession,
  recoverActiveSolve,
}: UseUc05eLiveSolveOptions) {
  const [state, dispatch] = useReducer(solveLiveReducer, defaultSolveLiveState);
  const connectionRef = useRef<Awaited<
    ReturnType<typeof connectSudokuSolveRealtime>
  > | null>(null);
  const stateRef = useRef(state);
  const persistedContextRef = useRef<PersistedLiveSolveContext | null>(null);
  const autoRecoveryRequestedRef = useRef(false);

  useEffect(() => {
    stateRef.current = state;
  }, [state]);

  const solveReadyGrid = useMemo(() => {
    if (!recognizedGrid || !isRecognizedGridReadyForSolve(recognizedGrid)) {
      return null;
    }

    return prepareRecognizedGridForSolve(recognizedGrid);
  }, [recognizedGrid]);

  const fallbackVisibleGrid = solveReadyGrid ?? recognizedGrid;

  const disconnectRealtime = useCallback(async () => {
    const connection = connectionRef.current;
    connectionRef.current = null;

    if (!connection) {
      return;
    }

    await connection.disconnect().catch(() => undefined);
  }, []);

  const failMonitoring = useCallback(
    async (
      error: SolveLiveError,
      connectionState: SolveLiveConnectionState,
      clearPersistedContext: boolean,
    ) => {
      if (clearPersistedContext) {
        clearPersistedLiveSolveContext();
        persistedContextRef.current = null;
        dispatch({
          type: "persistedContextDetected",
          hasPersistedContext: false,
        });
      }

      await disconnectRealtime();
      dispatch({
        type: "monitoringFailed",
        error,
        connectionState,
      });
    },
    [disconnectRealtime],
  );

  const ingestSolveEvent = useCallback(
    async (payload: SolveProgressEventApiResponse) => {
      try {
        const event = toSolveProgressEvent(payload);
        const currentState = stateRef.current;

        if (!currentState.inputGrid) {
          await failMonitoring(
            {
              kind: "recovery",
              message:
                "Brakuje inputGrid potrzebnego do monitoringu live solve.",
            },
            "failed",
            false,
          );
          return;
        }

        if (
          !shouldAcceptSolveProgressEvent({
            activeSolveSessionId: currentState.activeSolveSessionId,
            lastAcceptedSequence: currentState.lastAcceptedSequence,
            event,
          })
        ) {
          if (event.solveSessionId !== currentState.activeSolveSessionId) {
            console.warn("[UC-05E] Odrzucono event z innej sesji.", {
              solveSessionId: event.solveSessionId,
              sequence: event.sequence,
            });
          } else {
            console.warn("[UC-05E] Odrzucono opozniony albo zduplikowany event.", {
              solveSessionId: event.solveSessionId,
              sequence: event.sequence,
            });
          }

          return;
        }

        assertInputCellsInvariant(currentState.inputGrid, event.currentGrid);
        const nextVisibleGrid = mapCurrentGridToRecognizedGrid(
          currentState.inputGrid,
          event.currentGrid,
        );
        const changedCells = diffRecognizedGridChanges(
          currentState.visibleGrid ?? currentState.inputGrid,
          nextVisibleGrid,
        );
        const terminalEventType = isSolveProgressEventTerminal(event)
          ? event.eventType
          : null;

        dispatch({
          type: "eventAccepted",
          event: {
            eventType: event.eventType,
            status: event.status,
            sequence: event.sequence,
          },
          visibleGrid: nextVisibleGrid,
          changedCells,
          terminalEventType,
        });

        if (event.eventType === "snapshot") {
          console.info("[UC-05E] Przyjeto snapshot solve.", {
            solveSessionId: event.solveSessionId,
            eventType: event.eventType,
            status: event.status,
            sequence: event.sequence,
          });
        }

        if (terminalEventType) {
          console.info("[UC-05E] Przyjeto terminalny event solve.", {
            solveSessionId: event.solveSessionId,
            eventType: event.eventType,
            status: event.status,
            sequence: event.sequence,
            errorType: event.errorType,
          });

          clearPersistedLiveSolveContext();
          persistedContextRef.current = null;
          dispatch({
            type: "persistedContextDetected",
            hasPersistedContext: false,
          });
          await disconnectRealtime();
        }
      } catch (error) {
        if (error instanceof InputCellsInvariantError) {
          console.error("[UC-05E] Event naruszyl pola wejsciowe solvera.");
          await failMonitoring(
            toLiveError(
              "invariant",
              error,
              "Snapshot solve naruszyl pola wejsciowe.",
            ),
            "failed",
            true,
          );
          return;
        }

        console.error("[UC-05E] Nie udalo sie przetworzyc eventu solve.");
        await failMonitoring(
          toLiveError(
            "contract",
            error,
            "Nie udalo sie przetworzyc eventu live solve.",
          ),
          "failed",
          false,
        );
      }
    },
    [disconnectRealtime, failMonitoring],
  );

  const startMonitoring = useCallback(
    async (
      targetSession: SolveSessionViewModel,
      inputGrid: RecognizedGrid,
      startedGridSignature: string | null,
    ) => {
      const inputGridSignature = createGridSignature(inputGrid);
      const currentInputGridSignature = stateRef.current.inputGrid
        ? createGridSignature(stateRef.current.inputGrid)
        : null;
      const isSameSession =
        stateRef.current.activeSolveSessionId === targetSession.solveSessionId &&
        stateRef.current.progressChannelUrl === targetSession.progressChannelUrl &&
        currentInputGridSignature === inputGridSignature &&
        (stateRef.current.connectionState === "connecting" ||
          stateRef.current.connectionState === "connected" ||
          stateRef.current.connectionState === "reconnecting");

      if (isSameSession) {
        return;
      }

      const persistedContext: PersistedLiveSolveContext = {
        solveSessionId: targetSession.solveSessionId,
        progressChannelUrl: targetSession.progressChannelUrl,
        startedGridSignature,
        inputGrid,
      };

      savePersistedLiveSolveContext(persistedContext);
      persistedContextRef.current = persistedContext;
      dispatch({
        type: "persistedContextDetected",
        hasPersistedContext: true,
      });
      dispatch({
        type: "monitoringPrepared",
        solveSessionId: targetSession.solveSessionId,
        progressChannelUrl: targetSession.progressChannelUrl,
        inputGrid,
        visibleGrid: inputGrid,
      });
      dispatch({ type: "connectRequested" });

      console.info("[UC-05E] Start monitoringu live solve.", {
        solveSessionId: targetSession.solveSessionId,
      });

      await disconnectRealtime();

      try {
        const connection = await connectSudokuSolveRealtime({
          apiBaseUrl,
          solveSessionId: targetSession.solveSessionId,
          progressChannelUrl: targetSession.progressChannelUrl,
          onSnapshot: (event) => {
            void ingestSolveEvent(event);
          },
          onEvent: (event) => {
            void ingestSolveEvent(event);
          },
          onReconnecting: () => {
            console.warn("[UC-05E] SignalR przechodzi w reconnect.");
            dispatch({ type: "reconnecting" });
          },
          onReconnected: () => {
            dispatch({ type: "reconnected" });
          },
          onClose: () => {
            dispatch({ type: "connectionClosed" });
          },
          onContractError: (error) => {
            console.error("[UC-05E] Backend zwrocil niepoprawny payload realtime.");
            void failMonitoring(
              toLiveError(
                "contract",
                error,
                "Backend zwrocil niepoprawny payload live solve.",
              ),
              "failed",
              false,
            );
          },
        });

        connectionRef.current = connection;
        dispatch({ type: "connectSucceeded" });
      } catch (error) {
        console.error("[UC-05E] Nie udalo sie nawiazac polaczenia SignalR.");
        await failMonitoring(
          toLiveError(
            "connection",
            error,
            "Nie udalo sie nawiazac polaczenia live solve.",
          ),
          "disconnected",
          false,
        );
      }
    },
    [apiBaseUrl, disconnectRealtime, failMonitoring, ingestSolveEvent],
  );

  useEffect(() => {
    try {
      const persistedContext = loadPersistedLiveSolveContext();
      persistedContextRef.current = persistedContext;
      dispatch({
        type: "persistedContextDetected",
        hasPersistedContext: persistedContext !== null,
      });
    } catch (error) {
      clearPersistedLiveSolveContext();
      persistedContextRef.current = null;
      console.warn("[UC-05E] Wykryto uszkodzony persisted context live solve.");
      dispatch({
        type: "persistedContextDetected",
        hasPersistedContext: false,
      });
      dispatch({
        type: "monitoringFailed",
        error: toLiveError(
          "storage",
          error,
          "sessionStorage zawiera uszkodzony kontekst live solve.",
        ),
        connectionState: "disconnected",
      });
    }
  }, []);

  useEffect(() => {
    if (
      autoRecoveryRequestedRef.current ||
      solveSession !== null ||
      !state.hasPersistedContext
    ) {
      return;
    }

    autoRecoveryRequestedRef.current = true;
    console.info("[UC-05E] Wznawianie sesji solve po refresh z sessionStorage.");
    void recoverActiveSolve().catch(() => undefined);
  }, [recoverActiveSolve, solveSession, state.hasPersistedContext]);

  useEffect(() => {
    if (!solveSession) {
      return;
    }

    if (solveSession.isSessionStaleForCurrentGrid) {
      console.warn("[UC-05E] Nie wznowiono live solve dla stalej sesji.");
      void disconnectRealtime();
      dispatch({
        type: "degradedModeEntered",
        solveSessionId: solveSession.solveSessionId,
        progressChannelUrl: solveSession.progressChannelUrl,
        reason:
          "Aktywna sesja solve dotyczy starszego stanu planszy. Nie wznowiono live monitoringu.",
      });
      return;
    }

    if (isTerminalSolveSessionStatus(solveSession.status)) {
      console.warn("[UC-05E] Recovery zwrocil sesje w stanie terminalnym.", {
        solveSessionId: solveSession.solveSessionId,
        status: solveSession.status,
      });
      clearPersistedLiveSolveContext();
      persistedContextRef.current = null;
      dispatch({
        type: "persistedContextDetected",
        hasPersistedContext: false,
      });
      void disconnectRealtime();
      dispatch({
        type: "degradedModeEntered",
        solveSessionId: solveSession.solveSessionId,
        progressChannelUrl: solveSession.progressChannelUrl,
        reason:
          "Backend zwrocil sesje solve w stanie terminalnym. Live monitoring nie zostal wznowiony i mozna uruchomic nowa sesje od poczatku.",
      });
      return;
    }

    const persistedContext = persistedContextRef.current;
    const matchingPersistedContext =
      persistedContext &&
      persistedContext.solveSessionId === solveSession.solveSessionId
        ? persistedContext
        : null;

    if (persistedContext && !matchingPersistedContext) {
      console.warn("[UC-05E] Wykryto stale persisted context live solve.");
      clearPersistedLiveSolveContext();
      persistedContextRef.current = null;
      dispatch({
        type: "persistedContextDetected",
        hasPersistedContext: false,
      });
      void disconnectRealtime();
      dispatch({
        type: "degradedModeEntered",
        solveSessionId: solveSession.solveSessionId,
        progressChannelUrl: solveSession.progressChannelUrl,
        reason:
          "Lokalny persisted context dotyczy innej sesji solve, dlatego monitoring live nie zostal wznowiony.",
      });
      return;
    }

    const resolvedStartedGridSignature =
      solveSession.startedGridSignature ??
      matchingPersistedContext?.startedGridSignature ??
      null;

    if (resolvedStartedGridSignature && solveReadyGrid) {
      const currentGridSignature = createGridSignature(solveReadyGrid);

      if (currentGridSignature !== resolvedStartedGridSignature) {
        console.warn("[UC-05E] Aktywna sesja solve jest stala wobec aktualnego gridu.");
        void disconnectRealtime();
        dispatch({
          type: "degradedModeEntered",
          solveSessionId: solveSession.solveSessionId,
          progressChannelUrl: solveSession.progressChannelUrl,
          reason:
            "Aktywna sesja solve dotyczy starszego stanu planszy. Monitoring live nie zostal wznowiony dla aktualnego recognizedGrid.",
        });
        return;
      }
    }

    const resolvedInputGrid =
      solveReadyGrid ?? matchingPersistedContext?.inputGrid ?? null;

    if (!resolvedInputGrid) {
      console.warn(
        "[UC-05E] Recovery zwrocil sesje, ale brakuje inputGrid do live resume.",
        {
          solveSessionId: solveSession.solveSessionId,
          hasPersistedContext: matchingPersistedContext !== null,
        },
      );
      dispatch({
        type: "degradedModeEntered",
        solveSessionId: solveSession.solveSessionId,
        progressChannelUrl: solveSession.progressChannelUrl,
        reason:
          "Brakuje lokalnego inputGrid do poprawnego wznowienia live solve. Uruchom rozpoznanie ponownie albo odzyskaj sesje z aktualnym kontekstem.",
      });
      return;
    }

    void startMonitoring(
      solveSession,
      resolvedInputGrid,
      resolvedStartedGridSignature,
    );
  }, [disconnectRealtime, solveReadyGrid, solveSession, startMonitoring]);

  useEffect(() => {
    if (solveSession || !solveReadyGrid || !state.inputGrid) {
      return;
    }

    const currentSignature = createGridSignature(state.inputGrid);
    const nextSignature = createGridSignature(solveReadyGrid);
    if (currentSignature === nextSignature) {
      return;
    }

    dispatch({ type: "liveStateReset" });
  }, [solveReadyGrid, solveSession, state.inputGrid]);

  useEffect(() => {
    if (solveSession !== null || state.activeSolveSessionId === null) {
      return;
    }

    void disconnectRealtime();
    dispatch({
      type: "liveStateReset",
      preserveVisibleGrid: true,
    });
  }, [disconnectRealtime, solveSession, state.activeSolveSessionId]);

  useEffect(() => {
    return () => {
      void disconnectRealtime();
    };
  }, [disconnectRealtime]);

  const retryMonitoring = useCallback(async () => {
    if (!solveSession) {
      return;
    }

    if (isTerminalSolveSessionStatus(solveSession.status)) {
      dispatch({
        type: "degradedModeEntered",
        solveSessionId: solveSession.solveSessionId,
        progressChannelUrl: solveSession.progressChannelUrl,
        reason:
          "Ta sesja solve jest juz zakonczona, dlatego live monitoring nie zostal wznowiony.",
      });
      return;
    }

    if (solveSession.isSessionStaleForCurrentGrid) {
      dispatch({
        type: "degradedModeEntered",
        solveSessionId: solveSession.solveSessionId,
        progressChannelUrl: solveSession.progressChannelUrl,
        reason:
          "Ta sesja solve jest stala wobec aktualnego gridu i nie moze wznowic live monitoringu.",
      });
      return;
    }

    const persistedContext = persistedContextRef.current;
    const resolvedInputGrid =
      solveReadyGrid ??
      (persistedContext?.solveSessionId === solveSession.solveSessionId
        ? persistedContext.inputGrid
        : null);

    if (!resolvedInputGrid) {
      dispatch({
        type: "degradedModeEntered",
        solveSessionId: solveSession.solveSessionId,
        progressChannelUrl: solveSession.progressChannelUrl,
        reason:
          "Brakuje inputGrid potrzebnego do wznowienia live monitoringu dla tej sesji.",
      });
      return;
    }

    const resolvedStartedGridSignature =
      solveSession.startedGridSignature ??
      (persistedContext?.solveSessionId === solveSession.solveSessionId
        ? persistedContext.startedGridSignature
        : null);

    if (resolvedStartedGridSignature && solveReadyGrid) {
      const currentGridSignature = createGridSignature(solveReadyGrid);

      if (currentGridSignature !== resolvedStartedGridSignature) {
        dispatch({
          type: "degradedModeEntered",
          solveSessionId: solveSession.solveSessionId,
          progressChannelUrl: solveSession.progressChannelUrl,
          reason:
            "Ta sesja solve dotyczy starszego stanu planszy i nie moze wznowic live monitoringu.",
        });
        return;
      }
    }

    await startMonitoring(
      solveSession,
      resolvedInputGrid,
      resolvedStartedGridSignature,
    );
  }, [solveReadyGrid, solveSession, startMonitoring]);

  const resetLiveState = useCallback(async () => {
    clearPersistedLiveSolveContext();
    persistedContextRef.current = null;
    await disconnectRealtime();
    dispatch({
      type: "persistedContextDetected",
      hasPersistedContext: false,
    });
    dispatch({ type: "liveStateReset" });
  }, [disconnectRealtime]);

  const visibleGrid =
    state.visibleGrid ??
    state.inputGrid ??
    fallbackVisibleGrid;

  return {
    state,
    visibleGrid,
    retryMonitoring,
    resetLiveState,
    hasLiveSessionToResume:
      solveSession !== null &&
      !solveSession.isSessionStaleForCurrentGrid &&
      !isTerminalSolveSessionStatus(solveSession.status),
  };
}
