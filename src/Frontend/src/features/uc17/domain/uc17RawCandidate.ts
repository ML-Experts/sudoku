export type Uc17RawCandidateType = "board" | "digit";

export type Uc17RawCandidate = {
  key: string;
  name: string;
  type: Uc17RawCandidateType;
};

export function isUc17RawCandidateType(value: string): value is Uc17RawCandidateType {
  return value === "board" || value === "digit";
}
