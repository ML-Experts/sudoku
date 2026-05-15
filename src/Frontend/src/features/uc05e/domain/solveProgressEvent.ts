import type { SolveProgressEventApiResponse } from "../../../types/api";

export type SolveProgressEventType =
  | "snapshot"
  | "progress"
  | "completed"
  | "failed"
  | "cancelled";

export type SolveProgressStatus =
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export type SolveProgressEvent = Omit<
  SolveProgressEventApiResponse,
  "eventType" | "status"
> & {
  eventType: SolveProgressEventType;
  status: SolveProgressStatus;
};

export function isSolveProgressEventType(
  value: unknown,
): value is SolveProgressEventType {
  return (
    value === "snapshot" ||
    value === "progress" ||
    value === "completed" ||
    value === "failed" ||
    value === "cancelled"
  );
}

export function isSolveProgressStatus(
  value: unknown,
): value is SolveProgressStatus {
  return (
    value === "queued" ||
    value === "running" ||
    value === "completed" ||
    value === "failed" ||
    value === "cancelled"
  );
}

export function toSolveProgressEvent(
  payload: SolveProgressEventApiResponse,
): SolveProgressEvent {
  if (!isSolveProgressEventType(payload.eventType)) {
    throw new Error("Backend zwrocil nieznany eventType dla solve progress.");
  }

  if (!isSolveProgressStatus(payload.status)) {
    throw new Error("Backend zwrocil nieznany status dla solve progress.");
  }

  return {
    ...payload,
    eventType: payload.eventType,
    status: payload.status,
  };
}
