import { useCallback, useEffect, useMemo, useState } from "react";

import {
  getRawDatasetCandidates,
  RawDatasetCandidatesApiError,
} from "../api/datasetsRawCandidates";
import type { RawDatasetCandidateApiResponse } from "../types/api";

type LoadableState =
  | {
      kind: "idle";
      data: RawDatasetCandidateApiResponse[] | null;
      error: null;
      errorType: null;
      httpStatus: null;
    }
  | {
      kind: "loading";
      data: RawDatasetCandidateApiResponse[] | null;
      error: null;
      errorType: null;
      httpStatus: null;
    }
  | {
      kind: "success";
      data: RawDatasetCandidateApiResponse[];
      error: null;
      errorType: null;
      httpStatus: number;
    }
  | {
      kind: "error";
      data: RawDatasetCandidateApiResponse[] | null;
      error: string;
      errorType: string | null;
      httpStatus: number | null;
    };

const defaultState: LoadableState = {
  kind: "idle",
  data: null,
  error: null,
  errorType: null,
  httpStatus: null,
};

function resolveTypeLabel(type: string): string {
  if (type === "board") {
    return "Plansze sudoku";
  }

  if (type === "digit") {
    return "Zbior cyfr";
  }

  return "Nieznany typ";
}

type Uc11RawCandidatesSectionProps = {
  apiBaseUrl: string;
  accessToken?: string | null;
  onUnauthorized?: () => void;
};

export function Uc11RawCandidatesSection({
  apiBaseUrl,
  accessToken,
  onUnauthorized,
}: Uc11RawCandidatesSectionProps) {
  const [state, setState] = useState<LoadableState>(defaultState);

  const loadCandidates = useCallback(async () => {
    setState((previous) => ({
      kind: "loading",
      data: previous.data,
      error: null,
      errorType: null,
      httpStatus: null,
    }));

    try {
      const response = await getRawDatasetCandidates(apiBaseUrl, accessToken);
      setState({
        kind: "success",
        data: response,
        error: null,
        errorType: null,
        httpStatus: 200,
      });
    } catch (error) {
      if (error instanceof RawDatasetCandidatesApiError && error.status === 401) {
        onUnauthorized?.();
      }

      setState((previous) => ({
        kind: "error",
        data: previous.data,
        error:
          error instanceof Error
            ? error.message
            : "Nie udało się pobrać kandydatów datasetowych.",
        errorType:
          error instanceof RawDatasetCandidatesApiError
            ? error.errorType ?? null
            : null,
        httpStatus:
          error instanceof RawDatasetCandidatesApiError ? error.status : null,
      }));
    }
  }, [accessToken, apiBaseUrl, onUnauthorized]);

  useEffect(() => {
    void loadCandidates();
  }, [loadCandidates]);

  const candidates = state.data ?? [];
  const boardCount = useMemo(
    () => candidates.filter((item) => item.type === "board").length,
    [candidates]
  );
  const digitCount = useMemo(
    () => candidates.filter((item) => item.type === "digit").length,
    [candidates]
  );

  return (
    <section className="hero-card uc11-section">
      <p className="eyebrow">UC-11 — Surowe kandydaty datasetowe</p>
      <h2>Lista źródeł do dalszego przygotowania</h2>
      <p className="hero-copy">
        Widok przygotowuje dane wejściowe pod kolejny krok workflow datasetowego.
      </p>

      <div className="uc11-actions">
        <button
          className="secondary-button"
          type="button"
          disabled={state.kind === "loading"}
          onClick={() => void loadCandidates()}
        >
          {state.kind === "loading" ? "Odświeżanie..." : "Odśwież listę"}
        </button>
      </div>

      {state.kind === "loading" ? (
        <p className="status-banner status-loading">Pobieranie kandydatów z backendu...</p>
      ) : null}

      {state.kind === "error" ? (
        <>
          <p className="status-banner status-error">{state.error}</p>
          {state.httpStatus === 401 ? (
            <p className="muted-copy">
              Sesja administracyjna została wyczyszczona. Zaloguj się ponownie.
            </p>
          ) : null}
        </>
      ) : null}

      {state.kind === "success" ? (
        <>
          <p className="muted-copy">
            Wykryto {candidates.length} źródeł: board {boardCount}, digit {digitCount}.
          </p>
          {candidates.length === 0 ? (
            <p className="status-banner status-loading">
              Brak wykrytych datasetów w źródłach raw.
            </p>
          ) : (
            <>
              <p className="muted-copy">
                W UC-11 pokazujemy tylko podsumowanie kandydatow, aby nie dublowac tej samej listy.
                Szczegolowa lista z mozliwoscia zaznaczania zrodel jest dostepna w kroku UC-17.
              </p>
              <ul className="uc11-candidates-list">
                <li className="uc11-candidate-item">
                  <div>
                    <strong>Plansze sudoku</strong>
                    <p className="muted-copy">Typ: <code>board</code></p>
                  </div>
                  <span className="uc11-type-badge is-board">
                    {resolveTypeLabel("board")} ({boardCount})
                  </span>
                </li>
                <li className="uc11-candidate-item">
                  <div>
                    <strong>Zbiory cyfr</strong>
                    <p className="muted-copy">Typ: <code>digit</code></p>
                  </div>
                  <span className="uc11-type-badge is-digit">
                    {resolveTypeLabel("digit")} ({digitCount})
                  </span>
                </li>
              </ul>
            </>
          )}
        </>
      ) : null}
    </section>
  );
}
