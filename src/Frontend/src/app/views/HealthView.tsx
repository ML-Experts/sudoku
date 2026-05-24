import type { PingState } from "../state";
import { formatTimestamp } from "../utils";

type HealthViewProps = {
  apiBaseUrl: string;
  onPing: () => void;
  pingState: PingState;
};

export function HealthView({ apiBaseUrl, onPing, pingState }: HealthViewProps) {
  const pingEndpoint = `${apiBaseUrl}/ping`;

  return (
    <>
      <section className="hero-card">
        <p className="eyebrow">UC-00 - Smoke test FE / BE / ML</p>
        <h1>Sudoku Vision</h1>
        <p className="hero-copy">
          Ten ekran sluzy do szybkiego sprawdzenia, czy frontend moze wywolac
          backend, a backend ma polaczenie z serwisem ML.
        </p>

        <div className="configuration-card">
          <span className="configuration-label">Baza API</span>
          <code>{apiBaseUrl}</code>
        </div>

        <button
          className="primary-button"
          onClick={onPing}
          disabled={pingState.kind === "loading"}
          type="button"
        >
          {pingState.kind === "loading"
            ? "Trwa testowanie polaczenia..."
            : "Test polaczenia"}
        </button>
      </section>

      <section className="result-card" aria-live="polite">
        <h2>Wynik</h2>

        {pingState.kind === "idle" ? (
          <p className="muted-copy">
            Kliknij przycisk, aby wywolac endpoint <code>{pingEndpoint}</code>.
          </p>
        ) : null}

        {pingState.kind === "loading" ? (
          <p className="status-banner status-loading">
            Wysylanie zadania do backendu...
          </p>
        ) : null}

        {pingState.kind === "error" ? (
          <p className="status-banner status-error">{pingState.error}</p>
        ) : null}

        {pingState.kind === "success" ? (
          <p className="status-banner status-success">
            Polaczenie FE - BE - ML dziala poprawnie.
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
    </>
  );
}
