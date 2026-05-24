import type { Uc14NumberParameterDefinition } from "./uc14ParameterDefinition";
import type {
  Uc14ContextDefaults,
  Uc14ContextState,
} from "./uc14ParameterFieldState";

export function createUc14ContextState<TKey extends string>(
  definitions: readonly Uc14NumberParameterDefinition<TKey>[],
  defaults: Uc14ContextDefaults<TKey>,
): Uc14ContextState<TKey> {
  return definitions.reduce(
    (state, definition) => {
      const defaultValue = defaults[definition.key];

      state[definition.key] = {
        kind: "number",
        rawValue: String(defaultValue),
        parsedValue: typeof defaultValue === "number" ? defaultValue : null,
        defaultValue: typeof defaultValue === "number" ? defaultValue : 0,
        isDirty: false,
        error: null,
      };

      return state;
    },
    {} as Uc14ContextState<TKey>,
  );
}
