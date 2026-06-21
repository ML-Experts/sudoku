import type { ReactNode } from "react";

import { useUc18BoardImage } from "../application/useUc18BoardImage";
import type { Uc18BoardFile } from "../domain/uc18BoardFile";

type Uc18BoardImagePreviewProps = {
  apiBaseUrl: string;
  boardFile: Uc18BoardFile;
  accessToken?: string | null;
  onUnauthorized?: () => void;
  deleteAction?: ReactNode;
};

export function Uc18BoardImagePreview({
  apiBaseUrl,
  boardFile,
  accessToken,
  onUnauthorized,
  deleteAction,
}: Uc18BoardImagePreviewProps) {
  const boardImage = useUc18BoardImage({
    apiBaseUrl,
    imageEndpoint: boardFile.imageEndpoint,
    preparationName: boardFile.preparationName,
    sourceName: boardFile.sourceName,
    boardFolderName: boardFile.boardFolderName,
    accessToken,
    onUnauthorized,
  });
  const altText = `Podglad planszy ${boardFile.boardFolderName} ze zrodla ${boardFile.sourceName} w przygotowaniu ${boardFile.preparationName}.`;

  return (
    <div className="uc18-board-file-preview">
      <div className="uc18-board-file-preview-header">
        <span className="uc18-board-file-preview-label">Podglad obrazu</span>
        {deleteAction}
      </div>

      {boardImage.status === "loading" || boardImage.status === "idle" ? (
        <div
          className="uc18-board-image-state is-loading"
          aria-live="polite"
          aria-busy="true"
        >
          <div className="uc18-board-image-skeleton" aria-hidden="true" />
          <p className="muted-copy">
            Ladowanie obrazu <code>corrected-board.png</code> dla{" "}
            <code>{boardFile.boardFolderName}</code>...
          </p>
        </div>
      ) : null}

      {boardImage.status === "error" ? (
        <div className="uc18-board-image-state is-error" aria-live="polite">
          <p className="muted-copy">
            Nie udalo sie zaladowac podgladu dla{" "}
            <code>{boardFile.boardFolderName}</code>.
          </p>
          {boardImage.httpStatus === 404 ? (
            <p className="muted-copy">
              Backend nie znalazl juz tego obrazu. Rekord listy pozostaje widoczny, ale
              preview wymaga ponowienia po odswiezeniu danych.
            </p>
          ) : null}
          {boardImage.httpStatus === 401 ? (
            <p className="muted-copy">
              Sesja administracyjna wygasla. Zaloguj sie ponownie i sprobuj jeszcze raz.
            </p>
          ) : null}
          {boardImage.httpStatus !== null &&
          boardImage.httpStatus >= 500 ? (
            <p className="muted-copy">
              Backend zwrocil blad techniczny dla tej jednej planszy.
            </p>
          ) : null}
          {boardImage.error ? (
            <p className="uc18-board-image-error-text">{boardImage.error}</p>
          ) : null}
          <button
            className="secondary-button"
            type="button"
            onClick={() => void boardImage.retryLoadBoardImage()}
          >
            Ponow ladowanie podgladu
          </button>
        </div>
      ) : null}

      {boardImage.status === "success" && boardImage.imageDataUrl ? (
        <div className="uc18-board-image-state is-success">
          <img
            className="uc18-board-image"
            src={boardImage.imageDataUrl}
            alt={altText}
            loading="lazy"
          />
          <p className="muted-copy">
            Podglad <code>corrected-board.png</code> dla{" "}
            <code>{boardFile.boardFolderName}</code>.
          </p>
        </div>
      ) : null}
    </div>
  );
}
