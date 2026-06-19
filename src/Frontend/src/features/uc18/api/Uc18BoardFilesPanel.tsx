import type { UseUc18BoardFilesResult } from "../application/uc18BoardFilesTypes";
import { useUc18DeleteBoardFile } from "../application/useUc18DeleteBoardFile";
import { Uc18BoardFileDeleteAction } from "./Uc18BoardFileDeleteAction";
import { Uc18BoardImagePreview } from "./Uc18BoardImagePreview";

type Uc18BoardFilesPanelProps = {
  apiBaseUrl: string;
  preparationName: string | null;
  selectedSourceName: string | null;
  boardFiles: UseUc18BoardFilesResult;
  accessToken?: string | null;
  onUnauthorized?: () => void;
};

export function Uc18BoardFilesPanel({
  apiBaseUrl,
  preparationName,
  selectedSourceName,
  boardFiles,
  accessToken,
  onUnauthorized,
}: Uc18BoardFilesPanelProps) {
  const currentPreparationName = boardFiles.preparationName ?? preparationName;
  const currentSourceName = boardFiles.sourceName ?? selectedSourceName;
  const deleteBoardFile = useUc18DeleteBoardFile({
    apiBaseUrl,
    preparationName: currentPreparationName,
    sourceName: currentSourceName,
    page: boardFiles.page,
    pageSize: boardFiles.pageSize,
    accessToken,
    onUnauthorized,
    loadBoardFiles: boardFiles.loadBoardFiles,
  });
  const shouldRenderItems =
    (boardFiles.status === "success" ||
      boardFiles.status === "loading" ||
      boardFiles.status === "error") &&
    boardFiles.items.length > 0;

  return (
    <article className="uc17-panel">
      <div className="uc17-panel-header">
        <div>
          <h3>Krok 4 - Plansze `board` dla wybranego zrodla</h3>
          <p className="muted-copy">
            Ten panel pobiera paginowana liste logicznych plansz dla jednego zrodla
            `board`. Renderuje nazwy folderow oraz izolowany preview obrazu per karta bez
            budowania URL-i po stronie klienta.
          </p>
        </div>
        <button
          className="secondary-button"
          type="button"
          onClick={() => void boardFiles.retryLoadBoardFiles()}
          disabled={
            !preparationName ||
            !selectedSourceName ||
            boardFiles.status === "loading" ||
            deleteBoardFile.isDeleting
          }
        >
          {boardFiles.status === "loading"
            ? "Odswiezanie..."
            : "Odswiez liste plansz"}
        </button>
      </div>

      {!preparationName ? (
        <p className="muted-copy">
          Najpierw wybierz preparation, aby przejsc do listy plansz `board`.
        </p>
      ) : null}

      {preparationName && !selectedSourceName ? (
        <p className="muted-copy">
          Wybierz zrodlo `board` w poprzednim kroku. Dopiero wtedy frontend pobierze
          paginowana liste plansz.
        </p>
      ) : null}

      {boardFiles.status === "loading" && currentPreparationName && currentSourceName ? (
        <p className="status-banner status-loading">
          Pobieranie plansz `board` dla source <code>{currentSourceName}</code> z
          preparation <code>{currentPreparationName}</code> (strona {boardFiles.page})...
        </p>
      ) : null}

      {boardFiles.status === "error" ? (
        <>
          <p className="status-banner status-error">{boardFiles.error}</p>
          {boardFiles.httpStatus === 401 ? (
            <p className="muted-copy">
              Sesja administracyjna zostala wyczyszczona. Zaloguj sie ponownie.
            </p>
          ) : null}
          {boardFiles.httpStatus === 404 ? (
            <p className="muted-copy">
              Wybrane preparation albo source `board` nie jest juz dostepne. Wroc do
              poprzedniego kroku i wybierz zrodlo ponownie.
            </p>
          ) : null}
          {boardFiles.httpStatus === 400 ? (
            <p className="muted-copy">
              Backend odrzucil parametry paginacji albo kontraktu dla tej listy. Mozesz
              sprobowac ponownie po odswiezeniu.
            </p>
          ) : null}
          {boardFiles.httpStatus !== null && boardFiles.httpStatus >= 500 ? (
            <p className="muted-copy">
              Backend zwrocil blad techniczny. Jesli lista byla juz wczytana dla tego
              zrodla, ostatni poprawny wynik zostal zachowany.
            </p>
          ) : null}
        </>
      ) : null}

      {deleteBoardFile.status === "success" && deleteBoardFile.boardFolderName ? (
        <p className="status-banner status-success">
          Usunieto <code>{deleteBoardFile.boardFolderName}</code>. Lista plansz zostala
          odswiezona. Pozostalo rekordow: {deleteBoardFile.remainingItemsCount ?? "?"}.
        </p>
      ) : null}

      {deleteBoardFile.status === "error" &&
      deleteBoardFile.httpStatus !== 404 &&
      deleteBoardFile.error ? (
        <p className="status-banner status-error">{deleteBoardFile.error}</p>
      ) : null}

      {currentPreparationName && currentSourceName ? (
        <div className="uc18-summary">
          <span className="uc17-stat-chip">
            Preparation: <code>{currentPreparationName}</code>
          </span>
          <span className="uc17-stat-chip">
            Source: <code>{currentSourceName}</code>
          </span>
          <span className="uc17-stat-chip">Strona: {boardFiles.page}</span>
          <span className="uc17-stat-chip">Page size: {boardFiles.pageSize}</span>
          <span className="uc17-stat-chip">Liczba plansz: {boardFiles.totalCount}</span>
        </div>
      ) : null}

      {boardFiles.status === "success" && boardFiles.totalCount === 0 && currentSourceName ? (
        <p className="status-banner status-loading">
          To zrodlo `board` nie zawiera jeszcze zadnych plansz.
        </p>
      ) : null}

      {shouldRenderItems ? (
        <>
          <ul className="uc18-board-files-list">
            {boardFiles.items.map((item) => {
              const isDeletingCurrentItem =
                deleteBoardFile.deletingBoardFileKey === item.key &&
                deleteBoardFile.isDeleting;
              const isDeleteActionDisabled =
                deleteBoardFile.isDeleting || boardFiles.status === "loading";
              const deleteErrorForCurrentItem =
                deleteBoardFile.deletingBoardFileKey === item.key
                  ? deleteBoardFile.error
                  : null;

              return (
                <li key={item.key} className="uc18-board-file-item">
                  <article
                    className={`uc18-board-file-card ${isDeletingCurrentItem ? "is-deleting" : ""}`}
                  >
                    <div className="uc18-board-file-copy">
                      <strong>{item.boardFolderName}</strong>
                      <p className="muted-copy">
                        Folder logicznej planszy gotowy do review i ewentualnego usuniecia
                        bez lokalnego zgadywania nowej paginacji po stronie klienta.
                      </p>
                      <Uc18BoardFileDeleteAction
                        boardFolderName={item.boardFolderName}
                        isDeleting={isDeletingCurrentItem}
                        isDisabled={isDeleteActionDisabled}
                        error={deleteErrorForCurrentItem}
                        onConfirm={() => {
                          void deleteBoardFile.deleteBoardFile(item);
                        }}
                        onCancel={deleteBoardFile.clearDeleteFeedback}
                      />
                    </div>
                    <Uc18BoardImagePreview
                      apiBaseUrl={apiBaseUrl}
                      boardFile={item}
                      accessToken={accessToken}
                      onUnauthorized={onUnauthorized}
                    />
                  </article>
                </li>
              );
            })}
          </ul>

          <div className="uc18-board-files-footer">
            <p className="muted-copy">
              Strona {boardFiles.page} z {boardFiles.totalPages}. Backend pozostaje zrodlem
              prawdy dla kolejnosci i lacznej liczby rekordow.
            </p>
            <div className="uc18-board-files-pagination">
              <button
                className="secondary-button"
                type="button"
                onClick={() => void boardFiles.goToPreviousPage()}
                disabled={!boardFiles.canGoToPreviousPage || deleteBoardFile.isDeleting}
              >
                Poprzednia
              </button>
              <button
                className="secondary-button"
                type="button"
                onClick={() => void boardFiles.goToNextPage()}
                disabled={!boardFiles.canGoToNextPage || deleteBoardFile.isDeleting}
              >
                Nastepna
              </button>
            </div>
          </div>
        </>
      ) : null}
    </article>
  );
}
