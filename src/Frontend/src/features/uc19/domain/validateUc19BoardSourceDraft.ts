import { validateUc19PreparationSourceDraft } from "./validateUc19PreparationSourceDraft";
import type { Uc19BoardSourceDraft } from "./uc19BoardSourceDraft";
import type { Uc19PreparationSourceDraftValidation } from "./validateUc19PreparationSourceDraft";

export type Uc19BoardSourceDraftValidation = Uc19PreparationSourceDraftValidation;

export function validateUc19BoardSourceDraft(
  draft: Uc19BoardSourceDraft
): Uc19BoardSourceDraftValidation {
  return validateUc19PreparationSourceDraft(draft);
}
