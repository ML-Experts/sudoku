import type { Uc17RawCandidate } from "./uc17RawCandidate";

export type ReconciledSelectedCandidates = {
  selectedKeys: string[];
  removedKeys: string[];
};

export function reconcileSelectedCandidates(
  previousSelectedKeys: string[],
  candidates: Uc17RawCandidate[]
): ReconciledSelectedCandidates {
  const availableKeys = new Set(candidates.map((candidate) => candidate.key));
  const selectedKeys = previousSelectedKeys.filter((key) => availableKeys.has(key));
  const removedKeys = previousSelectedKeys.filter((key) => !availableKeys.has(key));

  return {
    selectedKeys,
    removedKeys,
  };
}
