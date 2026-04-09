import { useRef, useState } from "react";

import { ExampleUploadApiError, postExampleUpload } from "./api/examples";
import type { ExampleFileApiResponse } from "./types/api";

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

function formatBytes(sizeBytes: number): string {
  if (!Number.isFinite(sizeBytes) || sizeBytes < 0) {
    return String(sizeBytes);
  }

  if (sizeBytes < 1024) {
    return `${sizeBytes} B`;
  }

  const units = ["KiB", "MiB", "GiB"];
  let value = sizeBytes / 1024;
  let unitIndex = 0;

  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }

  return `${value < 10 ? value.toFixed(1) : Math.round(value)} ${units[unitIndex]}`;
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
      </section>

      <section className="result-card" aria-live="polite">
        <h2>Wynik (UC-00)</h2>

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

      <section className="result-card" aria-live="polite">
        <h2>Wynik uploadu (UC-01)</h2>

        {uploadState.kind === "idle" ? (
          <p className="muted-copy">
            Wybierz plik JPG lub PNG i wyślij go na backend.
          </p>
        ) : null}

        {uploadState.kind === "loading" ? (
          <p className="status-banner status-loading">Wysyłanie pliku...</p>
        ) : null}

        {uploadState.kind === "error" ? (
          <>
            <p className="status-banner status-error">{uploadState.error}</p>
            {uploadState.errorType ? (
              <p className="muted-copy">Typ błędu: {uploadState.errorType}</p>
            ) : null}
            {uploadState.httpStatus !== null ? (
              <p className="muted-copy">HTTP status: {uploadState.httpStatus}</p>
            ) : null}
          </>
        ) : null}

        {uploadState.kind === "success" ? (
          <>
            <p className="status-banner status-success">
              Plik zapisany w bibliotece przykładów (201 Created).
            </p>
            <p className="muted-copy">HTTP status: {uploadState.httpStatus}</p>
            <dl className="result-grid">
              <div>
                <dt>Nazwa (BE)</dt>
                <dd>{uploadState.response.name}</dd>
              </div>
              <div>
                <dt>Typ zawartości</dt>
                <dd>{uploadState.response.contentType}</dd>
              </div>
              <div>
                <dt>Rozmiar</dt>
                <dd>{formatBytes(uploadState.response.sizeBytes)}</dd>
              </div>
              <div>
                <dt>Zapisano (UTC)</dt>
                <dd>{formatTimestamp(uploadState.response.storedAtUtc)}</dd>
              </div>
            </dl>
          </>
        ) : null}

        {sessionExamples.length > 0 ? (
          <>
            <h3 className="muted-copy examples-session-heading">
              Przykłady dodane w tej sesji ({sessionExamples.length})
            </h3>
            <ul className="examples-list">
              {sessionExamples.map((item) => (
                <li key={`${item.name}-${item.storedAtUtc}`}>
                  <code>{item.name}</code>
                  {" · "}
                  {formatBytes(item.sizeBytes)}
                  {" · "}
                  {item.contentType}
                </li>
              ))}
            </ul>
          </>
        ) : null}
      </section>
    </main>
  );
}
