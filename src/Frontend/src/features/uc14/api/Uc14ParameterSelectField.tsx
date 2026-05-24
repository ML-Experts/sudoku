import type {
  Uc14SelectParameterDefinition,
  Uc14SelectParameterOption,
} from "../domain/uc14ParameterDefinition";

type Uc14ParameterSelectFieldState = {
  rawValue: string;
  defaultValue: string;
  isDirty: boolean;
  error: string | null;
};

type Uc14ParameterSelectFieldProps<TKey extends string> = {
  definition: Uc14SelectParameterDefinition<TKey>;
  state: Uc14ParameterSelectFieldState;
  onChange: (rawValue: string) => void;
};

function resolveOptionLabel(
  options: readonly Uc14SelectParameterOption[],
  value: string,
): string {
  return options.find((option) => option.value === value)?.label ?? value;
}

export function Uc14ParameterSelectField<TKey extends string>({
  definition,
  state,
  onChange,
}: Uc14ParameterSelectFieldProps<TKey>) {
  const inputId = `uc14-field-${definition.key}`;
  const errorId = `${inputId}-error`;
  const currentValueLabel = resolveOptionLabel(definition.options, state.rawValue);
  const defaultValueLabel = resolveOptionLabel(
    definition.options,
    state.defaultValue,
  );

  return (
    <article className="uc14-parameter-field">
      <div className="uc14-parameter-field-header">
        <div>
          <h4>{definition.label}</h4>
          <p className="muted-copy">{definition.description}</p>
        </div>
        <span
          className={`uc14-parameter-status ${state.isDirty ? "is-dirty" : "is-default"}`}
        >
          {state.isDirty ? "Override aktywny" : "Domyslna wartosc"}
        </span>
      </div>

      <label className="uc14-parameter-input" htmlFor={inputId}>
        <span>Aktualna wartosc</span>
        <div className="uc14-parameter-input-row">
          <select
            className="uc14-parameter-select-legacy"
            id={inputId}
            value={state.rawValue}
            aria-invalid={state.error ? true : undefined}
            aria-describedby={state.error ? errorId : undefined}
            onChange={(event) => onChange(event.target.value)}
          >
            {definition.options.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </label>

      {definition.guidance ? (
        <section className="uc14-parameter-guidance" aria-label="Opis parametru">
          <div>
            <h5>Do czego sluzy</h5>
            <p>{definition.guidance.purpose}</p>
          </div>
          <div>
            <h5>Wplyw zmiany</h5>
            <p>{definition.guidance.effect}</p>
          </div>
          <div>
            <h5>Kiedy warto zmienic</h5>
            <p>{definition.guidance.whenToChange}</p>
          </div>
          {definition.guidance.recommendation ? (
            <div>
              <h5>Rekomendacja</h5>
              <p>{definition.guidance.recommendation}</p>
            </div>
          ) : null}
        </section>
      ) : null}

      <dl className="uc14-parameter-meta">
        <div>
          <dt>Aktualnie</dt>
          <dd>{currentValueLabel}</dd>
        </div>
        <div>
          <dt>Domyslnie</dt>
          <dd>{defaultValueLabel}</dd>
        </div>
        <div>
          <dt>Dostepne opcje</dt>
          <dd>{definition.options.map((option) => option.label).join(", ")}</dd>
        </div>
      </dl>

      <section className="uc14-parameter-guidance" aria-label="Opcje parametru">
        {definition.options.map((option) => (
          <div key={option.value}>
            <h5>{option.label}</h5>
            <p>{option.description ?? "Brak dodatkowego opisu tej opcji."}</p>
          </div>
        ))}
      </section>

      {state.error ? (
        <p id={errorId} className="uc14-parameter-error" role="alert">
          {state.error}
        </p>
      ) : null}
    </article>
  );
}
