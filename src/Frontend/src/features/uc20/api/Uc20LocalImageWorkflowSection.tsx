import { toImageDataUrl } from "../../../shared/images/toImageDataUrl";
import {
  MAX_LOCAL_IMAGE_SIZE_BYTES,
  UC20_LOCAL_IMAGE_INPUT_ACCEPT,
} from "../domain/validateUc20LocalImageFile";
import type { UseUc20LocalImageFlowResult } from "../application/useUc20LocalImageFlow";

type Uc20LocalImageWorkflowSectionProps = {
  flow: UseUc20LocalImageFlowResult;
};

export function Uc20LocalImageWorkflowSection({
  flow,
}: Uc20LocalImageWorkflowSectionProps) {
  const selectedDraft = flow.draftState.selectedDraft;
  const maxLocalImageSizeMb = MAX_LOCAL_IMAGE_SIZE_BYTES / (1024 * 1024);

  return (
    <section className="hero-card uc20-local-section" aria-live="polite">
      <p className="eyebrow">UC-20 — Lokalny obraz bez zapisu</p>
      <h2>Przetworz obraz Sudoku z komputera</h2>
      <p className="hero-copy">
        Wybierz lokalny plik, przygotuj payload <code>ImageApiEntry</code> w
        przegladarce i uruchom preprocessing przez{" "}
        <code>PUT /api/examples/preprocess/board</code> bez dodawania obrazu do
        biblioteki przykladow.
      </p>
      <p className="muted-copy uc20-local-support-copy">
        Dozwolone typy: JPG, JPEG, PNG. Maksymalny rozmiar lokalny:{" "}
        {maxLocalImageSizeMb} MB.
      </p>

      <div className="upload-controls">
        <input
          className="file-picker"
          type="file"
          accept={UC20_LOCAL_IMAGE_INPUT_ACCEPT}
          disabled={flow.isFlowBusy}
          aria-busy={flow.isFlowBusy}
          onClick={(event) => {
            event.currentTarget.value = "";
          }}
          onChange={(event) =>
            void flow.handleSelectedLocalFileChange(event.target.files?.[0] ?? null)
          }
        />
      </div>

      {flow.draftState.validationError ? (
        <p className="status-banner status-error">
          {flow.draftState.validationError}
        </p>
      ) : null}

      {flow.draftState.isReading ? (
        <p className="status-banner status-loading">
          Przygotowywanie lokalnego obrazu do preprocessingu...
        </p>
      ) : null}

      {selectedDraft ? (
        <>
          <div className="uc20-local-selected-summary">
            <span>
              Aktywny obraz: <code>{selectedDraft.fileName}</code>
            </span>
            <span>{selectedDraft.mimeType}</span>
            <span>{(selectedDraft.sizeBytes / (1024 * 1024)).toFixed(2)} MB</span>
          </div>

          <div className="examples-row-actions">
            <button
              className="primary-button"
              type="button"
              disabled={!flow.canRunFlow}
              onClick={() => void flow.handleRunUc20Flow()}
            >
              {flow.isFlowBusy ? "Przetwarzanie..." : "Uruchom"}
            </button>
            <button
              className="secondary-button"
              type="button"
              disabled={!flow.canRetryFlow}
              onClick={() => void flow.handleRunUc20Flow()}
            >
              Uruchom ponownie
            </button>
            <button
              className="secondary-button"
              type="button"
              disabled={flow.isFlowBusy}
              onClick={flow.resetUc20Flow}
            >
              Wyczysc wybor
            </button>
          </div>

          <div className="uc04-stage-grid">
            <article className="uc04-stage-card">
              <h3>Etap 0 — Podglad lokalnego obrazu</h3>
              <img
                className="uc04-image-preview"
                src={selectedDraft.previewUrl}
                alt={`Lokalny podglad ${selectedDraft.fileName}`}
              />
            </article>

            <article className="uc04-stage-card">
              <h3>Etap 1 — Preprocess board</h3>
              <Uc20StageImageCard
                imageState={flow.boardStageState}
                loadingLabel="Przetwarzanie boarda..."
                alt={`Wynik board dla ${selectedDraft.fileName}`}
              />
            </article>
          </div>

          <article className="uc04-stage-card">
            <h3>Etap 2 — Siatka komorek 9x9</h3>
            {flow.cellsStageState.kind === "loading" ? (
              <p className="status-banner status-loading">
                Dzielenie boarda na komorki...
              </p>
            ) : null}
            {flow.cellsStageState.kind === "error" ? (
              <>
                <p className="status-banner status-error">
                  {flow.cellsStageState.error}
                </p>
                {flow.cellsStageState.errorType ? (
                  <p className="muted-copy">
                    Typ bledu: {flow.cellsStageState.errorType}
                  </p>
                ) : null}
                {flow.cellsStageState.httpStatus !== null ? (
                  <p className="muted-copy">
                    HTTP status: {flow.cellsStageState.httpStatus}
                  </p>
                ) : null}
              </>
            ) : null}
            {flow.cellsStageState.kind === "success" ? (
              <div className="uc04-cells-grid">
                {flow.cellsStageState.cells.cells.map((row, rowIndex) =>
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
        </>
      ) : null}
    </section>
  );
}

type Uc20StageImageCardProps = {
  alt: string;
  imageState: UseUc20LocalImageFlowResult["boardStageState"];
  loadingLabel: string;
};

function Uc20StageImageCard({
  alt,
  imageState,
  loadingLabel,
}: Uc20StageImageCardProps) {
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
        <img
          className="uc04-image-preview"
          src={toImageDataUrl(imageState.image)}
          alt={alt}
        />
      ) : null}
    </>
  );
}
