import { useCallback, useEffect, useMemo, useReducer, useRef } from "react";

import {
  DatasetPreparationsApiError,
  getDatasetPreparationFolders,
} from "../../../api/datasetPreparations";
import { mapDatasetPreparationBoardFoldersToDrafts } from "../domain/mapDatasetPreparationBoardFoldersToDrafts";
import { reconcileUc19BoardSourceDrafts } from "../domain/reconcileUc19BoardSourceDrafts";
import { toggleUc19BoardSourceSplit } from "../domain/toggleUc19BoardSourceSplit";
import { validateUc19BoardSourceDraft } from "../domain/validateUc19BoardSourceDraft";
import { uc19BoardFoldersSelectionReducer } from "./uc19BoardFoldersSelectionReducer";
import {
  defaultUc19BoardFoldersSelectionState,
  type Uc19BoardFoldersSelectionState,
  type UseUc19BoardFoldersSelectionOptions,
} from "./uc19BoardFoldersSelectionTypes";
import type { Uc19BoardSourceSplit } from "../domain/uc19BoardSourceDraft";

export function useUc19BoardFoldersSelection({
  apiBaseUrl,
  preparationName,
  accessToken,
  onUnauthorized,
}: UseUc19BoardFoldersSelectionOptions) {
  const [state, dispatch] = useReducer(
    uc19BoardFoldersSelectionReducer,
    defaultUc19BoardFoldersSelectionState
  );
  const activeControllerRef = useRef<AbortController | null>(null);
  const stateRef = useRef<Uc19BoardFoldersSelectionState>(state);
  const previousSelectedCountRef = useRef<number>(0);

  useEffect(() => {
    stateRef.current = state;
  }, [state]);

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

      console.info("[UC-19] Start ladowania zrodel board do builda datasetu.", {
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

        const freshDrafts = mapDatasetPreparationBoardFoldersToDrafts(response);
        const previousState = stateRef.current;
        const previousDrafts =
          previousState.preparationName === normalizedPreparationName
            ? previousState.drafts
            : [];
        const reconciledDrafts = reconcileUc19BoardSourceDrafts(
          previousDrafts,
          freshDrafts
        );

        if (reconciledDrafts.removedDrafts.length > 0) {
          console.warn("[UC-19] Usunieto nieaktualne wybrane zrodla board po odswiezeniu.", {
            preparationName: normalizedPreparationName,
            removedDraftsCount: reconciledDrafts.removedDrafts.length,
            type: "board",
          });
        }

        console.info("[UC-19] Zaladowano zrodla board do builda datasetu.", {
          preparationName: normalizedPreparationName,
          totalCount: response.totalCount,
          type: "board",
        });

        dispatch({
          type: "loadSucceeded",
          preparationName: normalizedPreparationName,
          drafts: reconciledDrafts.drafts,
          totalCount: response.totalCount,
        });
      } catch (error) {
        if (controller.signal.aborted) {
          return;
        }

        let clearDrafts = false;

        if (error instanceof DatasetPreparationsApiError) {
          if (error.status === 401) {
            console.warn("[UC-19] Sesja administracyjna wygasla podczas ladowania zrodel.", {
              errorType: error.errorType ?? null,
              httpStatus: error.status,
              preparationName: normalizedPreparationName,
              type: "board",
            });
            onUnauthorized?.();
          } else if (error.status === 404) {
            clearDrafts = true;
            console.warn("[UC-19] Wybrane preparation nie jest juz dostepne.", {
              errorType: error.errorType ?? null,
              httpStatus: error.status,
              preparationName: normalizedPreparationName,
              type: "board",
            });
          } else if (error.status >= 500) {
            console.error("[UC-19] Backend zwrocil blad podczas ladowania zrodel board.", {
              errorType: error.errorType ?? null,
              httpStatus: error.status,
              preparationName: normalizedPreparationName,
              type: "board",
            });
          }
        } else if (error instanceof Error) {
          console.error("[UC-19] Nie udalo sie przetworzyc odpowiedzi zrodel board.", {
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
          clearDrafts,
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

    console.info("[UC-19] Reczne odswiezenie listy zrodel board.", {
      preparationName: sourcePreparationName,
      type: "board",
    });
    await loadBoardFolders(sourcePreparationName);
  }, [loadBoardFolders, preparationName, state.preparationName]);

  const toggleBoardSourceEnabled = useCallback((folderName: string) => {
    dispatch({
      type: "sourceEnabledToggled",
      folderName,
    });
  }, []);

  const updateBoardSourceSplits = useCallback(
    (folderName: string, splits: Uc19BoardSourceSplit[]) => {
      dispatch({
        type: "sourceSplitsUpdated",
        folderName,
        splits,
      });
    },
    []
  );

  const toggleBoardSourceSplit = useCallback(
    (folderName: string, split: Uc19BoardSourceSplit) => {
      const draft = stateRef.current.drafts.find(
        (currentDraft) => currentDraft.folderName === folderName
      );

      if (!draft) {
        return;
      }

      const nextSplits = toggleUc19BoardSourceSplit(draft.splits, split);
      updateBoardSourceSplits(folderName, nextSplits);
    },
    [updateBoardSourceSplits]
  );

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

  const validationByKey = useMemo(
    () =>
      Object.fromEntries(
        state.drafts.map((draft) => [draft.key, validateUc19BoardSourceDraft(draft)])
      ),
    [state.drafts]
  );
  const selectedDrafts = useMemo(
    () => state.drafts.filter((draft) => draft.enabled),
    [state.drafts]
  );
  const invalidSelectedCount = useMemo(
    () =>
      selectedDrafts.filter((draft) => !validationByKey[draft.key]?.isValid).length,
    [selectedDrafts, validationByKey]
  );

  useEffect(() => {
    if (previousSelectedCountRef.current === selectedDrafts.length) {
      return;
    }

    console.info("[UC-19] Zmieniono liczbe wybranych zrodel board.", {
      preparationName: state.preparationName,
      selectedCount: selectedDrafts.length,
      type: "board",
    });
    previousSelectedCountRef.current = selectedDrafts.length;
  }, [selectedDrafts.length, state.preparationName]);

  return {
    status: state.status,
    preparationName: state.preparationName,
    drafts: state.drafts,
    selectedDrafts,
    selectedCount: selectedDrafts.length,
    invalidSelectedCount,
    totalCount: state.totalCount,
    error: state.error,
    errorType: state.errorType,
    httpStatus: state.httpStatus,
    validationByKey,
    loadBoardFolders,
    retryLoadBoardFolders,
    toggleBoardSourceEnabled,
    toggleBoardSourceSplit,
    updateBoardSourceSplits,
  };
}
