import type { CreateTrainingRunParametersApiEntry } from "../../../types/api";

export type TrainingRunParameterFormState = {
  epochs: string;
  learningRate: string;
  batchSize: string;
  earlyStoppingPatience: string;
  earlyStoppingMinDelta: string;
  warmupEpochs: string;
  lrSchedulerPatience: string;
  lrSchedulerFactor: string;
  fineTuningPolicy: string;
  useBestCheckpoint: string;
};

export type TrainingRunParameterErrors = Partial<
  Record<keyof CreateTrainingRunParametersApiEntry, string>
>;

export type TrainingRunParameterValidationResult = {
  apiEntry: CreateTrainingRunParametersApiEntry | null;
  isValid: boolean;
  errorCount: number;
  errors: TrainingRunParameterErrors;
  overrideCount: number;
};

export const trainingRunParameterDefaults: CreateTrainingRunParametersApiEntry = {
  epochs: 20,
  learningRate: 0.001,
  batchSize: 32,
  earlyStoppingPatience: 5,
  earlyStoppingMinDelta: 0.001,
  warmupEpochs: 0,
  lrSchedulerPatience: 3,
  lrSchedulerFactor: 0.5,
  fineTuningPolicy: "all",
  useBestCheckpoint: true,
};

const positiveIntegerFields = [
  "epochs",
  "batchSize",
  "earlyStoppingPatience",
  "lrSchedulerPatience",
] as const;

function parseNumber(rawValue: string): number | null {
  const normalizedValue = rawValue.trim().replace(",", ".");
  if (!normalizedValue) {
    return null;
  }

  const parsedValue = Number(normalizedValue);
  return Number.isFinite(parsedValue) ? parsedValue : null;
}

function countOverrides(
  state: TrainingRunParameterFormState,
  parsedValues: Partial<CreateTrainingRunParametersApiEntry>,
): number {
  let overrides = 0;
  const keys = Object.keys(trainingRunParameterDefaults) as Array<
    keyof CreateTrainingRunParametersApiEntry
  >;

  for (const key of keys) {
    const defaultValue = trainingRunParameterDefaults[key];
    const parsedValue = parsedValues[key];
    if (parsedValue === undefined) {
      continue;
    }

    if (key === "fineTuningPolicy" || key === "useBestCheckpoint") {
      if (parsedValue !== defaultValue) {
        overrides += 1;
      }
      continue;
    }

    const rawValue = state[key as keyof TrainingRunParameterFormState].trim();
    if (!rawValue) {
      continue;
    }

    if (parsedValue !== defaultValue) {
      overrides += 1;
    }
  }

  return overrides;
}

export function createTrainingRunParameterFormState(): TrainingRunParameterFormState {
  return {
    epochs: String(trainingRunParameterDefaults.epochs),
    learningRate: String(trainingRunParameterDefaults.learningRate),
    batchSize: String(trainingRunParameterDefaults.batchSize),
    earlyStoppingPatience: String(
      trainingRunParameterDefaults.earlyStoppingPatience,
    ),
    earlyStoppingMinDelta: String(
      trainingRunParameterDefaults.earlyStoppingMinDelta,
    ),
    warmupEpochs: String(trainingRunParameterDefaults.warmupEpochs),
    lrSchedulerPatience: String(trainingRunParameterDefaults.lrSchedulerPatience),
    lrSchedulerFactor: String(trainingRunParameterDefaults.lrSchedulerFactor),
    fineTuningPolicy: trainingRunParameterDefaults.fineTuningPolicy,
    useBestCheckpoint: String(trainingRunParameterDefaults.useBestCheckpoint),
  };
}

export function validateTrainingRunParameterState(
  state: TrainingRunParameterFormState,
): TrainingRunParameterValidationResult {
  const errors: TrainingRunParameterErrors = {};
  const parsedValues: Partial<CreateTrainingRunParametersApiEntry> = {};

  for (const field of positiveIntegerFields) {
    const parsedValue = parseNumber(state[field]);
    if (parsedValue === null) {
      errors[field] = "Pole jest wymagane.";
      continue;
    }

    if (!Number.isInteger(parsedValue)) {
      errors[field] = "Pole musi byc liczba calkowita.";
      continue;
    }

    if (parsedValue <= 0) {
      errors[field] = "Pole musi byc wieksze od zera.";
      continue;
    }

    parsedValues[field] = parsedValue;
  }

  const warmupEpochs = parseNumber(state.warmupEpochs);
  if (warmupEpochs === null) {
    errors.warmupEpochs = "Pole jest wymagane.";
  } else if (!Number.isInteger(warmupEpochs)) {
    errors.warmupEpochs = "Pole musi byc liczba calkowita.";
  } else if (warmupEpochs < 0) {
    errors.warmupEpochs = "Pole nie moze byc ujemne.";
  } else {
    parsedValues.warmupEpochs = warmupEpochs;
  }

  const learningRate = parseNumber(state.learningRate);
  if (learningRate === null) {
    errors.learningRate = "Pole jest wymagane.";
  } else if (learningRate <= 0 || learningRate > 1) {
    errors.learningRate = "Pole musi byc > 0 i <= 1.";
  } else {
    parsedValues.learningRate = learningRate;
  }

  const earlyStoppingMinDelta = parseNumber(state.earlyStoppingMinDelta);
  if (earlyStoppingMinDelta === null) {
    errors.earlyStoppingMinDelta = "Pole jest wymagane.";
  } else if (earlyStoppingMinDelta < 0) {
    errors.earlyStoppingMinDelta = "Pole nie moze byc ujemne.";
  } else {
    parsedValues.earlyStoppingMinDelta = earlyStoppingMinDelta;
  }

  const lrSchedulerFactor = parseNumber(state.lrSchedulerFactor);
  if (lrSchedulerFactor === null) {
    errors.lrSchedulerFactor = "Pole jest wymagane.";
  } else if (lrSchedulerFactor <= 0 || lrSchedulerFactor >= 1) {
    errors.lrSchedulerFactor = "Pole musi byc > 0 i < 1.";
  } else {
    parsedValues.lrSchedulerFactor = lrSchedulerFactor;
  }

  const fineTuningPolicy = state.fineTuningPolicy.trim().toLowerCase();
  if (fineTuningPolicy !== "all" && fineTuningPolicy !== "head-only") {
    errors.fineTuningPolicy = "Wybierz obslugiwana polityke fine-tuningu.";
  } else {
    parsedValues.fineTuningPolicy = fineTuningPolicy;
  }

  const useBestCheckpoint = state.useBestCheckpoint.trim().toLowerCase();
  if (useBestCheckpoint !== "true" && useBestCheckpoint !== "false") {
    errors.useBestCheckpoint = "Wybierz, czy finalny model ma pochodzic z najlepszego checkpointu.";
  } else {
    parsedValues.useBestCheckpoint = useBestCheckpoint === "true";
  }

  const errorCount = Object.keys(errors).length;
  if (errorCount > 0) {
    return {
      apiEntry: null,
      isValid: false,
      errorCount,
      errors,
      overrideCount: countOverrides(state, parsedValues),
    };
  }

  return {
    apiEntry: parsedValues as CreateTrainingRunParametersApiEntry,
    isValid: true,
    errorCount: 0,
    errors: {},
    overrideCount: countOverrides(state, parsedValues),
  };
}
