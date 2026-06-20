import { useCallback, useEffect, useRef, useState } from "react";

import {
  downloadExampleAsFile,
  ExampleUploadApiError,
  ExamplesApiError,
  getExampleImage,
  getExamplesList,
  postExampleUpload,
  putPreprocessBoard,
  putPreprocessCells,
} from "../../api/examples";
import { useUc20LocalImageFlow } from "../../features/uc20/application/useUc20LocalImageFlow";
import type {
  CellsGridApiResponse,
  ExampleFileApiResponse,
} from "../../types/api";
import {
  defaultCellsStageState,
  defaultExamplesListState,
  defaultImageStageState,
  defaultUploadState,
  type CellsStageState,
  type ExamplesListState,
  type ImageStageState,
  type UploadState,
} from "../state";

type UseExamplesModuleOptions = {
  apiBaseUrl: string;
  isAdminMode: boolean;
  accessToken?: string | null;
  onRequireLogin: () => void;
  onUnauthorized: (errorType?: string | null) => void;
};

type ResolvedExamplesSource = {
  sourceKind: "example" | "local" | null;
  sourceLabel: string | null;
  cellsGrid: CellsGridApiResponse | null;
};

function resolveActiveExamplesSource({
  selectedExampleName,
  uc04CellsStageState,
  localDraftFileName,
  localCellsStageState,
}: {
  selectedExampleName: string | null;
  uc04CellsStageState: CellsStageState;
  localDraftFileName: string | null;
  localCellsStageState: CellsStageState;
}): ResolvedExamplesSource {
  if (localDraftFileName) {
    return {
      sourceKind: "local",
      sourceLabel: localDraftFileName,
      cellsGrid:
        localCellsStageState.kind === "success" ? localCellsStageState.cells : null,
    };
  }

  if (selectedExampleName) {
    return {
      sourceKind: "example",
      sourceLabel: selectedExampleName,
      cellsGrid:
        uc04CellsStageState.kind === "success" ? uc04CellsStageState.cells : null,
    };
  }

  return {
    sourceKind: null,
    sourceLabel: null,
    cellsGrid: null,
  };
}

export function useExamplesModule({
  apiBaseUrl,
  isAdminMode,
  accessToken,
  onRequireLogin,
  onUnauthorized,
}: UseExamplesModuleOptions) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uc04AbortRef = useRef<AbortController | null>(null);

  const [uploadState, setUploadState] =
    useState<UploadState>(defaultUploadState);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [sessionExamples, setSessionExamples] = useState<
    ExampleFileApiResponse[]
  >([]);
  const [examplesListState, setExamplesListState] = useState<ExamplesListState>(
    defaultExamplesListState,
  );
  const [downloadingName, setDownloadingName] = useState<string | null>(null);
  const [selectedProcessName, setSelectedProcessName] = useState<string | null>(
    null,
  );
  const [previewStageState, setPreviewStageState] = useState<ImageStageState>(
    defaultImageStageState,
  );
  const [boardStageState, setBoardStageState] = useState<ImageStageState>(
    defaultImageStageState,
  );
  const [cellsStageState, setCellsStageState] = useState<CellsStageState>(
    defaultCellsStageState,
  );

  const loadExamplesList = useCallback(async () => {
    setExamplesListState((previous) => ({
      kind: "loading",
      data:
        previous.kind === "success"
          ? previous.data
          : previous.kind === "loading" && previous.data
            ? previous.data
            : null,
      error: null,
      httpStatus: null,
      errorType: null,
    }));

    try {
      const data = await getExamplesList(apiBaseUrl);
      setExamplesListState({
        kind: "success",
        data,
        error: null,
        httpStatus: 200,
        errorType: null,
      });
    } catch (error) {
      if (error instanceof ExamplesApiError) {
        setExamplesListState({
          kind: "error",
          data: null,
          error: error.message,
          httpStatus: error.status,
          errorType: error.errorType ?? null,
        });
        return;
      }

      setExamplesListState({
        kind: "error",
        data: null,
        error:
          error instanceof Error
            ? error.message
            : "Nie udało się pobrać listy przykładów.",
        httpStatus: null,
        errorType: null,
      });
    }
  }, [apiBaseUrl]);

  const handleUploadClick = useCallback(async () => {
    if (!selectedFile) {
      return;
    }

    if (!accessToken) {
      onRequireLogin();
      return;
    }

    setUploadState({
      kind: "loading",
      error: null,
      httpStatus: null,
    });

    try {
      const result = await postExampleUpload(apiBaseUrl, selectedFile, accessToken);

      setUploadState({
        kind: "success",
        error: null,
        httpStatus: 201,
        response: result,
      });

      setSessionExamples((previous) => [...previous, result]);
      setSelectedFile(null);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

      void loadExamplesList();
    } catch (error) {
      if (error instanceof ExampleUploadApiError) {
        if (error.status === 401) {
          onUnauthorized(error.errorType ?? null);
        }

        setUploadState({
          kind: "error",
          error: error.message,
          httpStatus: error.status,
          errorType: error.errorType ?? null,
        });
        return;
      }

      setUploadState({
        kind: "error",
        error:
          error instanceof Error
            ? error.message
            : "Nie udało się wysłać pliku do backendu.",
        httpStatus: null,
        errorType: null,
      });
    }
  }, [accessToken, apiBaseUrl, loadExamplesList, onRequireLogin, onUnauthorized, selectedFile]);

  const handleDownloadClick = useCallback(
    async (fileName: string) => {
      setDownloadingName(fileName);

      try {
        await downloadExampleAsFile(apiBaseUrl, fileName);
      } catch (error) {
        const message =
          error instanceof ExamplesApiError
            ? error.message
            : error instanceof Error
              ? error.message
              : "Nie udało się pobrać pliku.";
        window.alert(message);
      } finally {
        setDownloadingName(null);
      }
    },
    [apiBaseUrl],
  );

  const resetUc04Flow = useCallback(() => {
    uc04AbortRef.current?.abort();
    uc04AbortRef.current = null;
    setPreviewStageState(defaultImageStageState);
    setBoardStageState(defaultImageStageState);
    setCellsStageState(defaultCellsStageState);
  }, []);

  const handleActivateLocalSource = useCallback(() => {
    if (selectedProcessName) {
      console.info("[UC-20] Aktywacja lokalnego obrazu czysci aktywny flow biblioteki.", {
        selectedExampleName: selectedProcessName,
      });
    }

    resetUc04Flow();
    setSelectedProcessName(null);
  }, [resetUc04Flow, selectedProcessName]);

  const uc20LocalImageFlow = useUc20LocalImageFlow({
    apiBaseUrl,
    onActivateLocalSource: handleActivateLocalSource,
  });

  const runUc04Flow = useCallback(
    async (fileName: string) => {
      uc04AbortRef.current?.abort();
      const controller = new AbortController();
      uc04AbortRef.current = controller;
      let phase: "preview" | "board" | "cells" = "preview";

      setPreviewStageState({
        kind: "loading",
        image: null,
        error: null,
        errorType: null,
        httpStatus: null,
      });
      setBoardStageState(defaultImageStageState);
      setCellsStageState(defaultCellsStageState);

      try {
        const preview = await getExampleImage(apiBaseUrl, fileName, controller.signal);
        if (controller.signal.aborted) {
          return;
        }

        setPreviewStageState({
          kind: "success",
          image: preview,
          error: null,
          errorType: null,
          httpStatus: 200,
        });

        setBoardStageState({
          kind: "loading",
          image: null,
          error: null,
          errorType: null,
          httpStatus: null,
        });
        phase = "board";

        const board = await putPreprocessBoard(apiBaseUrl, fileName, controller.signal);
        if (controller.signal.aborted) {
          return;
        }

        setBoardStageState({
          kind: "success",
          image: board,
          error: null,
          errorType: null,
          httpStatus: 200,
        });

        setCellsStageState({
          kind: "loading",
          cells: null,
          error: null,
          errorType: null,
          httpStatus: null,
        });
        phase = "cells";

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

        const message =
          error instanceof Error
            ? error.message
            : "Nie udało się wykonać preprocessingu.";
        const errorType =
          error instanceof ExamplesApiError ? (error.errorType ?? null) : null;
        const httpStatus =
          error instanceof ExamplesApiError ? error.status : null;

        if (phase === "preview") {
          setPreviewStageState({
            kind: "error",
            image: null,
            error: message,
            errorType,
            httpStatus,
          });
          return;
        }

        if (phase === "board") {
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
      }
    },
    [apiBaseUrl],
  );

  useEffect(() => {
    void loadExamplesList();
  }, [loadExamplesList]);

  useEffect(() => {
    if (!selectedProcessName) {
      resetUc04Flow();
      return;
    }

    void runUc04Flow(selectedProcessName);
  }, [resetUc04Flow, runUc04Flow, selectedProcessName]);

  useEffect(() => {
    return () => {
      uc04AbortRef.current?.abort();
    };
  }, []);

  const handleSelectProcessName = useCallback(
    (value: string | null) => {
      if (value) {
        console.info("[UC-20] Zmiana zrodla na biblioteke przykladow resetuje lokalny flow.", {
          selectedExampleName: value,
        });
        uc20LocalImageFlow.resetUc20Flow();
      }

      setSelectedProcessName(value);
    },
    [uc20LocalImageFlow],
  );

  const activeSource = resolveActiveExamplesSource({
    selectedExampleName: selectedProcessName,
    uc04CellsStageState: cellsStageState,
    localDraftFileName: uc20LocalImageFlow.draftState.selectedDraft?.fileName ?? null,
    localCellsStageState: uc20LocalImageFlow.cellsStageState,
  });

  const isUploadBusy = uploadState.kind === "loading";
  const canSubmitUpload = Boolean(selectedFile) && !isUploadBusy && isAdminMode;
  const examplesListData =
    examplesListState.kind === "success"
      ? examplesListState.data
      : examplesListState.kind === "loading" && examplesListState.data
        ? examplesListState.data
        : null;

  return {
    activeCellsGrid: activeSource.cellsGrid,
    boardStageState,
    canSubmitUpload,
    cellsStageState,
    examplesListData,
    examplesListState,
    downloadingName,
    fileInputRef,
    handleDownloadClick,
    handleUploadClick,
    handleSelectProcessName,
    hasSelectedSource: activeSource.sourceKind !== null,
    isUploadBusy,
    loadExamplesList,
    previewStageState,
    runUc04Flow,
    selectedSourceKind: activeSource.sourceKind,
    selectedSourceLabel: activeSource.sourceLabel,
    selectedFile,
    selectedProcessName,
    sessionExamples,
    setSelectedFile,
    uc20LocalImageFlow,
    uploadState,
  };
}
