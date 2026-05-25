type OverlayImagePreviewProps = {
  previewUrl: string | null;
  status: "idle" | "running" | "completed" | "failed" | "cancelled";
};

function getPreviewTitle(
  status: OverlayImagePreviewProps["status"],
  hasPreview: boolean,
): string {
  if (!hasPreview) {
    return "Preview planszy 9x9 pojawi sie po zlozeniu obrazow komorek.";
  }

  switch (status) {
    case "running":
      return "Czesciowy preview rozwiazania";
    case "completed":
      return "Finalny obraz rozwiazanej planszy";
    case "failed":
      return "Czesciowy preview zachowany diagnostycznie";
    case "cancelled":
      return "Ostatni preview przed anulowaniem";
    default:
      return "Preview planszy 9x9";
  }
}

export function OverlayImagePreview({
  previewUrl,
  status,
}: OverlayImagePreviewProps) {
  const hasPreview = previewUrl !== null;

  return (
    <section className="uc05d-preview-panel">
      <div className="uc05d-preview-header">
        <div>
          <h3>{getPreviewTitle(status, hasPreview)}</h3>
          <p className="muted-copy">
            Plansza jest skladana lokalnie po stronie FE bez marginesow i odstepow
            miedzy komorkami.
          </p>
        </div>
      </div>

      {previewUrl ? (
        <div className="uc05d-preview-frame">
          <img
            className="uc05d-preview-image"
            src={previewUrl}
            alt="Preview rozwiazanej planszy sudoku z overlayem cyfr"
          />
        </div>
      ) : (
        <div className="uc05d-preview-placeholder">
          <p className="muted-copy">
            Po uruchomieniu `UC-05D` zobaczysz tutaj biezacy albo finalny obraz
            planszy.
          </p>
        </div>
      )}
    </section>
  );
}
