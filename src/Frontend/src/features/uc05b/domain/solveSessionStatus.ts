export type SolveSessionStatus =
  | "queued"
  | "running"
  | "cancelling"
  | "completed"
  | "failed"
  | "cancelled";

export function isSolveSessionStatus(value: unknown): value is SolveSessionStatus {
  return (
    value === "queued" ||
    value === "running" ||
    value === "cancelling" ||
    value === "completed" ||
    value === "failed" ||
    value === "cancelled"
  );
}

export function isActiveSolveSessionStatus(status: SolveSessionStatus): boolean {
  return status === "queued" || status === "running" || status === "cancelling";
}

export function isTerminalSolveSessionStatus(status: SolveSessionStatus): boolean {
  return (
    status === "completed" ||
    status === "failed" ||
    status === "cancelled"
  );
}
