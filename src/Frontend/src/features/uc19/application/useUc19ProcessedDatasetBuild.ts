import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  DatasetsApiError,
  postCreateProcessedDataset,
} from "../../../api/datasets";
import type {
  CreateProcessedDatasetApiEntry,
  ProcessedDatasetApiResponse,
} from "../../../types/api";
import { mapUc19SourceDraftsToProcessedDatasetSources } from "../domain/mapUc19SourceDraftsToProcessedDatasetSources";
import { validateUc19ProcessedDatasetBuildRequest } from "../domain/validateUc19ProcessedDatasetBuildRequest";
import type { Uc19BoardSourceDraft } from "../domain/uc19BoardSourceDraft";
import type { Uc19DigitSourceDraft } from "../domain/uc19DigitSourceDraft";

type RequestState =
  | {
      kind: "idle";
      response: ProcessedDatasetApiResponse | null;
      error: null;
      errorType: null;
      httpStatus: null;
    }
  | {
      kind: "loading";
      response: ProcessedDatasetApiResponse | null;
      error: null;
      errorType: null;
      httpStatus: null;
    }
  | {
      kind: "success";
      response: ProcessedDatasetApiResponse;
      error: null;
      errorType: null;
      httpStatus: number;
    }
  | {
      kind: "error";
      response: ProcessedDatasetApiResponse | null;
      error: string;
      errorType: string | null;
      httpStatus: number | null;
    };

type UseUc19ProcessedDatasetBuildOptions = {
  apiBaseUrl: string;
  accessToken?: string | null;
  onUnauthorized?: () => void;
  preparationName: string | null;
  canContinueToSources: boolean;
  boardSelectedDrafts: Uc19BoardSourceDraft[];
  digitSelectedDrafts: Uc19DigitSourceDraft[];
};

const defaultCreateState: RequestState = {
  kind: "idle",
  response: null,
  error: null,
  errorType: null,
  httpStatus: null,
};

function toCreateStatusHint(status: number | null): string | null {
  if (status === null) {
    return null;
  }

  const hints: Record<number, string> = {
    400: "Sprawdz nazwe datasetu i konfiguracje zrodel.",
    401: "Sesja administracyjna wygasla. Zaloguj sie ponownie.",
    404: "Przygotowanie albo jedno ze zrodel nie jest juz dostepne.",
    409: "Dataset o tej nazwie juz istnieje albo koliduje z istniejacym rekordem.",
    422: "Backend odrzucil budowe datasetu jako niespojna semantycznie.",
    500: "Backend nie zakonczyl builda z powodu bledu technicznego.",
    502: "Backend lub usluga posrednia jest chwilowo niedostepna.",
    503: "Backend lub usluga posrednia jest chwilowo niedostepna.",
    504: "Budowa datasetu przekroczyla limit czasu.",
  };

  return hints[status] ?? null;
}

export function useUc19ProcessedDatasetBuild({
  apiBaseUrl,
  accessToken,
  onUnauthorized,
  preparationName,
  canContinueToSources,
  boardSelectedDrafts,
  digitSelectedDrafts,
}: UseUc19ProcessedDatasetBuildOptions) {
  const [datasetName, setDatasetName] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [createState, setCreateState] = useState<RequestState>(defaultCreateState);
  const createAbortRef = useRef<AbortController | null>(null);

  const sources = useMemo(
    () =>
      mapUc19SourceDraftsToProcessedDatasetSources(
        boardSelectedDrafts,
        digitSelectedDrafts,
      ),
    [boardSelectedDrafts, digitSelectedDrafts],
  );

  const requestPreview = useMemo<CreateProcessedDatasetApiEntry | null>(() => {
    const normalizedPreparationName = preparationName?.trim() ?? "";
    if (!normalizedPreparationName) {
      return null;
    }

    return {
      preparationName: normalizedPreparationName,
      name: datasetName.trim(),
      sources,
    };
  }, [datasetName, preparationName, sources]);

  const handleSubmitProcessedDatasetBuild = useCallback(async (): Promise<ProcessedDatasetApiResponse | null> => {
    const validationError = validateUc19ProcessedDatasetBuildRequest({
      preparationName,
      canContinueToSources,
      name: datasetName,
      boardSelectedDrafts,
      digitSelectedDrafts,
    });

    if (validationError) {
      if (preparationName && !canContinueToSources) {
        console.warn("[UC-19] Build zablokowany przez brak gotowosci preparation.", {
          preparationName,
        });
      }

      setFormError(validationError);
      return null;
    }

    const request = {
      preparationName: preparationName!.trim(),
      name: datasetName.trim(),
      sources,
    } satisfies CreateProcessedDatasetApiEntry;

    createAbortRef.current?.abort();

    const controller = new AbortController();
    createAbortRef.current = controller;

    setCreateState((previous) => ({
      kind: "loading",
      response: previous.response,
      error: null,
      errorType: null,
      httpStatus: null,
    }));
    setFormError(null);

    console.info("[UC-19] Start builda finalnego datasetu.", {
      preparationName: request.preparationName,
      datasetName: request.name,
      boardSelectedCount: boardSelectedDrafts.length,
      digitSelectedCount: digitSelectedDrafts.length,
    });

    try {
      const response = await postCreateProcessedDataset(
        apiBaseUrl,
        request,
        accessToken,
        controller.signal,
      );

      if (controller.signal.aborted) {
        return null;
      }

      console.info("[UC-19] Build finalnego datasetu zakonczyl sie sukcesem.", {
        preparationName: request.preparationName,
        datasetName: response.name,
        warningsCount: response.warnings.length,
      });

      setCreateState({
        kind: "success",
        response,
        error: null,
        errorType: null,
        httpStatus: 201,
      });

      return response;
    } catch (error) {
      if (controller.signal.aborted) {
        return null;
      }

      if (error instanceof DatasetsApiError) {
        if (error.status === 401) {
          console.warn("[UC-19] Sesja administracyjna wygasla podczas builda datasetu.", {
            preparationName: request.preparationName,
            datasetName: request.name,
            httpStatus: error.status,
            errorType: error.errorType ?? null,
          });
          onUnauthorized?.();
        } else if (
          error.status === 404 ||
          error.status === 409 ||
          error.status === 422
        ) {
          console.warn("[UC-19] Backend odrzucil build finalnego datasetu.", {
            preparationName: request.preparationName,
            datasetName: request.name,
            httpStatus: error.status,
            errorType: error.errorType ?? null,
          });
        } else if (error.status >= 500) {
          console.error("[UC-19] Backend nie zakonczyl builda finalnego datasetu.", {
            preparationName: request.preparationName,
            datasetName: request.name,
            httpStatus: error.status,
            errorType: error.errorType ?? null,
          });
        }
      } else if (error instanceof Error) {
        console.error("[UC-19] Nie udalo sie przetworzyc odpowiedzi builda datasetu.", {
          preparationName: request.preparationName,
          datasetName: request.name,
          message: error.message,
        });
      }

      setCreateState((previous) => ({
        kind: "error",
        response: previous.response,
        error:
          error instanceof Error
            ? error.message
            : "Nie udalo sie zbudowac finalnego datasetu.",
        errorType: error instanceof DatasetsApiError ? error.errorType ?? null : null,
        httpStatus: error instanceof DatasetsApiError ? error.status : null,
      }));

      return null;
    } finally {
      if (createAbortRef.current === controller) {
        createAbortRef.current = null;
      }
    }
  }, [
    accessToken,
    apiBaseUrl,
    boardSelectedDrafts,
    canContinueToSources,
    datasetName,
    digitSelectedDrafts,
    onUnauthorized,
    preparationName,
    sources,
  ]);

  useEffect(() => {
    return () => {
      createAbortRef.current?.abort();
    };
  }, []);

  return {
    datasetName,
    setDatasetName,
    formError,
    setFormError,
    createState,
    createStatusHint: toCreateStatusHint(createState.httpStatus),
    requestPreview,
    sources,
    handleSubmitProcessedDatasetBuild,
  };
}
