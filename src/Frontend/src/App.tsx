import { useCallback, useEffect, useRef, useState } from "react";

import {
  downloadExampleAsFile,
  ExampleUploadApiError,
  ExamplesApiError,
  getExamplesList,
  getExampleImage,
  postExampleUpload,
  putPreprocessBoard,
  putPreprocessCells,
} from "./api/examples";
import { Uc06TrainingSection } from "./components/Uc06TrainingSection";
import type {
  CellsGridApiResponse,
  ExampleFileApiResponse,
  ExamplesListApiResponse,
  ImageApiResponse,
} from "./types/api";

type PingResponse = {
  backendStatus: string;
  mlStatus: string;
  timestampUtc: string;
  message: string;
};

type PingState =
  | {
      kind: "idle";
      response: null;
      error: null;
      httpStatus: null;
    }
  | {
      kind: "loading";
      response: null;
      error: null;
      httpStatus: null;
    }
  | {
      kind: "success";
      response: PingResponse;
      error: null;
      httpStatus: number;
    }
  | {
      kind: "error";
      response: PingResponse | null;
      error: string;
      httpStatus: number | null;
    };

type UploadState =
  | {
      kind: "idle";
      error: null;
      httpStatus: null;
    }
  | {
      kind: "loading";
      error: null;
      httpStatus: null;
    }
  | {
      kind: "success";
      error: null;
      httpStatus: number;
      response: ExampleFileApiResponse;
    }
  | {
      kind: "error";
      error: string;
      httpStatus: number | null;
      errorType: string | null;
    };

type ExamplesListState =
  | {
      kind: "idle";
      data: null;
      error: null;
      httpStatus: null;
      errorType: null;
    }
  | {
      kind: "loading";
      data: ExamplesListApiResponse | null;
      error: null;
      httpStatus: null;
      errorType: null;
    }
  | {
      kind: "success";
      data: ExamplesListApiResponse;
      error: null;
      httpStatus: number;
      errorType: null;
    }
  | {
      kind: "error";
      data: ExamplesListApiResponse | null;
      error: string;
      httpStatus: number | null;
      errorType: string | null;
    };

type ImageStageState =
  | {
      kind: "idle";
      image: null;
      error: null;
      errorType: null;
      httpStatus: null;
    }
  | {
      kind: "loading";
      image: null;
      error: null;
      errorType: null;
      httpStatus: null;
    }
  | {
      kind: "success";
      image: ImageApiResponse;
      error: null;
      errorType: null;
      httpStatus: number;
    }
  | {
      kind: "error";
      image: null;
      error: string;
      errorType: string | null;
      httpStatus: number | null;
    };

type CellsStageState =
  | {
      kind: "idle";
      cells: null;
      error: null;
      errorType: null;
      httpStatus: null;
    }
  | {
      kind: "loading";
      cells: null;
      error: null;
      errorType: null;
      httpStatus: null;
    }
  | {
      kind: "success";
      cells: CellsGridApiResponse;
      error: null;
      errorType: null;
      httpStatus: number;
    }
  | {
      kind: "error";
      cells: null;
      error: string;
      errorType: string | null;
      httpStatus: number | null;
    };

const defaultPingState: PingState = {
  kind: "idle",
  response: null,
  error: null,
  httpStatus: null,
};

const defaultUploadState: UploadState = {
  kind: "idle",
  error: null,
  httpStatus: null,
};

const defaultExamplesListState: ExamplesListState = {
  kind: "idle",
  data: null,
  error: null,
  httpStatus: null,
  errorType: null,
};

const defaultImageStageState: ImageStageState = {
  kind: "idle",
  image: null,
  error: null,
  errorType: null,
  httpStatus: null,
};

const defaultCellsStageState: CellsStageState = {
  kind: "idle",
  cells: null,
  error: null,
  errorType: null,
  httpStatus: null,
};
function normalizeBaseUrl(baseUrl: string | undefined): string {
  const trimmedBaseUrl = baseUrl?.trim();

  if (!trimmedBaseUrl) {
    return "/api";
  }

  return trimmedBaseUrl.endsWith("/")
    ? trimmedBaseUrl.slice(0, -1)
    : trimmedBaseUrl;
}

function formatTimestamp(timestampUtc: string): string {
  const parsedDate = new Date(timestampUtc);

  if (Number.isNaN(parsedDate.getTime())) {
    return timestampUtc;
  }

  return new Intl.DateTimeFormat("pl-PL", {
    dateStyle: "medium",
    timeStyle: "medium",
    timeZone: "UTC",
  }).format(parsedDate);
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function toImageDataUrl(image: ImageApiResponse): string {
  return `data:${image.mimeType};base64,${image.base64}`;
}

export default function App() {
  const apiBaseUrl = normalizeBaseUrl(import.meta.env.VITE_API_BASE_URL);
  const pingEndpoint = `${apiBaseUrl}/ping`;
  const examplesUploadEndpoint = `${apiBaseUrl}/examples`;

  const fileInputRef = useRef<HTMLInputElement>(null);

  const [pingState, setPingState] = useState<PingState>(defaultPingState);
  const [uploadState, setUploadState] = useState<UploadState>(defaultUploadState);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [sessionExamples, setSessionExamples] = useState<ExampleFileApiResponse[]>(
    []
  );
  const [examplesListState, setExamplesListState] = useState<ExamplesListState>(
    defaultExamplesListState
  );
  const [downloadingName, setDownloadingName] = useState<string | null>(null);
  const [selectedProcessName, setSelectedProcessName] = useState<string | null>(
    null
  );
  const [previewStageState, setPreviewStageState] =
    useState<ImageStageState>(defaultImageStageState);
  const [boardStageState, setBoardStageState] =
    useState<ImageStageState>(defaultImageStageState);
  const [cellsStageState, setCellsStageState] =
    useState<CellsStageState>(defaultCellsStageState);
  const uc04AbortRef = useRef<AbortController | null>(null);

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

  useEffect(() => {
    void loadExamplesList();
  }, [loadExamplesList]);

  async function handlePingClick() {
    setPingState({
      kind: "loading",
      response: null,
      error: null,
      httpStatus: null,
    });

    try {
      const response = await fetch(pingEndpoint, {
        headers: {
          Accept: "application/json",
        },
      });

      const rawBody = await response.text();
      let parsedBody: PingResponse | null = null;

      if (rawBody) {
        parsedBody = JSON.parse(rawBody) as PingResponse;
      }

      if (!response.ok) {
        setPingState({
          kind: "error",
          response: parsedBody,
          error:
            parsedBody?.message ??
            `Backend zwrócił odpowiedź HTTP ${response.status}.`,
          httpStatus: response.status,
        });
        return;
      }

      if (!parsedBody) {
        throw new Error("Backend zwrócił pustą odpowiedź.");
      }

      setPingState({
        kind: "success",
        response: parsedBody,
        error: null,
        httpStatus: response.status,
      });
    } catch (error) {
      setPingState({
        kind: "error",
        response: null,
        error:
          error instanceof Error
            ? error.message
            : "Nie udało się połączyć z backendem.",
        httpStatus: null,
      });
    }
  }

  async function handleUploadClick() {
    if (!selectedFile) {
      return;
    }

    setUploadState({
      kind: "loading",
      error: null,
      httpStatus: null,
    });

    try {
      const result = await postExampleUpload(apiBaseUrl, selectedFile);

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
  }

  const isUploadBusy = uploadState.kind === "loading";
  const canSubmitUpload = Boolean(selectedFile) && !isUploadBusy;
  const examplesListData =
    examplesListState.kind === "success"
      ? examplesListState.data
      : examplesListState.kind === "loading" && examplesListState.data
        ? examplesListState.data
        : null;

  async function handleDownloadClick(fileName: string) {
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
  }

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
        const preview = await getExampleImage(
          apiBaseUrl,
          fileName,
          controller.signal
        );
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
          controller.signal
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
        const errorType = error instanceof ExamplesApiError ? error.errorType ?? null : null;
        const httpStatus = error instanceof ExamplesApiError ? error.status : null;

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
    [apiBaseUrl]
  );

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
  return (
    <main className="page-shell">
      <section className="hero-card">
        <p className="eyebrow">UC-00 - Smoke test FE / BE / ML</p>
        <h1>Sudoku Vision</h1>
        <p className="hero-copy">
          Ten ekran służy do szybkiego sprawdzenia, czy frontend może wywołać
          backend, a backend ma połączenie z serwisem ML.
        </p>

        <div className="configuration-card">
          <span className="configuration-label">Baza API</span>
          <code>{apiBaseUrl}</code>
        </div>

        <button
          className="primary-button"
          onClick={() => void handlePingClick()}
          disabled={pingState.kind === "loading"}
          type="button"
        >
          {pingState.kind === "loading"
            ? "Trwa testowanie połączenia..."
            : "Test połączenia"}
        </button>
      </section>

      <section className="hero-card upload-section">
        <p className="eyebrow">UC-01 — Upload przykładu</p>
        <h2>Dodaj plik do biblioteki przykładów</h2>
        <p className="hero-copy">
          Wyślij obraz sudoku na endpoint{" "}
          <code>{examplesUploadEndpoint}</code> (<code>multipart/form-data</code>
          , pole <code>file</code>). Kanoniczną nazwę pliku nadaje backend.
        </p>

        <div className="upload-controls">
          <input
            ref={fileInputRef}
            className="file-picker"
            type="file"
            accept="image/jpeg,image/png,.jpg,.jpeg,.png"
            disabled={isUploadBusy}
            aria-busy={isUploadBusy}
            onChange={(event) => {
              const file = event.target.files?.[0] ?? null;
              setSelectedFile(file);
            }}
          />
          <button
            className="primary-button"
            type="button"
            disabled={!canSubmitUpload}
            onClick={() => void handleUploadClick()}
          >
            {isUploadBusy ? "Wysyłanie..." : "Wyślij plik"}
          </button>
        </div>

        {sessionExamples.length > 0 ? (
          <>
            <h3 className="examples-session-heading">Dodane w tej sesji</h3>
            <ul className="examples-list">
              {sessionExamples.map((example) => (
                <li key={`${example.name}-${example.storedAtUtc}`}>
                  <code>{example.name}</code> - {formatBytes(example.sizeBytes)} -{" "}
                  {example.contentType}
                </li>
              ))}
            </ul>
          </>
        ) : null}
      </section>

      <section className="hero-card examples-library-section">
        <p className="eyebrow">UC-02 — Lista przykładów</p>
        <h2>Biblioteka przykładów Sudoku</h2>
        <p className="hero-copy">
          Źródło: <code>{`${apiBaseUrl}/examples`}</code> (<code>GET</code>). Akcja
          „Pobierz” używa podglądu <code>GET /examples/{"{name}"}</code> (JSON +
          base64), dopóki backend nie udostępni surowego{" "}
          <code>/download</code> (UC-03).
        </p>

        <div className="examples-toolbar">
          <button
            className="primary-button"
            type="button"
            disabled={examplesListState.kind === "loading"}
            onClick={() => void loadExamplesList()}
          >
            {examplesListState.kind === "loading"
              ? "Ładowanie listy..."
              : "Odśwież listę"}
          </button>
          {examplesListState.kind === "success" ? (
            <span className="muted-copy examples-total">
              Łącznie: {examplesListState.data.totalCount}
            </span>
          ) : null}
        </div>

        {examplesListState.kind === "error" ? (
          <>
            <p className="status-banner status-error">{examplesListState.error}</p>
            {examplesListState.errorType ? (
              <p className="muted-copy">Typ błędu: {examplesListState.errorType}</p>
            ) : null}
            {examplesListState.httpStatus !== null ? (
              <p className="muted-copy">HTTP status: {examplesListState.httpStatus}</p>
            ) : null}
          </>
        ) : null}

        {examplesListData && examplesListData.items.length === 0 ? (
          <p className="muted-copy">Brak plików w bibliotece przykładów.</p>
        ) : null}

        {examplesListData && examplesListData.items.length > 0 ? (
          <div className="examples-table-wrap">
            <table className="examples-table">
              <thead>
                <tr>
                  <th scope="col">Nazwa</th>
                  <th scope="col">Typ</th>
                  <th scope="col">Rozmiar</th>
                  <th scope="col">Zapisano (UTC)</th>
                  <th scope="col">Akcje</th>
                </tr>
              </thead>
              <tbody>
                {examplesListData.items.map((item) => (
                  <tr key={`${item.name}-${item.storedAtUtc}`}>
                    <td>
                      <code className="examples-table-name">{item.name}</code>
                    </td>
                    <td>{item.contentType}</td>
                    <td>{formatBytes(item.sizeBytes)}</td>
                    <td>{formatTimestamp(item.storedAtUtc)}</td>
                    <td>
                      <div className="examples-row-actions">
                        <button
                          className="secondary-button"
                          type="button"
                          disabled={downloadingName === item.name}
                          onClick={() => void handleDownloadClick(item.name)}
                        >
                          {downloadingName === item.name
                            ? "Pobieranie..."
                            : "Pobierz"}
                        </button>
                        <button
                          className="secondary-button"
                          type="button"
                          onClick={() => setSelectedProcessName(item.name)}
                        >
                          Przetwórz
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>

      {selectedProcessName ? (
        <section className="result-card uc04-flow-section" aria-live="polite">
          <p className="eyebrow">UC-04 — Przetwarzanie przykładu</p>
          <h2>Pipeline preprocessingu</h2>
          <p className="muted-copy">
            Wybrany plik: <code>{selectedProcessName}</code>
          </p>

          <div className="examples-row-actions">
            <button
              className="secondary-button"
              type="button"
              onClick={() => void runUc04Flow(selectedProcessName)}
              disabled={
                previewStageState.kind === "loading" ||
                boardStageState.kind === "loading" ||
                cellsStageState.kind === "loading"
              }
            >
              Uruchom ponownie
            </button>
            <button
              className="secondary-button"
              type="button"
              onClick={() => setSelectedProcessName(null)}
            >
              Wyczyść wybór
            </button>
          </div>

          <div className="uc04-stage-grid">
            <article className="uc04-stage-card">
              <h3>Etap 0 — Podgląd wejścia</h3>
              {previewStageState.kind === "loading" ? (
                <p className="status-banner status-loading">
                  Pobieranie obrazu wejściowego...
                </p>
              ) : null}
              {previewStageState.kind === "error" ? (
                <>
                  <p className="status-banner status-error">{previewStageState.error}</p>
                  {previewStageState.errorType ? (
                    <p className="muted-copy">
                      Typ błędu: {previewStageState.errorType}
                    </p>
                  ) : null}
                  {previewStageState.httpStatus !== null ? (
                    <p className="muted-copy">
                      HTTP status: {previewStageState.httpStatus}
                    </p>
                  ) : null}
                </>
              ) : null}
              {previewStageState.kind === "success" ? (
                <img
                  className="uc04-image-preview"
                  src={toImageDataUrl(previewStageState.image)}
                  alt={`Podgląd ${selectedProcessName}`}
                />
              ) : null}
            </article>

            <article className="uc04-stage-card">
              <h3>Etap 1 — Preprocess board</h3>
              {boardStageState.kind === "loading" ? (
                <p className="status-banner status-loading">
                  Przetwarzanie boarda...
                </p>
              ) : null}
              {boardStageState.kind === "error" ? (
                <>
                  <p className="status-banner status-error">{boardStageState.error}</p>
                  {boardStageState.errorType ? (
                    <p className="muted-copy">Typ błędu: {boardStageState.errorType}</p>
                  ) : null}
                  {boardStageState.httpStatus !== null ? (
                    <p className="muted-copy">HTTP status: {boardStageState.httpStatus}</p>
                  ) : null}
                </>
              ) : null}
              {boardStageState.kind === "success" ? (
                <img
                  className="uc04-image-preview"
                  src={toImageDataUrl(boardStageState.image)}
                  alt="Wynik etapu preprocess board"
                />
              ) : null}
            </article>
          </div>

          <article className="uc04-stage-card">
            <h3>Etap 2 — Siatka komórek 9x9</h3>
            {cellsStageState.kind === "loading" ? (
              <p className="status-banner status-loading">
                Dzielenie boarda na komórki...
              </p>
            ) : null}
            {cellsStageState.kind === "error" ? (
              <>
                <p className="status-banner status-error">{cellsStageState.error}</p>
                {cellsStageState.errorType ? (
                  <p className="muted-copy">Typ błędu: {cellsStageState.errorType}</p>
                ) : null}
                {cellsStageState.httpStatus !== null ? (
                  <p className="muted-copy">HTTP status: {cellsStageState.httpStatus}</p>
                ) : null}
              </>
            ) : null}
            {cellsStageState.kind === "success" ? (
              <div className="uc04-cells-grid">
                {cellsStageState.cells.cells.map((row, rowIndex) =>
                  row.map((cell, cellIndex) => (
                    <img
                      key={`${rowIndex}-${cellIndex}`}
                      className="uc04-cell-image"
                      src={toImageDataUrl(cell)}
                      alt={`Komórka ${rowIndex + 1}-${cellIndex + 1}`}
                    />
                  ))
                )}
              </div>
            ) : null}
          </article>
        </section>
      ) : null}

      <Uc06TrainingSection apiBaseUrl={apiBaseUrl} />

      <section className="result-card" aria-live="polite">
        <h2>Wynik</h2>

        {pingState.kind === "idle" ? (
          <p className="muted-copy">
            Kliknij przycisk, aby wywołać endpoint <code>{pingEndpoint}</code>.
          </p>
        ) : null}

        {pingState.kind === "loading" ? (
          <p className="status-banner status-loading">
            Wysyłanie żądania do backendu...
          </p>
        ) : null}

        {pingState.kind === "error" ? (
          <p className="status-banner status-error">{pingState.error}</p>
        ) : null}

        {pingState.kind === "success" ? (
          <p className="status-banner status-success">
            Połączenie FE - BE - ML działa poprawnie.
          </p>
        ) : null}

        {pingState.httpStatus !== null ? (
          <p className="muted-copy">HTTP status: {pingState.httpStatus}</p>
        ) : null}

        {pingState.response ? (
          <dl className="result-grid">
            <div>
              <dt>Status backendu</dt>
              <dd>{pingState.response.backendStatus}</dd>
            </div>
            <div>
              <dt>Status ML</dt>
              <dd>{pingState.response.mlStatus}</dd>
            </div>
            <div>
              <dt>Znacznik czasu UTC</dt>
              <dd>{formatTimestamp(pingState.response.timestampUtc)}</dd>
            </div>
            <div>
              <dt>Komunikat</dt>
              <dd>{pingState.response.message}</dd>
            </div>
          </dl>
        ) : null}
      </section>
    </main>
  );
}
