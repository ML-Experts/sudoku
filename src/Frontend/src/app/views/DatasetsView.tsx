import { Uc06TrainingSection } from "../../components/Uc06TrainingSection";
import { Uc08CatalogSection } from "../../components/Uc08CatalogSection";
import { Uc11RawCandidatesSection } from "../../components/Uc11RawCandidatesSection";
import { Uc12DatasetPreparationSection } from "../../components/Uc12DatasetPreparationSection";
import type {
  TrainingRunParameterValidationResult,
} from "../../features/uc14/domain/trainingRunParameters";
import type { DatasetsStep } from "../state";

type DatasetsViewProps = {
  accessToken?: string | null;
  apiBaseUrl: string;
  datasetsStep: DatasetsStep;
  onDatasetsStepChange: (step: DatasetsStep) => void;
  onUnauthorized: () => void;
  setUc14PanelVisible: (visible: boolean) => void;
  trainingRunParameterValidation: TrainingRunParameterValidationResult;
};

export function DatasetsView({
  accessToken,
  apiBaseUrl,
  datasetsStep,
  onDatasetsStepChange,
  onUnauthorized,
  setUc14PanelVisible,
  trainingRunParameterValidation,
}: DatasetsViewProps) {
  return (
    <>
      <section className="hero-card datasets-module-header">
        <p className="eyebrow">Workflow datasetowy</p>
        <h2>UC-11 -&gt; UC-12 -&gt; UC-06 -&gt; UC-08</h2>
        <p className="hero-copy">
          Nawiguj krokami: najpierw kandydaci raw, potem budowa datasetu
          processed, potem start treningu i SignalR, a na koncu katalog runow oraz
          modeli.
        </p>
        <div className="datasets-stepper" role="tablist" aria-label="Kroki datasetu">
          <DatasetStepButton
            isActive={datasetsStep === "uc11"}
            label="1. Przeglad kandydatow raw (UC-11)"
            onClick={() => {
              setUc14PanelVisible(false);
              onDatasetsStepChange("uc11");
            }}
          />
          <DatasetStepButton
            isActive={datasetsStep === "uc12"}
            label="2. Budowa datasetu processed (UC-12)"
            onClick={() => {
              setUc14PanelVisible(false);
              onDatasetsStepChange("uc12");
            }}
          />
          <DatasetStepButton
            isActive={datasetsStep === "uc06"}
            label="3. Start i monitoring treningu (UC-06)"
            onClick={() => {
              onDatasetsStepChange("uc06");
              setUc14PanelVisible(true);
            }}
          />
          <DatasetStepButton
            isActive={datasetsStep === "uc08"}
            label="4. Katalog runow i modeli (UC-08)"
            onClick={() => {
              setUc14PanelVisible(false);
              onDatasetsStepChange("uc08");
            }}
          />
        </div>
      </section>

      <div hidden={datasetsStep !== "uc11"} aria-hidden={datasetsStep !== "uc11"}>
        <Uc11RawCandidatesSection
          apiBaseUrl={apiBaseUrl}
          accessToken={accessToken}
          onUnauthorized={onUnauthorized}
        />
      </div>
      <div hidden={datasetsStep !== "uc12"} aria-hidden={datasetsStep !== "uc12"}>
        <Uc12DatasetPreparationSection
          apiBaseUrl={apiBaseUrl}
          accessToken={accessToken}
          onUnauthorized={onUnauthorized}
        />
      </div>
      <div hidden={datasetsStep !== "uc06"} aria-hidden={datasetsStep !== "uc06"}>
        <Uc06TrainingSection
          apiBaseUrl={apiBaseUrl}
          accessToken={accessToken}
          onUnauthorized={onUnauthorized}
          trainingParameters={trainingRunParameterValidation.apiEntry}
          trainingParametersValid={trainingRunParameterValidation.isValid}
          trainingParameterErrorCount={trainingRunParameterValidation.errorCount}
          trainingParameterOverrideCount={trainingRunParameterValidation.overrideCount}
        />
      </div>
      <div hidden={datasetsStep !== "uc08"} aria-hidden={datasetsStep !== "uc08"}>
        <Uc08CatalogSection
          apiBaseUrl={apiBaseUrl}
          accessToken={accessToken}
          onUnauthorized={onUnauthorized}
        />
      </div>
    </>
  );
}

type DatasetStepButtonProps = {
  isActive: boolean;
  label: string;
  onClick: () => void;
};

function DatasetStepButton({
  isActive,
  label,
  onClick,
}: DatasetStepButtonProps) {
  return (
    <button
      type="button"
      role="tab"
      aria-selected={isActive}
      className={`datasets-step ${isActive ? "is-active" : ""}`}
      onClick={onClick}
    >
      {label}
    </button>
  );
}
