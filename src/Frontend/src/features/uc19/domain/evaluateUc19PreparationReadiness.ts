import type { DatasetPreparationListItemApiResponse } from "../../../types/api";

export type Uc19PreparationReadinessSeverity = "none" | "info" | "warning";

export type Uc19PreparationReadiness = {
  canContinue: boolean;
  reason: string | null;
  severity: Uc19PreparationReadinessSeverity;
};

export function evaluateUc19PreparationReadiness(
  item: Pick<DatasetPreparationListItemApiResponse, "status">
): Uc19PreparationReadiness {
  if (item.status === "completed") {
    return {
      canContinue: true,
      reason: null,
      severity: "none",
    };
  }

  if (item.status === "running" || item.status === "queued") {
    return {
      canContinue: false,
      reason: "Preparation nie jest jeszcze zakonczone.",
      severity: "info",
    };
  }

  if (item.status === "failed") {
    return {
      canContinue: false,
      reason: "Preparation zakonczylo sie niepowodzeniem.",
      severity: "warning",
    };
  }

  return {
    canContinue: false,
    reason: "Preparation ma nieznany status i nie odblokowuje kolejnego kroku.",
    severity: "warning",
  };
}
