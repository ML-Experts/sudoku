import type { ImageApiResponse } from "../../types/api";

export function isImageApiResponse(value: unknown): value is ImageApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;

  return (
    typeof record.mimeType === "string" && typeof record.base64 === "string"
  );
}
