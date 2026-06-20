import { useCallback, useEffect, useRef, useState } from "react";

import { ExamplesApiError, putPreprocessBoardFromImage, putPreprocessCells } from "../../../api/examples";
import { readFileAsImageApiEntry } from "../../../shared/images/readFileAsImageApiEntry";
import type { CellsStageState, ImageStageState } from "../../../app/state";
import {
  defaultUc20BoardStageState,
  defaultUc20CellsStageState,
  defaultUc20LocalImageDraftState,
  type Uc20LocalImageDraftState,
} from "./uc20LocalImageFlowTypes";
import { validateUc20LocalImageFile } from "../domain/validateUc20LocalImageFile";

type UseUc20LocalImageFlowOptions = {
  apiBaseUrl: string;
  onActivateLocalSource?: () => void;
};

export type UseUc20LocalImageFlowResult = {
  draftState: Uc20LocalImageDraftState;
  boardStageState: ImageStageState;
  cellsStageState: CellsStageState;
  canRunFlow: boolean;
  canRetryFlow: boolean;
  isFlowBusy: boolean;
  handleSelectedLocalFileChange: (file: File | null) => Promise<void>;
  handleRunUc20Flow: () => Promise<void>;
  resetUc20Flow: () => void;
};

type Uc20Stage = "board" | "cells";

function toUc20FileMeta(draftState: Uc20LocalImageDraftState) {
  const draft = draftState.selectedDraft;

  return draft
    ? {
        fileName: draft.fileName,
        mimeType: draft.mimeType,
        sizeBytes: draft.sizeBytes,
      }
    : null;
}

function logUc20ApiError(
  stage: Uc20Stage,
  error: unknown,
  fileMeta: ReturnType<typeof toUc20FileMeta>,
) {
  if (!(error instanceof ExamplesApiError)) {
    console.error("[UC-20] Nieoczekiwany blad przetwarzania lokalnego obrazu.", {
      stage,
      ...fileMeta,
      message: error instanceof Error ? error.message : "Nieznany blad.",
    });
    return;
  }

  const details = {
    stage,
    ...fileMeta,
    httpStatus: error.status,
    errorType: error.errorType,
  };

  if (error.status === 400 || error.status === 422) {
    console.warn("[UC-20] Backend odrzucil lokalny obraz.", details);
    return;
  }

  if (error.status === 503 || error.status === 504 || error.status >= 500) {
    console.error("[UC-20] Backend nie zakonczyl preprocessingu lokalnego obrazu.", details);
    return;
  }

  console.warn("[UC-20] Lokalny preprocessing zwrocil nieoczekiwany status.", details);
}

export function useUc20LocalImageFlow({
  apiBaseUrl,
  onActivateLocalSource,
}: UseUc20LocalImageFlowOptions): UseUc20LocalImageFlowResult {
  const requestAbortRef = useRef<AbortController | null>(null);
  const previewUrlRef = useRef<string | null>(null);
  const selectionVersionRef = useRef(0);

  const [draftState, setDraftState] = useState<Uc20LocalImageDraftState>(
    defaultUc20LocalImageDraftState,
  );
  const [boardStageState, setBoardStageState] = useState<ImageStageState>(
    defaultUc20BoardStageState,
  );
  const [cellsStageState, setCellsStageState] = useState<CellsStageState>(
    defaultUc20CellsStageState,
  );

  const revokePreviewUrl = useCallback((previewUrl: string | null) => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
  }, []);

  const replacePreviewUrl = useCallback(
    (nextPreviewUrl: string | null) => {
      const previousPreviewUrl = previewUrlRef.current;
      previewUrlRef.current = nextPreviewUrl;

      if (previousPreviewUrl && previousPreviewUrl !== nextPreviewUrl) {
        revokePreviewUrl(previousPreviewUrl);
      }
    },
    [revokePreviewUrl],
  );

  const clearProcessingStages = useCallback(() => {
    requestAbortRef.current?.abort();
    requestAbortRef.current = null;
    setBoardStageState(defaultUc20BoardStageState);
    setCellsStageState(defaultUc20CellsStageState);
  }, []);

  const resetUc20Flow = useCallback(() => {
    selectionVersionRef.current += 1;
    clearProcessingStages();
    replacePreviewUrl(null);

    const fileMeta = toUc20FileMeta(draftState);

    if (fileMeta) {
      console.info("[UC-20] Zresetowano lokalny flow obrazu.", fileMeta);
    }

    setDraftState(defaultUc20LocalImageDraftState);
  }, [clearProcessingStages, draftState, replacePreviewUrl]);

  const handleSelectedLocalFileChange = useCallback(
    async (file: File | null) => {
      selectionVersionRef.current += 1;
      const selectionVersion = selectionVersionRef.current;

      clearProcessingStages();
      replacePreviewUrl(null);

      if (!file) {
        setDraftState(defaultUc20LocalImageDraftState);
        return;
      }

      const validationError = validateUc20LocalImageFile(file);

      if (validationError) {
        console.warn("[UC-20] Lokalna walidacja odrzucila obraz.", {
          fileName: file.name,
          mimeType: file.type,
          sizeBytes: file.size,
        });

        setDraftState({
          selectedDraft: null,
          validationError,
          isReading: false,
        });
        return;
      }

      setDraftState({
        selectedDraft: null,
        validationError: null,
        isReading: true,
      });

      const previewUrl = URL.createObjectURL(file);

      try {
        const requestEntry = await readFileAsImageApiEntry(file);

        if (selectionVersionRef.current !== selectionVersion) {
          revokePreviewUrl(previewUrl);
          console.warn("[UC-20] Porzucono wynik odczytu lokalnego pliku po zmianie wyboru.", {
            fileName: file.name,
            mimeType: file.type,
            sizeBytes: file.size,
          });
          return;
        }

        replacePreviewUrl(previewUrl);
        setDraftState({
          selectedDraft: {
            fileName: file.name,
            mimeType: file.type,
            sizeBytes: file.size,
            previewUrl,
            requestEntry,
          },
          validationError: null,
          isReading: false,
        });

        console.info("[UC-20] Przygotowano lokalny obraz do preprocessingu.", {
          fileName: file.name,
          mimeType: file.type,
          sizeBytes: file.size,
        });

        onActivateLocalSource?.();
      } catch (error) {
        revokePreviewUrl(previewUrl);

        if (selectionVersionRef.current !== selectionVersion) {
          return;
        }

        console.error("[UC-20] Nie udalo sie przygotowac lokalnego obrazu.", {
          fileName: file.name,
          mimeType: file.type,
          sizeBytes: file.size,
          message: error instanceof Error ? error.message : "Nieznany blad.",
        });

        setDraftState({
          selectedDraft: null,
          validationError: "Nie udalo sie odczytac wybranego obrazu.",
          isReading: false,
        });
      }
    },
    [clearProcessingStages, onActivateLocalSource, replacePreviewUrl, revokePreviewUrl],
  );

  const handleRunUc20Flow = useCallback(async () => {
    const selectedDraft = draftState.selectedDraft;

    if (!selectedDraft || draftState.isReading) {
      setDraftState((previous) => ({
        ...previous,
        validationError: previous.validationError ?? "Wybierz plik obrazu Sudoku.",
      }));
      return;
    }

    requestAbortRef.current?.abort();
    const controller = new AbortController();
    requestAbortRef.current = controller;

    const fileMeta = toUc20FileMeta(draftState);
    let stage: Uc20Stage = "board";

    console.info("[UC-20] Start lokalnego preprocessingu obrazu.", {
      stage,
      ...fileMeta,
    });

    setBoardStageState({
      kind: "loading",
      image: null,
      error: null,
      errorType: null,
      httpStatus: null,
    });
    setCellsStageState(defaultUc20CellsStageState);

    try {
      const board = await putPreprocessBoardFromImage(
        apiBaseUrl,
        selectedDraft.requestEntry,
        controller.signal,
      );

      if (controller.signal.aborted) {
        return;
      }

      console.info("[UC-20] Sukces etapu board dla lokalnego obrazu.", {
        stage,
        ...fileMeta,
      });

      setBoardStageState({
        kind: "success",
        image: board,
        error: null,
        errorType: null,
        httpStatus: 200,
      });

      stage = "cells";
      setCellsStageState({
        kind: "loading",
        cells: null,
        error: null,
        errorType: null,
        httpStatus: null,
      });

      const cells = await putPreprocessCells(
        apiBaseUrl,
        {
          mimeType: board.mimeType,
          base64: board.base64,
        },
        controller.signal,
      );

      if (controller.signal.aborted) {
        return;
      }

      console.info("[UC-20] Sukces etapu cells dla lokalnego obrazu.", {
        stage,
        ...fileMeta,
      });

      setCellsStageState({
        kind: "success",
        cells,
        error: null,
        errorType: null,
        httpStatus: 200,
      });
    } catch (error) {
      if (controller.signal.aborted) {
        return;
      }

      logUc20ApiError(stage, error, fileMeta);

      const message =
        error instanceof Error
          ? error.message
          : "Nie udało się wykonać preprocessingu lokalnego obrazu.";
      const errorType =
        error instanceof ExamplesApiError ? (error.errorType ?? null) : null;
      const httpStatus = error instanceof ExamplesApiError ? error.status : null;

      if (stage === "board") {
        setBoardStageState({
          kind: "error",
          image: null,
          error: message,
          errorType,
          httpStatus,
        });
        return;
      }

      setCellsStageState({
        kind: "error",
        cells: null,
        error: message,
        errorType,
        httpStatus,
      });
    } finally {
      if (requestAbortRef.current === controller) {
        requestAbortRef.current = null;
      }
    }
  }, [apiBaseUrl, draftState]);

  useEffect(() => {
    return () => {
      requestAbortRef.current?.abort();
      revokePreviewUrl(previewUrlRef.current);
      previewUrlRef.current = null;
    };
  }, [revokePreviewUrl]);

  const isFlowBusy =
    draftState.isReading ||
    boardStageState.kind === "loading" ||
    cellsStageState.kind === "loading";
  const canRunFlow = draftState.selectedDraft !== null && !isFlowBusy;
  const canRetryFlow =
    draftState.selectedDraft !== null &&
    !isFlowBusy &&
    (boardStageState.kind !== "idle" || cellsStageState.kind !== "idle");

  return {
    draftState,
    boardStageState,
    cellsStageState,
    canRunFlow,
    canRetryFlow,
    isFlowBusy,
    handleSelectedLocalFileChange,
    handleRunUc20Flow,
    resetUc20Flow,
  };
}
