import type {
  AdminLoginApiEntry,
  AuthTokenApiResponse,
  ErrorApiResponse,
} from "../types/api";

export class AuthApiError extends Error {
  readonly status: number;
  readonly errorType: string | undefined;

  constructor(message: string, status: number, errorType?: string) {
    super(message);
    this.name = "AuthApiError";
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
    typeof record.message === "string" && typeof record.errorType === "string"
  );
}

function isAuthTokenApiResponse(value: unknown): value is AuthTokenApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    typeof record.accessToken === "string" &&
    typeof record.tokenType === "string" &&
    typeof record.expiresAtUtc === "string"
  );
}

export async function postAdminLogin(
  apiBaseUrl: string,
  entry: AdminLoginApiEntry,
  signal?: AbortSignal
): Promise<AuthTokenApiResponse> {
  const response = await fetch(`${apiBaseUrl}/auth/login`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(entry),
    signal,
  });

  const rawBody = await response.text();
  const parsed = tryParseJson(rawBody);

  if (response.status === 200) {
    if (!isAuthTokenApiResponse(parsed)) {
      throw new Error("Backend zwrocil niepoprawny ksztalt AuthTokenApiResponse.");
    }

    return parsed;
  }

  if (isErrorApiResponse(parsed)) {
    throw new AuthApiError(parsed.message, response.status, parsed.errorType);
  }

  throw new AuthApiError(
    rawBody.trim()
      ? `Backend zwrocil odpowiedz HTTP ${response.status}.`
      : `Backend zwrocil odpowiedz HTTP ${response.status} bez tresci.`,
    response.status
  );
}
