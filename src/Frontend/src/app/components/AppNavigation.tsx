import type { AppView } from "../state";

type AppNavigationProps = {
  activeView: AppView;
  onViewChange: (view: AppView) => void;
};

export function AppNavigation({
  activeView,
  onViewChange,
}: AppNavigationProps) {
  return (
    <aside className="workspace-nav">
      <div className="workspace-nav-header">
        <h2>Moduly</h2>
      </div>
      <nav className="workspace-nav-list" aria-label="Widoki aplikacji">
        <button
          type="button"
          className={`workspace-nav-button ${activeView === "health" ? "is-active" : ""}`}
          onClick={() => onViewChange("health")}
        >
          Healthcheck
        </button>
        <button
          type="button"
          className={`workspace-nav-button ${activeView === "examples" ? "is-active" : ""}`}
          onClick={() => onViewChange("examples")}
        >
          Przyklady
        </button>
        <button
          type="button"
          className={`workspace-nav-button ${activeView === "datasets" ? "is-active" : ""}`}
          onClick={() => onViewChange("datasets")}
        >
          Datasety
        </button>
      </nav>
    </aside>
  );
}
