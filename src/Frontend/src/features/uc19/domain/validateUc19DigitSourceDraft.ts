import { validateUc19PreparationSourceDraft } from "./validateUc19PreparationSourceDraft";
import type { Uc19DigitSourceDraft } from "./uc19DigitSourceDraft";
import type { Uc19PreparationSourceDraftValidation } from "./validateUc19PreparationSourceDraft";

export type Uc19DigitSourceDraftValidation = Uc19PreparationSourceDraftValidation;

export function validateUc19DigitSourceDraft(
  draft: Uc19DigitSourceDraft
): Uc19DigitSourceDraftValidation {
  return validateUc19PreparationSourceDraft(draft);
}
