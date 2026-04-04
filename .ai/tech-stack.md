# Stack techniczny (stan `src/Backend` i `src/Frontend`)


## Frontend — Vite + React

- **Vite** (ok. 6.x) — dev server i bundling (`vite`, `@vitejs/plugin-react`).
- **React** 18 — SPA (`react`, `react-dom`).
- **TypeScript** (ok. 5.7) — `tsc -b` przy buildzie; skrypty: `dev`, `build`, `check`, `preview`.
- **CSS** — globalne style i klasy w `src/index.css` (bez Tailwinda i bez shadcn/ui w zależnościach).

## Backend — ASP.NET Core (.NET 10)

- **.NET / C#** — `TargetFramework: net10.0` we wszystkich projektach warstwowych.
- **ASP.NET Core** — host webowy (`Microsoft.NET.Sdk.Web`), **Minimal APIs** (mapowanie endpointów, np. `MapGet`).
- **Warstwy solutionu** (folder `src/Backend/Sudoku/`):
  - **Sudoku** — aplikacja hostująca (`Program.cs`), konfiguracja, endpointy HTTP.
  - **Application** — logika aplikacyjna; **MediatR** do obsługi zapytań/komend (CQRS-light).
  - **Infrastructure** — integracje (np. `HttpClient` do serwisu ML), rejestracja DI.
  - **Models** — modele domenowe / DTO współdzielone.
- **Konfiguracja** — `appsettings.json`, strongly-typed options (`IOptions`), walidacja przy starcie.
- **Integracja z ML** — HTTP do zewnętrznego serwisu ML (ścieżka i timeout z konfiguracji, np. `MlService:PingPath`); przykładowy kontrakt: health/ping w `GET /api/ping`.

## CI/CD (repozytorium `sudoku/`)

- **GitHub Actions** — m.in. `backend-cd.yml`, `frontend-cd.yml` (wdrożenia po merge z `dev` → `main` lub ręcznie); zmienne środowiskowe dla frontu m.in. `FE_VITE_API_BASE_URL`.

## Testowanie

- W tym momencie **brak** dedykowanych projektów testów (np. xUnit, Vitest) w drzewie `sudoku/` — do uzupełnienia wraz z rozwojem funkcji.
