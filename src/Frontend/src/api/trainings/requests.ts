import type {
  ActiveModelApiResponse,
  CancelTrainingRunApiResponse,
  CreateTrainingRunApiEntry,
  RegistryModelsListApiResponse,
  SetActiveModelApiEntry,
  TrainingRunApiResponse,
  TrainingRunDetailsApiResponse,
  TrainingRunsListApiResponse,
} from "../../types/api";
import {
  isCancelTrainingRunApiResponse,
  isLegacyCancelTrainingRunApiResponse,
} from "./cancelGuards";
import {
  buildAuthHeaders,
  buildErrorFromResponse,
  tryParseJson,
} from "./errorHandling";
import {
  isActiveModelApiResponse,
  isRegistryModelsListApiResponse,
} from "./modelGuards";
import {
  isTrainingRunApiResponse,
  isTrainingRunDetailsApiResponse,
  isTrainingRunsListApiResponse,
} from "./trainingRunGuards";

export async function postCreateTrainingRun(
  apiBaseUrl: string,
  entry: CreateTrainingRunApiEntry,
  accessToken?: string | null,
  signal?: AbortSignal,
): Promise<TrainingRunApiResponse> {
  const response = await fetch(`${apiBaseUrl}/trainings`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...buildAuthHeaders(accessToken),
    },
    body: JSON.stringify(entry),
    signal,
  });

  const rawBody = await response.text();
  const parsed = tryParseJson(rawBody);

  if (response.status === 202) {
    if (!isTrainingRunApiResponse(parsed)) {
      throw new Error("Backend zwrocil niepoprawny ksztalt TrainingRunApiResponse.");
    }

    return parsed;
  }

  throw buildErrorFromResponse(rawBody, response.status);
}

export async function getActiveTrainingRun(
  apiBaseUrl: string,
  accessToken?: string | null,
  signal?: AbortSignal,
): Promise<TrainingRunApiResponse | null> {
  const response = await fetch(`${apiBaseUrl}/trainings/active`, {
    method: "GET",
    headers: {
      Accept: "application/json",
      ...buildAuthHeaders(accessToken),
    },
    signal,
  });

  if (response.status === 204) {
    return null;
  }

  const rawBody = await response.text();
  const parsed = tryParseJson(rawBody);

  if (response.status === 200) {
    if (!isTrainingRunApiResponse(parsed)) {
      throw new Error("Backend zwrocil niepoprawny ksztalt TrainingRunApiResponse.");
    }

    return parsed;
  }

  throw buildErrorFromResponse(rawBody, response.status);
}

export async function getTrainingRuns(
  apiBaseUrl: string,
  accessToken?: string | null,
  signal?: AbortSignal,
): Promise<TrainingRunsListApiResponse> {
  const response = await fetch(`${apiBaseUrl}/trainings`, {
    method: "GET",
    headers: {
      Accept: "application/json",
      ...buildAuthHeaders(accessToken),
    },
    signal,
  });

  const rawBody = await response.text();
  const parsed = tryParseJson(rawBody);

  if (response.status === 200) {
    if (!isTrainingRunsListApiResponse(parsed)) {
      throw new Error(
        "Backend zwrocil niepoprawny ksztalt TrainingRunsListApiResponse.",
      );
    }

    return parsed;
  }

  throw buildErrorFromResponse(rawBody, response.status);
}

export async function getTrainingRunDetails(
  apiBaseUrl: string,
  runName: string,
  accessToken?: string | null,
  signal?: AbortSignal,
): Promise<TrainingRunDetailsApiResponse> {
  const response = await fetch(
    `${apiBaseUrl}/trainings/${encodeURIComponent(runName)}`,
    {
      method: "GET",
      headers: {
        Accept: "application/json",
        ...buildAuthHeaders(accessToken),
      },
      signal,
    },
  );

  const rawBody = await response.text();
  const parsed = tryParseJson(rawBody);

  if (response.status === 200) {
    if (!isTrainingRunDetailsApiResponse(parsed)) {
      throw new Error(
        "Backend zwrocil niepoprawny ksztalt TrainingRunDetailsApiResponse.",
      );
    }

    return parsed;
  }

  throw buildErrorFromResponse(rawBody, response.status);
}

export async function getRegistryModels(
  apiBaseUrl: string,
  accessToken?: string | null,
  signal?: AbortSignal,
): Promise<RegistryModelsListApiResponse> {
  const response = await fetch(`${apiBaseUrl}/models/registry`, {
    method: "GET",
    headers: {
      Accept: "application/json",
      ...buildAuthHeaders(accessToken),
    },
    signal,
  });

  const rawBody = await response.text();
  const parsed = tryParseJson(rawBody);

  if (response.status === 200) {
    if (!isRegistryModelsListApiResponse(parsed)) {
      throw new Error(
        "Backend zwrocil niepoprawny ksztalt RegistryModelsListApiResponse.",
      );
    }

    return parsed;
  }

  throw buildErrorFromResponse(rawBody, response.status);
}

export async function getActiveModel(
  apiBaseUrl: string,
  accessToken?: string | null,
  signal?: AbortSignal,
): Promise<ActiveModelApiResponse | null> {
  const response = await fetch(`${apiBaseUrl}/models/active`, {
    method: "GET",
    headers: {
      Accept: "application/json",
      ...buildAuthHeaders(accessToken),
    },
    signal,
  });

  if (response.status === 204) {
    return null;
  }

  const rawBody = await response.text();
  const parsed = tryParseJson(rawBody);

  if (response.status === 200) {
    if (!isActiveModelApiResponse(parsed)) {
      throw new Error("Backend zwrocil niepoprawny ksztalt ActiveModelApiResponse.");
    }

    return parsed;
  }

  throw buildErrorFromResponse(rawBody, response.status);
}

export async function putActiveModel(
  apiBaseUrl: string,
  entry: SetActiveModelApiEntry,
  accessToken?: string | null,
  signal?: AbortSignal,
): Promise<ActiveModelApiResponse> {
  const response = await fetch(`${apiBaseUrl}/models/active`, {
    method: "PUT",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...buildAuthHeaders(accessToken),
    },
    body: JSON.stringify(entry),
    signal,
  });

  const rawBody = await response.text();
  const parsed = tryParseJson(rawBody);

  if (response.status === 200) {
    if (!isActiveModelApiResponse(parsed)) {
      throw new Error("Backend zwrocil niepoprawny ksztalt ActiveModelApiResponse.");
    }

    return parsed;
  }

  throw buildErrorFromResponse(rawBody, response.status);
}

export async function postCancelTrainingRun(
  apiBaseUrl: string,
  runName: string,
  accessToken?: string | null,
  signal?: AbortSignal,
): Promise<CancelTrainingRunApiResponse> {
  const response = await fetch(
    `${apiBaseUrl}/trainings/${encodeURIComponent(runName)}/cancel`,
    {
      method: "POST",
      headers: {
        Accept: "application/json",
        ...buildAuthHeaders(accessToken),
      },
      signal,
    },
  );

  const rawBody = await response.text();
  const parsed = tryParseJson(rawBody);

  if (response.status === 202) {
    if (!isCancelTrainingRunApiResponse(parsed)) {
      if (isLegacyCancelTrainingRunApiResponse(parsed)) {
        return {
          runName: parsed.runName,
          status: parsed.status,
          requestDisposition: parsed.requestDisposition,
          cancellationRequestedAtUtc: null,
        };
      }

      throw new Error(
        "Backend zwrocil niepoprawny ksztalt CancelTrainingRunApiResponse.",
      );
    }

    return parsed;
  }

  throw buildErrorFromResponse(rawBody, response.status);
}
