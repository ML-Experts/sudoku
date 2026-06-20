import { useCallback, useEffect, useMemo, useState } from "react";

import { AdminLoginModal } from "./app/components/AdminLoginModal";
import { AppHeader } from "./app/components/AppHeader";
import { AppNavigation } from "./app/components/AppNavigation";
import { AuthSessionCard } from "./app/components/AuthSessionCard";
import { useExamplesModule } from "./app/hooks/useExamplesModule";
import {
  defaultLoginState,
  defaultPingState,
  type AppView,
  type DatasetsStep,
  type LoginState,
  type PingResponse,
  type PingState,
} from "./app/state";
import { formatTimestamp, normalizeBaseUrl } from "./app/utils";
import { DatasetsView } from "./app/views/DatasetsView";
import { ExamplesView } from "./app/views/ExamplesView";
import { HealthView } from "./app/views/HealthView";
import { AuthApiError, postAdminLogin } from "./api/auth";
import { useAdminSession } from "./context/AdminSessionContext";
import { getUc14ActiveParameterContext } from "./features/uc14/application/uc14ParameterContexts";
import { Uc14SolveCellInferenceParametersPanel } from "./features/uc14/api/Uc14SolveCellInferenceParametersPanel";
import { Uc14SolveLiveParametersPanel } from "./features/uc14/api/Uc14SolveLiveParametersPanel";
import { Uc14TrainingRunParametersPanel } from "./features/uc14/api/Uc14TrainingRunParametersPanel";
import { createUc14ContextState } from "./features/uc14/domain/createUc14ContextState";
import { solveCellInferenceDefaults } from "./features/uc14/domain/solveCellInferenceDefaults";
import {
  solveCellInferenceParameterDefinitions,
  type SolveCellInferenceContextState,
  type SolveCellInferenceParameterKey,
} from "./features/uc14/domain/solveCellInferenceParameterDefinitions";
import { solveLiveDefaults } from "./features/uc14/domain/solveLiveDefaults";
import {
  solveLiveParameterDefinitions,
  type SolveLiveContextState,
  type SolveLiveParameterKey,
} from "./features/uc14/domain/solveLiveParameterDefinitions";
import { toSolveSudokuParametersApiEntry } from "./features/uc14/domain/toSolveSudokuParametersApiEntry";
import { toSudokuCellInferenceParametersApiEntry } from "./features/uc14/domain/toSudokuCellInferenceParametersApiEntry";
import type { Uc14ContextState } from "./features/uc14/domain/uc14ParameterFieldState";
import type { Uc14ActiveParameterContext } from "./features/uc14/domain/uc14ParameterContext";
import {
  createTrainingRunParameterFormState,
  type TrainingRunParameterFormState,
  validateTrainingRunParameterState,
} from "./features/uc14/domain/trainingRunParameters";
import { updateUc14FieldValue } from "./features/uc14/domain/updateUc14FieldValue";
import { validateUc14ContextState } from "./features/uc14/domain/validateUc14ContextState";

function countUc14Overrides<TKey extends string>(state: Uc14ContextState<TKey>): number {
  return (Object.values(state) as Array<Uc14ContextState<TKey>[TKey]>).filter(
    (field) => field.isDirty && !field.error,
  ).length;
}

function getExamplesUc14ContextLabel(
  context: Exclude<Uc14ActiveParameterContext, null>,
): string {
  return context === "solveCellInference"
    ? "Rozpoznanie komorek"
    : "Live solve";
}

export default function App() {
  const apiBaseUrl = normalizeBaseUrl(import.meta.env.VITE_API_BASE_URL);
  const pingEndpoint = `${apiBaseUrl}/ping`;
  const examplesUploadEndpoint = `${apiBaseUrl}/examples`;
  const {
    mode,
    authToken,
    loginModalOpen,
    loginPromptMessage,
    continueInDemoMode,
    openLoginModal,
    applyAdminSession,
    clearAdminSessionAndRequireLogin,
    logoutAdmin,
  } = useAdminSession();

  const [pingState, setPingState] = useState<PingState>(defaultPingState);
  const [adminPassword, setAdminPassword] = useState("");
  const [loginState, setLoginState] = useState<LoginState>(defaultLoginState);
  const [activeView, setActiveView] = useState<AppView>("health");
  const [datasetsStep, setDatasetsStep] = useState<DatasetsStep>("uc11");
  const [examplesWorkflowContext, setExamplesWorkflowContext] =
    useState<Uc14ActiveParameterContext>(null);
  const [manualExamplesWorkflowContext, setManualExamplesWorkflowContext] =
    useState<Uc14ActiveParameterContext>(null);
  const [solveCellInferenceState, setSolveCellInferenceState] =
    useState<SolveCellInferenceContextState>(() =>
      createUc14ContextState(
        solveCellInferenceParameterDefinitions,
        solveCellInferenceDefaults,
      ),
    );
  const [solveLiveState, setSolveLiveState] = useState<SolveLiveContextState>(() =>
    createUc14ContextState(solveLiveParameterDefinitions, solveLiveDefaults),
  );
  const [trainingRunParameterState, setTrainingRunParameterState] = useState(
    createTrainingRunParameterFormState,
  );
  const isAdminMode = mode === "admin";
  const isDemoMode = mode === "demo";
  const solveCellInferenceValidation = useMemo(
    () => validateUc14ContextState(solveCellInferenceState),
    [solveCellInferenceState],
  );
  const solveLiveValidation = useMemo(
    () => validateUc14ContextState(solveLiveState),
    [solveLiveState],
  );
  const solveCellInferenceParameters = useMemo(
    () =>
      solveCellInferenceValidation.isValid
        ? toSudokuCellInferenceParametersApiEntry(solveCellInferenceState)
        : null,
    [solveCellInferenceState, solveCellInferenceValidation.isValid],
  );
  const solveLiveParameters = useMemo(
    () =>
      solveLiveValidation.isValid
        ? toSolveSudokuParametersApiEntry(solveLiveState)
        : null,
    [solveLiveState, solveLiveValidation.isValid],
  );
  const solveCellInferenceOverrideCount = useMemo(
    () => countUc14Overrides(solveCellInferenceState),
    [solveCellInferenceState],
  );
  const solveLiveOverrideCount = useMemo(
    () => countUc14Overrides(solveLiveState),
    [solveLiveState],
  );
  const trainingRunParameterValidation = useMemo(
    () => validateTrainingRunParameterState(trainingRunParameterState),
    [trainingRunParameterState],
  );
  const availableExamplesUc14Contexts = useMemo<
    Array<Exclude<Uc14ActiveParameterContext, null>>
  >(() => {
    if (examplesWorkflowContext === "solveLive") {
      return ["solveCellInference", "solveLive"];
    }

    if (examplesWorkflowContext === "solveCellInference") {
      return ["solveCellInference"];
    }

    return [];
  }, [examplesWorkflowContext]);
  const resolvedExamplesWorkflowContext =
    manualExamplesWorkflowContext !== null &&
    availableExamplesUc14Contexts.includes(manualExamplesWorkflowContext)
      ? manualExamplesWorkflowContext
      : examplesWorkflowContext;
  const activeUc14Context = getUc14ActiveParameterContext({
    activeView,
    datasetsStep,
    examplesWorkflowContext: resolvedExamplesWorkflowContext,
  });
  const hasUc14Panel = activeUc14Context !== null;

  const handleAdminUnauthorized = useCallback(
    (tokenErrorType?: string | null) => {
      const isTokenError =
        tokenErrorType === "admin_token_expired" ||
        tokenErrorType === "admin_token_invalid" ||
        tokenErrorType === "invalid_token";

      clearAdminSessionAndRequireLogin(
        isTokenError
          ? "Sesja administracyjna wygasla lub token jest niepoprawny. Zaloguj sie ponownie."
          : "Brak autoryzacji do operacji administracyjnej. Zaloguj sie ponownie.",
      );
      setAdminPassword("");
      setLoginState(defaultLoginState);
    },
    [clearAdminSessionAndRequireLogin],
  );

  const examplesModule = useExamplesModule({
    apiBaseUrl,
    isAdminMode,
    accessToken: authToken?.accessToken ?? null,
    onRequireLogin: openLoginModal,
    onUnauthorized: handleAdminUnauthorized,
  });

  const activeViewLabel =
    activeView === "health"
      ? "Healthcheck"
      : activeView === "examples"
        ? "Przyklady"
        : "Datasety";
  const datasetsStepLabel =
    datasetsStep === "uc11"
      ? "UC-11 — Przeglad kandydatow raw"
      : datasetsStep === "uc17"
        ? "UC-17 — Przygotowanie datasetu"
        : datasetsStep === "uc18"
          ? "UC-18 — Przeglad zrodel preparation"
          : datasetsStep === "uc12"
            ? "UC-12 — Legacy: budowa datasetu processed"
            : datasetsStep === "uc06"
              ? "UC-06 — Start i monitoring treningu"
              : "UC-08 — Katalog runow i modeli";

  async function handleAdminLoginSubmit() {
    if (!adminPassword.trim()) {
      setLoginState({
        kind: "error",
        error: "Podaj haslo administracyjne.",
        errorType: null,
        httpStatus: null,
      });
      return;
    }

    setLoginState({
      kind: "loading",
      error: null,
      errorType: null,
      httpStatus: null,
    });

    try {
      const token = await postAdminLogin(apiBaseUrl, { password: adminPassword });
      applyAdminSession(token);
      setAdminPassword("");
      setLoginState(defaultLoginState);
    } catch (error) {
      if (error instanceof AuthApiError) {
        setLoginState({
          kind: "error",
          error: error.message,
          errorType: error.errorType ?? null,
          httpStatus: error.status,
        });
        return;
      }

      setLoginState({
        kind: "error",
        error:
          error instanceof Error
            ? error.message
            : "Nie udalo sie zalogowac do trybu administracyjnego.",
        errorType: null,
        httpStatus: null,
      });
    }
  }

  const handleTrainingRunParameterChange = useCallback(
    (key: keyof TrainingRunParameterFormState, value: string) => {
      setTrainingRunParameterState((previous) => ({
        ...previous,
        [key]: value,
      }));
    },
    [],
  );

  const resetTrainingRunParameters = useCallback(() => {
    setTrainingRunParameterState(createTrainingRunParameterFormState());
  }, []);
  const handleSolveCellInferenceParameterChange = useCallback(
    (key: SolveCellInferenceParameterKey, rawValue: string) => {
      setSolveCellInferenceState((previous) =>
        updateUc14FieldValue(
          previous,
          solveCellInferenceParameterDefinitions,
          key,
          rawValue,
        ),
      );
    },
    [],
  );
  const handleSolveLiveParameterChange = useCallback(
    (key: SolveLiveParameterKey, rawValue: string) => {
      setSolveLiveState((previous) =>
        updateUc14FieldValue(
          previous,
          solveLiveParameterDefinitions,
          key,
          rawValue,
        ),
      );
    },
    [],
  );
  const resetSolveCellInferenceParameters = useCallback(() => {
    setSolveCellInferenceState(
      createUc14ContextState(
        solveCellInferenceParameterDefinitions,
        solveCellInferenceDefaults,
      ),
    );
  }, []);
  const resetSolveLiveParameters = useCallback(() => {
    setSolveLiveState(
      createUc14ContextState(solveLiveParameterDefinitions, solveLiveDefaults),
    );
  }, []);

  async function handlePingClick() {
    setPingState({
      kind: "loading",
      response: null,
      error: null,
      httpStatus: null,
    });

    try {
      const response = await fetch(pingEndpoint, {
        headers: {
          Accept: "application/json",
        },
      });

      const rawBody = await response.text();
      let parsedBody: PingResponse | null = null;

      if (rawBody) {
        parsedBody = JSON.parse(rawBody) as PingResponse;
      }

      if (!response.ok) {
        setPingState({
          kind: "error",
          response: parsedBody,
          error:
            parsedBody?.message ??
            `Backend zwrócił odpowiedź HTTP ${response.status}.`,
          httpStatus: response.status,
        });
        return;
      }

      if (!parsedBody) {
        throw new Error("Backend zwrócił pustą odpowiedź.");
      }

      setPingState({
        kind: "success",
        response: parsedBody,
        error: null,
        httpStatus: response.status,
      });
    } catch (error) {
      setPingState({
        kind: "error",
        response: null,
        error:
          error instanceof Error
            ? error.message
            : "Nie udało się połączyć z backendem.",
        httpStatus: null,
      });
    }
  }

  useEffect(() => {
    if (!loginModalOpen) {
      return;
    }

    setLoginState(defaultLoginState);
  }, [loginModalOpen]);

  useEffect(() => {
    if (
      manualExamplesWorkflowContext !== null &&
      !availableExamplesUc14Contexts.includes(manualExamplesWorkflowContext)
    ) {
      setManualExamplesWorkflowContext(null);
    }
  }, [availableExamplesUc14Contexts, manualExamplesWorkflowContext]);

  useEffect(() => {
    if (activeView !== "examples" || !examplesModule.hasSelectedSource) {
      setExamplesWorkflowContext(null);
      setManualExamplesWorkflowContext(null);
    }
  }, [activeView, examplesModule.hasSelectedSource]);
  return (
    <main className="app-root">
      <AppHeader
        activeViewLabel={activeViewLabel}
        apiBaseUrl={apiBaseUrl}
        datasetsStepLabel={datasetsStepLabel}
        isDatasetsView={activeView === "datasets"}
      />

      <div className={`workspace-shell${hasUc14Panel ? " has-context-panel" : ""}`}>
        <AppNavigation activeView={activeView} onViewChange={setActiveView} />

        <div className="page-shell">
          <AuthSessionCard
            authExpiresAtUtc={authToken?.expiresAtUtc ?? null}
            isAdminMode={isAdminMode}
            isDemoMode={isDemoMode}
            onLoginClick={() => {
              setAdminPassword("");
              openLoginModal();
            }}
            onLogoutClick={logoutAdmin}
            formatTimestamp={formatTimestamp}
          />

          {activeView === "health" ? (
            <HealthView
              apiBaseUrl={apiBaseUrl}
              onPing={() => void handlePingClick()}
              pingState={pingState}
            />
          ) : null}

          {activeView === "examples" ? (
            <ExamplesView
              activeCellsGrid={examplesModule.activeCellsGrid}
              apiBaseUrl={apiBaseUrl}
              boardStageState={examplesModule.boardStageState}
              canSubmitUpload={examplesModule.canSubmitUpload}
              cellsStageState={examplesModule.cellsStageState}
              downloadingName={examplesModule.downloadingName}
              examplesListData={examplesModule.examplesListData}
              examplesListState={examplesModule.examplesListState}
              examplesUploadEndpoint={examplesUploadEndpoint}
              fileInputRef={examplesModule.fileInputRef}
              isAdminMode={isAdminMode}
              isUploadBusy={examplesModule.isUploadBusy}
              hasSelectedSource={examplesModule.hasSelectedSource}
              onDownload={(fileName) => void examplesModule.handleDownloadClick(fileName)}
              onLoadExamples={() => void examplesModule.loadExamplesList()}
              onRunUpload={() => void examplesModule.handleUploadClick()}
              onSelectedFileChange={examplesModule.setSelectedFile}
              onSelectProcessName={examplesModule.handleSelectProcessName}
              onUc14ContextChange={setExamplesWorkflowContext}
              previewStageState={examplesModule.previewStageState}
              runUc04Flow={(fileName) => void examplesModule.runUc04Flow(fileName)}
              selectedProcessName={examplesModule.selectedProcessName}
              selectedSourceLabel={examplesModule.selectedSourceLabel}
              sessionExamples={examplesModule.sessionExamples}
              solveCellInferenceParameters={solveCellInferenceParameters}
              solveCellInferenceParametersValid={solveCellInferenceValidation.isValid}
              solveCellInferenceParameterErrorCount={solveCellInferenceValidation.errorCount}
              solveCellInferenceOverrideCount={solveCellInferenceOverrideCount}
              solveLiveParameters={solveLiveParameters}
              solveLiveParametersValid={solveLiveValidation.isValid}
              solveLiveParameterErrorCount={solveLiveValidation.errorCount}
              solveLiveOverrideCount={solveLiveOverrideCount}
              uc20LocalImageFlow={examplesModule.uc20LocalImageFlow}
            />
          ) : null}

          {activeView === "datasets" ? (
            <DatasetsView
              accessToken={authToken?.accessToken ?? null}
              apiBaseUrl={apiBaseUrl}
              datasetsStep={datasetsStep}
              onDatasetsStepChange={setDatasetsStep}
              onUnauthorized={() => handleAdminUnauthorized("invalid_token")}
              trainingRunParameterValidation={trainingRunParameterValidation}
            />
          ) : null}
        </div>

        {hasUc14Panel ? (
          <aside className="workspace-context-panel">
            {activeView === "examples" && availableExamplesUc14Contexts.length > 1 ? (
              <section
                className="workspace-context-switcher"
                aria-label="Przelacznik kontekstu parametrow UC-14"
              >
                <p className="eyebrow">Panel parametrow</p>
                <p className="muted-copy">
                  Workflow automatycznie przechodzi do kolejnego etapu, ale tutaj
                  mozesz wrocic do wczesniejszych parametrow bez zmiany widoku.
                </p>
                <div
                  className="workspace-context-switcher-list"
                  role="tablist"
                  aria-label="Konteksty parametrow Examples"
                >
                  {availableExamplesUc14Contexts.map((context) => {
                    const isActive = activeUc14Context === context;

                    return (
                      <button
                        key={context}
                        className={`workspace-context-switcher-button ${
                          isActive ? "is-active" : ""
                        }`}
                        type="button"
                        role="tab"
                        aria-selected={isActive}
                        onClick={() => setManualExamplesWorkflowContext(context)}
                      >
                        {getExamplesUc14ContextLabel(context)}
                      </button>
                    );
                  })}
                </div>
              </section>
            ) : null}
            {activeUc14Context === "solveCellInference" ? (
              <Uc14SolveCellInferenceParametersPanel
                state={solveCellInferenceState}
                isValid={solveCellInferenceValidation.isValid}
                errorCount={solveCellInferenceValidation.errorCount}
                overrideCount={solveCellInferenceOverrideCount}
                onReset={resetSolveCellInferenceParameters}
                onSetValue={handleSolveCellInferenceParameterChange}
              />
            ) : null}
            {activeUc14Context === "solveLive" ? (
              <Uc14SolveLiveParametersPanel
                state={solveLiveState}
                isValid={solveLiveValidation.isValid}
                errorCount={solveLiveValidation.errorCount}
                overrideCount={solveLiveOverrideCount}
                onReset={resetSolveLiveParameters}
                onSetValue={handleSolveLiveParameterChange}
              />
            ) : null}
            {activeUc14Context === "trainingRun" ? (
              <Uc14TrainingRunParametersPanel
                state={trainingRunParameterState}
                errors={trainingRunParameterValidation.errors}
                isValid={trainingRunParameterValidation.isValid}
                errorCount={trainingRunParameterValidation.errorCount}
                overrideCount={trainingRunParameterValidation.overrideCount}
                onReset={resetTrainingRunParameters}
                onFieldChange={handleTrainingRunParameterChange}
              />
            ) : null}
          </aside>
        ) : null}

      </div>
      {loginModalOpen ? (
        <AdminLoginModal
          adminPassword={adminPassword}
          loginPromptMessage={loginPromptMessage}
          loginState={loginState}
          onAdminPasswordChange={setAdminPassword}
          onContinueDemo={() => {
            setAdminPassword("");
            continueInDemoMode();
          }}
          onSubmit={() => void handleAdminLoginSubmit()}
        />
      ) : null}
    </main>
  );
}
