import { useCallback, useEffect, useMemo, useReducer, useRef } from "react";

import {
  DatasetPreparationsApiError,
  getDatasetPreparationFolders,
} from "../../../api/datasetPreparations";
import { mapDatasetPreparationFoldersToDomain } from "../domain/mapDatasetPreparationFoldersToDomain";
import { reconcileSelectedPreparationFolder } from "../domain/reconcileSelectedPreparationFolder";
import { uc18BoardFoldersReducer } from "./uc18BoardFoldersReducer";
import {
  defaultUc18BoardFoldersState,
  type UseUc18BoardFoldersOptions,
} from "./uc18BoardFoldersTypes";

export function useUc18BoardFolders({
  apiBaseUrl,
  preparationName,
  accessToken,
  onUnauthorized,
}: UseUc18BoardFoldersOptions) {
  const [state, dispatch] = useReducer(
    uc18BoardFoldersReducer,
    defaultUc18BoardFoldersState
  );
  const activeControllerRef = useRef<AbortController | null>(null);
  const loadedPreparationNameRef = useRef<string | null>(state.preparationName);
  const selectedSourceNameRef = useRef<string | null>(state.selectedSourceName);

  useEffect(() => {
    loadedPreparationNameRef.current = state.preparationName;
  }, [state.preparationName]);

  useEffect(() => {
    selectedSourceNameRef.current = state.selectedSourceName;
  }, [state.selectedSourceName]);

  const loadBoardFolders = useCallback(
    async (nextPreparationName: string) => {
      const normalizedPreparationName = nextPreparationName.trim();

      if (!normalizedPreparationName) {
        activeControllerRef.current?.abort();
        dispatch({ type: "stateReset" });
        return;
      }

      activeControllerRef.current?.abort();

      const controller = new AbortController();
      activeControllerRef.current = controller;

      if (loadedPreparationNameRef.current !== normalizedPreparationName) {
        selectedSourceNameRef.current = null;
      }
      loadedPreparationNameRef.current = normalizedPreparationName;

      console.info("[UC-18] Start ladowania zrodel board.", {
        preparationName: normalizedPreparationName,
        type: "board",
      });
      dispatch({
        type: "loadStarted",
        preparationName: normalizedPreparationName,
      });

      try {
        const response = await getDatasetPreparationFolders(
          apiBaseUrl,
          normalizedPreparationName,
          "board",
          accessToken,
          controller.signal
        );

        if (controller.signal.aborted) {
          return;
        }

        const folders = mapDatasetPreparationFoldersToDomain(response, "board");
        const previousSelectedSourceName =
          loadedPreparationNameRef.current === normalizedPreparationName
            ? selectedSourceNameRef.current
            : null;
        const reconciledSelection = reconcileSelectedPreparationFolder(
          previousSelectedSourceName,
          folders
        );

        if (reconciledSelection.wasRemoved) {
          console.warn("[UC-18] Usunieto nieaktualne wybrane zrodlo po odswiezeniu.", {
            preparationName: normalizedPreparationName,
            removedSelection: true,
            type: "board",
          });
        }

        console.info("[UC-18] Zaladowano zrodla board.", {
          preparationName: normalizedPreparationName,
          totalCount: response.totalCount,
          type: "board",
        });

        dispatch({
          type: "loadSucceeded",
          preparationName: normalizedPreparationName,
          folders,
          totalCount: response.totalCount,
          selectedSourceName: reconciledSelection.selectedSourceName,
        });
      } catch (error) {
        if (controller.signal.aborted) {
          return;
        }

        let clearSelection = false;

        if (error instanceof DatasetPreparationsApiError) {
          if (error.status === 401) {
            console.warn("[UC-18] Sesja administracyjna wygasla podczas ladowania zrodel.", {
              errorType: error.errorType ?? null,
              httpStatus: error.status,
              preparationName: normalizedPreparationName,
              type: "board",
            });
            onUnauthorized?.();
          } else if (error.status === 404) {
            clearSelection = true;
            console.warn("[UC-18] Wybrane preparation nie jest juz dostepne.", {
              errorType: error.errorType ?? null,
              httpStatus: error.status,
              preparationName: normalizedPreparationName,
              type: "board",
            });
          } else if (error.status >= 500) {
            console.error("[UC-18] Backend zwrocil blad podczas ladowania zrodel.", {
              errorType: error.errorType ?? null,
              httpStatus: error.status,
              preparationName: normalizedPreparationName,
              type: "board",
            });
          }
        } else if (error instanceof Error) {
          console.error("[UC-18] Nie udalo sie przetworzyc odpowiedzi zrodel board.", {
            message: error.message,
            preparationName: normalizedPreparationName,
            type: "board",
          });
        }

        dispatch({
          type: "loadFailed",
          preparationName: normalizedPreparationName,
          error:
            error instanceof Error
              ? error.message
              : "Nie udalo sie pobrac listy zrodel board.",
          errorType:
            error instanceof DatasetPreparationsApiError ? error.errorType ?? null : null,
          httpStatus:
            error instanceof DatasetPreparationsApiError ? error.status : null,
          clearSelection,
        });
      } finally {
        if (activeControllerRef.current === controller) {
          activeControllerRef.current = null;
        }
      }
    },
    [accessToken, apiBaseUrl, onUnauthorized]
  );

  const retryLoadBoardFolders = useCallback(async () => {
    const sourcePreparationName = preparationName?.trim() || state.preparationName;
    if (!sourcePreparationName) {
      return;
    }

    console.info("[UC-18] Reczne odswiezenie listy zrodel board.", {
      preparationName: sourcePreparationName,
      type: "board",
    });
    await loadBoardFolders(sourcePreparationName);
  }, [loadBoardFolders, preparationName, state.preparationName]);

  const selectBoardSource = useCallback((sourceName: string) => {
    dispatch({
      type: "selectionChanged",
      sourceName,
    });
  }, []);

  useEffect(() => {
    const normalizedPreparationName = preparationName?.trim() ?? "";

    if (!normalizedPreparationName) {
      activeControllerRef.current?.abort();
      dispatch({ type: "stateReset" });
      return;
    }

    void loadBoardFolders(normalizedPreparationName);
  }, [loadBoardFolders, preparationName]);

  useEffect(() => {
    return () => {
      activeControllerRef.current?.abort();
    };
  }, []);

  const selectedFolder = useMemo(
    () =>
      state.selectedSourceName === null
        ? null
        : state.folders.find((folder) => folder.folderName === state.selectedSourceName) ??
          null,
    [state.folders, state.selectedSourceName]
  );

  return {
    status: state.status,
    preparationName: state.preparationName,
    folders: state.folders,
    selectedSourceName: state.selectedSourceName,
    selectedFolder,
    error: state.error,
    errorType: state.errorType,
    httpStatus: state.httpStatus,
    totalCount: state.totalCount,
    loadBoardFolders,
    retryLoadBoardFolders,
    selectBoardSource,
  };
}
