import type { CancelTrainingRunApiResponse } from "../../types/api";

export function isCancelTrainingRunApiResponse(
  value: unknown,
): value is CancelTrainingRunApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    typeof record.runName === "string" &&
    (typeof record.status === "string" || record.status === null) &&
    typeof record.requestDisposition === "string" &&
    (typeof record.cancellationRequestedAtUtc === "string" ||
      record.cancellationRequestedAtUtc === null)
  );
}

export function isLegacyCancelTrainingRunApiResponse(value: unknown): value is {
  runName: string;
  status: string | null;
  requestDisposition: string;
} {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    typeof record.runName === "string" &&
    (typeof record.status === "string" || record.status === null) &&
    typeof record.requestDisposition === "string"
  );
}
