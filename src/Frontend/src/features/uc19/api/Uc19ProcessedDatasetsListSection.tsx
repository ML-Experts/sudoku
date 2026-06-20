import type { ProcessedDatasetListItemApiResponse } from "../../../types/api";
import type { Uc19ProcessedDatasetHighlightedItem } from "../domain/resolveUc19ProcessedDatasetHighlight";

type Uc19ProcessedDatasetsListSectionProps = {
  status: "idle" | "loading" | "success" | "error";
  items: Uc19ProcessedDatasetHighlightedItem[];
  totalCount: number;
  error: string | null;
  httpStatus: number | null;
  typedDatasetName: string;
  collisionItem: ProcessedDatasetListItemApiResponse | null;
  syncWarning: string | null;
  onRefresh: () => Promise<void>;
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

export function Uc19ProcessedDatasetsListSection({
  status,
  items,
  totalCount,
  error,
  httpStatus,
  typedDatasetName,
  collisionItem,
  syncWarning,
  onRefresh,
}: Uc19ProcessedDatasetsListSectionProps) {
  const normalizedTypedDatasetName = typedDatasetName.trim();
  const shouldRenderList = items.length > 0;

  return (
    <article className="uc17-panel">
      <div className="uc17-panel-header">
        <div>
          <h3>Krok 6 - Katalog gotowych datasetow</h3>
          <p className="muted-copy">
            Ten panel korzysta z <code>GET /api/datasets/processed</code> jako
            pomocniczego katalogu tylko do odczytu przed budowa datasetu i do
            weryfikacji po sukcesie{" "}
            <code>POST /api/datasets/processed</code>.
          </p>
        </div>
        <button
          className="secondary-button"
          type="button"
          onClick={() => void onRefresh()}
          disabled={status === "loading"}
        >
          {status === "loading" ? "Odswiezanie..." : "Odswiez liste datasetow"}
        </button>
      </div>

      <div className="uc18-summary">
        <span className="uc17-stat-chip">Liczba rekordow: {totalCount}</span>
        <span className="uc17-stat-chip">
          Aktualna nazwa: {normalizedTypedDatasetName ? <code>{normalizedTypedDatasetName}</code> : "brak"}
        </span>
      </div>

      {status === "idle" ? (
        <p className="muted-copy">
          Lista pojawi sie tutaj po uzyskaniu sesji administracyjnej.
        </p>
      ) : null}

      {status === "loading" ? (
        <p className="status-banner status-loading">
          Odczytywanie katalogu gotowych datasetow...
        </p>
      ) : null}

      {error ? (
        <>
          <p className="status-banner status-error">{error}</p>
          {httpStatus === 401 ? (
            <p className="muted-copy">
              Sesja administracyjna zostala wyczyszczona. Zaloguj sie ponownie.
            </p>
          ) : null}
        </>
      ) : null}

      {syncWarning ? <p className="status-banner status-loading">{syncWarning}</p> : null}

      {collisionItem ? (
        <p className="status-banner status-loading">
          Nazwa <code>{normalizedTypedDatasetName}</code> prawdopodobnie juz istnieje w
          katalogu jako <code>{collisionItem.fileName}</code>. To tylko hint UX - finalna
          walidacja nalezy do backendu.
        </p>
      ) : null}

      {status === "success" && totalCount === 0 ? (
        <p className="muted-copy">Brak gotowych datasetow w systemie.</p>
      ) : null}

      {shouldRenderList ? (
        <ul className="uc19-processed-datasets-list">
          {items.map((item) => (
            <li
              key={`${item.name}:${item.createdAtUtc}`}
              className={`uc19-processed-dataset-card ${
                item.isFreshlyCreated ? "is-freshly-created" : ""
              } ${item.isMatchingTypedName ? "is-name-match" : ""}`}
            >
              <div className="uc19-processed-dataset-header">
                <div className="uc19-processed-dataset-copy">
                  <strong>{item.fileName}</strong>
                  <p className="muted-copy">
                    Nazwa rekordu: <code>{item.name}</code>
                  </p>
                  <p className="muted-copy">
                    Profil preprocessingu: <code>{item.preprocessingProfile}</code>
                  </p>
                  <p className="muted-copy">
                    Utworzono: {formatTimestamp(item.createdAtUtc)}
                  </p>
                </div>
                <div className="uc19-processed-dataset-badges">
                  {item.isFreshlyCreated ? (
                    <span className="uc19-processed-flag is-freshly-created">
                      Nowo potwierdzony rekord
                    </span>
                  ) : null}
                  {item.isMatchingTypedName ? (
                    <span className="uc19-processed-flag is-name-match">
                      Pasuje do wpisanej nazwy
                    </span>
                  ) : null}
                </div>
              </div>

              <div className="uc19-processed-sample-counts">
                <span className="uc19-sample-count-badge">
                  train: {item.sampleCounts.train}
                </span>
                <span className="uc19-sample-count-badge">val: {item.sampleCounts.val}</span>
                <span className="uc19-sample-count-badge">test: {item.sampleCounts.test}</span>
              </div>
            </li>
          ))}
        </ul>
      ) : null}
    </article>
  );
}
