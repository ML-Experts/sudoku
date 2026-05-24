export type Uc14ParameterGuidance = {
  purpose: string;
  effect: string;
  whenToChange: string;
  recommendation?: string;
};

type Uc14BaseParameterDefinition<TKey extends string> = {
  key: TKey;
  label: string;
  description: string;
  guidance?: Uc14ParameterGuidance;
  advanced?: boolean;
};

export type Uc14NumberParameterDefinition<TKey extends string = string> =
  Uc14BaseParameterDefinition<TKey> & {
    kind: "number";
    min?: number;
    max?: number;
    minInclusive?: boolean;
    maxInclusive?: boolean;
    step?: number;
    unitLabel?: string;
    integerOnly?: boolean;
  };

export type Uc14SelectParameterOption<TValue extends string = string> = {
  value: TValue;
  label: string;
  description?: string;
};

export type Uc14SelectParameterDefinition<TKey extends string = string> =
  Uc14BaseParameterDefinition<TKey> & {
    kind: "select";
    options: readonly Uc14SelectParameterOption[];
  };

export type Uc14ParameterDefinition<TKey extends string = string> =
  | Uc14NumberParameterDefinition<TKey>
  | Uc14SelectParameterDefinition<TKey>;
