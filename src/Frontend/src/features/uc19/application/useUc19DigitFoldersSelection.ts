import { useCallback, useEffect, useMemo, useReducer, useRef } from "react";

import {
  DatasetPreparationsApiError,
  getDatasetPreparationFolders,
} from "../../../api/datasetPreparations";
import { mapDatasetPreparationDigitFoldersToDrafts } from "../domain/mapDatasetPreparationDigitFoldersToDrafts";
import { reconcileUc19DigitSourceDrafts } from "../domain/reconcileUc19DigitSourceDrafts";
import { toggleUc19DigitSourceSplit } from "../domain/toggleUc19DigitSourceSplit";
import type { Uc19DigitSourceSplit } from "../domain/uc19DigitSourceDraft";
import { validateUc19DigitSourceDraft } from "../domain/validateUc19DigitSourceDraft";
import { uc19DigitFoldersSelectionReducer } from "./uc19DigitFoldersSelectionReducer";
import {
  defaultUc19DigitFoldersSelectionState,
  type Uc19DigitFoldersSelectionState,
  type UseUc19DigitFoldersSelectionOptions,
} from "./uc19DigitFoldersSelectionTypes";

export function useUc19DigitFoldersSelection({
  apiBaseUrl,
  preparationName,
  accessToken,
  onUnauthorized,
}: UseUc19DigitFoldersSelectionOptions) {
  const [state, dispatch] = useReducer(
    uc19DigitFoldersSelectionReducer,
    defaultUc19DigitFoldersSelectionState
  );
  const activeControllerRef = useRef<AbortController | null>(null);
  const stateRef = useRef<Uc19DigitFoldersSelectionState>(state);
  const previousSelectedCountRef = useRef<number>(0);

  useEffect(() => {
    stateRef.current = state;
  }, [state]);

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

      console.info("[UC-19] Start ladowania zrodel digit do builda datasetu.", {
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

        const freshDrafts = mapDatasetPreparationDigitFoldersToDrafts(response);
        const previousState = stateRef.current;
        const previousDrafts =
          previousState.preparationName === normalizedPreparationName
            ? previousState.drafts
            : [];
        const reconciledDrafts = reconcileUc19DigitSourceDrafts(
          previousDrafts,
          freshDrafts
        );

        if (reconciledDrafts.removedDrafts.length > 0) {
          console.warn("[UC-19] Usunieto nieaktualne wybrane zrodla digit po odswiezeniu.", {
            preparationName: normalizedPreparationName,
            removedDraftsCount: reconciledDrafts.removedDrafts.length,
            type: "digit",
          });
        }

        console.info("[UC-19] Zaladowano zrodla digit do builda datasetu.", {
          preparationName: normalizedPreparationName,
          totalCount: response.totalCount,
          type: "digit",
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
              type: "digit",
            });
            onUnauthorized?.();
          } else if (error.status === 404) {
            clearDrafts = true;
            console.warn("[UC-19] Wybrane preparation nie jest juz dostepne.", {
              errorType: error.errorType ?? null,
              httpStatus: error.status,
              preparationName: normalizedPreparationName,
              type: "digit",
            });
          } else if (error.status >= 500) {
            console.error("[UC-19] Backend zwrocil blad podczas ladowania zrodel digit.", {
              errorType: error.errorType ?? null,
              httpStatus: error.status,
              preparationName: normalizedPreparationName,
              type: "digit",
            });
          }
        } else if (error instanceof Error) {
          console.error("[UC-19] Nie udalo sie przetworzyc odpowiedzi zrodel digit.", {
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

  const retryLoadDigitFolders = useCallback(async () => {
    const sourcePreparationName = preparationName?.trim() || state.preparationName;

    if (!sourcePreparationName) {
      return;
    }

    console.info("[UC-19] Reczne odswiezenie listy zrodel digit.", {
      preparationName: sourcePreparationName,
      type: "digit",
    });
    await loadDigitFolders(sourcePreparationName);
  }, [loadDigitFolders, preparationName, state.preparationName]);

  const toggleDigitSourceEnabled = useCallback((folderName: string) => {
    dispatch({
      type: "sourceEnabledToggled",
      folderName,
    });
  }, []);

  const updateDigitSourceSplits = useCallback(
    (folderName: string, splits: Uc19DigitSourceSplit[]) => {
      dispatch({
        type: "sourceSplitsUpdated",
        folderName,
        splits,
      });
    },
    []
  );

  const toggleDigitSourceSplit = useCallback(
    (folderName: string, split: Uc19DigitSourceSplit) => {
      const draft = stateRef.current.drafts.find(
        (currentDraft) => currentDraft.folderName === folderName
      );

      if (!draft) {
        return;
      }

      const nextSplits = toggleUc19DigitSourceSplit(draft.splits, split);
      updateDigitSourceSplits(folderName, nextSplits);
    },
    [updateDigitSourceSplits]
  );

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

  const validationByKey = useMemo(
    () =>
      Object.fromEntries(
        state.drafts.map((draft) => [draft.key, validateUc19DigitSourceDraft(draft)])
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

    console.info("[UC-19] Zmieniono liczbe wybranych zrodel digit.", {
      preparationName: state.preparationName,
      selectedCount: selectedDrafts.length,
      type: "digit",
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
    loadDigitFolders,
    retryLoadDigitFolders,
    toggleDigitSourceEnabled,
    toggleDigitSourceSplit,
    updateDigitSourceSplits,
  };
}
