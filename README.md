# Sudoku Vision

System webowy do rozpoznawania i rozwiązywania Sudoku ze zdjęcia. Projekt składa się z trzech głównych warstw: `Frontend`, `Backend` oraz `MachineLearning`. Oprócz ścieżki solve aplikacja obejmuje również operacje administracyjne związane z datasetami, treningami i wyborem aktywnego modelu.

## Skład zespołu

- **Osoba 1** - `do uzupełnienia`
- **Osoba 2** - `do uzupełnienia`
- **Osoba 3** - `do uzupełnienia`

## Cel projektu

Projekt ma umożliwiać:

- wgranie zdjęcia planszy Sudoku,
- wykrycie planszy i korekcję perspektywy,
- podział planszy na siatkę `9x9`,
- rozpoznanie cyfr `1-9` i pustych pól,
- rozwiązanie układanki algorytmem backtrackingu,
- wygenerowanie obrazu z naniesionym rozwiązaniem,
- przygotowanie datasetów treningowych `.npz`,
- uruchamianie i monitorowanie treningów modeli,
- wybór aktywnego modelu inferencyjnego,
- wdrażanie każdej warstwy niezależnie w modelu release-based.

## Architektura warstwowa

System działa w modelu trójwarstwowym:

- **FE** - `Frontend` w React/Vite, publicznie dostępny przez `nginx`
- **BE** - `Backend` w ASP.NET Core / .NET 10, wystawia publiczne API i jest głównym `source of truth`
- **ML** - wewnętrzna usługa Python / FastAPI odpowiedzialna za CV, inferencję, przygotowanie danych i trening

### Zasady komunikacji

Dozwolona komunikacja:

- `Przeglądarka -> nginx -> FE`
- `Przeglądarka -> nginx -> BE` przez `/api/...`
- `BE -> ML` przez `http://127.0.0.1:8000`

Niedozwolona komunikacja:

- `FE -> ML` bezpośrednio
- `Internet -> ML` bezpośrednio
- `Internet -> BE` z pominięciem `nginx`

### Odpowiedzialność warstw

- **Frontend** odpowiada za UI, formularze, nawigację, wizualizację wyników, monitoring sesji i treningów.
- **Backend** odpowiada za publiczne API, walidację, autoryzację, workflow, rekordy systemowe, statusy procesów i integrację z ML.
- **MachineLearning** odpowiada za wykrycie planszy, preprocessing komórek, inferencję, solver, overlay, przygotowanie datasetów i trening modeli.

### Aktualnie funkcjonujące warstwy aplikacyjne

- `src/Frontend` - interfejs użytkownika
- `src/Backend/Sudoku` - warstwa API i orkiestracji
- `src/MachineLearning` - warstwa ML / CV / trening
- `nginx` - publiczna brama wejściowa na serwerze
- `systemd` - uruchamianie i restart usług `BE` oraz `ML`

## Najważniejsze funkcje systemu

- upload i przegląd przykładów Sudoku,
- preprocessing planszy i komórek,
- rozpoznawanie cyfr i rozwiązywanie Sudoku,
- live solve z eventami czasu rzeczywistego,
- logowanie administracyjne prostym tokenem,
- przegląd surowych datasetów,
- przygotowanie jednego artefaktu `{name}.npz`,
- uruchamianie treningów i śledzenie postępu przez `SignalR`,
- przegląd modeli i wybór aktywnego modelu,
- diagnostyczny podgląd przygotowanego datasetu i artefaktów preview.

## Podział odpowiedzialności i historyjki

Poniższa ramka służy do wpisania odpowiedzialności zespołu za konkretne historyjki. Tam, gdzie dana warstwa nie bierze udziału, pozostawiono `—`.

Skróty:

- `INFRA` - serwer, deploy, runtime, dokumentacja, workflow, jakość
- `FE` - frontend i interfejs użytkownika
- `BE` - backend C# / ASP.NET Core i workflow aplikacyjny
- `ML` - Computer Vision, inferencja, datasety i trening

| ID | Zakres | INFRA | FE | BE | ML |
|---|---|---|---|---|---|
| `INF-01` | Szkielet repo, README, przykłady do demo | `do uzupełnienia` | — | — | — |
| `INF-02` | Uruchomienie lokalne całego systemu | `do uzupełnienia` | — | — | — |
| `INF-03` | Środowisko serwerowe, domena, SSL, reverse proxy, layout runtime | `do uzupełnienia` | — | — | — |
| `INF-04` | Standardy jakości i zasady pracy | `do uzupełnienia` | — | — | — |
| `INF-05` | Opcjonalny Jupyter / środowisko eksperymentalne | `do uzupełnienia` | — | — | `do uzupełnienia` |
| `INF-06` | Opcjonalne CI na PR | `do uzupełnienia` | `do uzupełnienia` | `do uzupełnienia` | `do uzupełnienia` |
| `INF-07` | CD / deploy na serwer | `do uzupełnienia` | `do uzupełnienia` | `do uzupełnienia` | `do uzupełnienia` |
| `INF-08` | Bootstrap rejestru modeli i manifestów | `do uzupełnienia` | — | `do uzupełnienia` | `do uzupełnienia` |
| `UC-00` | Smoke test `FE -> BE -> ML` | — | `do uzupełnienia` | `do uzupełnienia` | `do uzupełnienia` |
| `UC-01` | Upload pliku Sudoku do `examples` | — | `do uzupełnienia` | `do uzupełnienia` | — |
| `UC-02` | Lista dostępnych przykładów Sudoku | — | `do uzupełnienia` | `do uzupełnienia` | — |
| `UC-03` | Pobierz wybrany plik przykładowy | — | `do uzupełnienia` | `do uzupełnienia` | — |
| `UC-04` | Wybór przykładu i wstępna obróbka | — | `do uzupełnienia` | `do uzupełnienia` | `do uzupełnienia` |
| `UC-05` | Rozpoznanie cyfr, solve i prezentacja wyniku | — | `do uzupełnienia` | `do uzupełnienia` | `do uzupełnienia` |
| `UC-06` | Uruchomienie treningu na `.npz` | — | `do uzupełnienia` | `do uzupełnienia` | `do uzupełnienia` |
| `UC-07` | Postęp treningu i status zakończenia | — | `do uzupełnienia` | `do uzupełnienia` | `do uzupełnienia` |
| `UC-08` | Lista treningów i modeli | — | `do uzupełnienia` | `do uzupełnienia` | `do uzupełnienia` |
| `UC-09` | Szczegóły treningu i metryki | — | `do uzupełnienia` | `do uzupełnienia` | `do uzupełnienia` |
| `UC-10` | Wybór aktywnego modelu do inferencji | — | `do uzupełnienia` | `do uzupełnienia` | `do uzupełnienia` |
| `UC-11` | Lista surowych datasetów | — | `do uzupełnienia` | `do uzupełnienia` | — |
| `UC-12` | Przygotowanie datasetu `.npz` | — | `do uzupełnienia` | `do uzupełnienia` | `do uzupełnienia` |
| `UC-13` | Prosta autoryzacja administracyjna | — | `do uzupełnienia` | `do uzupełnienia` | — |
| `UC-14` | Parametryzacja funkcjonalności z UI | — | `do uzupełnienia` | `do uzupełnienia` | `do uzupełnienia` |
| `UC-15` | Spowolnienie live solve | — | `do uzupełnienia` | `do uzupełnienia` | — |
| `UC-16` | Przegląd przygotowanego datasetu i preview | — | `do uzupełnienia` | `do uzupełnienia` | `do uzupełnienia` |

### Podział pracy w formie osobowej

Na końcu można dodatkowo dopisać podsumowanie osobowe, na przykład:

- **[Imię Nazwisko]** - `INF-01`, `INF-02`, `INF-03`, `INF-07`
- **[Imię Nazwisko]** - `UC-01`, `UC-02`, `UC-03`, `UC-04`, `UC-05`
- **[Imię Nazwisko]** - `UC-06`, `UC-07`, `UC-08`, `UC-09`, `UC-10`, `UC-12`, `UC-16`

## Layout runtime i katalogi serwera

Schemat katalogów runtime i deployu powinien być rozumiany według docelowego layoutu serwera, a nie 1:1 według struktury repo.

```text
/opt/sudoku/
├── backend/                   # aktywna wersja BE
├── ml/                        # aktywna wersja ML
├── releases/
│   ├── backend/               # wrzutnia release'ów BE
│   ├── ml/                    # wrzutnia release'ów ML
│   └── fe/                    # wrzutnia release'ów FE
├── shared/
│   ├── data/
│   │   ├── raw/
│   │   │   ├── boards/
│   │   │   └── digits/
│   │   ├── processed/
│   │   └── benchmark/
│   ├── models/
│   │   ├── active/
│   │   │   └── inference.json
│   │   └── registry/
│   │       └── {modelName}/
│   │           ├── model.json
│   │           └── artifacts/
│   ├── trainings/
│   │   ├── runs/
│   │   ├── reports/
│   │   └── metadata/
│   ├── examples/
│   │   ├── uploads/
│   │   └── generated/
│   └── tmp/
└── scripts/

/var/www/sudoku/fe             # aktywny frontend dla nginx
/etc/sudoku/                   # konfiguracja systemowa / dodatki
/var/log/sudoku/               # logi
```

### Znaczenie katalogów runtime

- `/opt/sudoku/backend` - aktywny publish `Backendu`
- `/opt/sudoku/ml` - aktywny kod `MachineLearning`
- `/opt/sudoku/releases/...` - wrzutnia artefaktów release
- `/opt/sudoku/shared/...` - trwały stan systemu, który żyje dłużej niż pojedynczy release
- `/var/www/sudoku/fe` - statyczny build `Frontendu`

### Kluczowa zasada runtime

Deploy nie może czyścić ani nadpisywać katalogów współdzielonych runtime, takich jak:

- `shared/data`
- `shared/models`
- `shared/trainings`
- `shared/examples`

To jest stan systemu, a nie zawartość pojedynczego release'u.

## Deploy i model wdrożenia

Projekt zakłada deploy **release-based**:

1. workflow buduje artefakt,
2. artefakt trafia do katalogu `releases`,
3. uruchamiany jest odpowiedni skrypt deployowy,
4. release jest promowany do katalogu aktywnego,
5. usługa jest restartowana.

### Deploy Frontendu

- build wykonywany jest w CI/CD,
- wynik statyczny trafia do `/opt/sudoku/releases/fe/`,
- deploy kopiuje build do `/var/www/sudoku/fe`,
- `nginx` serwuje pliki statyczne,
- ta warstwa nie wymaga restartu osobnej usługi aplikacyjnej.

### Deploy Backendu

- workflow wykonuje `dotnet restore`, `dotnet build`, testy i `dotnet publish`,
- release zawiera `appsettings.json` i `appsettings.production.json`,
- artefakt trafia do `/opt/sudoku/releases/backend/`,
- deploy promuje go do `/opt/sudoku/backend`,
- po wdrożeniu restartowana jest usługa `sudoku-backend.service`.

### Deploy warstwy ML

- workflow pakuje kod, `requirements.txt` i `api/.env`,
- artefakt trafia do `/opt/sudoku/releases/ml/`,
- deploy promuje go do `/opt/sudoku/ml`,
- na serwerze utrzymywane jest `.venv`,
- deploy wykonuje `pip install -r requirements.txt`,
- po wdrożeniu restartowana jest usługa `sudoku-ml.service`.

### Niezależność wdrożeń

`FE`, `BE` i `ML` powinny móc być wdrażane niezależnie osobnymi workflow.

## Runtime sieciowy

### Publiczne porty

Na zewnątrz powinny być wystawione tylko:

- `80/tcp`
- `443/tcp`
- `22/tcp`

### Porty wewnętrzne

- `BE` - `127.0.0.1:5000`
- `ML` - `127.0.0.1:8000`

Oznacza to, że `Backend` i `ML` słuchają tylko na `localhost`.

## Konfiguracja

### Backend

Backend korzysta z:

- `appsettings.json`
- `appsettings.{environment}.json`
- zmiennych środowiskowych
- argumentów procesu

W środowisku lokalnym wykorzystywany jest `SUDOKU_ENVIRONMENT=local`. W środowisku serwerowym deploy powinien wskazywać `SUDOKU_ENVIRONMENT=production`.

### MachineLearning

Warstwa ML korzysta z:

- `api/.env`
- `requirements.txt`

Konfiguracja runtime jest dostarczana razem z release'em.

## Uruchomienie lokalne

Uruchom aplikację w trzech terminalach.

### Backend

```bash
cd src/Backend/Sudoku/Sudoku
dotnet restore
dotnet run --launch-profile Sudoku
```

### MachineLearning

```bash
cd src/MachineLearning
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Frontend

```bash
cd src/Frontend
npm install
npm run dev
```

### Smoke test

```bash
curl http://127.0.0.1:8000/ml/ping
curl http://127.0.0.1:5000/api/ping
```

## Najważniejsze endpointy

Backend:

- `POST /api/auth/login`
- `GET /api/examples`
- `POST /api/examples`
- `PUT /api/examples/{name}/preprocess/board`
- `PUT /api/examples/preprocess/cells`
- `GET /api/datasets/raw-candidates`
- `POST /api/datasets/processed`
- `GET /api/datasets/processed`
- `GET /api/models/registry`
- `GET /api/models/active`
- `PUT /api/models/active`
- `POST /api/trainings`
- `GET /api/trainings`
- `GET /api/trainings/{runName}`
- `GET /api/trainings/active`
- `POST /api/trainings/{runName}/cancel`
- `PUT /api/sudoku/cells/inference`
- `POST /api/sudoku/solve`

Kanały realtime:

- `/ws/trainings/{runName}`
- `/ws/sudoku/solving/{solveSessionId}`

ML:

- `GET /ml/ping`
- `GET /ml/health`
- `PUT /ml/preprocess/board`
- `PUT /ml/preprocess/cells`
- `PUT /ml/cells/inference`
- `POST /ml/datasets/prepare`
- `POST /ml/trainings`

## Dane, modele i artefakty

### Surowe datasety

Surowe dane są dostarczane poza UI do katalogów runtime:

- `board` - katalogi z parami `.jpg` + `.dat`
- `digit` - pary `*.idx3-ubyte` + `*.idx1-ubyte`

### Dataset przetworzony

Każde przygotowanie kończy się jednym plikiem `{name}.npz`.

### Rejestr modeli

Każdy model jest osobnym wpisem:

```text
/opt/sudoku/shared/models/registry/{modelName}/
├── model.json
└── artifacts/
```

Aktywny model inferencyjny wskazuje:

```text
/opt/sudoku/shared/models/active/inference.json
```

### Treningi

Każdy `runName` ma:

- rekord metadanych w `trainings/metadata`,
- artefakty techniczne w `trainings/runs`,
- raporty i metryki w `trainings/reports`.

## Testy

### Backend

```bash
dotnet test src/Backend/Sudoku/Application.Tests/Application.Tests.csproj
```

### MachineLearning

```bash
cd src/MachineLearning
source .venv/bin/activate
pytest tests
```

## Ograniczenia

- jakość rozpoznania zależy od jakości zdjęcia i warunków oświetlenia,
- prosta autoryzacja administracyjna nie jest pełnym systemem IAM,
- skuteczność solve zależy od jakości aktywnego modelu,
- dane treningowe mogą różnić się domeną od rzeczywistych zdjęć użytkownika,
- część zakresu z PRD nadal ma charakter rozwojowy.

## Zasady pracy w repozytorium

- każdy członek zespołu powinien mieć minimum `3` commity,
- commit messages powinny być opisowe,
- README powinno odzwierciedlać realny stan architektury, runtime i deployu.
