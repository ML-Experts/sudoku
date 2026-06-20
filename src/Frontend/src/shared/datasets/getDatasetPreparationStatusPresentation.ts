export type DatasetPreparationStatusPresentation = {
  label: string;
  className: string;
  description: string | null;
};

const STATUS_PRESENTATIONS: Record<string, DatasetPreparationStatusPresentation> = {
  queued: {
    label: "W kolejce",
    className: "is-queued",
    description: "Przygotowanie czeka na rozpoczecie przetwarzania.",
  },
  running: {
    label: "W trakcie",
    className: "is-running",
    description: "Przygotowanie jest aktualnie przetwarzane.",
  },
  completed: {
    label: "Gotowe",
    className: "is-completed",
    description: "Przygotowanie zostalo zakonczone i jest widoczne na liscie backendu.",
  },
  failed: {
    label: "Niepowodzenie",
    className: "is-failed",
    description: "Przygotowanie zakonczylo sie bledem i wymaga weryfikacji.",
  },
};

export function getDatasetPreparationStatusPresentation(
  status: string
): DatasetPreparationStatusPresentation {
  return (
    STATUS_PRESENTATIONS[status] ?? {
      label: status,
      className: "is-unknown",
      description: "Przygotowanie ma nieznany status zwrocony przez backend.",
    }
  );
}
