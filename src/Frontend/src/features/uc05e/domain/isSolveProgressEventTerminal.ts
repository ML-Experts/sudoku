import type {
  SolveProgressEvent,
  SolveProgressEventType,
} from "./solveProgressEvent";

export type TerminalSolveProgressEventType = Extract<
  SolveProgressEventType,
  "completed" | "failed" | "cancelled"
>;

export function isSolveProgressEventTerminal(
  event: SolveProgressEvent,
): event is SolveProgressEvent & { eventType: TerminalSolveProgressEventType } {
  return (
    event.eventType === "completed" ||
    event.eventType === "failed" ||
    event.eventType === "cancelled"
  );
}
