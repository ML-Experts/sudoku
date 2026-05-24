import type { SolveCellInferenceContextState } from "../domain/solveCellInferenceParameterDefinitions";
import {
  solveCellInferenceParameterDefinitions,
  type SolveCellInferenceParameterKey,
} from "../domain/solveCellInferenceParameterDefinitions";
import type { Uc14NumberParameterFieldState } from "../domain/uc14ParameterFieldState";
import { Uc14ParameterNumberField } from "./Uc14ParameterNumberField";
import { Uc14ParameterSelector } from "./Uc14ParameterSelector";

type Uc14SolveCellInferenceParametersPanelProps = {
  state: SolveCellInferenceContextState;
  isValid: boolean;
  errorCount: number;
  overrideCount: number;
  onReset: () => void;
  onSetValue: (key: SolveCellInferenceParameterKey, rawValue: string) => void;
};

export function Uc14SolveCellInferenceParametersPanel({
  state,
  isValid,
  errorCount,
  overrideCount,
  onReset,
  onSetValue,
}: Uc14SolveCellInferenceParametersPanelProps) {
  return (
    <section className="uc14-aside-card" aria-label="Panel parametrow rozpoznania">
      <div className="uc14-aside-header">
        <p className="eyebrow">UC-14 - Parametry solve</p>
        <h2>Detekcja zajetosci komorki</h2>
        <p className="muted-copy">
          Pola sa wysylane razem z <code>PUT /api/sudoku/cells/inference</code>.
        </p>
      </div>

      <div className="uc14-panel">
        <div className="uc14-panel-header">
          <div>
            <p className="eyebrow">Solve / cell inference</p>
            <h3>Parametry rozpoznania komorek</h3>
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
          Frontend wysyla pelny snapshot parametrow detekcji pustej lub zajetej
          komorki, a backend nadal pozostaje zrodlem prawdy dla walidacji i
          wartosci efektywnych.
        </p>

        <Uc14ParameterSelector
          title="Wybierz parametr do zmiany"
          description="Edytor pokazuje jeden parametr naraz, zgodnie ze stylem panelu z pominietego wdrozenia UC-14."
          definitions={solveCellInferenceParameterDefinitions}
          state={state}
        >
          {(activeKey) => {
            const activeDefinition = solveCellInferenceParameterDefinitions.find(
              (definition) => definition.key === activeKey,
            );

            if (!activeDefinition) {
              return null;
            }

            return (
              <Uc14ParameterNumberField
                definition={activeDefinition}
                state={state[activeDefinition.key] as Uc14NumberParameterFieldState}
                onChange={(rawValue) => onSetValue(activeDefinition.key, rawValue)}
              />
            );
          }}
        </Uc14ParameterSelector>

        {!isValid ? (
          <p className="status-banner status-error">
            Popraw pola z bledami, zanim uruchomisz rozpoznanie komorek.
          </p>
        ) : null}
      </div>
    </section>
  );
}
