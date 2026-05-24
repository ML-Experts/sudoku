import type { LoginState } from "../state";

type AdminLoginModalProps = {
  adminPassword: string;
  loginPromptMessage: string | null;
  loginState: LoginState;
  onAdminPasswordChange: (value: string) => void;
  onContinueDemo: () => void;
  onSubmit: () => void;
};

export function AdminLoginModal({
  adminPassword,
  loginPromptMessage,
  loginState,
  onAdminPasswordChange,
  onContinueDemo,
  onSubmit,
}: AdminLoginModalProps) {
  return (
    <div className="auth-modal-overlay" role="presentation">
      <section
        className="auth-modal-card"
        role="dialog"
        aria-modal="true"
        aria-labelledby="auth-modal-title"
      >
        <p className="eyebrow">UC-13 — Logowanie administracyjne</p>
        <h2 id="auth-modal-title">Tryb admin lub demo</h2>
        <p className="muted-copy">
          Zaloguj sie haslem administracyjnym, aby odblokowac operacje chronione.
          Mozesz tez kontynuowac w trybie demo bez hasla.
        </p>
        {loginPromptMessage ? (
          <p className="status-banner status-error">{loginPromptMessage}</p>
        ) : null}
        {loginState.kind === "error" ? (
          <>
            <p className="status-banner status-error">{loginState.error}</p>
            {loginState.errorType ? (
              <p className="muted-copy">Typ bledu: {loginState.errorType}</p>
            ) : null}
            {loginState.httpStatus !== null ? (
              <p className="muted-copy">HTTP status: {loginState.httpStatus}</p>
            ) : null}
          </>
        ) : null}
        <label className="auth-modal-field">
          <span>Haslo administratora</span>
          <input
            type="password"
            value={adminPassword}
            autoFocus
            onChange={(event) => onAdminPasswordChange(event.target.value)}
            placeholder="Wpisz haslo"
            disabled={loginState.kind === "loading"}
          />
        </label>
        <div className="examples-row-actions">
          <button
            className="primary-button"
            type="button"
            disabled={loginState.kind === "loading"}
            onClick={onSubmit}
          >
            {loginState.kind === "loading"
              ? "Logowanie..."
              : "Zaloguj do trybu admin"}
          </button>
          <button
            className="secondary-button"
            type="button"
            disabled={loginState.kind === "loading"}
            onClick={onContinueDemo}
          >
            Kontynuuj w trybie demo
          </button>
        </div>
      </section>
    </div>
  );
}
