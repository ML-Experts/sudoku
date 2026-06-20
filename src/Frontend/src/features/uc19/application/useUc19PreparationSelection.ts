import { useEffect, useMemo, useRef, useState } from "react";

import type {
  DatasetPreparationApiResponse,
  DatasetPreparationListItemApiResponse,
} from "../../../types/api";
import { getDatasetPreparationStatusPresentation } from "../../../shared/datasets/getDatasetPreparationStatusPresentation";
import { useUc17DatasetPreparations } from "../../uc17/application/useUc17DatasetPreparations";
import {
  evaluateUc19PreparationReadiness,
  type Uc19PreparationReadiness,
  type Uc19PreparationReadinessSeverity,
} from "../domain/evaluateUc19PreparationReadiness";

type UseUc19PreparationSelectionOptions = {
  apiBaseUrl: string;
  accessToken?: string | null;
  onUnauthorized?: () => void;
  preferredPreparationName?: string | null;
};

type Uc19PreparationSelectionWarning = {
  message: string;
  severity: Exclude<Uc19PreparationReadinessSeverity, "none">;
};

export type Uc19PreparationListItem = DatasetPreparationListItemApiResponse & {
  readiness: Uc19PreparationReadiness;
  statusPresentation: ReturnType<typeof getDatasetPreparationStatusPresentation>;
};

export type Uc19PreparationDetails = DatasetPreparationApiResponse & {
  readiness: Uc19PreparationReadiness;
  statusPresentation: ReturnType<typeof getDatasetPreparationStatusPresentation>;
};

export function useUc19PreparationSelection({
  apiBaseUrl,
  accessToken,
  onUnauthorized,
  preferredPreparationName,
}: UseUc19PreparationSelectionOptions) {
  const {
    preparationsState,
    detailsState,
    selectedPreparationName,
    loadPreparationDetails,
    refreshPreparations,
    refreshSelectedPreparation,
  } = useUc17DatasetPreparations({
    apiBaseUrl,
    accessToken,
    onUnauthorized,
  });
  const [selectionWarningState, setSelectionWarningState] =
    useState<Uc19PreparationSelectionWarning | null>(null);
  const previousSelectedPreparationNameRef = useRef<string | null>(null);
  const previousCanContinueRef = useRef<boolean>(false);
  const preferredSelectionRef = useRef<string | null>(null);

  const preparationItems = useMemo<Uc19PreparationListItem[]>(
    () =>
      (preparationsState.data ?? []).map((item) => ({
        ...item,
        readiness: evaluateUc19PreparationReadiness(item),
        statusPresentation: getDatasetPreparationStatusPresentation(item.status),
      })),
    [preparationsState.data]
  );

  const selectedPreparation = useMemo(
    () =>
      preparationItems.find(
        (item) => item.preparationName === selectedPreparationName
      ) ?? null,
    [selectedPreparationName, preparationItems]
  );
  const selectedPreparationDetails = useMemo<Uc19PreparationDetails | null>(() => {
    if (
      !detailsState.data ||
      !selectedPreparationName ||
      detailsState.data.preparationName !== selectedPreparationName
    ) {
      return null;
    }

    return {
      ...detailsState.data,
      readiness: evaluateUc19PreparationReadiness(detailsState.data),
      statusPresentation: getDatasetPreparationStatusPresentation(detailsState.data.status),
    };
  }, [detailsState.data, selectedPreparationName]);
  const canContinueToSources =
    detailsState.kind === "success" &&
    (selectedPreparation?.readiness.canContinue ?? false) &&
    (selectedPreparationDetails?.readiness.canContinue ?? false);

  useEffect(() => {
    if (!preferredPreparationName) {
      preferredSelectionRef.current = null;
      return;
    }

    if (selectedPreparationName === preferredPreparationName) {
      preferredSelectionRef.current = preferredPreparationName;
      return;
    }

    const preferredPreparationExists = preparationItems.some(
      (item) => item.preparationName === preferredPreparationName
    );

    if (!preferredPreparationExists) {
      return;
    }

    if (preferredSelectionRef.current === preferredPreparationName) {
      return;
    }

    preferredSelectionRef.current = preferredPreparationName;
    void loadPreparationDetails(preferredPreparationName);
  }, [loadPreparationDetails, preferredPreparationName, preparationItems, selectedPreparationName]);

  useEffect(() => {
    const previousSelection = previousSelectedPreparationNameRef.current;
    const currentSelection = selectedPreparationName;

    if (previousSelection && !currentSelection) {
      const selectionStillExists = preparationItems.some(
        (item) => item.preparationName === previousSelection
      );

      if (!selectionStillExists) {
        console.warn("[UC-19] Wybrane preparation zniknelo po odswiezeniu listy.", {
          preparationName: previousSelection,
        });
        setSelectionWarningState({
          message:
            "Wybrane przygotowanie nie jest juz dostepne. Wybierz inny rekord przed przejsciem dalej.",
          severity: "warning",
        });
      }
    }

    previousSelectedPreparationNameRef.current = currentSelection;
  }, [preparationItems, selectedPreparationName]);

  useEffect(() => {
    if (!selectedPreparationName) {
      previousCanContinueRef.current = false;
      return;
    }

    if (previousCanContinueRef.current && !canContinueToSources) {
      console.warn("[UC-19] Wybrane preparation przestalo byc gotowe do dalszego kroku.", {
        preparationName: selectedPreparationName,
        httpStatus: detailsState.httpStatus,
        status: selectedPreparationDetails?.status ?? selectedPreparation?.status ?? null,
      });
      setSelectionWarningState({
        message:
          "Wybrane przygotowanie nie jest juz gotowe do dalszego kroku. Odswiez lub wybierz inny rekord.",
        severity: "warning",
      });
    }

    previousCanContinueRef.current = canContinueToSources;
  }, [
    canContinueToSources,
    detailsState.httpStatus,
    selectedPreparation,
    selectedPreparationDetails,
    selectedPreparationName,
  ]);

  const selectionWarning =
    selectionWarningState ??
    (detailsState.kind === "error" && selectedPreparationName
      ? {
          message:
            detailsState.httpStatus === 404
              ? "Wybrane przygotowanie nie istnieje juz po stronie backendu. Odswiez liste lub wybierz inny rekord przed przejsciem dalej."
              : "Nie udalo sie potwierdzic szczegolow wybranego przygotowania. Dalszy krok pozostaje zablokowany do czasu poprawnego odswiezenia.",
          severity: "warning" as const,
        }
      : selectedPreparationDetails?.readiness.reason
        ? {
            message: selectedPreparationDetails.readiness.reason,
            severity:
              selectedPreparationDetails.readiness.severity === "warning"
                ? "warning"
                : "info",
          }
        : selectedPreparation?.readiness.reason
      ? {
          message: selectedPreparation.readiness.reason,
          severity:
            selectedPreparation.readiness.severity === "warning" ? "warning" : "info",
        }
      : null);

  async function handlePreparationSelect(preparationName: string) {
    console.info("[UC-19] Wybrano preparation do builda datasetu.", {
      preparationName,
    });
    setSelectionWarningState(null);
    await loadPreparationDetails(preparationName);
  }

  async function handleRefreshPreparations() {
    console.info("[UC-19] Reczne odswiezenie listy przygotowan dla builda datasetu.");
    await refreshPreparations();
  }

  return {
    preparationsState,
    detailsState,
    preparationItems,
    selectedPreparationName,
    selectedPreparation,
    selectedPreparationDetails,
    canContinueToSources,
    selectionWarning,
    refreshPreparations: handleRefreshPreparations,
    refreshSelectedPreparation,
    handlePreparationSelect,
  };
}
