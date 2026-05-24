import type { RefObject } from "react";

import { Uc05WorkflowSection } from "../../features/uc05/api";
import { toImageDataUrl } from "../../shared/images/toImageDataUrl";
import type { ExampleFileApiResponse } from "../../types/api";
import type {
  CellsStageState,
  ExamplesListState,
  ImageStageState,
} from "../state";
import { formatBytes, formatTimestamp } from "../utils";

type ExamplesViewProps = {
  apiBaseUrl: string;
  boardStageState: ImageStageState;
  canSubmitUpload: boolean;
  cellsStageState: CellsStageState;
  downloadingName: string | null;
  examplesListData:
    | {
        items: Array<{
          name: string;
          contentType: string;
          sizeBytes: number;
          storedAtUtc: string;
        }>;
        totalCount: number;
      }
    | null;
  examplesListState: ExamplesListState;
  examplesUploadEndpoint: string;
  fileInputRef: RefObject<HTMLInputElement>;
  isAdminMode: boolean;
  isUploadBusy: boolean;
  onDownload: (fileName: string) => void;
  onLoadExamples: () => void;
  onRunUpload: () => void;
  onSelectedFileChange: (file: File | null) => void;
  onSelectProcessName: (value: string | null) => void;
  previewStageState: ImageStageState;
  runUc04Flow: (fileName: string) => void;
  selectedProcessName: string | null;
  sessionExamples: ExampleFileApiResponse[];
};

export function ExamplesView({
  apiBaseUrl,
  boardStageState,
  canSubmitUpload,
  cellsStageState,
  downloadingName,
  examplesListData,
  examplesListState,
  examplesUploadEndpoint,
  fileInputRef,
  isAdminMode,
  isUploadBusy,
  onDownload,
  onLoadExamples,
  onRunUpload,
  onSelectedFileChange,
  onSelectProcessName,
  previewStageState,
  runUc04Flow,
  selectedProcessName,
  sessionExamples,
}: ExamplesViewProps) {
  return (
    <>
      <section className="hero-card upload-section">
        <p className="eyebrow">UC-01 — Upload przykladu</p>
        <h2>Dodaj plik do biblioteki przykladow</h2>
        <p className="hero-copy">
          Wyslij obraz sudoku na endpoint <code>{examplesUploadEndpoint}</code> (
          <code>multipart/form-data</code>, pole <code>file</code>). Kanoniczna
          nazwe pliku nadaje backend.
        </p>
        {!isAdminMode ? (
          <p className="status-banner status-loading">
            Upload jest dostepny tylko po zalogowaniu do trybu administracyjnego.
          </p>
        ) : null}

        <div className="upload-controls">
          <input
            ref={fileInputRef}
            className="file-picker"
            type="file"
            accept="image/jpeg,image/png,.jpg,.jpeg,.png"
            disabled={isUploadBusy || !isAdminMode}
            aria-busy={isUploadBusy}
            onChange={(event) => onSelectedFileChange(event.target.files?.[0] ?? null)}
          />
          <button
            className="primary-button"
            type="button"
            disabled={!canSubmitUpload}
            onClick={onRunUpload}
          >
            {isUploadBusy
              ? "Wysylanie..."
              : isAdminMode
                ? "Wyslij plik"
                : "Wymagane logowanie"}
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
        <p className="eyebrow">UC-02 — Lista przykladow</p>
        <h2>Biblioteka przykladow Sudoku</h2>
        <p className="hero-copy">
          Zrodlo: <code>{`${apiBaseUrl}/examples`}</code> (<code>GET</code>). Akcja
          "Pobierz" uzywa podgladu <code>GET /examples/{"{name}"}</code> (JSON +
          base64), dopoki backend nie udostepni surowego <code>/download</code>{" "}
          (UC-03).
        </p>

        <div className="examples-toolbar">
          <button
            className="primary-button"
            type="button"
            disabled={examplesListState.kind === "loading"}
            onClick={onLoadExamples}
          >
            {examplesListState.kind === "loading"
              ? "Ladowanie listy..."
              : "Odswiez liste"}
          </button>
          {examplesListState.kind === "success" ? (
            <span className="muted-copy examples-total">
              Lacznie: {examplesListState.data.totalCount}
            </span>
          ) : null}
        </div>

        {examplesListState.kind === "error" ? (
          <>
            <p className="status-banner status-error">{examplesListState.error}</p>
            {examplesListState.errorType ? (
              <p className="muted-copy">
                Typ bledu: {examplesListState.errorType}
              </p>
            ) : null}
            {examplesListState.httpStatus !== null ? (
              <p className="muted-copy">
                HTTP status: {examplesListState.httpStatus}
              </p>
            ) : null}
          </>
        ) : null}

        {examplesListData && examplesListData.items.length === 0 ? (
          <p className="muted-copy">Brak plikow w bibliotece przykladow.</p>
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
                          onClick={() => onDownload(item.name)}
                        >
                          {downloadingName === item.name ? "Pobieranie..." : "Pobierz"}
                        </button>
                        <button
                          className="secondary-button"
                          type="button"
                          onClick={() => onSelectProcessName(item.name)}
                        >
                          Przetworz
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
        <>
          <section className="result-card uc04-flow-section" aria-live="polite">
            <p className="eyebrow">UC-04 — Przetwarzanie przykladu</p>
            <h2>Pipeline preprocessingu</h2>
            <p className="muted-copy">
              Wybrany plik: <code>{selectedProcessName}</code>
            </p>

            <div className="examples-row-actions">
              <button
                className="secondary-button"
                type="button"
                onClick={() => runUc04Flow(selectedProcessName)}
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
                onClick={() => onSelectProcessName(null)}
              >
                Wyczysc wybor
              </button>
            </div>

            <div className="uc04-stage-grid">
              <article className="uc04-stage-card">
                <h3>Etap 0 — Podglad wejscia</h3>
                <StageImageCard
                  imageState={previewStageState}
                  loadingLabel="Pobieranie obrazu wejsciowego..."
                  alt={`Podglad ${selectedProcessName}`}
                />
              </article>

              <article className="uc04-stage-card">
                <h3>Etap 1 — Preprocess board</h3>
                <StageImageCard
                  imageState={boardStageState}
                  loadingLabel="Przetwarzanie boarda..."
                  alt="Wynik etapu preprocess board"
                />
              </article>
            </div>

            <article className="uc04-stage-card">
              <h3>Etap 2 — Siatka komorek 9x9</h3>
              {cellsStageState.kind === "loading" ? (
                <p className="status-banner status-loading">
                  Dzielenie boarda na komorki...
                </p>
              ) : null}
              {cellsStageState.kind === "error" ? (
                <>
                  <p className="status-banner status-error">{cellsStageState.error}</p>
                  {cellsStageState.errorType ? (
                    <p className="muted-copy">
                      Typ bledu: {cellsStageState.errorType}
                    </p>
                  ) : null}
                  {cellsStageState.httpStatus !== null ? (
                    <p className="muted-copy">
                      HTTP status: {cellsStageState.httpStatus}
                    </p>
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
                        alt={`Komorka ${rowIndex + 1}-${cellIndex + 1}`}
                      />
                    )),
                  )}
                </div>
              ) : null}
            </article>
          </section>

          <Uc05WorkflowSection
            apiBaseUrl={apiBaseUrl}
            cellsGrid={cellsStageState.kind === "success" ? cellsStageState.cells : null}
            selectedProcessName={selectedProcessName}
          />
        </>
      ) : null}
    </>
  );
}

type StageImageCardProps = {
  alt: string;
  imageState: ImageStageState;
  loadingLabel: string;
};

function StageImageCard({ alt, imageState, loadingLabel }: StageImageCardProps) {
  return (
    <>
      {imageState.kind === "loading" ? (
        <p className="status-banner status-loading">{loadingLabel}</p>
      ) : null}
      {imageState.kind === "error" ? (
        <>
          <p className="status-banner status-error">{imageState.error}</p>
          {imageState.errorType ? (
            <p className="muted-copy">Typ bledu: {imageState.errorType}</p>
          ) : null}
          {imageState.httpStatus !== null ? (
            <p className="muted-copy">HTTP status: {imageState.httpStatus}</p>
          ) : null}
        </>
      ) : null}
      {imageState.kind === "success" ? (
        <img className="uc04-image-preview" src={toImageDataUrl(imageState.image)} alt={alt} />
      ) : null}
    </>
  );
}
