import { toggleUc19PreparationSourceSplit } from "./toggleUc19PreparationSourceSplit";
import type { Uc19BoardSourceSplit } from "./uc19BoardSourceDraft";

export function toggleUc19BoardSourceSplit(
  previousSplits: Uc19BoardSourceSplit[],
  split: Uc19BoardSourceSplit
): Uc19BoardSourceSplit[] {
  return toggleUc19PreparationSourceSplit(previousSplits, split);
}
