import { useMemo } from "react";

import type {
  TrainingRunParameterErrors,
  TrainingRunParameterFormState,
} from "../domain/trainingRunParameters";
import { trainingRunParameterDefaults } from "../domain/trainingRunParameters";
import {
  trainingRunParameterDefinitions,
  type TrainingRunParameterKey,
} from "../domain/trainingRunParameterDefinitions";
import { Uc14ParameterNumberField } from "./Uc14ParameterNumberField";
import { Uc14ParameterSelector } from "./Uc14ParameterSelector";
import { Uc14ParameterSelectField } from "./Uc14ParameterSelectField";

type Uc14TrainingRunParametersPanelProps = {
  state: TrainingRunParameterFormState;
  errors: TrainingRunParameterErrors;
  isValid: boolean;
  errorCount: number;
  overrideCount: number;
  onReset: () => void;
  onFieldChange: (key: TrainingRunParameterKey, value: string) => void;
};

type TrainingRunNumberParameterKey = Exclude<
  TrainingRunParameterKey,
  "fineTuningPolicy"
>;

function parseNumber(rawValue: string): number | null {
  const normalizedValue = rawValue.trim().replace(",", ".");
  if (!normalizedValue) {
    return null;
  }

  const parsedValue = Number(normalizedValue);
  return Number.isFinite(parsedValue) ? parsedValue : null;
}

function isFieldDirty(
  key: TrainingRunParameterKey,
  state: TrainingRunParameterFormState,
): boolean {
  if (key === "fineTuningPolicy") {
    return (
      state.fineTuningPolicy.trim().toLowerCase() !==
      trainingRunParameterDefaults.fineTuningPolicy
    );
  }

  const rawValue = state[key].trim();
  if (!rawValue) {
    return false;
  }

  const parsedValue = parseNumber(state[key]);
  if (parsedValue === null) {
    return rawValue !== String(trainingRunParameterDefaults[key]);
  }

  return parsedValue !== trainingRunParameterDefaults[key];
}

function createNumberFieldState(
  key: TrainingRunNumberParameterKey,
  state: TrainingRunParameterFormState,
  errors: TrainingRunParameterErrors,
) {
  return {
    kind: "number" as const,
    rawValue: state[key],
    parsedValue: parseNumber(state[key]),
    defaultValue: trainingRunParameterDefaults[key],
    isDirty: isFieldDirty(key, state),
    error: errors[key] ?? null,
  };
}

function createSelectFieldState(
  state: TrainingRunParameterFormState,
  errors: TrainingRunParameterErrors,
) {
  return {
    rawValue: state.fineTuningPolicy,
    defaultValue: trainingRunParameterDefaults.fineTuningPolicy,
    isDirty: isFieldDirty("fineTuningPolicy", state),
    error: errors.fineTuningPolicy ?? null,
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
  const selectorState = useMemo(
    () =>
      trainingRunParameterDefinitions.reduce<
        Record<TrainingRunParameterKey, { error: string | null; isDirty: boolean }>
      >(
        (result, definition) => {
          result[definition.key] = {
            error: errors[definition.key] ?? null,
            isDirty: isFieldDirty(definition.key, state),
          };

          return result;
        },
        {} as Record<
          TrainingRunParameterKey,
          { error: string | null; isDirty: boolean }
        >,
      ),
    [errors, state],
  );

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

        <p className="muted-copy">
          Frontend wysyla pelny snapshot parametrow treningu, a backend nadal
          pozostaje zrodlem prawdy dla walidacji i wartosci efektywnych.
        </p>

        <Uc14ParameterSelector
          title="Wybierz parametr do zmiany"
          description="Edytor pokazuje jeden parametr treningu naraz, tak jak w pozostalych panelach UC-14."
          definitions={trainingRunParameterDefinitions}
          state={selectorState}
        >
          {(activeKey) => {
            const activeDefinition = trainingRunParameterDefinitions.find(
              (definition) => definition.key === activeKey,
            );

            if (!activeDefinition) {
              return null;
            }

            if (activeDefinition.kind === "number") {
              const numberKey = activeDefinition.key as TrainingRunNumberParameterKey;

              return (
                <Uc14ParameterNumberField
                  definition={activeDefinition}
                  state={createNumberFieldState(numberKey, state, errors)}
                  onChange={(rawValue) => onFieldChange(numberKey, rawValue)}
                />
              );
            }

            return (
              <Uc14ParameterSelectField
                definition={activeDefinition}
                state={createSelectFieldState(state, errors)}
                onChange={(rawValue) => onFieldChange("fineTuningPolicy", rawValue)}
              />
            );
          }}
        </Uc14ParameterSelector>

        {!isValid ? (
          <p className="status-banner status-error">
            Popraw pola z bledami, zanim uruchomisz nowy run treningowy.
          </p>
        ) : null}
      </div>
    </section>
  );
}
