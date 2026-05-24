export type Uc14NumberParameterFieldState = {
  kind: "number";
  rawValue: string;
  parsedValue: number | null;
  defaultValue: number;
  isDirty: boolean;
  error: string | null;
};

export type Uc14ParameterFieldState = Uc14NumberParameterFieldState;

export type Uc14ContextDefaults<TKey extends string = string> = Record<TKey, number>;

export type Uc14ContextState<TKey extends string = string> = Record<
  TKey,
  Uc14ParameterFieldState
>;
