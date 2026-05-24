# UC-08-BE - Plan implementacyjny dla `GET /api/trainings`

## 1) Przeznaczenie endpointa
- Endpoint `GET /api/trainings` zwraca chronioną listę runów treningowych utrzymywanych przez Backend w plikach `trainings/metadata/{runName}.json`.
- Lista ma zasilać katalog treningów w `UC-08`: runy aktywne, zakończone sukcesem, anulowane i nieudane, wraz ze skrótem konfiguracji, postępu, raportu i metryk.
- Endpoint jest read-only: nie startuje treningu, nie anuluje runu, nie finalizuje modelu i nie odpytuje `ML`.
- Backend pozostaje `source of truth`; `FE` nie czyta plików runtime i nie woła `ML`.

## 2) Zakres i założenia
- Plan dotyczy wyłącznie części BE dla endpointa `GET /api/trainings`.
- Nie opierać decyzji o kontrakcie na bieżącym stanie `FE` lub `ML`.
- Endpoint jest chroniony tokenem administracyjnym z `UC-13`.
- Źródłem listy są rekordy systemowe Backendu z `TrainingsStorage.MetadataDirectoryPath`, nie rejestr `ML` i nie katalog raportów.
- `GET /api/models/registry` istnieje jako osobny endpoint katalogowy modeli; `UC-08` łączy te listy po stronie widoku, ale `GET /api/trainings` nie ma zwracać pełnych manifestów modeli.
- Na obecnym stanie repo część plików jest już gotowa po historyjkach `UC-06`, `UC-11`, `UC-12`, `UC-13` i `UC-10`; przy implementacji należy je reużyć, a nie tworzyć równoległe adaptery lub DTO.

## 3) Kontrakty API FE i ML

### 3.1 FE -> BE (`GET /api/trainings`)
- Request body: brak.
- Query params: brak w MVP.
- Autoryzacja: token administracyjny (`Bearer`).

### 3.2 Odpowiedzi publiczne
- `200 OK` -> `TrainingRunsListApiResponse`.
- `401 Unauthorized` -> brak albo niepoprawny token.
- `500 Internal Server Error` -> błąd odczytu, parsowania albo niespójność metadanych uniemożliwiająca zbudowanie listy.

### 3.3 Model wejściowy/wyjściowy FE
- Wejście FE -> BE:
  - brak body.
- Wyjście BE -> FE (`TrainingRunsListApiResponse`):
  - `items: TrainingRunListItemApiResponse[]`
  - `totalCount: number`
- `TrainingRunListItemApiResponse`:
  - `runName: string`
  - `status: string`
  - `createdAtUtc: string`
  - `updatedAtUtc: string | null`
  - `startedAtUtc: string | null`
  - `finishedAtUtc: string | null`
  - `baseModelName: string`
  - `producedModelName: string`
  - `processedDatasetName: string`
  - `trainingMode: string`
  - `trainingProfileName: string`
  - `augmentationProfileName: string`
  - `benchmarkName: string`
  - `reportStatus: string | null`
  - `progress: TrainingRunProgressApiResponse | null`
  - `metricsSummary: TrainingMetricsSummaryApiResponse | null`
  - `warnings: string[]`

Przykład:

```json
{
  "items": [
    {
      "runName": "train-20260503-112233",
      "status": "succeeded",
      "createdAtUtc": "2026-05-03T09:22:33Z",
      "updatedAtUtc": "2026-05-03T09:40:12Z",
      "startedAtUtc": "2026-05-03T09:23:02Z",
      "finishedAtUtc": "2026-05-03T09:40:12Z",
      "baseModelName": "cnn-bootstrap",
      "producedModelName": "train-20260503-112233",
      "processedDatasetName": "sudokuDigitsV1",
      "trainingMode": "fineTuning",
      "trainingProfileName": "cnn-default-v1",
      "augmentationProfileName": "digits-light-v1",
      "benchmarkName": "sudoku-benchmark-v1",
      "reportStatus": "ready",
      "progress": {
        "percent": 100,
        "epoch": 10,
        "totalEpochs": 20,
        "trainLoss": 0.05,
        "validationLoss": 0.08,
        "trainAccuracy": 0.98,
        "validationAccuracy": 0.96
      },
      "metricsSummary": {
        "accuracy": 0.96,
        "macroF1": 0.95
      },
      "warnings": []
    }
  ],
  "totalCount": 1
}
```

### 3.4 BE <-> ML dla tego endpointa
- Brak nowego endpointu `BE -> ML`.
- Brak nowego endpointu `ML -> BE`.
- Dane z `ML` trafiają do listy wyłącznie pośrednio przez wcześniejsze eventy z `UC-06/UC-07`, zapisywane przez Backend do `trainings/metadata/{runName}.json`.

## 4) Zachowanie per warstwa

### API (`Sudoku`)
- Cienki kontroler:
  - wymusza autoryzację,
  - wywołuje `ListTrainingRunsQuery` przez MediatR,
  - mapuje DTO aplikacyjne na `TrainingRunsListApiResponse`,
  - mapuje błędy na `ErrorApiResponse`.
- Nie wykonuje I/O, nie skanuje katalogów, nie parsuje JSON i nie decyduje o sortowaniu biznesowym poza prostym mapowaniem odpowiedzi.

### Application (`Application`)
- Use-case odczytowy `ListTrainingRunsQuery`.
- Logika aplikacyjna:
  - pobiera wszystkie rekordy metadanych przez `ITrainingRunsGateway`,
  - sprawdza invariant braku zduplikowanych `runName`,
  - waliduje minimalny zakres pól potrzebny do publicznej listy,
  - mapuje metadane runów do `TrainingRunListItemDto`,
  - sortuje deterministycznie: `createdAtUtc` malejąco, potem `runName` rosnąco,
  - wylicza `totalCount`.
- Nie zna szczegółów filesystem, nazw plików `.json`, serializerów ani ścieżek runtime.

### Domain / Models (`Models`)
- Reużyć neutralne modele statusów treningu, np. `Models/Trainings/TrainingRunStatus.cs`, jeśli są potrzebne do wspólnej semantyki statusów.
- Dla tego endpointa nie trzeba dodawać nowego modelu domenowego, jeśli obecny moduł `Trainings` utrzymuje DTO w `Application`.
- Nie przenosić modeli HTTP (`TrainingRunsListApiResponse`, `TrainingRunListItemApiResponse`) do `Models`.

### Infrastructure (`Infrastructure`)
- Implementuje port `ITrainingRunsGateway`.
- Techniczne odpowiedzialności:
  - listowanie plików w `TrainingsStorage.MetadataDirectoryPath`,
  - filtrowanie plików `*.json`,
  - odczyt i deserializacja metadanych runów,
  - zwrócenie `TrainingRunMetadataDto` do Application.
- Infrastructure nie decyduje, czy run jest widoczny, aktywny albo poprawny biznesowo; to należy do `Application`.

## 5) Pliki per warstwa i odpowiedzialności

### API (`src/Backend/Sudoku/Sudoku`)
- `[REUSE/UTWARDZENIE]` `Controllers/TrainingsController.cs`
  - akcja `ListAsync` dla `GET /api/trainings`,
  - `[Authorize]`, `[HttpGet]`, `[Route("api/trainings")]`,
  - mapowanie `ListTrainingRunsQueryResultDto` -> `TrainingRunsListApiResponse`,
  - mapowanie `IOException`, `UnauthorizedAccessException`, `InvalidDataException`, `JsonException`, `FileStorageItemNotFoundException` na `500`.
- `[REUSE]` `Contracts/TrainingRunsListApiResponse.cs`
  - publiczny kontener listy `items`, `totalCount`.
- `[REUSE]` `Contracts/TrainingRunListItemApiResponse.cs`
  - publiczny element listy runów.
- `[REUSE]` `Contracts/TrainingRunProgressApiResponse.cs`
  - publiczny skrót postępu.
- `[REUSE]` `Contracts/TrainingMetricsSummaryApiResponse.cs`
  - publiczny skrót metryk.
- `[REUSE]` `Contracts/ErrorApiResponse.cs`
  - wspólny model błędu HTTP `errorType`, `message`.
- `[REUSE]` `Program.cs`
  - bind i walidacja `TrainingsStorageOptions`,
  - rejestracja kontrolerów, autoryzacji i MediatR.
- `[REUSE]` `appsettings.local.json`
  - twarde lokalne ścieżki `TrainingsStorage.*`, w tym `MetadataDirectoryPath`.
- `[REUSE]` `appsettings.production.json`
  - placeholdery produkcyjne dla `TrainingsStorage.*` podmieniane przez workflow.

### Application (`src/Backend/Sudoku/Application`)
- `[REUSE]` `Trainings/ListTrainingRunsQuery.cs`
  - query MediatR bez parametrów.
- `[REUSE/UTWARDZENIE]` `Trainings/ListTrainingRunsQueryHandler.cs`
  - pobranie metadanych, walidacja invariantów, sortowanie i mapowanie listy.
- `[REUSE]` `Trainings/ListTrainingRunsQueryResultDto.cs`
  - wynik query: `Items`, `TotalCount`.
- `[REUSE]` `Trainings/TrainingRunListItemDto.cs`
  - DTO elementu listy używane między Application i API.
- `[REUSE]` `Trainings/TrainingRunMetadataDto.cs`
  - plikowy rekord runu utrzymywany przez Backend.
- `[REUSE]` `Trainings/TrainingRunProgressDto.cs`
  - aplikacyjny model postępu.
- `[REUSE]` `Trainings/TrainingMetricsSummaryDto.cs`
  - aplikacyjny model skrótu metryk.
- `[REUSE]` `Trainings/ListTrainingRunsErrorTypes.cs`
  - stałe `errorType` dla listowania.
- `[REUSE]` `Trainings/TrainingsStorageOptions.cs`
  - typed options dla katalogów `runs`, `reports`, `metadata`, `working`.
- `[REUSE]` `Abstractions/ITrainingRunsGateway.cs`
  - port aplikacyjny do listowania i odczytu metadanych runów; używany też przez `GET /api/trainings/active`, cancel, events i późniejsze szczegóły.

### Domain / Models (`src/Backend/Sudoku/Models`)
- `[REUSE]` `Trainings/TrainingRunStatus.cs`
  - kanoniczne statusy runu, jeżeli handler lub inne use-case'y potrzebują wspólnej semantyki.
- `[REUSE]` `Trainings/TrainingReportStatus.cs`
  - kanoniczne statusy raportu, jeżeli są używane przy zapisie metadanych po eventach.
- `[BRAK NOWEGO PLIKU]`
  - dla samego listowania nie dodawać nowych modeli domenowych, dopóki logika pozostaje prostym odczytem rekordu systemowego.

### Infrastructure (`src/Backend/Sudoku/Infrastructure`)
- `[REUSE]` `Storage/TrainingRunsGateway.cs`
  - implementacja `ITrainingRunsGateway`,
  - odczyt `trainings/metadata/*.json`,
  - deserializacja przez `JsonSerializerDefaults.Web`,
  - metody `ListAsync`, `GetByRunNameAsync`, `TryCreateAsync`, `UpdateAsync`, `DeleteAsync` wspólne dla kilku use-case'ów.
- `[REUSE]` `Storage/LocalFileStorageGateway.cs`
  - generyczne operacje plikowe; nie dublować ich w osobnym readerze metadanych.
- `[REUSE]` `DependencyInjection.cs`
  - rejestracja `ITrainingRunsGateway -> TrainingRunsGateway`.
- `[BRAK ZMIAN]` `Ml/*`
  - listowanie treningów nie komunikuje się z `ML`.

### Workflow (`.github/workflows`)
- `[REUSE/ZWERYFIKOWAĆ]` `.github/workflows/backend-cd.yml`
  - workflow już powinien walidować i podstawiać:
    - `BE_TRAININGS_RUNS_DIRECTORY_PATH`,
    - `BE_TRAININGS_REPORTS_DIRECTORY_PATH`,
    - `BE_TRAININGS_METADATA_DIRECTORY_PATH`,
    - `BE_TRAININGS_WORKING_DIRECTORY_PATH`.
  - dla tego endpointa nie dodawać nowych zmiennych, jeśli powyższe istnieją i trafiają do `TrainingsStorage`.

## 6) Weryfikacja usług Infrastructure i antyduplikacja
- Istnieje `ITrainingRunsGateway` oraz `TrainingRunsGateway`; używać ich jako jedynego adaptera metadanych treningów.
- Istnieje `IFileStorageGateway` oraz `LocalFileStorageGateway`; nie dodawać klas typu `TrainingMetadataReader`, `TrainingDirectoryScanner` ani bezpośredniego `Directory.*` / `File.*` poza generycznym adapterem storage.
- Jeśli potrzeba nowej operacji plikowej, najpierw rozszerzyć `IFileStorageGateway` generycznie, zamiast dokładać logikę specyficzną dla listy treningów.
- `TrainingRunsGateway` ma pozostać reużywalny dla `GET /api/trainings`, `GET /api/trainings/active`, `POST /api/trainings/{runName}/cancel`, eventów `ML -> BE` i przyszłego `GET /api/trainings/{runName}`.

## 7) Przepływ w obrębie BE
1. `FE` wysyła `GET /api/trainings` z tokenem admin.
2. Middleware autoryzacji weryfikuje token z `UC-13`.
3. `TrainingsController.ListAsync` loguje rozpoczęcie i wysyła `ListTrainingRunsQuery`.
4. `ListTrainingRunsQueryHandler` woła `ITrainingRunsGateway.ListAsync`.
5. `TrainingRunsGateway` listuje pliki z `TrainingsStorage.MetadataDirectoryPath`.
6. Gateway filtruje `*.json`, odczytuje każdy plik i deserializuje `TrainingRunMetadataDto`.
7. Handler sprawdza duplikaty `runName` i wymagane pola listy.
8. Handler mapuje do `TrainingRunListItemDto`, sortuje i zwraca `ListTrainingRunsQueryResultDto`.
9. Kontroler mapuje DTO na `TrainingRunsListApiResponse`.
10. `FE` otrzymuje listę i może korelować `producedModelName` z osobną listą `GET /api/models/registry`.

## 8) Główne funkcje
- `TrainingsController.ListAsync(...)`
- `TrainingsController.ToTrainingRunListItemApiResponse(...)`
- `TrainingsController.ToTrainingRunProgressApiResponse(...)`
- `TrainingsController.ToTrainingMetricsSummaryApiResponse(...)`
- `ListTrainingRunsQueryHandler.Handle(...)`
- `ListTrainingRunsQueryHandler.EnsureNoDuplicateRunNames(...)`
- `ListTrainingRunsQueryHandler.EnsureListableMetadata(...)`
- `ITrainingRunsGateway.ListAsync(...)`
- `TrainingRunsGateway.ListAsync(...)`
- `IFileStorageGateway.ListFilesAsync(...)`
- `IFileStorageGateway.OpenReadAsync(...)`

## 9) Wyjątki, fallbacki i zachowanie błędowe

### 9.1 Publiczne statusy
- `200 OK`:
  - metadane odczytane poprawnie,
  - pusta lista jest poprawnym stanem świeżego środowiska albo środowiska bez uruchomionych treningów.
- `401 Unauthorized`:
  - brak tokenu albo token niepoprawny.
- `500 Internal Server Error`:
  - błąd I/O katalogu metadanych,
  - brak uprawnień,
  - uszkodzony JSON,
  - deserializacja zwróciła `null`,
  - duplikat `runName`,
  - brak wymaganego pola w metadanych,
  - niespójny rekord, którego nie da się bezpiecznie pokazać publicznie.

### 9.2 Fallbacki
- Brak fallbacku do `ML`.
- Brak fallbacku do katalogu `trainings/reports`.
- Brak fallbacku do `models/registry`.
- Brak fallbacku do cache po stronie `FE`.
- Pusty katalog metadanych -> `200 OK` z `items=[]` i `totalCount=0`.
- Brak katalogu metadanych:
  - preferowane zachowanie zależy od `IFileStorageGateway`; jeśli zwraca pustą listę dla nieistniejącego katalogu, endpoint zwraca `200`.
  - jeśli adapter rzuca błąd I/O, endpoint zwraca `500`; tworzenie katalogów powinno należeć do init/deploy/runtime setup, nie do `GET`.

### 9.3 Scenariusze graniczne
- Pojedynczy uszkodzony plik metadanych:
  - fail fast całego endpointa z `500`, żeby operator nie dostał częściowo fałszywego katalogu treningów.
- Plik bez rozszerzenia `.json` w katalogu metadata:
  - ignorować technicznie w gatewayu.
- Dwa pliki z tym samym `runName`:
  - `500`, bo `runName` jest publicznym identyfikatorem runu.
- Run terminalny bez `finishedAtUtc`:
  - w MVP można go zwrócić, jeśli metadane mają wymagane pola listy; szczegółowa walidacja terminalnych dat należy do event/finalizacji albo `UC-09`.
- `warnings = null`:
  - Application normalizuje do pustej listy.
- Brak `metricsSummary` albo `reportStatus`:
  - poprawne dla runu aktywnego, anulowanego, nieudanego albo zakończonego z brakującym raportem.

## 10) Pseudokod specyficznej logiki

```text
handleListTrainingRuns():
  metadataItems = trainingRunsGateway.list()

  ensureNoDuplicateRunNames(metadataItems)

  items = metadataItems
    .map(metadata => {
      ensureRequiredListFields(metadata)

      return TrainingRunListItemDto(
        runName = metadata.runName,
        status = metadata.status,
        createdAtUtc = metadata.createdAtUtc,
        updatedAtUtc = metadata.updatedAtUtc,
        startedAtUtc = metadata.startedAtUtc,
        finishedAtUtc = metadata.finishedAtUtc,
        baseModelName = metadata.baseModelName,
        producedModelName = metadata.producedModelName,
        processedDatasetName = metadata.processedDatasetName,
        trainingMode = metadata.trainingMode,
        trainingProfileName = metadata.trainingProfileName,
        augmentationProfileName = metadata.augmentationProfileName,
        benchmarkName = metadata.benchmarkName,
        reportStatus = metadata.reportStatus,
        progress = metadata.progress,
        metricsSummary = metadata.metricsSummary,
        warnings = metadata.warnings ?? []
      )
    })
    .orderByDescending(createdAtUtc)
    .thenBy(runName)

  return TrainingRunsListDto(items, totalCount = items.count)
```

```text
trainingRunsGateway.list():
  files = fileStorage.listFiles(metadataDirectoryPath)
  metadataFiles = files
    .where(name endsWith ".json")
    .orderBy(name)

  for file in metadataFiles:
    stream = fileStorage.openRead(metadataDirectoryPath, file.name)
    metadata = deserializeJson<TrainingRunMetadataDto>(stream)

    if metadata is null:
      throw InvalidDataException

    yield metadata
```

## 11) Workflow GitHub i konfiguracja runtime
- Lokalnie:
  - `appsettings.local.json` ma zawierać absolutne, lokalne ścieżki `TrainingsStorage.*`, np. `/home/wojtek/projects/sudoku/data/trainings/metadata`.
  - Lokalne ścieżki są wpisane na sztywno w overlay local.
- Produkcyjnie:
  - `appsettings.production.json` zawiera placeholdery.
  - `.github/workflows/backend-cd.yml` podstawia wartości produkcyjne z GitHub Variables do `appsettings.production.json` podczas budowania release'u.
  - Workflow nie może czyścić ani nadpisywać `/opt/sudoku/shared/trainings`; to trwały runtime state, a nie część release'u.
- Dla tego endpointa wymagane są przede wszystkim:
  - `BE_TRAININGS_METADATA_DIRECTORY_PATH`,
  - pośrednio pozostałe `BE_TRAININGS_*`, bo `TrainingsStorageOptions` waliduje całą sekcję.
- Jeśli workflow już je waliduje i podstawia, nie dodawać nowego kroku deployu tylko dla `GET /api/trainings`.

## 12) Logging
- Cel: umożliwić diagnostykę uszkodzonych metadanych bez logowania pełnych payloadów i bez spamowania.
- `Information`:
  - rozpoczęto listowanie runów treningowych,
  - zakończono listowanie z `TotalCount`.
- `Warning`:
  - opcjonalnie: wykryto nieistotny plik w katalogu metadata, jeśli zostanie uznane, że warto to obserwować.
- `Error`:
  - błąd odczytu listy runów,
  - `errorType = training_runs_list_read_failed`,
  - typ wyjątku i kontekst operacji.
- Guardrail:
  - nie logować pełnej treści plików metadata,
  - nie logować tokenów ani sekretów,
  - nie zwracać ścieżek systemowych w `ErrorApiResponse`,
  - w logach preferować `runName`, `metadataFileName`, `errorType` zamiast absolutnych ścieżek.

## 13) Kolejność implementacji kodu dla historyjki
1. Zweryfikować istniejące pliki `TrainingRunsListApiResponse`, `TrainingRunListItemApiResponse`, `ListTrainingRunsQuery*`, `ITrainingRunsGateway` i `TrainingRunsGateway`.
2. Jeśli endpoint nie istnieje, dodać `TrainingsController.ListAsync`; jeśli istnieje, sprawdzić mapowanie wszystkich pól kontraktu z `UC-08`.
3. Upewnić się, że `ListTrainingRunsQueryHandler` sortuje `createdAtUtc desc`, potem `runName asc`.
4. Upewnić się, że `Warnings` jest normalizowane do pustej listy.
5. Upewnić się, że handler wykrywa duplikaty `runName` i wymagane pola publicznej listy.
6. Upewnić się, że `TrainingRunsGateway` używa `IFileStorageGateway`, a nie bezpośredniego filesystem w Application/API.
7. Zweryfikować `Program.cs`: `TrainingsStorageOptions` jest zbindowane, waliduje absolutne ścieżki i ma `ValidateOnStart`.
8. Zweryfikować `appsettings.local.json` i `appsettings.production.json` dla `TrainingsStorage`.
9. Zweryfikować `.github/workflows/backend-cd.yml`, czy podstawia `BE_TRAININGS_METADATA_DIRECTORY_PATH` i pozostałe `BE_TRAININGS_*`.
10. Dodać testy jednostkowe handlera: pusta lista, sortowanie, `totalCount`, `warnings = null`, duplikat `runName`, brak wymaganego pola.
11. Dodać testy gatewaya: ignorowanie plików nie-JSON, poprawny odczyt JSON, uszkodzony JSON, `null` payload.
12. Dodać testy API/integracyjne: `200`, `401`, `500` dla uszkodzonych metadanych.

## 14) Guardraile implementacyjne
- Kontroler ma pozostać cienki; bez `Directory.*`, `File.*`, `JsonSerializer.Deserialize` i reguł biznesowych.
- `Application` decyduje o sortowaniu, wymaganych polach i publicznym kształcie listy.
- `Infrastructure` implementuje storage i deserializację, nic ponad to.
- Nie dodawać minimal API `MapGet`; używać kontrolera ASP.NET.
- Nie hardcodować `/opt/sudoku/...` ani lokalnych ścieżek w kodzie.
- Nie dublować `TrainingRunsGateway`.
- Nie wywoływać `ML` podczas listowania.
- Nie czytać raportów z `trainings/reports` dla listy; szczegóły raportu należą do `UC-09`.
- Nie zwracać do `FE` ścieżek systemowych, nazw plików metadata ani technicznych lokalizacji artefaktów.
- Publiczny JSON ma pozostać w `camelCase`, modele HTTP z sufiksem `ApiResponse`, DTO aplikacyjne z sufiksem `Dto`.

## 15) Zależności pomiędzy historyjkami
- Wejściowe:
  - `UC-13` - autoryzacja endpointu tokenem administracyjnym.
  - `UC-06 POST /api/trainings` - tworzy `trainings/metadata/{runName}.json`.
  - `UC-06 POST /api/trainings/{runName}/cancel` - aktualizuje status runu i może zostawić terminalny `cancelled`.
  - `UC-06 POST /internal/ml/trainings/{runName}/events` - aktualizuje postęp, status końcowy, `reportStatus`, `metricsSummary`, `warnings`.
  - `UC-12 GET /api/datasets/processed` - źródło nazw datasetów używanych przy tworzeniu runu.
  - `UC-06 GET /api/models/registry` - źródło modeli bazowych używanych przy tworzeniu runu.
- Równoległe / konsumujące:
  - `UC-07` - monitoring realtime korzysta z tego samego rekordu metadata, ale innym kanałem.
  - `UC-08 GET /api/models/registry` - lista modeli korelowana z runami przez `producedModelName` / `sourceRunName`.
  - `UC-09 GET /api/trainings/{runName}` - szczegóły runu i pełne metryki.
  - `UC-10 PUT /api/models/active` - wybór aktywnego modelu po analizie listy treningów i modeli.

## 16) Inne istotne reguły
- `GET /api/trainings` zwraca wszystkie znane runy, a nie tylko aktywne.
- Endpoint nie paginuje w MVP; jeśli lista urośnie, paginacja/sort/filter powinny być dodane jawnie jako rozszerzenie kontraktu.
- `totalCount` oznacza liczbę elementów po zbudowaniu listy.
- `producedModelName` może wskazywać model, którego manifest jeszcze nie istnieje dla runu aktywnego lub nieudanego; to nie jest błąd listy treningów.
- Bootstrap modelu nie pojawia się na liście treningów, bo nie ma `runName`; pojawia się w `GET /api/models/registry`.
- Brak raportu nie oznacza automatycznie `failed`, jeśli finalizacja runu zapisała sukces z ostrzeżeniem.
- Statusy i ostrzeżenia mają być prezentowane jako dane katalogowe, bez prób naprawiania stanu w endpointcie GET.

## 17) Model API wejściowy i wyjściowy w komunikacji z FE i ML
- FE -> BE:
  - `GET /api/trainings`
  - brak body.
- BE -> FE:
  - `TrainingRunsListApiResponse`,
  - `TrainingRunListItemApiResponse[]`,
  - `TrainingRunProgressApiResponse | null`,
  - `TrainingMetricsSummaryApiResponse | null`,
  - `ErrorApiResponse` dla błędów.
- BE -> ML:
  - brak komunikacji dla tego endpointa.
- ML -> BE:
  - brak komunikacji inicjowanej przez ten endpoint.
  - historycznie istotne dane pochodzą z `POST /internal/ml/trainings/{runName}/events`, ale endpoint listy czyta już tylko zapisany rekord Backendu.
- Plikowy kontrakt wejściowy dla BE:
  - `trainings/metadata/{runName}.json`.
