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
import { Uc14TrainingRunParametersPanel } from "./features/uc14/api/Uc14TrainingRunParametersPanel";
import {
  createTrainingRunParameterFormState,
  type TrainingRunParameterFormState,
  validateTrainingRunParameterState,
} from "./features/uc14/domain/trainingRunParameters";

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
  const [uc14PanelVisible, setUc14PanelVisible] = useState(false);
  const [trainingRunParameterState, setTrainingRunParameterState] = useState(
    createTrainingRunParameterFormState,
  );
  const isAdminMode = mode === "admin";
  const isDemoMode = mode === "demo";
  const hasUc14Panel =
    activeView === "datasets" && datasetsStep === "uc06" && uc14PanelVisible;
  const trainingRunParameterValidation = useMemo(
    () => validateTrainingRunParameterState(trainingRunParameterState),
    [trainingRunParameterState],
  );

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
      : datasetsStep === "uc12"
        ? "UC-12 — Budowa datasetu processed"
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
    if (activeView !== "datasets" || datasetsStep !== "uc06") {
      setUc14PanelVisible(false);
    }
  }, [activeView, datasetsStep]);
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
              onDownload={(fileName) => void examplesModule.handleDownloadClick(fileName)}
              onLoadExamples={() => void examplesModule.loadExamplesList()}
              onRunUpload={() => void examplesModule.handleUploadClick()}
              onSelectedFileChange={examplesModule.setSelectedFile}
              onSelectProcessName={examplesModule.setSelectedProcessName}
              previewStageState={examplesModule.previewStageState}
              runUc04Flow={(fileName) => void examplesModule.runUc04Flow(fileName)}
              selectedProcessName={examplesModule.selectedProcessName}
              sessionExamples={examplesModule.sessionExamples}
            />
          ) : null}

          {activeView === "datasets" ? (
            <DatasetsView
              accessToken={authToken?.accessToken ?? null}
              apiBaseUrl={apiBaseUrl}
              datasetsStep={datasetsStep}
              onDatasetsStepChange={setDatasetsStep}
              onUnauthorized={() => handleAdminUnauthorized("invalid_token")}
              setUc14PanelVisible={setUc14PanelVisible}
              trainingRunParameterValidation={trainingRunParameterValidation}
            />
          ) : null}
        </div>

        {hasUc14Panel ? (
          <aside className="workspace-context-panel">
            <Uc14TrainingRunParametersPanel
              state={trainingRunParameterState}
              errors={trainingRunParameterValidation.errors}
              isValid={trainingRunParameterValidation.isValid}
              errorCount={trainingRunParameterValidation.errorCount}
              overrideCount={trainingRunParameterValidation.overrideCount}
              onReset={resetTrainingRunParameters}
              onFieldChange={handleTrainingRunParameterChange}
            />
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
