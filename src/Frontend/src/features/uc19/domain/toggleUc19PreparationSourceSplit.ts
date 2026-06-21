import type { Uc19PreparationSourceSplit } from "./uc19PreparationSourceDraft";

export function toggleUc19PreparationSourceSplit(
  previousSplits: Uc19PreparationSourceSplit[],
  split: Uc19PreparationSourceSplit
): Uc19PreparationSourceSplit[] {
  if (split === "mix") {
    return previousSplits.includes("mix") ? [] : ["mix"];
  }

  const withoutMix = previousSplits.filter((item) => item !== "mix");

  if (withoutMix.includes(split)) {
    return withoutMix.filter((item) => item !== split);
  }

  return [...withoutMix, split];
}
