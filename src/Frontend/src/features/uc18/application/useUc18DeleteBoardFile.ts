import { useCallback, useEffect, useReducer, useRef } from "react";

import {
  DatasetPreparationsApiError,
  deleteDatasetPreparationBoardFile,
} from "../../../api/datasetPreparations";
import { isUc18BoardFileWithinScope } from "../domain/isUc18BoardFileWithinScope";
import type { Uc18BoardFile } from "../domain/uc18BoardFile";
import { uc18DeleteBoardFileReducer } from "./uc18DeleteBoardFileReducer";
import {
  defaultUc18DeleteBoardFileState,
  type UseUc18DeleteBoardFileOptions,
  type UseUc18DeleteBoardFileResult,
} from "./uc18DeleteBoardFileTypes";

export function useUc18DeleteBoardFile({
  apiBaseUrl,
  preparationName,
  sourceName,
  page,
  pageSize,
  accessToken,
  onUnauthorized,
  loadBoardFiles,
}: UseUc18DeleteBoardFileOptions): UseUc18DeleteBoardFileResult {
  const [state, dispatch] = useReducer(
    uc18DeleteBoardFileReducer,
    defaultUc18DeleteBoardFileState
  );
  const activeControllerRef = useRef<AbortController | null>(null);

  const clearDeleteFeedback = useCallback(() => {
    dispatch({ type: "stateReset" });
  }, []);

  const deleteBoardFile = useCallback(
    async (boardFile: Uc18BoardFile) => {
      const normalizedPreparationName = preparationName?.trim() ?? "";
      const normalizedSourceName = sourceName?.trim() ?? "";

      if (!normalizedPreparationName || !normalizedSourceName) {
        console.warn("[UC-18] Odrzucono delete planszy bez aktywnego scope'u.", {
          boardFolderName: boardFile.boardFolderName,
          preparationName: normalizedPreparationName || null,
          sourceName: normalizedSourceName || null,
        });
        dispatch({
          type: "deleteFailed",
          boardFileKey: boardFile.key,
          boardFolderName: boardFile.boardFolderName,
          error: "Brak aktywnego przygotowania albo zrodla do usuniecia planszy.",
          errorType: null,
          httpStatus: null,
        });
        return false;
      }

      if (
        !isUc18BoardFileWithinScope(
          boardFile,
          normalizedPreparationName,
          normalizedSourceName
        )
      ) {
        console.warn("[UC-18] Odrzucono delete planszy spoza aktywnego scope'u.", {
          boardFolderName: boardFile.boardFolderName,
          preparationName: normalizedPreparationName,
          sourceName: normalizedSourceName,
        });
        dispatch({
          type: "deleteFailed",
          boardFileKey: boardFile.key,
          boardFolderName: boardFile.boardFolderName,
          error: "Klikniety rekord nie nalezy do aktualnej listy plansz.",
          errorType: null,
          httpStatus: null,
        });
        return false;
      }

      activeControllerRef.current?.abort();

      const controller = new AbortController();
      activeControllerRef.current = controller;

      console.info("[UC-18] Start usuwania planszy board.", {
        boardFolderName: boardFile.boardFolderName,
        page,
        pageSize,
        preparationName: normalizedPreparationName,
        sourceName: normalizedSourceName,
      });
      dispatch({
        type: "deleteStarted",
        boardFileKey: boardFile.key,
        boardFolderName: boardFile.boardFolderName,
      });

      try {
        const response = await deleteDatasetPreparationBoardFile(
          apiBaseUrl,
          {
            preparationName: normalizedPreparationName,
            sourceName: normalizedSourceName,
            boardFolderName: boardFile.boardFolderName,
          },
          accessToken,
          controller.signal
        );

        if (controller.signal.aborted) {
          return false;
        }

        if (response.deleted !== true) {
          throw new Error(
            "Backend zwrocil niespojny kontrakt delete dla planszy board."
          );
        }

        console.info("[UC-18] Usunieto plansze board, odswiezam liste.", {
          boardFolderName: response.boardFolderName,
          page,
          pageSize,
          preparationName: normalizedPreparationName,
          remainingItemsCount: response.remainingItemsCount,
          sourceName: normalizedSourceName,
        });
        await loadBoardFiles(
          normalizedPreparationName,
          normalizedSourceName,
          page,
          pageSize
        );

        dispatch({
          type: "deleteSucceeded",
          boardFileKey: boardFile.key,
          boardFolderName: response.boardFolderName,
          remainingItemsCount: response.remainingItemsCount,
        });
        return true;
      } catch (error) {
        if (controller.signal.aborted) {
          return false;
        }

        let shouldReloadAfterFailure = false;

        if (error instanceof DatasetPreparationsApiError) {
          if (error.status === 401) {
            console.warn("[UC-18] Sesja administracyjna wygasla podczas usuwania planszy.", {
              boardFolderName: boardFile.boardFolderName,
              errorType: error.errorType ?? null,
              httpStatus: error.status,
              page,
              pageSize,
              preparationName: normalizedPreparationName,
              sourceName: normalizedSourceName,
            });
            onUnauthorized?.();
          } else if (error.status === 404) {
            shouldReloadAfterFailure = true;
            console.warn("[UC-18] Usuwana plansza nie jest juz dostepna, wykonuje reconcile listy.", {
              boardFolderName: boardFile.boardFolderName,
              errorType: error.errorType ?? null,
              httpStatus: error.status,
              page,
              pageSize,
              preparationName: normalizedPreparationName,
              sourceName: normalizedSourceName,
            });
          } else if (error.status === 409 || error.status === 422) {
            console.warn("[UC-18] Backend odrzucil usuniecie planszy board.", {
              boardFolderName: boardFile.boardFolderName,
              errorType: error.errorType ?? null,
              httpStatus: error.status,
              page,
              pageSize,
              preparationName: normalizedPreparationName,
              sourceName: normalizedSourceName,
            });
          } else if (error.status >= 500) {
            console.error("[UC-18] Backend zwrocil blad podczas usuwania planszy board.", {
              boardFolderName: boardFile.boardFolderName,
              errorType: error.errorType ?? null,
              httpStatus: error.status,
              page,
              pageSize,
              preparationName: normalizedPreparationName,
              sourceName: normalizedSourceName,
            });
          }
        } else if (error instanceof Error) {
          console.error("[UC-18] Nie udalo sie przetworzyc odpowiedzi delete planszy board.", {
            boardFolderName: boardFile.boardFolderName,
            message: error.message,
            page,
            pageSize,
            preparationName: normalizedPreparationName,
            sourceName: normalizedSourceName,
          });
        }

        dispatch({
          type: "deleteFailed",
          boardFileKey: boardFile.key,
          boardFolderName: boardFile.boardFolderName,
          error:
            error instanceof Error
              ? error.message
              : "Nie udalo sie usunac planszy board.",
          errorType:
            error instanceof DatasetPreparationsApiError ? error.errorType ?? null : null,
          httpStatus:
            error instanceof DatasetPreparationsApiError ? error.status : null,
        });

        if (shouldReloadAfterFailure) {
          await loadBoardFiles(
            normalizedPreparationName,
            normalizedSourceName,
            page,
            pageSize
          );
        }

        return false;
      } finally {
        if (activeControllerRef.current === controller) {
          activeControllerRef.current = null;
        }
      }
    },
    [
      accessToken,
      apiBaseUrl,
      loadBoardFiles,
      onUnauthorized,
      page,
      pageSize,
      preparationName,
      sourceName,
    ]
  );

  const retryDeleteBoardFile = useCallback(
    async (boardFile: Uc18BoardFile) => {
      return deleteBoardFile(boardFile);
    },
    [deleteBoardFile]
  );

  useEffect(() => {
    dispatch({ type: "stateReset" });
  }, [preparationName, sourceName]);

  useEffect(() => {
    return () => {
      activeControllerRef.current?.abort();
    };
  }, []);

  return {
    status: state.status,
    deletingBoardFileKey: state.boardFileKey,
    boardFolderName: state.boardFolderName,
    remainingItemsCount: state.remainingItemsCount,
    error: state.error,
    errorType: state.errorType,
    httpStatus: state.httpStatus,
    isDeleting: state.status === "deleting",
    deleteBoardFile,
    retryDeleteBoardFile,
    clearDeleteFeedback,
  };
}
