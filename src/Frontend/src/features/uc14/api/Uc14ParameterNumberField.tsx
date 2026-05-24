import type { Uc14NumberParameterDefinition } from "../domain/uc14ParameterDefinition";
import type { Uc14NumberParameterFieldState } from "../domain/uc14ParameterFieldState";

type Uc14ParameterNumberFieldProps<TKey extends string> = {
  definition: Uc14NumberParameterDefinition<TKey>;
  state: Uc14NumberParameterFieldState;
  onChange: (rawValue: string) => void;
};

function formatNumber(value: number): string {
  if (Number.isInteger(value)) {
    return String(value);
  }

  return value.toFixed(4).replace(/\.?0+$/, "");
}

function formatRange<TKey extends string>(
  definition: Uc14NumberParameterDefinition<TKey>,
): string {
  const lowerBoundary = (definition.minInclusive ?? true) ? "[" : "(";
  const upperBoundary = (definition.maxInclusive ?? true) ? "]" : ")";
  const unitLabel = definition.unitLabel ?? "";
  const minLabel =
    typeof definition.min === "number" ? formatNumber(definition.min) : "-inf";
  const maxLabel =
    typeof definition.max === "number" ? formatNumber(definition.max) : "+inf";

  return `${lowerBoundary}${minLabel}, ${maxLabel}${upperBoundary}${unitLabel}`;
}

export function Uc14ParameterNumberField<TKey extends string>({
  definition,
  state,
  onChange,
}: Uc14ParameterNumberFieldProps<TKey>) {
  const inputId = `uc14-field-${definition.key}`;
  const errorId = `${inputId}-error`;
  const unitLabel = definition.unitLabel ?? "";
  const currentValueLabel =
    state.parsedValue === null ? state.rawValue : formatNumber(state.parsedValue);

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
          <input
            id={inputId}
            type="number"
            inputMode={definition.integerOnly ? "numeric" : "decimal"}
            step={definition.step ?? "any"}
            min={definition.min}
            max={definition.max}
            value={state.rawValue}
            aria-invalid={state.error ? true : undefined}
            aria-describedby={state.error ? errorId : undefined}
            onChange={(event) => onChange(event.target.value)}
          />
          {unitLabel ? <span className="uc14-parameter-unit">{unitLabel}</span> : null}
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
          <dd>
            {currentValueLabel}
            {unitLabel}
          </dd>
        </div>
        <div>
          <dt>Domyslnie</dt>
          <dd>
            {formatNumber(state.defaultValue)}
            {unitLabel}
          </dd>
        </div>
        <div>
          <dt>Zakres</dt>
          <dd>{formatRange(definition)}</dd>
        </div>
      </dl>

      {state.error ? (
        <p id={errorId} className="uc14-parameter-error" role="alert">
          {state.error}
        </p>
      ) : null}
    </article>
  );
}
