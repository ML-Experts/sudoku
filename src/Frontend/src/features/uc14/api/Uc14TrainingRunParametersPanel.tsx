import type { ChangeEvent } from "react";

import type {
  TrainingRunParameterErrors,
  TrainingRunParameterFormState,
} from "../domain/trainingRunParameters";

type Uc14TrainingRunParametersPanelProps = {
  state: TrainingRunParameterFormState;
  errors: TrainingRunParameterErrors;
  isValid: boolean;
  errorCount: number;
  overrideCount: number;
  onReset: () => void;
  onFieldChange: (
    key: keyof TrainingRunParameterFormState,
    value: string,
  ) => void;
};

type NumberFieldDefinition = {
  key:
    | "epochs"
    | "learningRate"
    | "batchSize"
    | "earlyStoppingPatience"
    | "lrSchedulerPatience"
    | "lrSchedulerFactor";
  label: string;
  description: string;
  inputMode: "numeric" | "decimal";
  step?: string;
};

const numberFieldDefinitions: NumberFieldDefinition[] = [
  {
    key: "epochs",
    label: "Liczba epok",
    description: "Maksymalna liczba epok dla nowego runu treningowego.",
    inputMode: "numeric",
    step: "1",
  },
  {
    key: "learningRate",
    label: "Learning rate",
    description: "Krok uczenia przekazywany do workflow treningu.",
    inputMode: "decimal",
    step: "0.0001",
  },
  {
    key: "batchSize",
    label: "Batch size",
    description: "Rozmiar batcha dla treningu modelu.",
    inputMode: "numeric",
    step: "1",
  },
  {
    key: "earlyStoppingPatience",
    label: "Early stopping patience",
    description: "Liczba epok bez poprawy przed wczesnym zatrzymaniem.",
    inputMode: "numeric",
    step: "1",
  },
  {
    key: "lrSchedulerPatience",
    label: "LR scheduler patience",
    description: "Liczba epok bez poprawy przed redukcja learning rate.",
    inputMode: "numeric",
    step: "1",
  },
  {
    key: "lrSchedulerFactor",
    label: "LR scheduler factor",
    description: "Wspolczynnik redukcji learning rate.",
    inputMode: "decimal",
    step: "0.1",
  },
];

function handleInputChange(
  key: keyof TrainingRunParameterFormState,
  onFieldChange: (
    fieldKey: keyof TrainingRunParameterFormState,
    value: string,
  ) => void,
) {
  return (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    onFieldChange(key, event.target.value);
  };
}

export function Uc14TrainingRunParametersPanel({
  state,
  errors,
  isValid,
  errorCount,
  overrideCount,
  onReset,
  onFieldChange,
}: Uc14TrainingRunParametersPanelProps) {
  return (
    <section className="uc14-aside-card" aria-label="Panel parametrow treningu">
      <div className="uc14-aside-header">
        <p className="eyebrow">UC-14 — Parametry treningu</p>
        <h2>Panel startu runu</h2>
        <p className="muted-copy">
          Pola sa wysylane razem z <code>POST /api/trainings</code> jako{" "}
          <code>trainingParameters</code>.
        </p>
      </div>

      <div className="uc14-panel">
        <div className="uc14-panel-header">
          <div>
            <p className="eyebrow">Train / run start</p>
            <h3>Parametry UC-06</h3>
          </div>
          <button className="secondary-button" type="button" onClick={onReset}>
            Przywroc domyslne
          </button>
        </div>

        <div className="uc14-panel-summary">
          <span className="app-chip">Aktywne override&apos;y: {overrideCount}</span>
          <span
            className={`app-chip ${isValid ? "app-chip-muted" : "uc14-chip-error"}`}
          >
            {isValid ? "Walidacja lokalna: OK" : `Walidacja lokalna: ${errorCount} bledy`}
          </span>
        </div>

        <div className="uc14-fields-list">
          {numberFieldDefinitions.map((field) => (
            <label key={field.key} className="uc12-field">
              <span>{field.label}</span>
              <input
                value={state[field.key]}
                inputMode={field.inputMode}
                step={field.step}
                aria-invalid={errors[field.key] ? "true" : "false"}
                onChange={handleInputChange(field.key, onFieldChange)}
              />
              <span className="muted-copy">{field.description}</span>
              {errors[field.key] ? (
                <span className="uc14-parameter-error">{errors[field.key]}</span>
              ) : null}
            </label>
          ))}

          <label className="uc12-field">
            <span>Fine-tuning policy</span>
            <select
              value={state.fineTuningPolicy}
              aria-invalid={errors.fineTuningPolicy ? "true" : "false"}
              onChange={handleInputChange("fineTuningPolicy", onFieldChange)}
            >
              <option value="all">all</option>
              <option value="head-only">head-only</option>
            </select>
            <span className="muted-copy">
              Polityka <code>head-only</code> jest walidowana dodatkowo przez BE
              i przejdzie tylko dla wspieranych modeli.
            </span>
            {errors.fineTuningPolicy ? (
              <span className="uc14-parameter-error">
                {errors.fineTuningPolicy}
              </span>
            ) : null}
          </label>
        </div>

        {!isValid ? (
          <p className="status-banner status-error">
            Popraw pola z bledami, zanim uruchomisz nowy run treningowy.
          </p>
        ) : null}
      </div>
    </section>
  );
}
