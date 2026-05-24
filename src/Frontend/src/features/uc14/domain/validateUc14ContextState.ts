import type { Uc14ContextState } from "./uc14ParameterFieldState";

export type Uc14ContextValidationResult<TKey extends string = string> = {
  isValid: boolean;
  invalidKeys: TKey[];
  errorCount: number;
};

export function validateUc14ContextState<TKey extends string>(
  state: Uc14ContextState<TKey>,
): Uc14ContextValidationResult<TKey> {
  const invalidKeys = (Object.keys(state) as TKey[]).reduce<TKey[]>(
    (result, key) => {
      if (state[key].error) {
        result.push(key);
      }

      return result;
    },
    [],
  );

  return {
    isValid: invalidKeys.length === 0,
    invalidKeys,
    errorCount: invalidKeys.length,
  };
}
