import type {
  ErrorApiResponse,
  ExampleFileApiResponse,
  ExamplesListApiResponse,
  ImageApiResponse,
} from "../types/api";

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

export class ExamplesApiError extends Error {
  readonly status: number;
  readonly errorType: string | undefined;

  constructor(message: string, status: number, errorType?: string) {
    super(message);
    this.name = "ExamplesApiError";
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

function isExamplesListApiResponse(
  value: unknown
): value is ExamplesListApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  if (!Array.isArray(record.items) || typeof record.totalCount !== "number") {
    return false;
  }

  return record.items.every((item) => isExampleFileApiResponse(item));
}

function isImageApiResponse(value: unknown): value is ImageApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    typeof record.mimeType === "string" && typeof record.base64 === "string"
  );
}

function base64ToUint8Array(base64: string): Uint8Array {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }

  return bytes;
}

export async function getExamplesList(
  apiBaseUrl: string,
  signal?: AbortSignal
): Promise<ExamplesListApiResponse> {
  const url = `${apiBaseUrl}/examples`;

  const response = await fetch(url, {
    method: "GET",
    headers: {
      Accept: "application/json",
    },
    signal,
  });

  const rawBody = await response.text();
  const parsed = tryParseJson(rawBody);

  if (response.status === 200) {
    if (!isExamplesListApiResponse(parsed)) {
      throw new Error(
        "Backend zwrócił niepoprawny kształt ExamplesListApiResponse."
      );
    }

    return parsed;
  }

  if (isErrorApiResponse(parsed)) {
    throw new ExamplesApiError(
      parsed.message,
      response.status,
      parsed.errorType
    );
  }

  throw new ExamplesApiError(
    rawBody.trim()
      ? `Backend zwrócił odpowiedź HTTP ${response.status}.`
      : `Backend zwrócił odpowiedź HTTP ${response.status} bez treści.`,
    response.status
  );
}

/** Uses GET /api/examples/{name} (ImageApiResponse); BE may add raw /download later (UC-03). */
export async function downloadExampleAsFile(
  apiBaseUrl: string,
  fileName: string,
  signal?: AbortSignal
): Promise<void> {
  const url = `${apiBaseUrl}/examples/${encodeURIComponent(fileName)}`;

  const response = await fetch(url, {
    method: "GET",
    headers: {
      Accept: "application/json",
    },
    signal,
  });

  const rawBody = await response.text();
  const parsed = tryParseJson(rawBody);

  if (response.status === 200) {
    if (!isImageApiResponse(parsed)) {
      throw new Error("Backend zwrócił niepoprawny kształt ImageApiResponse.");
    }

    let bytes: Uint8Array;

    try {
      bytes = base64ToUint8Array(parsed.base64);
    } catch {
      throw new Error("Nie udało się zdekodować obrazu z odpowiedzi backendu.");
    }

    const blob = new Blob([bytes], { type: parsed.mimeType });
    const objectUrl = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = objectUrl;
    anchor.download = fileName;
    anchor.rel = "noopener";
    anchor.click();
    URL.revokeObjectURL(objectUrl);
    return;
  }

  if (isErrorApiResponse(parsed)) {
    throw new ExamplesApiError(
      parsed.message,
      response.status,
      parsed.errorType
    );
  }

  throw new ExamplesApiError(
    rawBody.trim()
      ? `Backend zwrócił odpowiedź HTTP ${response.status}.`
      : `Backend zwrócił odpowiedź HTTP ${response.status} bez treści.`,
    response.status
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
