type AuthSessionCardProps = {
  authExpiresAtUtc?: string | null;
  isAdminMode: boolean;
  isDemoMode: boolean;
  onLoginClick: () => void;
  onLogoutClick: () => void;
  formatTimestamp: (value: string) => string;
};

export function AuthSessionCard({
  authExpiresAtUtc,
  isAdminMode,
  isDemoMode,
  onLoginClick,
  onLogoutClick,
  formatTimestamp,
}: AuthSessionCardProps) {
  return (
    <section className="hero-card auth-session-card" aria-live="polite">
      <p className="eyebrow">UC-13 — Autoryzacja administracyjna</p>
      <h2>Tryb pracy</h2>
      <p className="muted-copy">
        {isAdminMode
          ? "Tryb administracyjny jest aktywny."
          : "Tryb demo aktywny. Operacje administracyjne sa zablokowane."}
      </p>
      {authExpiresAtUtc ? (
        <p className="muted-copy">
          Sesja wygasa: {formatTimestamp(authExpiresAtUtc)}
        </p>
      ) : null}
      <div className="examples-row-actions">
        {isDemoMode ? (
          <button className="secondary-button" type="button" onClick={onLoginClick}>
            Zaloguj jako admin
          </button>
        ) : (
          <button className="secondary-button" type="button" onClick={onLogoutClick}>
            Wyloguj
          </button>
        )}
      </div>
    </section>
  );
}
