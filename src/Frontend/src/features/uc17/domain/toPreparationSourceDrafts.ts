import type { CreateDatasetPreparationSourceApiEntry } from "../../../types/api";
import type { Uc17RawCandidate } from "./uc17RawCandidate";

export function toPreparationSourceDrafts(
  candidates: Uc17RawCandidate[],
  selectedKeys: string[]
): CreateDatasetPreparationSourceApiEntry[] {
  const selectedKeySet = new Set(selectedKeys);

  return candidates
    .filter((candidate) => selectedKeySet.has(candidate.key))
    .map((candidate) => ({
      name: candidate.name,
      type: candidate.type,
    }));
}
