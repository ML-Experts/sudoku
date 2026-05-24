import type { SolveProgressEvent } from "./solveProgressEvent";

type ShouldAcceptSolveProgressEventOptions = {
  activeSolveSessionId: string | null;
  lastAcceptedSequence: number;
  event: SolveProgressEvent;
};

export function shouldAcceptSolveProgressEvent({
  activeSolveSessionId,
  lastAcceptedSequence,
  event,
}: ShouldAcceptSolveProgressEventOptions): boolean {
  if (!activeSolveSessionId || event.solveSessionId !== activeSolveSessionId) {
    return false;
  }

  return event.sequence > lastAcceptedSequence;
}
