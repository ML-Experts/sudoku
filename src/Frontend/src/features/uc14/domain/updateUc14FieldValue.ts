import type { Uc14NumberParameterDefinition } from "./uc14ParameterDefinition";
import type { Uc14ContextState } from "./uc14ParameterFieldState";

function isWithinRange<TKey extends string>(
  parsedValue: number,
  definition: Uc14NumberParameterDefinition<TKey>,
): boolean {
  const minInclusive = definition.minInclusive ?? true;
  const maxInclusive = definition.maxInclusive ?? true;
  const minCheck =
    definition.min === undefined
      ? true
      : minInclusive
        ? parsedValue >= definition.min
        : parsedValue > definition.min;
  const maxCheck =
    definition.max === undefined
      ? true
      : maxInclusive
        ? parsedValue <= definition.max
        : parsedValue < definition.max;

  return minCheck && maxCheck;
}

function createRangeMessage<TKey extends string>(
  definition: Uc14NumberParameterDefinition<TKey>,
): string {
  const lowerBoundary = (definition.minInclusive ?? true) ? "[" : "(";
  const upperBoundary = (definition.maxInclusive ?? true) ? "]" : ")";
  const unitLabel = definition.unitLabel ?? "";
  const minLabel = definition.min ?? "-inf";
  const maxLabel = definition.max ?? "+inf";

  return `Wartosc musi miescic sie w zakresie ${lowerBoundary}${minLabel}, ${maxLabel}${upperBoundary}${unitLabel}.`;
}

export function updateUc14FieldValue<TKey extends string>(
  state: Uc14ContextState<TKey>,
  definitions: readonly Uc14NumberParameterDefinition<TKey>[],
  key: TKey,
  rawValue: string,
): Uc14ContextState<TKey> {
  const definition = definitions.find((item) => item.key === key);
  if (!definition) {
    return state;
  }

  const currentField = state[key];
  const trimmedValue = rawValue.trim();

  if (trimmedValue.length === 0) {
    return {
      ...state,
      [key]: {
        ...currentField,
        rawValue,
        parsedValue: null,
        isDirty: false,
        error: "Podaj wartosc liczbowa.",
      },
    };
  }

  const parsedValue = Number(trimmedValue);
  if (!Number.isFinite(parsedValue)) {
    return {
      ...state,
      [key]: {
        ...currentField,
        rawValue,
        parsedValue: null,
        isDirty: true,
        error: "Podaj poprawna liczbe.",
      },
    };
  }

  if (definition.integerOnly && !Number.isInteger(parsedValue)) {
    return {
      ...state,
      [key]: {
        ...currentField,
        rawValue,
        parsedValue,
        isDirty: parsedValue !== currentField.defaultValue,
        error: "Podaj liczbe calkowita.",
      },
    };
  }

  if (!isWithinRange(parsedValue, definition)) {
    return {
      ...state,
      [key]: {
        ...currentField,
        rawValue,
        parsedValue,
        isDirty: parsedValue !== currentField.defaultValue,
        error: createRangeMessage(definition),
      },
    };
  }

  return {
    ...state,
    [key]: {
      ...currentField,
      rawValue,
      parsedValue,
      isDirty: parsedValue !== currentField.defaultValue,
      error: null,
    },
  };
}
