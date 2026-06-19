import { Uc06TrainingSection } from "../../components/Uc06TrainingSection";
import { Uc08CatalogSection } from "../../components/Uc08CatalogSection";
import { Uc11RawCandidatesSection } from "../../components/Uc11RawCandidatesSection";
import { Uc12DatasetPreparationSection } from "../../components/Uc12DatasetPreparationSection";
import { Uc17RawCandidatesSection } from "../../features/uc17/api";
import { Uc18BoardFoldersSection } from "../../features/uc18/api";
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
  trainingRunParameterValidation: TrainingRunParameterValidationResult;
};

export function DatasetsView({
  accessToken,
  apiBaseUrl,
  datasetsStep,
  onDatasetsStepChange,
  onUnauthorized,
  trainingRunParameterValidation,
}: DatasetsViewProps) {
  const activeSection =
    datasetsStep === "uc11" ? (
      <Uc11RawCandidatesSection
        apiBaseUrl={apiBaseUrl}
        accessToken={accessToken}
        onUnauthorized={onUnauthorized}
      />
    ) : datasetsStep === "uc17" ? (
      <Uc17RawCandidatesSection
        apiBaseUrl={apiBaseUrl}
        accessToken={accessToken}
        onUnauthorized={onUnauthorized}
      />
    ) : datasetsStep === "uc18" ? (
      <Uc18BoardFoldersSection
        apiBaseUrl={apiBaseUrl}
        accessToken={accessToken}
        onUnauthorized={onUnauthorized}
      />
    ) : datasetsStep === "uc12" ? (
      <Uc12DatasetPreparationSection
        apiBaseUrl={apiBaseUrl}
        accessToken={accessToken}
        onUnauthorized={onUnauthorized}
      />
    ) : datasetsStep === "uc06" ? (
      <Uc06TrainingSection
        apiBaseUrl={apiBaseUrl}
        accessToken={accessToken}
        onUnauthorized={onUnauthorized}
        trainingParameters={trainingRunParameterValidation.apiEntry}
        trainingParametersValid={trainingRunParameterValidation.isValid}
        trainingParameterErrorCount={trainingRunParameterValidation.errorCount}
        trainingParameterOverrideCount={trainingRunParameterValidation.overrideCount}
      />
    ) : (
      <Uc08CatalogSection
        apiBaseUrl={apiBaseUrl}
        accessToken={accessToken}
        onUnauthorized={onUnauthorized}
      />
    );

  return (
    <>
      <section className="hero-card datasets-module-header">
        <p className="eyebrow">Workflow datasetowy</p>
        <h2>UC-11 -&gt; UC-17 -&gt; UC-18 -&gt; UC-12 (legacy) -&gt; UC-06 -&gt; UC-08</h2>
        <p className="hero-copy">
          Nawiguj krokami: najpierw kandydaci raw, potem przygotowanie datasetu i
          przeglad zrodel `board`, a osobno pozostaje stary workflow `UC-12` do
          bezposredniego builda datasetu processed.
        </p>
        <div className="datasets-stepper" role="tablist" aria-label="Kroki datasetu">
          <DatasetStepButton
            isActive={datasetsStep === "uc11"}
            label="1. Przeglad kandydatow raw (UC-11)"
            onClick={() => onDatasetsStepChange("uc11")}
          />
          <DatasetStepButton
            isActive={datasetsStep === "uc17"}
            label="2. Przygotowanie datasetu (UC-17)"
            onClick={() => onDatasetsStepChange("uc17")}
          />
          <DatasetStepButton
            isActive={datasetsStep === "uc18"}
            label="3. Przeglad zrodel preparation (UC-18)"
            onClick={() => onDatasetsStepChange("uc18")}
          />
          <DatasetStepButton
            isActive={datasetsStep === "uc12"}
            label="4. Legacy: dataset processed (UC-12)"
            onClick={() => onDatasetsStepChange("uc12")}
          />
          <DatasetStepButton
            isActive={datasetsStep === "uc06"}
            label="5. Start i monitoring treningu (UC-06)"
            onClick={() => onDatasetsStepChange("uc06")}
          />
          <DatasetStepButton
            isActive={datasetsStep === "uc08"}
            label="6. Katalog runow i modeli (UC-08)"
            onClick={() => onDatasetsStepChange("uc08")}
          />
        </div>
      </section>
      {activeSection}
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
