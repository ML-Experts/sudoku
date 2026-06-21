import { validateUc19BoardSourceDraft } from "./validateUc19BoardSourceDraft";
import { validateUc19DigitSourceDraft } from "./validateUc19DigitSourceDraft";
import type { Uc19BoardSourceDraft } from "./uc19BoardSourceDraft";
import type { Uc19DigitSourceDraft } from "./uc19DigitSourceDraft";

type ValidateUc19ProcessedDatasetBuildRequestInput = {
  preparationName: string | null;
  canContinueToSources: boolean;
  name: string;
  boardSelectedDrafts: Uc19BoardSourceDraft[];
  digitSelectedDrafts: Uc19DigitSourceDraft[];
};

const DATASET_NAME_PATTERN = /^[A-Za-z0-9][A-Za-z0-9._-]*$/;

export function validateUc19ProcessedDatasetBuildRequest({
  preparationName,
  canContinueToSources,
  name,
  boardSelectedDrafts,
  digitSelectedDrafts,
}: ValidateUc19ProcessedDatasetBuildRequestInput): string | null {
  const normalizedPreparationName = preparationName?.trim() ?? "";

  if (!normalizedPreparationName) {
    return "Wybierz przygotowanie datasetu przed rozpoczeciem budowy.";
  }

  if (!canContinueToSources) {
    return "Wybrane przygotowanie nie odblokowuje jeszcze budowy datasetu.";
  }

  const trimmedName = name.trim();
  if (!trimmedName) {
    return "Podaj nazwe finalnego datasetu.";
  }

  if (
    trimmedName.includes("..") ||
    trimmedName.includes("/") ||
    trimmedName.includes("\\") ||
    !DATASET_NAME_PATTERN.test(trimmedName)
  ) {
    return "Nazwa datasetu zawiera niedozwolone znaki.";
  }

  const selectedSources = [...boardSelectedDrafts, ...digitSelectedDrafts];
  if (selectedSources.length === 0) {
    return "Wybierz przynajmniej jedno zrodlo board lub digit.";
  }

  for (const draft of boardSelectedDrafts) {
    if (draft.preparationName !== normalizedPreparationName) {
      return "Co najmniej jedno wybrane zrodlo plansz pochodzi z innego przygotowania.";
    }

    const validation = validateUc19BoardSourceDraft(draft);
    if (!validation.isValid) {
      return validation.message ?? "Popraw splity dla zaznaczonych zrodel board.";
    }
  }

  for (const draft of digitSelectedDrafts) {
    if (draft.preparationName !== normalizedPreparationName) {
      return "Co najmniej jedno wybrane zrodlo cyfr pochodzi z innego przygotowania.";
    }

    const validation = validateUc19DigitSourceDraft(draft);
    if (!validation.isValid) {
      return validation.message ?? "Popraw splity dla zaznaczonych zrodel digit.";
    }
  }

  return null;
}
