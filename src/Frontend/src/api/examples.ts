import type { ErrorApiResponse, ExampleFileApiResponse } from "../types/api";

export class ExampleUploadApiError extends Error {
  readonly status: number;
  readonly errorType: string | undefined;

  constructor(message: string, status: number, errorType?: string) {
    super(message);
    this.name = "ExampleUploadApiError";
    this.status = status;
    this.errorType = errorType;
  }
}

function tryParseJson(raw: string): unknown {
  if (!raw.trim()) {
    return null;
  }

  try {
    return JSON.parse(raw) as unknown;
  } catch {
    return null;
  }
}

function isErrorApiResponse(value: unknown): value is ErrorApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    typeof record.message === "string" &&
    typeof record.errorType === "string"
  );
}

function isExampleFileApiResponse(
  value: unknown
): value is ExampleFileApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    typeof record.name === "string" &&
    typeof record.contentType === "string" &&
    typeof record.sizeBytes === "number" &&
    typeof record.storedAtUtc === "string"
  );
}

export async function postExampleUpload(
  apiBaseUrl: string,
  file: File,
  signal?: AbortSignal
): Promise<ExampleFileApiResponse> {
  const url = `${apiBaseUrl}/examples`;
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(url, {
    method: "POST",
    body: formData,
    headers: {
      Accept: "application/json",
    },
    signal,
  });

  const rawBody = await response.text();
  const parsed = tryParseJson(rawBody);

  if (response.status === 201) {
    if (!isExampleFileApiResponse(parsed)) {
      throw new Error("Backend zwrócił niepoprawny kształt ExampleFileApiResponse.");
    }

    return parsed;
  }

  if (isErrorApiResponse(parsed)) {
    throw new ExampleUploadApiError(
      parsed.message,
      response.status,
      parsed.errorType
    );
  }

  throw new ExampleUploadApiError(
    rawBody.trim()
      ? `Backend zwrócił odpowiedź HTTP ${response.status}.`
      : `Backend zwrócił odpowiedź HTTP ${response.status} bez treści.`,
    response.status
  );
}
