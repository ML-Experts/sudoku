import { useEffect, useState } from "react";

type Uc18BoardFileDeleteActionProps = {
  boardFolderName: string;
  isDeleting: boolean;
  isDisabled: boolean;
  error?: string | null;
  onConfirm: () => void;
  onCancel: () => void;
};

export function Uc18BoardFileDeleteAction({
  boardFolderName,
  isDeleting,
  isDisabled,
  error,
  onConfirm,
  onCancel,
}: Uc18BoardFileDeleteActionProps) {
  const [isConfirming, setIsConfirming] = useState(false);

  useEffect(() => {
    if (isDeleting || isDisabled) {
      setIsConfirming(false);
    }
  }, [isDeleting, isDisabled]);

  return (
    <div className="uc18-board-file-delete-slot">
      <button
        className="uc18-board-file-delete-icon"
        type="button"
        onClick={() => setIsConfirming(true)}
        disabled={isDisabled || isDeleting}
        aria-label={`Usun plansze ${boardFolderName}`}
        title="Usun plansze"
      >
        x
      </button>

      {isConfirming ? (
        <div className="uc18-board-file-delete-confirmation">
          <p className="uc18-board-file-delete-warning">
            Usunac folder planszy <code>{boardFolderName}</code> z biezacego
            przygotowania?
          </p>
          <div className="uc18-board-file-delete-actions">
            <button
              className="danger-button"
              type="button"
              onClick={() => {
                setIsConfirming(false);
                onConfirm();
              }}
              disabled={isDisabled || isDeleting}
            >
              {isDeleting ? "Usuwanie..." : "Usun"}
            </button>
            <button
              className="secondary-button"
              type="button"
              onClick={() => {
                setIsConfirming(false);
                onCancel();
              }}
              disabled={isDeleting}
            >
              Anuluj
            </button>
          </div>
          {error ? <p className="uc18-board-file-delete-error">{error}</p> : null}
        </div>
      ) : null}

      {!isConfirming && error ? (
        <p className="uc18-board-file-delete-error">{error}</p>
      ) : null}
    </div>
  );
}
