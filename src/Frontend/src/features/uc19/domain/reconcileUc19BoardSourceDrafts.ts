import { reconcileUc19PreparationSourceDrafts } from "./reconcileUc19PreparationSourceDrafts";
import type { Uc19BoardSourceDraft } from "./uc19BoardSourceDraft";

export type ReconciledUc19BoardSourceDrafts = {
  drafts: Uc19BoardSourceDraft[];
  removedDrafts: string[];
};

export function reconcileUc19BoardSourceDrafts(
  previousDrafts: Uc19BoardSourceDraft[],
  freshDrafts: Uc19BoardSourceDraft[]
): ReconciledUc19BoardSourceDrafts {
  return reconcileUc19PreparationSourceDrafts(previousDrafts, freshDrafts);
}
