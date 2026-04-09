import { useState } from "react";

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

const defaultState: PingState = {
  kind: "idle",
  response: null,
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

export default function App() {
  const apiBaseUrl = normalizeBaseUrl(import.meta.env.VITE_API_BASE_URL);
  const pingEndpoint = `${apiBaseUrl}/ping`;
  const [pingState, setPingState] = useState<PingState>(defaultState);

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
