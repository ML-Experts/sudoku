import { useCallback, useEffect, useMemo, useReducer, useRef } from "react";

import {
  DatasetPreparationsApiError,
  getDatasetPreparationBoardImageByEndpoint,
} from "../../../api/datasetPreparations";
import { toImageDataUrl } from "../../../shared/images/toImageDataUrl";
import { toUc18BoardImageRequestKey } from "../domain/toUc18BoardImageRequestKey";
import { uc18BoardImageReducer } from "./uc18BoardImageReducer";
import {
  defaultUc18BoardImageState,
  type UseUc18BoardImageOptions,
  type UseUc18BoardImageResult,
} from "./uc18BoardImageTypes";

export function useUc18BoardImage({
  apiBaseUrl,
  imageEndpoint,
  preparationName,
  sourceName,
  boardFolderName,
  accessToken,
  onUnauthorized,
}: UseUc18BoardImageOptions): UseUc18BoardImageResult {
  const [state, dispatch] = useReducer(
    uc18BoardImageReducer,
    defaultUc18BoardImageState
  );
  const activeControllerRef = useRef<AbortController | null>(null);

  const requestKey = useMemo(
    () =>
      toUc18BoardImageRequestKey({
        preparationName,
        sourceName,
        boardFolderName,
      }),
    [boardFolderName, preparationName, sourceName]
  );

  const loadBoardImage = useCallback(async () => {
    const normalizedEndpoint = imageEndpoint.trim();

    if (!normalizedEndpoint) {
      activeControllerRef.current?.abort();
      console.warn("[UC-18] Brak endpointu preview planszy.", {
        boardFolderName,
        preparationName,
        sourceName,
      });
      dispatch({
        type: "loadStarted",
        requestKey,
      });
      dispatch({
        type: "loadFailed",
        requestKey,
        error: "Brak endpointu preview.",
        errorType: null,
        httpStatus: null,
      });
      return;
    }

    activeControllerRef.current?.abort();

    const controller = new AbortController();
    activeControllerRef.current = controller;

    dispatch({
      type: "loadStarted",
      requestKey,
    });

    try {
      const response = await getDatasetPreparationBoardImageByEndpoint(
        apiBaseUrl,
        normalizedEndpoint,
        accessToken,
        controller.signal
      );

      if (controller.signal.aborted) {
        return;
      }

      dispatch({
        type: "loadSucceeded",
        requestKey,
        imageDataUrl: toImageDataUrl(response),
      });
    } catch (error) {
      if (controller.signal.aborted) {
        return;
      }

      if (error instanceof DatasetPreparationsApiError) {
        if (error.status === 401) {
          console.warn("[UC-18] Sesja administracyjna wygasla podczas ladowania preview planszy.", {
            boardFolderName,
            errorType: error.errorType ?? null,
            httpStatus: error.status,
            preparationName,
            sourceName,
          });
          onUnauthorized?.();
        } else if (error.status === 403 || error.status === 404) {
          console.warn("[UC-18] Nie udalo sie pobrac preview planszy.", {
            boardFolderName,
            errorType: error.errorType ?? null,
            httpStatus: error.status,
            preparationName,
            sourceName,
          });
        } else if (error.status >= 500) {
          console.error("[UC-18] Backend zwrocil blad podczas ladowania preview planszy.", {
            boardFolderName,
            errorType: error.errorType ?? null,
            httpStatus: error.status,
            preparationName,
            sourceName,
          });
        }
      } else if (error instanceof Error) {
        console.error("[UC-18] Nie udalo sie przetworzyc preview planszy.", {
          boardFolderName,
          message: error.message,
          preparationName,
          sourceName,
        });
      }

      dispatch({
        type: "loadFailed",
        requestKey,
        error:
          error instanceof Error
            ? error.message
            : "Nie udalo sie pobrac preview planszy.",
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
  }, [
    accessToken,
    apiBaseUrl,
    boardFolderName,
    imageEndpoint,
    onUnauthorized,
    preparationName,
    requestKey,
    sourceName,
  ]);

  const retryLoadBoardImage = useCallback(async () => {
    console.info("[UC-18] Reczne ponowienie ladowania preview planszy.", {
      boardFolderName,
      preparationName,
      sourceName,
    });
    await loadBoardImage();
  }, [boardFolderName, loadBoardImage, preparationName, sourceName]);

  useEffect(() => {
    void loadBoardImage();
  }, [loadBoardImage]);

  useEffect(() => {
    return () => {
      activeControllerRef.current?.abort();
    };
  }, []);

  return {
    status: state.status,
    requestKey: state.requestKey,
    imageDataUrl: state.imageDataUrl,
    error: state.error,
    errorType: state.errorType,
    httpStatus: state.httpStatus,
    loadBoardImage,
    retryLoadBoardImage,
  };
}
