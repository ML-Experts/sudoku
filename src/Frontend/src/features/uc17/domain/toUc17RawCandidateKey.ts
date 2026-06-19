import type { Uc17RawCandidateType } from "./uc17RawCandidate";

type Uc17RawCandidateIdentity = {
  name: string;
  type: Uc17RawCandidateType;
};

export function toUc17RawCandidateKey({
  name,
  type,
}: Uc17RawCandidateIdentity): string {
  return `${type}:${name}`;
}
