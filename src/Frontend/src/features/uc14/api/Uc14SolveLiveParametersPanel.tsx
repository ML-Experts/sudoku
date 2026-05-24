import type { SolveLiveContextState } from "../domain/solveLiveParameterDefinitions";
import {
  solveLiveParameterDefinitions,
  type SolveLiveParameterKey,
} from "../domain/solveLiveParameterDefinitions";
import { solveLiveDefaults } from "../domain/solveLiveDefaults";
import type { Uc14NumberParameterFieldState } from "../domain/uc14ParameterFieldState";
import { Uc14ParameterNumberField } from "./Uc14ParameterNumberField";
import { Uc14ParameterSelector } from "./Uc14ParameterSelector";

type Uc14SolveLiveParametersPanelProps = {
  state: SolveLiveContextState;
  isValid: boolean;
  errorCount: number;
  overrideCount: number;
  onReset: () => void;
  onSetValue: (key: SolveLiveParameterKey, rawValue: string) => void;
};

export function Uc14SolveLiveParametersPanel({
  state,
  isValid,
  errorCount,
  overrideCount,
  onReset,
  onSetValue,
}: Uc14SolveLiveParametersPanelProps) {
  return (
    <section className="uc14-aside-card" aria-label="Panel parametrow live solve">
      <div className="uc14-aside-header">
        <p className="eyebrow">UC-14 - Parametry solve</p>
        <h2>Start sesji live solve</h2>
        <p className="muted-copy">
          Parametry sa wysylane razem z <code>POST /api/sudoku/solve</code>.
        </p>
      </div>

      <div className="uc14-panel">
        <div className="uc14-panel-header">
          <div>
            <p className="eyebrow">Solve / live</p>
            <h3>Parametry startu solvera</h3>
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
          Domyslne opoznienie startowe wynosi{" "}
          <strong>{solveLiveDefaults.solverStepDelayMs} ms</strong>.
        </p>

        <Uc14ParameterSelector
          title="Wybierz parametr do zmiany"
          description="Edytor pokazuje pojedynczy parametr dla nowo uruchamianej sesji solve."
          definitions={solveLiveParameterDefinitions}
          state={state}
        >
          {(activeKey) => {
            const activeDefinition = solveLiveParameterDefinitions.find(
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
            Popraw pola z bledami, zanim uruchomisz nowa sesje live solve.
          </p>
        ) : null}
      </div>
    </section>
  );
}
