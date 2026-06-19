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

  if (isConfirming) {
    return (
      <div className="uc18-board-file-delete-confirmation">
        <p className="uc18-board-file-delete-warning">
          Usuniesz caly folder planszy <code>{boardFolderName}</code> z aktualnego
          preparation.
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
            {isDeleting ? "Usuwanie..." : "Potwierdz usuniecie"}
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
    );
  }

  return (
    <div className="uc18-board-file-delete-slot">
      <button
        className="danger-button"
        type="button"
        onClick={() => setIsConfirming(true)}
        disabled={isDisabled || isDeleting}
      >
        {isDeleting ? "Usuwanie..." : "Usun plansze"}
      </button>
      {error ? <p className="uc18-board-file-delete-error">{error}</p> : null}
    </div>
  );
}
