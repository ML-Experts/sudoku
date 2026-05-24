type AppHeaderProps = {
  activeViewLabel: string;
  apiBaseUrl: string;
  datasetsStepLabel: string;
  isDatasetsView: boolean;
};

export function AppHeader({
  activeViewLabel,
  apiBaseUrl,
  datasetsStepLabel,
  isDatasetsView,
}: AppHeaderProps) {
  return (
    <header className="hero-card app-header">
      <div className="app-brand">
        <div className="app-brand-mark" aria-hidden="true">
          SV
        </div>
        <div className="app-brand-copy">
          <p className="eyebrow">Sudoku Vision</p>
          <h1 className="app-brand-title">Data & preprocessing console</h1>
        </div>
      </div>
      <div className="app-header-meta">
        <span className="app-chip">Modul: {activeViewLabel}</span>
        {isDatasetsView ? (
          <span className="app-chip">Krok: {datasetsStepLabel}</span>
        ) : null}
        <span className="app-chip app-chip-muted">
          API: <code>{apiBaseUrl}</code>
        </span>
      </div>
    </header>
  );
}
