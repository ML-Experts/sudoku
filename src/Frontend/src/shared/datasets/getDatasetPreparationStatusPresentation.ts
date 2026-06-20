export type DatasetPreparationStatusPresentation = {
  label: string;
  className: string;
  description: string | null;
};

const STATUS_PRESENTATIONS: Record<string, DatasetPreparationStatusPresentation> = {
  queued: {
    label: "W kolejce",
    className: "is-queued",
    description: "Preparation czeka na rozpoczecie przetwarzania.",
  },
  running: {
    label: "W trakcie",
    className: "is-running",
    description: "Preparation jest aktualnie przetwarzane.",
  },
  completed: {
    label: "Gotowe",
    className: "is-completed",
    description: "Preparation zostalo zakonczone i jest widoczne na liscie backendu.",
  },
  failed: {
    label: "Niepowodzenie",
    className: "is-failed",
    description: "Preparation zakonczylo sie bledem i wymaga weryfikacji.",
  },
};

export function getDatasetPreparationStatusPresentation(
  status: string
): DatasetPreparationStatusPresentation {
  return (
    STATUS_PRESENTATIONS[status] ?? {
      label: status,
      className: "is-unknown",
      description: "Preparation ma nieznany status zwrocony przez backend.",
    }
  );
}
