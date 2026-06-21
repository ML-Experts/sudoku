# Tech Stack

Ten plik jest szybkim katalogiem zależności projektowych. Źródłem prawdy dla konkretnych wersji pozostają pliki projektu:

- `src/Backend/Sudoku/**/*.csproj`
- `src/MachineLearning/requirements.txt`
- `src/Frontend/package.json`

## Narzędzia systemowe

Do lokalnego uruchomienia potrzebne są:

- `.NET SDK 10`
- `Python 3.12`
- `Node.js 22`
- `npm`
- `git`

## Backend

Backend działa na `.NET 10` i `ASP.NET Core Web API`.

Projekty backendu:

- `src/Backend/Sudoku/Sudoku` - projekt startowy API
- `src/Backend/Sudoku/Application` - use case'y, walidacja, orkiestracja
- `src/Backend/Sudoku/Infrastructure` - integracje, storage, klient ML
- `src/Backend/Sudoku/Models` - modele domenowe i DTO
- `src/Backend/Sudoku/Application.Tests` - testy automatyczne

Najważniejsze zależności `NuGet`:

- `Microsoft.AspNetCore.Authentication.JwtBearer`
- `FluentValidation`
- `FluentValidation.DependencyInjectionExtensions`
- `MediatR` w linii `12.x`
- `Microsoft.Extensions.Options`
- `xunit`
- `Microsoft.NET.Test.Sdk`
- `coverlet.collector`

## MachineLearning

Warstwa `ML` działa w Pythonie i używa `FastAPI` jako wewnętrznego API dla backendu.

Najważniejsze zależności `Python`:

- `fastapi`
- `uvicorn`
- `pydantic`
- `httpx`
- `python-dotenv`
- `numpy`
- `opencv-python-headless`
- `torch`
- `torchvision`
- `pytest`
- `python-slugify`

## Frontend

Frontend jest aplikacją `React` uruchamianą przez `Vite`.

Najważniejsze zależności `npm`:

- `react`
- `react-dom`
- `@microsoft/signalr`
- `vite`
- `typescript`
- `@vitejs/plugin-react`

## Uwagi

- Frontend nie komunikuje się bezpośrednio z `MachineLearning`; publicznym API produktu jest `Backend`.
- Backend jest `source of truth` dla statusów workflow, rekordów treningów, modeli i aktywnego modelu.
- `ML` tworzy artefakty techniczne i wykonuje obliczenia, ale nie powinien zastępować backendowego rejestru stanu systemu.
