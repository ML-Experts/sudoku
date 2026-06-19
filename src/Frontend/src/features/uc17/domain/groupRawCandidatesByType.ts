import type { Uc17RawCandidate } from "./uc17RawCandidate";

export type GroupedRawCandidates = {
  boardCandidates: Uc17RawCandidate[];
  digitCandidates: Uc17RawCandidate[];
  counts: {
    total: number;
    board: number;
    digit: number;
  };
};

export function groupRawCandidatesByType(
  candidates: Uc17RawCandidate[]
): GroupedRawCandidates {
  const boardCandidates = candidates.filter((candidate) => candidate.type === "board");
  const digitCandidates = candidates.filter((candidate) => candidate.type === "digit");

  return {
    boardCandidates,
    digitCandidates,
    counts: {
      total: candidates.length,
      board: boardCandidates.length,
      digit: digitCandidates.length,
    },
  };
}
