import { reconcileUc19PreparationSourceDrafts } from "./reconcileUc19PreparationSourceDrafts";
import type { Uc19DigitSourceDraft } from "./uc19DigitSourceDraft";

export type ReconciledUc19DigitSourceDrafts = {
  drafts: Uc19DigitSourceDraft[];
  removedDrafts: string[];
};

export function reconcileUc19DigitSourceDrafts(
  previousDrafts: Uc19DigitSourceDraft[],
  freshDrafts: Uc19DigitSourceDraft[]
): ReconciledUc19DigitSourceDrafts {
  return reconcileUc19PreparationSourceDrafts(previousDrafts, freshDrafts);
}
