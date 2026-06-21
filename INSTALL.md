# Instalacja i uruchomienie

Ten dokument opisuje wyłącznie:
- przygotowanie środowiska,
- instalację narzędzi i zależności,
- lokalne pliki konfiguracyjne,
- ręczne katalogi i pliki, których aplikacja sama nie tworzy,
- bootstrap lokalnego rejestru modeli,
- uruchomienie `Backend`, `MachineLearning` i `Frontend`.

Opis produktu, pełny workflow, `UC-*`, odpowiedzialności zespołu i linki do dokumentacji projektowej są w `README.md`.
Katalog technologii i zależności projektowych jest w `TECH-STACK.md`.

## 1. Docelowe środowisko

Projekt został przygotowany pod środowisko unixowe, w praktyce najlepiej:
- `Ubuntu`,
- inny kompatybilny `Linux`,
- albo `WSL` na Windows.

Jeżeli pracujesz na Windows, rekomendowany wariant to:

1. zainstalować `WSL`,
2. zainstalować w nim `Ubuntu`,
3. uruchamiać cały projekt z poziomu środowiska linuxowego w `WSL`.

Instalacja `WSL` jest poza zakresem tego repo. Jeśli masz już działające środowisko linuxowe, możesz pominąć ten krok.

## 2. Narzędzia do zainstalowania poza projektem

Zanim wejdziesz do repo, przygotuj:
- `git`,
- `.NET SDK 10`,
- `Python 3.12`,
- `Node.js 22`,
- `npm`.

To są narzędzia systemowe instalowane poza projektem. Samo repo ich nie dostarcza.

## 3. Jak sprawdzić, czy środowisko jest gotowe

Uruchom:

```bash
git --version
dotnet --version
python3 --version
node --version
npm --version
```

Jeżeli któreś polecenie nie działa, najpierw dokończ instalację narzędzi systemowych.

## 4. Sklonowanie repo

Przykład:

```bash
git clone <URL_REPOZYTORIUM>
cd sudoku
```

W dalszej części dokumentu używamy:

```text
<REPO_ROOT>=/home/twoj-user/projects/sudoku
```

Podstaw tam własną ścieżkę absolutną.

## 5. Jak działa wybór lokalnego vs produkcyjnego środowiska

To ważne, żeby lokalnie nie używać przypadkiem konfiguracji produkcyjnej.

### Backend

Lokalny backend powinien startować z:

```text
SUDOKU_ENVIRONMENT=local
```

Najbezpieczniejszy wariant to:

```bash
dotnet run --launch-profile Sudoku
```

bo profil `Sudoku` ustawia lokalne środowisko automatycznie.

Pliki:
- baza: `src/Backend/Sudoku/Sudoku/appsettings.json`
- lokalny override: `src/Backend/Sudoku/Sudoku/appsettings.local.json`
- produkcja: `src/Backend/Sudoku/Sudoku/appsettings.production.json`

### MachineLearning

Lokalne `ML` powinno działać z:

```text
ML_ENVIRONMENT=local
```

Pliki:
- baza: `src/MachineLearning/api/.env`
- lokalny override: `src/MachineLearning/api/.env.local`
- produkcja: `src/MachineLearning/api/.env.production`

Nie ustawiaj lokalnie `ML_ENVIRONMENT=production`.

### Frontend

Przy `npm run dev` frontend lokalnie korzysta z `Vite` i proxy do `Backendu`.

Pliki:
- konfiguracja dev servera: `src/Frontend/vite.config.ts`
- opcjonalny lokalny override: `src/Frontend/.env.local`

Jeżeli ustawiasz `VITE_API_BASE_URL`, upewnij się, że wskazuje lokalny backend, a nie adres produkcyjny.

## 6. Lokalne pliki konfiguracyjne

### 6.1. Backend - `appsettings.local.json`

Utwórz plik:

```text
src/Backend/Sudoku/Sudoku/appsettings.local.json
```

Przykład:

```jsonc
{
  "$schema": "https://json.schemastore.org/appsettings.json",
  "Kestrel": {
    "Endpoints": {
      "Http": {
        "Url": "http://127.0.0.1:5000"
      }
    }
  },
  "AdminAuth": {
    "SharedPassword": "TU_WLASNE_HASLO_ADMINA",
    "JwtSigningKey": "TU_WLASNY_DLUGI_KLUCZ_MIN_32_ZNAKI",
    "TokenLifetimeMinutes": 240
  },
  "ExamplesStorage": {
    "RootPath": "<REPO_ROOT>/examples"
  },
  "RawDatasetsStorage": {
    "BoardsSubdirectory": "<REPO_ROOT>/data/raw/boards",
    "DigitsSubdirectory": "<REPO_ROOT>/data/raw/digits"
  },
  "TrainingsStorage": {
    "RunsDirectoryPath": "<REPO_ROOT>/data/trainings/runs",
    "ReportsDirectoryPath": "<REPO_ROOT>/data/trainings/reports",
    "MetadataDirectoryPath": "<REPO_ROOT>/data/trainings/metadata",
    "WorkingDirectoryPath": "<REPO_ROOT>/tmp/trainings"
  },
  "SudokuSolveSessionsStorage": {
    "MetadataDirectoryPath": "<REPO_ROOT>/tmp/solve-sessions/metadata"
  },
  "ModelsRegistryStorage": {
    "RegistryDirectoryPath": "<REPO_ROOT>/data/models/registry"
  },
  "ModelsActiveStorage": {
    "ActiveDirectoryPath": "<REPO_ROOT>/data/models/active"
  },
  "DatasetsPreparation": {
    "BoardsSubdirectory": "<REPO_ROOT>/data/raw/boards",
    "DigitsSubdirectory": "<REPO_ROOT>/data/raw/digits",
    "PreparationsDirectoryPath": "<REPO_ROOT>/data/preparations",
    "ProcessedDatasetsDirectoryPath": "<REPO_ROOT>/data/processed",
    "TemporaryArtifactsDirectoryPath": "<REPO_ROOT>/tmp/datasets",
    "DefaultPreprocessingProfile": "default-28x28-v1",
    "DefaultMixSplitRatios": {
      "Train": 0.8,
      "Val": 0.1,
      "Test": 0.1
    }
  }
}
```

Uwagi:
- używaj ścieżek absolutnych,
- wpisz własne hasło admina,
- wpisz własny długi klucz JWT,
- nie kopiuj produkcyjnych sekretów do lokalnego pliku.

### 6.2. MachineLearning - `.env.local`

Utwórz plik:

```text
src/MachineLearning/api/.env.local
```

Przykład:

```dotenv
ML_ENVIRONMENT=local
ML_BOARDS_SUBDIRECTORY=<REPO_ROOT>/data/raw/boards
ML_DIGITS_SUBDIRECTORY=<REPO_ROOT>/data/raw/digits
ML_TEMP_DATASETS_DIRECTORY_PATH=<REPO_ROOT>/tmp/datasets
ML_DATASET_PREPARATIONS_DIRECTORY_PATH=<REPO_ROOT>/data/preparations
ML_EXAMPLES_UPLOADS_DIR=<REPO_ROOT>/examples/uploads
ML_MODELS_ACTIVE_DIR=<REPO_ROOT>/data/models/active
ML_MODELS_REGISTRY_DIR=<REPO_ROOT>/data/models/registry
ML_TRAINING_RUNNER=mock
ML_TRAINING_DEVICE=auto
ML_TRAINING_ALLOWED_OUTPUT_ROOTS=<REPO_ROOT>
```

Ważne:
- domyślnie lokalny `ML` startuje z `ML_TRAINING_RUNNER=mock`,
- to wynika z bazowego `src/MachineLearning/api/.env`,
- jeżeli chcesz realny lokalny trening, ustaw:

```dotenv
ML_TRAINING_RUNNER=pytorch
```

### 6.3. MachineLearning bootstrap - `.env.local`

Przed pierwszym lokalnym użyciem aplikacji trzeba zainicjalizować rejestr modeli i aktywny model. Konfiguracja tego kroku jest trzymana osobno od głównego `.env` serwisu `ML`.

Utwórz albo popraw plik:

```text
src/MachineLearning/init_bootstrap/.env.local
```

Minimalny przykład:

```dotenv
ML_ENVIRONMENT=local
ML_MODELS_REGISTRY_DIRECTORY_PATH=<REPO_ROOT>/data/models/registry
ML_ACTIVE_MODEL_DIRECTORY_PATH=<REPO_ROOT>/data/models/active
ML_BOOTSTRAP_MODELS_JSON=[{"family":"cnn","type":"custom-cnn-v1","name":"cnn-baseline","displayName":"CNN baseline"}]
ML_BOOTSTRAP_OVERWRITE_EXISTING=false
ML_BOOTSTRAP_SET_ACTIVE_IF_MISSING=true
ML_BOOTSTRAP_DEFAULT_ACTIVE_MODEL=cnn-baseline
```

Uwagi:
- użyj ścieżek absolutnych,
- lokalnie wystarczy `cnn-baseline`, ale możesz dopisać kolejne deklaracje modeli,
- nie ustawiaj tutaj ścieżek produkcyjnych typu `/opt/sudoku/...`.

Ważne rozróżnienie:
- `init_bootstrap` potrafi utworzyć wpisy registry dla `custom-cnn-v1` oraz kilku wariantów `resnet`,
- kod treningowy ma obecnie fabrykę modeli dla `custom-cnn-v1`, `resnet18` i `resnet50`,
- katalog domyślnych profili treningowych zawiera dziś `cnn-default-v1` i `resnet18-finetune-v1`.

W praktyce najbezpieczniejszy lokalny bootstrap to `cnn-baseline` (`custom-cnn-v1`). `resnet18` jest drugim realnie przygotowanym wariantem treningowym. `resnet50` ma obsługę w fabryce modelu, ale nie ma obecnie osobnego domyślnego profilu w katalogu profili. Pozostałe wpisy `resnet` mogą istnieć jako deklaracje bootstrap/registry, ale wymagają dopisania obsługi runtime lub profili zanim będą normalnym wyborem operacyjnym.

### 6.4. Frontend - opcjonalny `.env.local`

Frontend lokalnie zwykle nie potrzebuje osobnego `.env`, bo `Vite` ma proxy:
- `/api -> http://127.0.0.1:5000`
- `/ws -> http://127.0.0.1:5000`

Jeżeli jednak chcesz jawnie ustawić endpoint, utwórz:

```text
src/Frontend/.env.local
```

Przykład:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:5000/api
```

## 7. Instalacja zależności projektowych

### 7.1. Backend - pakiety `.NET`

Wejdź do projektu startowego backendu i pobierz zależności `NuGet`:

```bash
cd "<REPO_ROOT>/src/Backend/Sudoku/Sudoku"
dotnet restore
```

To jest właściwy krok instalacji bibliotek `.NET` dla backendu. Lista najważniejszych zależności backendu jest w `TECH-STACK.md`; dokładne wersje są w plikach `*.csproj`.

### 7.2. MachineLearning - pakiety `Python`

Rekomendowany wariant:

```bash
cd "<REPO_ROOT>"
python3 -m venv .ml-venv
source .ml-venv/bin/activate
pip install -r src/MachineLearning/requirements.txt
```

To instaluje zależności `Python` wymagane przez `ML`.

### 7.3. Frontend - pakiety `npm`

```bash
cd "<REPO_ROOT>/src/Frontend"
npm install
```

To instaluje biblioteki frontendu i tworzy lokalny `node_modules`.

## 8. Katalogi, które trzeba przygotować ręcznie

To są elementy poza normalnym użyciem aplikacji, które warto utworzyć ręcznie na starcie:

```bash
mkdir -p \
  "<REPO_ROOT>/examples/uploads" \
  "<REPO_ROOT>/data/raw/boards" \
  "<REPO_ROOT>/data/raw/digits" \
  "<REPO_ROOT>/data/preparations" \
  "<REPO_ROOT>/data/processed" \
  "<REPO_ROOT>/data/models/registry" \
  "<REPO_ROOT>/data/models/active" \
  "<REPO_ROOT>/data/trainings/runs" \
  "<REPO_ROOT>/data/trainings/reports" \
  "<REPO_ROOT>/data/trainings/metadata" \
  "<REPO_ROOT>/tmp/datasets" \
  "<REPO_ROOT>/tmp/solve-sessions/metadata" \
  "<REPO_ROOT>/tmp/trainings"
```

## 9. Bootstrap modeli przed pierwszym użyciem lokalnym

Ten krok tworzy wpisy w lokalnym rejestrze modeli oraz ustawia domyślny aktywny model, jeśli jeszcze go nie ma.

Uruchom go po instalacji zależności `Python` i po utworzeniu katalogów z poprzedniego punktu:

```bash
cd "<REPO_ROOT>/src/MachineLearning"
source "<REPO_ROOT>/.ml-venv/bin/activate"
ML_ENVIRONMENT=local python -m init_bootstrap --dry-run
ML_ENVIRONMENT=local python -m init_bootstrap
```

Lokalnie trzeba wykonać to ręcznie przed pierwszym użyciem aplikacji. Na serwerze bootstrap jest elementem automatyzacji deployu, więc nie jest osobnym ręcznym krokiem operacyjnym.

Jeżeli `--dry-run` pokazuje błędne ścieżki, popraw `src/MachineLearning/init_bootstrap/.env.local` i uruchom komendę ponownie.

Jeżeli rozszerzasz `ML_BOOTSTRAP_MODELS_JSON` o kolejne modele, traktuj to jako deklarację wpisu w rejestrze. Zanim użyjesz takiego modelu do treningu lub inferencji, sprawdź, czy dana architektura i profil są obsługiwane w kodzie `ML`.

## 10. Pliki i dane wrzucane ręcznie

To jest jeden z nielicznych etapów wykonywanych ręcznie, bo duże datasety nie są częścią repo.

### 10.1. `board`

Wrzuć katalogi źródłowe do:

```text
<REPO_ROOT>/data/raw/boards
```

Przykład:

```text
data/raw/boards/
  v1_training/
  v1_test/
  v2_train/
  v2_test/
```

W środku oczekiwane są pary:
- `*.jpg`
- `*.dat`

o tej samej nazwie bazowej.

### 10.2. `digit`

Wrzuć pliki do:

```text
<REPO_ROOT>/data/raw/digits
```

Oczekiwane są pary:
- `{prefix}.idx3-ubyte`
- `{prefix}.idx1-ubyte`

Przykład:

```text
data/raw/digits/
  train.idx3-ubyte
  train.idx1-ubyte
  t10k.idx3-ubyte
  t10k.idx1-ubyte
```

### 10.3. Przykłady Sudoku

Jeżeli chcesz mieć lokalne przykłady w aplikacji, wrzuć obrazy do:

```text
<REPO_ROOT>/examples/uploads
```

## 11. Uruchomienie aplikacji lokalnie

Najwygodniej uruchomić system w trzech terminalach.

### 11.1. Backend

```bash
cd "<REPO_ROOT>/src/Backend/Sudoku/Sudoku"
dotnet run --launch-profile Sudoku
```

Backend będzie dostępny pod:

```text
http://127.0.0.1:5000
```

### 11.2. MachineLearning

```bash
cd "<REPO_ROOT>"
source .ml-venv/bin/activate
python src/MachineLearning/main.py
```

`ML` będzie dostępny pod:

```text
http://127.0.0.1:8000
```

### 11.3. Frontend

```bash
cd "<REPO_ROOT>/src/Frontend"
npm run dev
```

Frontend zwykle wystartuje pod lokalnym adresem Vite, np.:

```text
http://127.0.0.1:5173
```

## 12. Szybka weryfikacja po starcie

Sprawdź:

```bash
curl http://127.0.0.1:8000/ml/ping
curl http://127.0.0.1:5000/api/ping
```

Jeżeli oba endpointy odpowiadają, podstawowa instalacja i uruchomienie są gotowe.

## 13. Gdzie szukać reszty informacji

- opis produktu, flow i `UC-*`: `README.md`
- katalog technologii i zależności: `TECH-STACK.md`
- szczegółowy zakres produktu: `.ai/prd.md`
- rozpiski funkcjonalne: `.ai/feature/`
- deploy i runtime serwera: `.ai/DokumentacjaDeployuRuntimeSerwera.md`
