import { useCallback, useEffect, useMemo, useReducer, useRef } from "react";

import {
  getRawDatasetCandidates,
  RawDatasetCandidatesApiError,
} from "../../../api/datasetsRawCandidates";
import { reconcileSelectedCandidates } from "../domain/reconcileSelectedCandidates";
import { toPreparationSourceDrafts } from "../domain/toPreparationSourceDrafts";
import { toUc17RawCandidateKey } from "../domain/toUc17RawCandidateKey";
import {
  isUc17RawCandidateType,
  type Uc17RawCandidate,
} from "../domain/uc17RawCandidate";
import { uc17RawCandidatesReducer } from "./uc17RawCandidatesReducer";
import {
  defaultUc17RawCandidatesState,
  type UseUc17RawCandidatesOptions,
} from "./uc17RawCandidatesTypes";

function mapRawCandidates(
  candidates: Awaited<ReturnType<typeof getRawDatasetCandidates>>
): {
  candidates: Uc17RawCandidate[];
  unknownTypeCount: number;
} {
  const supportedCandidates: Uc17RawCandidate[] = [];
  let unknownTypeCount = 0;

  for (const candidate of candidates) {
    if (!isUc17RawCandidateType(candidate.type)) {
      unknownTypeCount += 1;
      continue;
    }

    supportedCandidates.push({
      key: toUc17RawCandidateKey({
        name: candidate.name,
        type: candidate.type,
      }),
      name: candidate.name,
      type: candidate.type,
    });
  }

  return {
    candidates: supportedCandidates,
    unknownTypeCount,
  };
}

export function useUc17RawCandidates({
  apiBaseUrl,
  accessToken,
  onUnauthorized,
}: UseUc17RawCandidatesOptions) {
  const [state, dispatch] = useReducer(
    uc17RawCandidatesReducer,
    defaultUc17RawCandidatesState
  );
  const activeControllerRef = useRef<AbortController | null>(null);
  const selectedKeysRef = useRef(state.selectedKeys);

  useEffect(() => {
    selectedKeysRef.current = state.selectedKeys;
  }, [state.selectedKeys]);

  const loadRawCandidates = useCallback(async () => {
    activeControllerRef.current?.abort();

    const controller = new AbortController();
    activeControllerRef.current = controller;

    console.info("[UC-17] Start ladowania kandydatow raw.");
    dispatch({ type: "loadStarted" });

    try {
      const response = await getRawDatasetCandidates(
        apiBaseUrl,
        accessToken,
        controller.signal
      );

      if (controller.signal.aborted) {
        return;
      }

      const mapped = mapRawCandidates(response);
      const reconciledSelection = reconcileSelectedCandidates(
        selectedKeysRef.current,
        mapped.candidates
      );

      if (mapped.unknownTypeCount > 0) {
        console.warn("[UC-17] Odrzucono kandydatow z nieznanym typem.", {
          count: mapped.unknownTypeCount,
        });
      }

      if (reconciledSelection.removedKeys.length > 0) {
        console.warn("[UC-17] Usunieto nieaktualne zaznaczenia po odswiezeniu.", {
          removedCount: reconciledSelection.removedKeys.length,
        });
      }

      console.info("[UC-17] Zaladowano kandydatow raw.", {
        total: mapped.candidates.length,
        board: mapped.candidates.filter((candidate) => candidate.type === "board").length,
        digit: mapped.candidates.filter((candidate) => candidate.type === "digit").length,
      });

      dispatch({
        type: "loadSucceeded",
        candidates: mapped.candidates,
        selectedKeys: reconciledSelection.selectedKeys,
        unknownTypeCount: mapped.unknownTypeCount,
      });
    } catch (error) {
      if (controller.signal.aborted) {
        return;
      }

      if (error instanceof RawDatasetCandidatesApiError && error.status === 401) {
        console.warn("[UC-17] Sesja administracyjna wygasla podczas ladowania.", {
          errorType: error.errorType ?? null,
          httpStatus: error.status,
        });
        onUnauthorized?.();
      } else if (
        error instanceof RawDatasetCandidatesApiError &&
        error.status >= 500
      ) {
        console.error("[UC-17] Backend zwrocil blad podczas ladowania kandydatow.", {
          errorType: error.errorType ?? null,
          httpStatus: error.status,
        });
      } else if (error instanceof Error) {
        console.error("[UC-17] Nie udalo sie przetworzyc odpowiedzi kandydatow.", {
          message: error.message,
        });
      }

      dispatch({
        type: "loadFailed",
        error:
          error instanceof Error
            ? error.message
            : "Nie udalo sie pobrac kandydatow datasetowych.",
        errorType:
          error instanceof RawDatasetCandidatesApiError
            ? error.errorType ?? null
            : null,
        httpStatus:
          error instanceof RawDatasetCandidatesApiError ? error.status : null,
      });
    } finally {
      if (activeControllerRef.current === controller) {
        activeControllerRef.current = null;
      }
    }
  }, [accessToken, apiBaseUrl, onUnauthorized]);

  const retryLoadRawCandidates = useCallback(async () => {
    console.info("[UC-17] Reczny retry ladowania kandydatow raw.");
    await loadRawCandidates();
  }, [loadRawCandidates]);

  const toggleRawCandidateSelection = useCallback((candidateKey: string) => {
    dispatch({
      type: "selectionToggled",
      candidateKey,
    });
  }, []);

  useEffect(() => {
    void loadRawCandidates();
  }, [loadRawCandidates]);

  useEffect(() => {
    return () => {
      activeControllerRef.current?.abort();
    };
  }, []);

  const sourceDrafts = useMemo(
    () => toPreparationSourceDrafts(state.candidates, state.selectedKeys),
    [state.candidates, state.selectedKeys]
  );

  return {
    status: state.status,
    candidates: state.candidates,
    selectedKeys: state.selectedKeys,
    selectedCount: state.selectedKeys.length,
    error: state.error,
    errorType: state.errorType,
    httpStatus: state.httpStatus,
    unknownTypeCount: state.unknownTypeCount,
    sourceDrafts,
    loadRawCandidates,
    retryLoadRawCandidates,
    toggleRawCandidateSelection,
  };
}
