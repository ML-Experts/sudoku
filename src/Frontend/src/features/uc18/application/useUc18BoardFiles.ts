import { useCallback, useEffect, useMemo, useReducer, useRef } from "react";

import {
  DatasetPreparationsApiError,
  getDatasetPreparationBoardFiles,
} from "../../../api/datasetPreparations";
import { mapDatasetPreparationBoardFilesToDomain } from "../domain/mapDatasetPreparationBoardFilesToDomain";
import { resolveUc18BoardFilesPageAfterLoad } from "../domain/resolveUc18BoardFilesPageAfterLoad";
import { uc18BoardFilesReducer } from "./uc18BoardFilesReducer";
import {
  defaultUc18BoardFilesPage,
  defaultUc18BoardFilesPageSize,
  defaultUc18BoardFilesState,
  type UseUc18BoardFilesOptions,
  type UseUc18BoardFilesResult,
} from "./uc18BoardFilesTypes";

export function useUc18BoardFiles({
  apiBaseUrl,
  preparationName,
  sourceName,
  accessToken,
  onUnauthorized,
}: UseUc18BoardFilesOptions): UseUc18BoardFilesResult {
  const [state, dispatch] = useReducer(
    uc18BoardFilesReducer,
    defaultUc18BoardFilesState
  );
  const activeControllerRef = useRef<AbortController | null>(null);

  const loadBoardFiles = useCallback(
    async (
      nextPreparationName: string,
      nextSourceName: string,
      requestedPage = defaultUc18BoardFilesPage,
      requestedPageSize = defaultUc18BoardFilesPageSize,
      allowPageFallback = true
    ) => {
      const normalizedPreparationName = nextPreparationName.trim();
      const normalizedSourceName = nextSourceName.trim();
      const normalizedPage = Math.max(1, Math.floor(requestedPage));
      const normalizedPageSize = Math.max(1, Math.floor(requestedPageSize));

      if (!normalizedPreparationName || !normalizedSourceName) {
        activeControllerRef.current?.abort();
        dispatch({ type: "stateReset" });
        return;
      }

      activeControllerRef.current?.abort();

      const controller = new AbortController();
      activeControllerRef.current = controller;

      console.info("[UC-18] Start ladowania listy plansz board.", {
        page: normalizedPage,
        pageSize: normalizedPageSize,
        preparationName: normalizedPreparationName,
        sourceName: normalizedSourceName,
      });
      dispatch({
        type: "loadStarted",
        preparationName: normalizedPreparationName,
        sourceName: normalizedSourceName,
        page: normalizedPage,
        pageSize: normalizedPageSize,
      });

      try {
        const response = await getDatasetPreparationBoardFiles(
          apiBaseUrl,
          {
            preparationName: normalizedPreparationName,
            sourceName: normalizedSourceName,
            page: normalizedPage,
            pageSize: normalizedPageSize,
          },
          accessToken,
          controller.signal
        );

        if (controller.signal.aborted) {
          return;
        }

        const items = mapDatasetPreparationBoardFilesToDomain(
          response,
          normalizedPreparationName,
          normalizedSourceName
        );
        const pageResolution = resolveUc18BoardFilesPageAfterLoad(
          normalizedPage,
          response.page,
          response.pageSize,
          response.totalCount,
          items.length
        );

        if (allowPageFallback && pageResolution.shouldReloadLastPage) {
          console.warn("[UC-18] Odswiezam ostatnia dostepna strone listy plansz board.", {
            lastPage: pageResolution.lastPage,
            page: normalizedPage,
            pageSize: pageResolution.responsePageSize,
            preparationName: normalizedPreparationName,
            sourceName: normalizedSourceName,
            totalCount: response.totalCount,
          });

          await loadBoardFiles(
            normalizedPreparationName,
            normalizedSourceName,
            pageResolution.lastPage,
            pageResolution.responsePageSize,
            false
          );
          return;
        }

        console.info("[UC-18] Zaladowano liste plansz board.", {
          page: response.page,
          pageSize: response.pageSize,
          preparationName: normalizedPreparationName,
          sourceName: normalizedSourceName,
          totalCount: response.totalCount,
        });
        dispatch({
          type: "loadSucceeded",
          preparationName: normalizedPreparationName,
          sourceName: normalizedSourceName,
          items,
          page: response.page,
          pageSize: response.pageSize,
          totalCount: response.totalCount,
        });
      } catch (error) {
        if (controller.signal.aborted) {
          return;
        }

        let clearItems = false;

        if (error instanceof DatasetPreparationsApiError) {
          if (error.status === 401) {
            console.warn("[UC-18] Sesja administracyjna wygasla podczas ladowania listy plansz.", {
              errorType: error.errorType ?? null,
              httpStatus: error.status,
              page: normalizedPage,
              pageSize: normalizedPageSize,
              preparationName: normalizedPreparationName,
              sourceName: normalizedSourceName,
            });
            onUnauthorized?.();
          } else if (error.status === 404) {
            clearItems = true;
            console.warn("[UC-18] Wybrane preparation lub source board nie jest juz dostepne.", {
              errorType: error.errorType ?? null,
              httpStatus: error.status,
              page: normalizedPage,
              pageSize: normalizedPageSize,
              preparationName: normalizedPreparationName,
              sourceName: normalizedSourceName,
            });
          } else if (error.status === 400) {
            console.warn("[UC-18] Backend odrzucil request listy plansz board.", {
              errorType: error.errorType ?? null,
              httpStatus: error.status,
              page: normalizedPage,
              pageSize: normalizedPageSize,
              preparationName: normalizedPreparationName,
              sourceName: normalizedSourceName,
            });
          } else if (error.status >= 500) {
            console.error("[UC-18] Backend zwrocil blad podczas ladowania listy plansz.", {
              errorType: error.errorType ?? null,
              httpStatus: error.status,
              page: normalizedPage,
              pageSize: normalizedPageSize,
              preparationName: normalizedPreparationName,
              sourceName: normalizedSourceName,
            });
          }
        } else if (error instanceof Error) {
          console.error("[UC-18] Nie udalo sie przetworzyc odpowiedzi listy plansz board.", {
            message: error.message,
            page: normalizedPage,
            pageSize: normalizedPageSize,
            preparationName: normalizedPreparationName,
            sourceName: normalizedSourceName,
          });
        }

        dispatch({
          type: "loadFailed",
          preparationName: normalizedPreparationName,
          sourceName: normalizedSourceName,
          page: normalizedPage,
          pageSize: normalizedPageSize,
          error:
            error instanceof Error
              ? error.message
              : "Nie udalo sie pobrac listy plansz board.",
          errorType:
            error instanceof DatasetPreparationsApiError ? error.errorType ?? null : null,
          httpStatus:
            error instanceof DatasetPreparationsApiError ? error.status : null,
          clearItems,
        });
      } finally {
        if (activeControllerRef.current === controller) {
          activeControllerRef.current = null;
        }
      }
    },
    [accessToken, apiBaseUrl, onUnauthorized]
  );

  const retryLoadBoardFiles = useCallback(async () => {
    const retryPreparationName = preparationName?.trim() || state.preparationName;
    const retrySourceName = sourceName?.trim() || state.sourceName;

    if (!retryPreparationName || !retrySourceName) {
      return;
    }

    console.info("[UC-18] Reczne odswiezenie listy plansz board.", {
      page: state.page,
      pageSize: state.pageSize,
      preparationName: retryPreparationName,
      sourceName: retrySourceName,
    });
    await loadBoardFiles(retryPreparationName, retrySourceName, state.page, state.pageSize);
  }, [
    loadBoardFiles,
    preparationName,
    sourceName,
    state.page,
    state.pageSize,
    state.preparationName,
    state.sourceName,
  ]);

  const goToPage = useCallback(
    async (page: number) => {
      const targetPreparationName = preparationName?.trim() || state.preparationName;
      const targetSourceName = sourceName?.trim() || state.sourceName;
      const nextPage = Math.max(1, Math.floor(page));

      if (!targetPreparationName || !targetSourceName) {
        return;
      }

      console.info("[UC-18] Zmieniam strone listy plansz board.", {
        nextPage,
        pageSize: state.pageSize,
        preparationName: targetPreparationName,
        sourceName: targetSourceName,
      });
      await loadBoardFiles(
        targetPreparationName,
        targetSourceName,
        nextPage,
        state.pageSize
      );
    },
    [
      loadBoardFiles,
      preparationName,
      sourceName,
      state.pageSize,
      state.preparationName,
      state.sourceName,
    ]
  );

  const goToNextPage = useCallback(async () => {
    const totalPages = Math.max(1, Math.ceil(state.totalCount / state.pageSize));

    if (state.page >= totalPages) {
      return;
    }

    await goToPage(state.page + 1);
  }, [goToPage, state.page, state.pageSize, state.totalCount]);

  const goToPreviousPage = useCallback(async () => {
    if (state.page <= 1) {
      return;
    }

    await goToPage(state.page - 1);
  }, [goToPage, state.page]);

  useEffect(() => {
    const normalizedPreparationName = preparationName?.trim() ?? "";
    const normalizedSourceName = sourceName?.trim() ?? "";

    if (!normalizedPreparationName || !normalizedSourceName) {
      activeControllerRef.current?.abort();
      dispatch({ type: "stateReset" });
      return;
    }

    void loadBoardFiles(
      normalizedPreparationName,
      normalizedSourceName,
      defaultUc18BoardFilesPage,
      defaultUc18BoardFilesPageSize
    );
  }, [loadBoardFiles, preparationName, sourceName]);

  useEffect(() => {
    return () => {
      activeControllerRef.current?.abort();
    };
  }, []);

  const totalPages = useMemo(
    () => Math.max(1, Math.ceil(state.totalCount / state.pageSize)),
    [state.pageSize, state.totalCount]
  );

  return {
    status: state.status,
    preparationName: state.preparationName,
    sourceName: state.sourceName,
    items: state.items,
    page: state.page,
    pageSize: state.pageSize,
    totalCount: state.totalCount,
    totalPages,
    error: state.error,
    errorType: state.errorType,
    httpStatus: state.httpStatus,
    canGoToPreviousPage: state.page > 1 && state.status !== "loading",
    canGoToNextPage:
      state.totalCount > 0 && state.page < totalPages && state.status !== "loading",
    loadBoardFiles,
    retryLoadBoardFiles,
    goToPage,
    goToNextPage,
    goToPreviousPage,
  };
}
