import { toggleUc19PreparationSourceSplit } from "./toggleUc19PreparationSourceSplit";
import type { Uc19DigitSourceSplit } from "./uc19DigitSourceDraft";

export function toggleUc19DigitSourceSplit(
  previousSplits: Uc19DigitSourceSplit[],
  split: Uc19DigitSourceSplit
): Uc19DigitSourceSplit[] {
  return toggleUc19PreparationSourceSplit(previousSplits, split);
}
