import { useCallback, useEffect, useReducer, useRef } from "react";

import {
  DatasetPreparationsApiError,
  getDatasetPreparationFolders,
} from "../../../api/datasetPreparations";
import { mapDatasetPreparationFoldersToDomain } from "../domain/mapDatasetPreparationFoldersToDomain";
import { uc18DigitFoldersReducer } from "./uc18DigitFoldersReducer";
import {
  defaultUc18DigitFoldersState,
  type UseUc18DigitFoldersOptions,
} from "./uc18DigitFoldersTypes";

export function useUc18DigitFolders({
  apiBaseUrl,
  preparationName,
  accessToken,
  onUnauthorized,
}: UseUc18DigitFoldersOptions) {
  const [state, dispatch] = useReducer(
    uc18DigitFoldersReducer,
    defaultUc18DigitFoldersState
  );
  const activeControllerRef = useRef<AbortController | null>(null);

  const loadDigitFolders = useCallback(
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

      console.info("[UC-18] Start ladowania zrodel digit.", {
        preparationName: normalizedPreparationName,
        type: "digit",
      });
      dispatch({
        type: "loadStarted",
        preparationName: normalizedPreparationName,
      });

      try {
        const response = await getDatasetPreparationFolders(
          apiBaseUrl,
          normalizedPreparationName,
          "digit",
          accessToken,
          controller.signal
        );

        if (controller.signal.aborted) {
          return;
        }

        const folders = mapDatasetPreparationFoldersToDomain(response, "digit");

        console.info("[UC-18] Zaladowano zrodla digit.", {
          preparationName: normalizedPreparationName,
          totalCount: response.totalCount,
          type: "digit",
        });

        dispatch({
          type: "loadSucceeded",
          preparationName: normalizedPreparationName,
          folders,
          totalCount: response.totalCount,
        });
      } catch (error) {
        if (controller.signal.aborted) {
          return;
        }

        if (error instanceof DatasetPreparationsApiError) {
          if (error.status === 401) {
            console.warn("[UC-18] Sesja administracyjna wygasla podczas ladowania zrodel.", {
              errorType: error.errorType ?? null,
              httpStatus: error.status,
              preparationName: normalizedPreparationName,
              type: "digit",
            });
            onUnauthorized?.();
          } else if (error.status === 404) {
            console.warn("[UC-18] Wybrane preparation nie jest juz dostepne.", {
              errorType: error.errorType ?? null,
              httpStatus: error.status,
              preparationName: normalizedPreparationName,
              type: "digit",
            });
          } else if (error.status >= 500) {
            console.error("[UC-18] Backend zwrocil blad podczas ladowania zrodel.", {
              errorType: error.errorType ?? null,
              httpStatus: error.status,
              preparationName: normalizedPreparationName,
              type: "digit",
            });
          }
        } else if (error instanceof Error) {
          console.error("[UC-18] Nie udalo sie przetworzyc odpowiedzi zrodel digit.", {
            message: error.message,
            preparationName: normalizedPreparationName,
            type: "digit",
          });
        }

        dispatch({
          type: "loadFailed",
          preparationName: normalizedPreparationName,
          error:
            error instanceof Error
              ? error.message
              : "Nie udalo sie pobrac listy zrodel digit.",
          errorType:
            error instanceof DatasetPreparationsApiError ? error.errorType ?? null : null,
          httpStatus:
            error instanceof DatasetPreparationsApiError ? error.status : null,
        });
      } finally {
        if (activeControllerRef.current === controller) {
          activeControllerRef.current = null;
        }
      }
    },
    [accessToken, apiBaseUrl, onUnauthorized]
  );

  const retryLoadDigitFolders = useCallback(async () => {
    const sourcePreparationName = preparationName?.trim() || state.preparationName;
    if (!sourcePreparationName) {
      return;
    }

    console.info("[UC-18] Reczne odswiezenie listy zrodel digit.", {
      preparationName: sourcePreparationName,
      type: "digit",
    });
    await loadDigitFolders(sourcePreparationName);
  }, [loadDigitFolders, preparationName, state.preparationName]);

  useEffect(() => {
    const normalizedPreparationName = preparationName?.trim() ?? "";

    if (!normalizedPreparationName) {
      activeControllerRef.current?.abort();
      dispatch({ type: "stateReset" });
      return;
    }

    void loadDigitFolders(normalizedPreparationName);
  }, [loadDigitFolders, preparationName]);

  useEffect(() => {
    return () => {
      activeControllerRef.current?.abort();
    };
  }, []);

  return {
    status: state.status,
    preparationName: state.preparationName,
    folders: state.folders,
    totalCount: state.totalCount,
    error: state.error,
    errorType: state.errorType,
    httpStatus: state.httpStatus,
    loadDigitFolders,
    retryLoadDigitFolders,
  };
}
