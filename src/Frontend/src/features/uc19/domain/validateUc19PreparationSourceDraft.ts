import type { Uc19PreparationSourceDraft } from "./uc19PreparationSourceDraft";

export type Uc19PreparationSourceDraftValidation = {
  isValid: boolean;
  message: string | null;
};

export function validateUc19PreparationSourceDraft(
  draft: Pick<Uc19PreparationSourceDraft, "enabled" | "splits" | "type">
): Uc19PreparationSourceDraftValidation {
  if (!draft.enabled) {
    return {
      isValid: true,
      message: null,
    };
  }

  if (draft.splits.length === 0) {
    return {
      isValid: false,
      message: `Wybierz split dla zrodla ${draft.type}.`,
    };
  }

  if (draft.splits.includes("mix") && draft.splits.length > 1) {
    return {
      isValid: false,
      message: "Split mix nie moze byc laczony z train/val/test.",
    };
  }

  return {
    isValid: true,
    message: null,
  };
}
