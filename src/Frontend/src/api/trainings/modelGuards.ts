import type {
  ActiveModelApiResponse,
  RegistryModelListItemApiResponse,
  RegistryModelsListApiResponse,
  TrainingRunModelReferenceApiResponse,
} from "../../types/api";

export function isTrainingRunModelReferenceApiResponse(
  value: unknown,
): value is TrainingRunModelReferenceApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    typeof record.name === "string" &&
    typeof record.displayName === "string" &&
    typeof record.sourceType === "string" &&
    (typeof record.sourceRunName === "string" || record.sourceRunName === null) &&
    (typeof record.parentModelName === "string" || record.parentModelName === null) &&
    typeof record.inputProfile === "string" &&
    typeof record.canUseForInference === "boolean" &&
    typeof record.canStartTraining === "boolean"
  );
}

export function isRegistryModelListItemApiResponse(
  value: unknown,
): value is RegistryModelListItemApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    typeof record.name === "string" &&
    typeof record.displayName === "string" &&
    typeof record.sourceType === "string" &&
    (typeof record.sourceRunName === "string" || record.sourceRunName === null) &&
    (typeof record.parentModelName === "string" || record.parentModelName === null) &&
    typeof record.trainingMode === "string" &&
    typeof record.inputProfile === "string" &&
    (typeof record.trainingProfileName === "string" ||
      record.trainingProfileName === null) &&
    (typeof record.augmentationProfileName === "string" ||
      record.augmentationProfileName === null) &&
    (typeof record.createdAtUtc === "string" || record.createdAtUtc === null) &&
    typeof record.canStartTraining === "boolean" &&
    typeof record.canUseForInference === "boolean" &&
    Array.isArray(record.warnings) &&
    record.warnings.every((warning) => typeof warning === "string")
  );
}

export function isRegistryModelsListApiResponse(
  value: unknown,
): value is RegistryModelsListApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    Array.isArray(record.items) &&
    record.items.every((item) => isRegistryModelListItemApiResponse(item)) &&
    typeof record.totalCount === "number"
  );
}

export function isActiveModelApiResponse(
  value: unknown,
): value is ActiveModelApiResponse {
  if (!value || typeof value !== "object") {
    return false;
  }

  const record = value as Record<string, unknown>;
  return (
    typeof record.modelName === "string" &&
    typeof record.displayName === "string" &&
    typeof record.sourceType === "string" &&
    (typeof record.sourceRunName === "string" || record.sourceRunName === null) &&
    (typeof record.parentModelName === "string" || record.parentModelName === null) &&
    typeof record.inputProfile === "string" &&
    typeof record.canUseForInference === "boolean" &&
    (typeof record.activatedAtUtc === "string" || record.activatedAtUtc === null)
  );
}
