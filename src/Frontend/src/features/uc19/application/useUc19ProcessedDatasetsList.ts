import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  DatasetsApiError,
  getProcessedDatasets,
} from "../../../api/datasets";
import type { ProcessedDatasetListItemApiResponse } from "../../../types/api";
import { findUc19ProcessedDatasetNameCollision } from "../domain/findUc19ProcessedDatasetNameCollision";
import {
  resolveUc19ProcessedDatasetHighlight,
  type Uc19ProcessedDatasetHighlightedItem,
} from "../domain/resolveUc19ProcessedDatasetHighlight";

type Uc19ProcessedDatasetsListStatus = "idle" | "loading" | "success" | "error";

type Uc19ProcessedDatasetsListState = {
  status: Uc19ProcessedDatasetsListStatus;
  items: ProcessedDatasetListItemApiResponse[];
  totalCount: number;
  error: string | null;
  errorType: string | null;
  httpStatus: number | null;
};

type UseUc19ProcessedDatasetsListOptions = {
  apiBaseUrl: string;
  accessToken?: string | null;
  onUnauthorized?: () => void;
  typedDatasetName: string;
};

const defaultState: Uc19ProcessedDatasetsListState = {
  status: "idle",
  items: [],
  totalCount: 0,
  error: null,
  errorType: null,
  httpStatus: null,
};

type LoadProcessedDatasetsOptions = {
  reason: "initial" | "manual" | "sync";
  createdDatasetName?: string | null;
};

type LoadProcessedDatasetsResult = {
  ok: boolean;
  foundCreatedDataset: boolean | null;
};

export function useUc19ProcessedDatasetsList({
  apiBaseUrl,
  accessToken,
  onUnauthorized,
  typedDatasetName,
}: UseUc19ProcessedDatasetsListOptions) {
  const [state, setState] = useState<Uc19ProcessedDatasetsListState>(defaultState);
  const [syncWarning, setSyncWarning] = useState<string | null>(null);
  const [freshlyCreatedDatasetName, setFreshlyCreatedDatasetName] = useState<string | null>(
    null
  );
  const activeControllerRef = useRef<AbortController | null>(null);
  const lastCollisionKeyRef = useRef<string | null>(null);

  const loadProcessedDatasets = useCallback(
    async ({
      reason,
      createdDatasetName = null,
    }: LoadProcessedDatasetsOptions): Promise<LoadProcessedDatasetsResult> => {
      if (!accessToken) {
        activeControllerRef.current?.abort();
        setState(defaultState);
        setSyncWarning(null);
        setFreshlyCreatedDatasetName(null);
        return {
          ok: false,
          foundCreatedDataset: null,
        };
      }

      activeControllerRef.current?.abort();

      const controller = new AbortController();
      activeControllerRef.current = controller;

      console.info("[UC-19] Start ladowania katalogu processed datasetow.", {
        reason,
      });

      setState((previous) => ({
        status: "loading",
        items: previous.items,
        totalCount: previous.totalCount,
        error: null,
        errorType: null,
        httpStatus: null,
      }));

      try {
        const response = await getProcessedDatasets(
          apiBaseUrl,
          accessToken,
          controller.signal
        );

        if (controller.signal.aborted) {
          return {
            ok: false,
            foundCreatedDataset: null,
          };
        }

        const foundCreatedDataset =
          createdDatasetName?.trim()
            ? response.items.some((item) => item.name === createdDatasetName.trim())
            : null;

        if (reason === "sync" && createdDatasetName?.trim()) {
          if (foundCreatedDataset) {
            setFreshlyCreatedDatasetName(createdDatasetName.trim());
            setSyncWarning(null);
          } else {
            setFreshlyCreatedDatasetName(null);
            setSyncWarning(
              "Build zakonczyl sie sukcesem, ale odswiezony katalog nie potwierdzil jeszcze nowego rekordu."
            );
            console.warn(
              "[UC-19] Odswiezony katalog processed nie potwierdzil nowo utworzonego datasetu.",
              {
                datasetName: createdDatasetName.trim(),
                freshlyCreatedFound: false,
              }
            );
          }
        } else if (reason !== "sync") {
          setSyncWarning(null);
        }

        console.info("[UC-19] Zaladowano katalog processed datasetow.", {
          reason,
          totalCount: response.totalCount,
        });

        setState({
          status: "success",
          items: response.items,
          totalCount: response.totalCount,
          error: null,
          errorType: null,
          httpStatus: 200,
        });

        return {
          ok: true,
          foundCreatedDataset,
        };
      } catch (error) {
        if (controller.signal.aborted) {
          return {
            ok: false,
            foundCreatedDataset: null,
          };
        }

        if (error instanceof DatasetsApiError) {
          if (error.status === 401) {
            console.warn("[UC-19] Sesja administracyjna wygasla podczas ladowania katalogu processed.", {
              httpStatus: error.status,
              errorType: error.errorType ?? null,
              reason,
            });
            onUnauthorized?.();
          } else if (error.status >= 500) {
            console.error("[UC-19] Backend zwrocil blad podczas ladowania katalogu processed.", {
              httpStatus: error.status,
              errorType: error.errorType ?? null,
              reason,
            });
          }
        } else if (error instanceof Error) {
          console.error("[UC-19] Nie udalo sie przetworzyc odpowiedzi katalogu processed.", {
            message: error.message,
            reason,
          });
        }

        if (reason === "sync") {
          setFreshlyCreatedDatasetName(null);
          setSyncWarning(
            "Build zakonczyl sie sukcesem, ale nie udalo sie odswiezyc katalogu processed."
          );
          console.warn("[UC-19] Nie potwierdzono katalogu processed po sukcesie POST.", {
            datasetName: createdDatasetName?.trim() || null,
            httpStatus: error instanceof DatasetsApiError ? error.status : null,
            errorType: error instanceof DatasetsApiError ? error.errorType ?? null : null,
          });
        }

        setState((previous) => ({
          status: "error",
          items: previous.items,
          totalCount: previous.totalCount,
          error:
            error instanceof Error
              ? error.message
              : "Nie udalo sie pobrac katalogu processed datasetow.",
          errorType: error instanceof DatasetsApiError ? error.errorType ?? null : null,
          httpStatus: error instanceof DatasetsApiError ? error.status : null,
        }));

        return {
          ok: false,
          foundCreatedDataset: null,
        };
      } finally {
        if (activeControllerRef.current === controller) {
          activeControllerRef.current = null;
        }
      }
    },
    [accessToken, apiBaseUrl, onUnauthorized]
  );

  const refreshProcessedDatasets = useCallback(async () => {
    console.info("[UC-19] Reczne odswiezenie katalogu processed datasetow.");
    await loadProcessedDatasets({ reason: "manual" });
  }, [loadProcessedDatasets]);

  const syncProcessedDatasetsAfterCreate = useCallback(
    async (createdDatasetName: string) => {
      const normalizedCreatedDatasetName = createdDatasetName.trim();

      if (!normalizedCreatedDatasetName) {
        return;
      }

      console.info("[UC-19] Synchronizacja katalogu processed po sukcesie POST.", {
        datasetName: normalizedCreatedDatasetName,
      });

      await loadProcessedDatasets({
        reason: "sync",
        createdDatasetName: normalizedCreatedDatasetName,
      });
    },
    [loadProcessedDatasets]
  );

  useEffect(() => {
    if (!accessToken) {
      activeControllerRef.current?.abort();
      setState(defaultState);
      setSyncWarning(null);
      setFreshlyCreatedDatasetName(null);
      return;
    }

    void loadProcessedDatasets({ reason: "initial" });
  }, [accessToken, loadProcessedDatasets]);

  useEffect(() => {
    return () => {
      activeControllerRef.current?.abort();
    };
  }, []);

  const collisionItem = useMemo(
    () => findUc19ProcessedDatasetNameCollision(typedDatasetName, state.items),
    [typedDatasetName, state.items]
  );
  const highlightedItems = useMemo<Uc19ProcessedDatasetHighlightedItem[]>(
    () =>
      resolveUc19ProcessedDatasetHighlight(
        state.items,
        freshlyCreatedDatasetName,
        typedDatasetName
      ),
    [freshlyCreatedDatasetName, state.items, typedDatasetName]
  );

  useEffect(() => {
    const nextCollisionKey = collisionItem
      ? `${collisionItem.name}:${collisionItem.fileName}`
      : null;

    if (!nextCollisionKey) {
      lastCollisionKeyRef.current = null;
      return;
    }

    if (lastCollisionKeyRef.current === nextCollisionKey) {
      return;
    }

    lastCollisionKeyRef.current = nextCollisionKey;
    console.warn("[UC-19] Wpisana nazwa datasetu pasuje do istniejacego rekordu.", {
      datasetName: typedDatasetName.trim(),
      collisionDetected: true,
    });
  }, [collisionItem, typedDatasetName]);

  return {
    status: state.status,
    items: state.items,
    highlightedItems,
    totalCount: state.totalCount,
    error: state.error,
    errorType: state.errorType,
    httpStatus: state.httpStatus,
    syncWarning,
    freshlyCreatedDatasetName,
    collisionItem,
    loadProcessedDatasets,
    refreshProcessedDatasets,
    syncProcessedDatasetsAfterCreate,
  };
}
