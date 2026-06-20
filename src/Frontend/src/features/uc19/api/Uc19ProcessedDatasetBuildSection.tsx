import type {
  CreateProcessedDatasetApiEntry,
  ProcessedDatasetApiResponse,
  SelectedPreparedDatasetSourceApiEntry,
} from "../../../types/api";

type Uc19ProcessedDatasetBuildSectionProps = {
  selectedPreparationName: string | null;
  canContinueToSources: boolean;
  datasetName: string;
  onDatasetNameChange: (value: string) => void;
  selectedBoardCount: number;
  selectedDigitCount: number;
  requestPreview: CreateProcessedDatasetApiEntry | null;
  formError: string | null;
  createState:
    | {
        kind: "idle" | "loading";
        response: ProcessedDatasetApiResponse | null;
        error: null;
        errorType: null;
        httpStatus: null;
      }
    | {
        kind: "success";
        response: ProcessedDatasetApiResponse;
        error: null;
        errorType: null;
        httpStatus: number;
      }
    | {
        kind: "error";
        response: ProcessedDatasetApiResponse | null;
        error: string;
        errorType: string | null;
        httpStatus: number | null;
      };
  createStatusHint: string | null;
  onSubmit: () => Promise<ProcessedDatasetApiResponse | null>;
};

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

function renderSourceSummary(source: SelectedPreparedDatasetSourceApiEntry): string {
  return source.splits.length > 0 ? source.splits.join(", ") : "brak splitow";
}

export function Uc19ProcessedDatasetBuildSection({
  selectedPreparationName,
  canContinueToSources,
  datasetName,
  onDatasetNameChange,
  selectedBoardCount,
  selectedDigitCount,
  requestPreview,
  formError,
  createState,
  createStatusHint,
  onSubmit,
}: Uc19ProcessedDatasetBuildSectionProps) {
  const totalSelectedCount = selectedBoardCount + selectedDigitCount;
  const latestResponse =
    createState.kind === "success" ? createState.response : createState.response;

  return (
    <article className="uc17-panel">
      <div className="uc17-panel-header">
        <div>
          <h3>Krok 5 - Build finalnego datasetu `.npz`</h3>
          <p className="muted-copy">
            Ten krok sklada payload <code>CreateProcessedDatasetApiEntry</code> na
            podstawie wybranego <code>preparation</code> i zaznaczonych zrodel{" "}
            <code>board</code> oraz <code>digit</code>.
          </p>
        </div>
      </div>

      <div className="uc19-build-summary">
        <span className="uc17-stat-chip">
          Preparation:{" "}
          {selectedPreparationName ? <code>{selectedPreparationName}</code> : "brak"}
        </span>
        <span className="uc17-stat-chip">Wybrane board: {selectedBoardCount}</span>
        <span className="uc17-stat-chip">Wybrane digit: {selectedDigitCount}</span>
        <span className="uc17-stat-chip">Lacznie zrodel: {totalSelectedCount}</span>
      </div>

      {!selectedPreparationName ? (
        <p className="muted-copy">
          Najpierw wybierz preparation, aby zbudowac finalny dataset.
        </p>
      ) : null}

      {selectedPreparationName && !canContinueToSources ? (
        <p className="status-banner status-loading">
          Build pozostaje zablokowany do czasu potwierdzenia gotowosci wybranego
          preparation.
        </p>
      ) : null}

      <label className="uc12-field">
        <span>Nazwa finalnego datasetu (bez `.npz`)</span>
        <input
          value={datasetName}
          onChange={(event) => onDatasetNameChange(event.target.value)}
          placeholder="np. digits-dataset-v2"
          aria-invalid={formError ? "true" : "false"}
        />
      </label>

      {requestPreview?.sources.length ? (
        <div className="uc19-selected-sources">
          <strong>Wybrane zrodla</strong>
          <ul className="uc12-warnings-list">
            {requestPreview.sources.map((source) => (
              <li key={`${source.type}:${source.name}`}>
                <code>{source.name}</code> ({source.type}) - splity:{" "}
                <code>{renderSourceSummary(source)}</code>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p className="muted-copy">
          Zaznacz przynajmniej jedno zrodlo `board` lub `digit`, aby zbudowac request.
        </p>
      )}

      <div className="uc19-request-preview">
        <strong>Preview requestu</strong>
        <pre className="uc06-json-preview">
          {JSON.stringify(
            requestPreview ?? {
              preparationName: selectedPreparationName ?? "",
              name: datasetName.trim(),
              sources: [],
            },
            null,
            2,
          )}
        </pre>
      </div>

      {formError ? <p className="status-banner status-error">{formError}</p> : null}

      <button
        className="primary-button"
        type="button"
        onClick={() => void onSubmit()}
        disabled={createState.kind === "loading"}
      >
        {createState.kind === "loading"
          ? "Budowanie datasetu..."
          : "Buduj dataset .npz"}
      </button>

      {createState.kind === "error" ? (
        <>
          <p className="status-banner status-error">{createState.error}</p>
          {createStatusHint ? <p className="muted-copy">{createStatusHint}</p> : null}
        </>
      ) : null}

      {createState.kind === "success" ? (
        <div className="uc19-build-result">
          <p className="status-banner status-success">
            Dataset <code>{createState.response.fileName}</code> zostal utworzony.
          </p>
          <p className="muted-copy">
            Profil: <code>{createState.response.preprocessingProfile}</code> | Utworzono:{" "}
            {formatTimestamp(createState.response.createdAtUtc)}
          </p>
          <p className="muted-copy">
            Sample counts: train {createState.response.sampleCounts.train}, val{" "}
            {createState.response.sampleCounts.val}, test{" "}
            {createState.response.sampleCounts.test}
          </p>

          <div className="uc19-source-reports">
            {createState.response.sourceReports.map((report) => (
              <div
                key={`${report.type}-${report.name}`}
                className="uc19-source-report-card"
              >
                <p>
                  <strong>{report.name}</strong> ({report.type})
                </p>
                <p className="muted-copy">
                  processed: {report.processedSampleCount}, included:{" "}
                  {report.includedSampleCount}, empty: {report.emptyCellCount}, rejected:{" "}
                  {report.rejectedSampleCount}
                </p>
                {report.warnings.length > 0 ? (
                  <ul className="uc12-warnings-list">
                    {report.warnings.map((warning, index) => (
                      <li key={`${report.type}-${report.name}-warning-${index}`}>
                        {warning}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="muted-copy">Brak ostrzezen dla tego zrodla.</p>
                )}
              </div>
            ))}
          </div>

          {createState.response.warnings.length > 0 ? (
            <div className="uc19-global-warnings">
              <strong>Ostrzezenia globalne</strong>
              <ul className="uc12-warnings-list">
                {createState.response.warnings.map((warning, index) => (
                  <li key={`uc19-global-warning-${index}`}>{warning}</li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="muted-copy">Brak globalnych ostrzezen po buildzie.</p>
          )}
        </div>
      ) : latestResponse ? (
        <p className="muted-copy">
          Ostatni poprawny build: <code>{latestResponse.fileName}</code>.
        </p>
      ) : null}
    </article>
  );
}
