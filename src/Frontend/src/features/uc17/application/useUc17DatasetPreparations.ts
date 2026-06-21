import { useCallback, useEffect, useRef, useState } from "react";

import {
  createDatasetPreparation,
  DatasetPreparationsApiError,
  getDatasetPreparationDetails,
  getDatasetPreparations,
} from "../../../api/datasetPreparations";
import type {
  CreateDatasetPreparationSourceApiEntry,
  DatasetPreparationApiResponse,
  DatasetPreparationListItemApiResponse,
} from "../../../types/api";

type LoadableState<T> =
  | {
      kind: "idle";
      data: T | null;
      error: null;
      errorType: null;
      httpStatus: null;
    }
  | {
      kind: "loading";
      data: T | null;
      error: null;
      errorType: null;
      httpStatus: null;
    }
  | {
      kind: "success";
      data: T;
      error: null;
      errorType: null;
      httpStatus: number;
    }
  | {
      kind: "error";
      data: T | null;
      error: string;
      errorType: string | null;
      httpStatus: number | null;
    };

type RequestState<T> =
  | {
      kind: "idle";
      response: T | null;
      error: null;
      errorType: null;
      httpStatus: null;
    }
  | {
      kind: "loading";
      response: T | null;
      error: null;
      errorType: null;
      httpStatus: null;
    }
  | {
      kind: "success";
      response: T;
      error: null;
      errorType: null;
      httpStatus: number;
    }
  | {
      kind: "error";
      response: T | null;
      error: string;
      errorType: string | null;
      httpStatus: number | null;
    };

type UseUc17DatasetPreparationsOptions = {
  apiBaseUrl: string;
  accessToken?: string | null;
  onUnauthorized?: () => void;
};

const defaultPreparationsState: LoadableState<DatasetPreparationListItemApiResponse[]> = {
  kind: "idle",
  data: null,
  error: null,
  errorType: null,
  httpStatus: null,
};

const defaultPreparationDetailsState: LoadableState<DatasetPreparationApiResponse> = {
  kind: "idle",
  data: null,
  error: null,
  errorType: null,
  httpStatus: null,
};

const defaultCreateState: RequestState<DatasetPreparationApiResponse> = {
  kind: "idle",
  response: null,
  error: null,
  errorType: null,
  httpStatus: null,
};

type CreatePreparationParams = {
  preparationName: string;
  sources: CreateDatasetPreparationSourceApiEntry[];
};

type LogMetadata = {
  preparationName?: string;
  sourcesCount?: number;
};

function toCreateStatusHint(status: number | null): string | null {
  if (status === null) {
    return null;
  }

  const hints: Record<number, string> = {
    400: "Sprawdz nazwe przygotowania i liste zrodel.",
    401: "Sesja administracyjna wygasla. Zaloguj sie ponownie.",
    404: "Jedno z wybranych zrodel nie jest juz dostepne.",
    409: "Przygotowanie o tej nazwie juz istnieje.",
    422: "Backend odrzucil request z powodu niespojnosci danych.",
    500: "Backend nie rozpoczal przygotowania z powodu bledu technicznego.",
    502: "Backend lub posrednia usluga jest chwilowo niedostepna.",
    503: "Backend lub posrednia usluga jest chwilowo niedostepna.",
    504: "Backend lub posrednia usluga nie odpowiedziala na czas.",
  };

  return hints[status] ?? null;
}

function logPreparationsError(
  error: unknown,
  context: "list" | "details" | "create",
  metadata: LogMetadata = {}
) {
  const messages = {
    list: "[UC-17] Nie udalo sie pobrac listy przygotowan.",
    details: "[UC-17] Nie udalo sie pobrac szczegolow przygotowania.",
    create: "[UC-17] Backend nie rozpoczal przygotowania.",
  } as const;

  if (error instanceof DatasetPreparationsApiError) {
    if (context === "details" && error.status === 404) {
      console.warn("[UC-17] Nie znaleziono wybranego przygotowania.", {
        errorType: error.errorType ?? null,
        httpStatus: error.status,
        preparationName: metadata.preparationName,
      });
      return;
    }

    if (
      context === "create" &&
      (error.status === 404 || error.status === 409 || error.status === 422)
    ) {
      console.warn(messages[context], {
        errorType: error.errorType ?? null,
        httpStatus: error.status,
        preparationName: metadata.preparationName,
        sourcesCount: metadata.sourcesCount,
      });
      return;
    }

    if (error.status >= 500) {
      console.error(messages[context], {
        errorType: error.errorType ?? null,
        httpStatus: error.status,
        preparationName: metadata.preparationName,
        sourcesCount: metadata.sourcesCount,
      });
      return;
    }

    return;
  }

  if (error instanceof Error) {
    console.error(messages[context], {
      message: error.message,
      preparationName: metadata.preparationName,
      sourcesCount: metadata.sourcesCount,
    });
  }
}

export function useUc17DatasetPreparations({
  apiBaseUrl,
  accessToken,
  onUnauthorized,
}: UseUc17DatasetPreparationsOptions) {
  const [preparationsState, setPreparationsState] = useState(defaultPreparationsState);
  const [detailsState, setDetailsState] = useState(defaultPreparationDetailsState);
  const [createState, setCreateState] = useState(defaultCreateState);
  const [selectedPreparationName, setSelectedPreparationName] = useState<string | null>(null);
  const listAbortRef = useRef<AbortController | null>(null);
  const detailsAbortRef = useRef<AbortController | null>(null);
  const createAbortRef = useRef<AbortController | null>(null);
  const selectedPreparationNameRef = useRef<string | null>(null);

  useEffect(() => {
    selectedPreparationNameRef.current = selectedPreparationName;
  }, [selectedPreparationName]);

  const handleUnauthorizedError = useCallback(
    (error: DatasetPreparationsApiError) => {
      if (error.status !== 401) {
        return;
      }

      console.warn("[UC-17] Sesja administracyjna wygasla podczas operacji przygotowan.", {
        errorType: error.errorType ?? null,
        httpStatus: error.status,
      });
      onUnauthorized?.();
    },
    [onUnauthorized]
  );

  const loadPreparations = useCallback(async () => {
    listAbortRef.current?.abort();

    const controller = new AbortController();
    listAbortRef.current = controller;

    setPreparationsState((previous) => ({
      kind: "loading",
      data: previous.data,
      error: null,
      errorType: null,
      httpStatus: null,
    }));

    try {
      const response = await getDatasetPreparations(
        apiBaseUrl,
        accessToken,
        controller.signal
      );

      if (controller.signal.aborted) {
        return;
      }

      setPreparationsState({
        kind: "success",
        data: response.items,
        error: null,
        errorType: null,
        httpStatus: 200,
      });

      console.info("[UC-17] Zaladowano liste przygotowan.", {
        totalCount: response.totalCount,
      });

      if (
        selectedPreparationNameRef.current &&
        !response.items.some(
          (item) => item.preparationName === selectedPreparationNameRef.current
        )
      ) {
        console.warn("[UC-17] Usunieto wybrane przygotowanie po odswiezeniu listy.", {
          selectedPreparationName: selectedPreparationNameRef.current,
          totalCount: response.totalCount,
        });
        setSelectedPreparationName(null);
        setDetailsState(defaultPreparationDetailsState);
      }
    } catch (error) {
      if (controller.signal.aborted) {
        return;
      }

      if (error instanceof DatasetPreparationsApiError) {
        handleUnauthorizedError(error);
      }

      logPreparationsError(error, "list");

      setPreparationsState((previous) => ({
        kind: "error",
        data: previous.data,
        error:
          error instanceof Error
            ? error.message
            : "Nie udalo sie pobrac listy przygotowan datasetu.",
        errorType:
          error instanceof DatasetPreparationsApiError
            ? error.errorType ?? null
            : null,
        httpStatus:
          error instanceof DatasetPreparationsApiError ? error.status : null,
      }));
    } finally {
      if (listAbortRef.current === controller) {
        listAbortRef.current = null;
      }
    }
  }, [accessToken, apiBaseUrl, handleUnauthorizedError]);

  const refreshPreparations = useCallback(async () => {
    console.info("[UC-17] Reczne odswiezenie listy przygotowan.");
    await loadPreparations();
  }, [loadPreparations]);

  const loadPreparationDetails = useCallback(
    async (preparationName: string) => {
      detailsAbortRef.current?.abort();

      const controller = new AbortController();
      detailsAbortRef.current = controller;
      setSelectedPreparationName(preparationName);

      setDetailsState((previous) => ({
        kind: "loading",
        data:
          previous.data?.preparationName === preparationName ? previous.data : null,
        error: null,
        errorType: null,
        httpStatus: null,
      }));

      try {
        const response = await getDatasetPreparationDetails(
          apiBaseUrl,
          preparationName,
          accessToken,
          controller.signal
        );

        if (controller.signal.aborted) {
          return;
        }

        setDetailsState({
          kind: "success",
          data: response,
          error: null,
          errorType: null,
          httpStatus: 200,
        });

        console.info("[UC-17] Zaladowano szczegoly przygotowania.", {
          preparationName: response.preparationName,
          sourcesCount: response.sources.length,
          warningsCount: response.warnings.length,
        });
      } catch (error) {
        if (controller.signal.aborted) {
          return;
        }

        if (error instanceof DatasetPreparationsApiError) {
          handleUnauthorizedError(error);
        }

        logPreparationsError(error, "details", {
          preparationName,
        });

        setDetailsState((previous) => ({
          kind: "error",
          data:
            previous.data?.preparationName === preparationName
              ? previous.data
              : null,
          error:
            error instanceof Error
              ? error.message
              : "Nie udalo sie pobrac szczegolow przygotowania.",
          errorType:
            error instanceof DatasetPreparationsApiError
              ? error.errorType ?? null
              : null,
          httpStatus:
            error instanceof DatasetPreparationsApiError ? error.status : null,
        }));
      } finally {
        if (detailsAbortRef.current === controller) {
          detailsAbortRef.current = null;
        }
      }
    },
    [accessToken, apiBaseUrl, handleUnauthorizedError]
  );

  const refreshSelectedPreparation = useCallback(async () => {
    if (!selectedPreparationName) {
      return;
    }

    console.info("[UC-17] Reczne odswiezenie szczegolow przygotowania.", {
      preparationName: selectedPreparationName,
    });

    await loadPreparationDetails(selectedPreparationName);
  }, [loadPreparationDetails, selectedPreparationName]);

  const createPreparationRequest = useCallback(
    async ({ preparationName, sources }: CreatePreparationParams) => {
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

      console.info("[UC-17] Start tworzenia przygotowania datasetu.", {
        preparationName,
        sourcesCount: sources.length,
      });

      try {
        const response = await createDatasetPreparation(
          apiBaseUrl,
          {
            preparationName,
            sources,
          },
          accessToken,
          controller.signal
        );

        if (controller.signal.aborted) {
          return false;
        }

        console.info("[UC-17] Backend zaakceptowal przygotowanie datasetu.", {
          preparationName: response.preparationName,
          status: response.status,
          sourcesCount: response.sources.length,
        });

        setCreateState({
          kind: "success",
          response,
          error: null,
          errorType: null,
          httpStatus: 202,
        });

        console.info("[UC-17] Odswiezam liste przygotowan po create.", {
          preparationName: response.preparationName,
        });
        await loadPreparations();
        console.info("[UC-17] Odswiezam szczegoly nowo utworzonego przygotowania.", {
          preparationName: response.preparationName,
          status: response.status,
        });
        await loadPreparationDetails(response.preparationName);
        return true;
      } catch (error) {
        if (controller.signal.aborted) {
          return false;
        }

        if (error instanceof DatasetPreparationsApiError) {
          handleUnauthorizedError(error);
        }

        logPreparationsError(error, "create", {
          preparationName,
          sourcesCount: sources.length,
        });

        setCreateState((previous) => ({
          kind: "error",
          response: previous.response,
          error:
            error instanceof Error
              ? error.message
              : "Nie udalo sie rozpoczac przygotowania datasetu.",
          errorType:
            error instanceof DatasetPreparationsApiError
              ? error.errorType ?? null
              : null,
          httpStatus:
            error instanceof DatasetPreparationsApiError ? error.status : null,
        }));

        return false;
      } finally {
        if (createAbortRef.current === controller) {
          createAbortRef.current = null;
        }
      }
    },
    [
      accessToken,
      apiBaseUrl,
      handleUnauthorizedError,
      loadPreparationDetails,
      loadPreparations,
    ]
  );

  useEffect(() => {
    void loadPreparations();
  }, [loadPreparations]);

  useEffect(() => {
    return () => {
      listAbortRef.current?.abort();
      detailsAbortRef.current?.abort();
      createAbortRef.current?.abort();
    };
  }, []);

  return {
    preparationsState,
    detailsState,
    createState,
    selectedPreparationName,
    createStatusHint: toCreateStatusHint(createState.httpStatus),
    loadPreparations,
    refreshPreparations,
    loadPreparationDetails,
    refreshSelectedPreparation,
    createPreparationRequest,
  };
}
