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
import type { ExampleFileApiResponse } from "../../types/api";
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

  const isUploadBusy = uploadState.kind === "loading";
  const canSubmitUpload = Boolean(selectedFile) && !isUploadBusy && isAdminMode;
  const examplesListData =
    examplesListState.kind === "success"
      ? examplesListState.data
      : examplesListState.kind === "loading" && examplesListState.data
        ? examplesListState.data
        : null;

  return {
    boardStageState,
    canSubmitUpload,
    cellsStageState,
    examplesListData,
    examplesListState,
    downloadingName,
    fileInputRef,
    handleDownloadClick,
    handleUploadClick,
    isUploadBusy,
    loadExamplesList,
    previewStageState,
    runUc04Flow,
    selectedFile,
    selectedProcessName,
    sessionExamples,
    setSelectedFile,
    setSelectedProcessName,
    uploadState,
  };
}
