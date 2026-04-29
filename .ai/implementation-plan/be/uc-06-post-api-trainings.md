# UC-06-BE - Plan implementacyjny dla `POST /api/trainings`

## 1) Przeznaczenie endpointa
- Endpoint `POST /api/trainings` uruchamia asynchroniczny trening na jednym przygotowanym zestawie `.npz` i jednym modelu bazowym z rejestru.
- Endpoint jest chroniony tokenem administracyjnym z `UC-13`; bez tokenu nie wolno tworzyć runu ani wywoływać `ML`.
- Backend pozostaje `source of truth` dla runu: generuje `runName`, rezerwuje `producedModelName`, zapisuje `trainings/metadata/{runName}.json`, pilnuje pojedynczego aktywnego runu i dopiero potem zleca start do `ML`.
- Publicznym identyfikatorem jest `runName`, a nie techniczne `training_id` z bazy danych. `runName` jest używany później przez `GET /api/trainings/active`, `GET /api/trainings/{runName}`, `POST /api/trainings/{runName}/cancel` oraz kanał `/ws/trainings/{runName}`.
- W MVP `FE` przekazuje tylko `baseModelName` i `processedDatasetName`; profile, seed, benchmark, tryb treningu i ścieżki runtime rozwiązuje `BE`.

## 2) Zakres i założenia
- Plan opiera się na `PRD`, `UC-06`, zasadach runtime/deployu i obecnych planach dla `GET /api/trainings/active` oraz `GET /api/models/registry`.
- Nie sugerować się aktualnym stanem `FE` i `ML`; kontrakt ma wynikać z wymagań backendu jako warstwy aplikacyjnej.
- System dopuszcza dokładnie jeden aktywny run jednocześnie. Drugi start zwraca `409 training_run_already_active` i nie tworzy kolejki.
- `BE` waliduje zgodność modelu i datasetu przed wywołaniem `ML`: `RegistryModel.inputProfile == ProcessedDataset.preprocessingProfile`.
- `trainingMode = fineTuning` jest nadawane przez `BE`; `trainingProfileName`, `augmentationProfileName`, `benchmarkName` i `seed` pochodzą z typed options.
- Jeżeli start po stronie `ML` nie zostanie potwierdzony przed odpowiedzią do `FE`, `BE` robi rollback prowizorycznego rekordu runu albo oznacza go jako `failed` tylko wtedy, gdy rekord został już trwale przyjęty do workflow.
- Publiczny JSON ma klucze `camelCase`; modele wejściowe HTTP mają sufiks `ApiEntry`, wyjściowe `ApiResponse`, a DTO aplikacyjne `Dto`.

## 3) Kontrakty API FE i ML

### 3.1 FE -> BE (`POST /api/trainings`)
- Request body: `CreateTrainingRunApiEntry`.
- Autoryzacja: token administracyjny (`Bearer`).
- Body w MVP:

```json
{
  "baseModelName": "cnn-mnist-baseline",
  "processedDatasetName": "sudokuDigitsV1"
}
```

### 3.2 BE -> FE
- `202 Accepted` -> `TrainingRunApiResponse`.
- `400 Bad Request` -> `ErrorApiResponse`, gdy body jest niepoprawne albo model/dataset są profilowo niezgodne.
- `401 Unauthorized` -> brak albo niepoprawny token.
- `404 Not Found` -> wskazany model bazowy albo dataset `.npz` nie istnieje.
- `409 Conflict` -> istnieje aktywny run (`training_run_already_active`).
- `422 Unprocessable Entity` -> model istnieje, ale nie może startować treningu (`canStartTraining = false`) albo dataset ma niespójne metadane.
- `502 Bad Gateway` -> `ML` zwrócił nieoczekiwany kontrakt odpowiedzi.
- `503 Service Unavailable` -> `ML` niedostępny.
- `504 Gateway Timeout` -> timeout potwierdzenia startu przez `ML`.
- `500 Internal Server Error` -> błąd zapisu metadanych, rollbacku, niespójność stanu plikowego albo inny błąd techniczny `BE`.

Przykład `202 Accepted`:

```json
{
  "runName": "train-20260429-143000-cnn-mnist-baseline-sudokuDigitsV1",
  "status": "queued",
  "createdAtUtc": "2026-04-29T14:30:00Z",
  "baseModelName": "cnn-mnist-baseline",
  "producedModelName": "train-20260429-143000-cnn-mnist-baseline-sudokuDigitsV1",
  "processedDatasetName": "sudokuDigitsV1",
  "trainingMode": "fineTuning",
  "trainingProfileName": "cnn-default-v1",
  "augmentationProfileName": "digits-light-v1",
  "benchmarkName": "sudoku-benchmark-v1",
  "seed": 1234,
  "progressChannelUrl": "/ws/trainings/train-20260429-143000-cnn-mnist-baseline-sudokuDigitsV1"
}
```

### 3.3 BE -> ML (`POST /ml/trainings`)
- `BE` wywołuje `ML` dopiero po pozytywnej walidacji i rezerwacji runu.
- Payload wewnętrzny powinien być jawny i zawierać ścieżki rozwiązane przez `BE`, bez oczekiwania, że `ML` zgadnie layout katalogów:

```json
{
  "runName": "train-20260429-143000-cnn-mnist-baseline-sudokuDigitsV1",
  "baseModel": {
    "name": "cnn-mnist-baseline",
    "manifestPath": "/opt/sudoku/shared/models/registry/cnn-mnist-baseline/model.json",
    "primaryArtifactPath": "/opt/sudoku/shared/models/registry/cnn-mnist-baseline/artifacts/model.keras",
    "inputProfile": "default-28x28-v1"
  },
  "dataset": {
    "name": "sudokuDigitsV1",
    "artifactPath": "/opt/sudoku/shared/data/processed/sudokuDigitsV1.npz",
    "preprocessingProfile": "default-28x28-v1"
  },
  "training": {
    "mode": "fineTuning",
    "trainingProfileName": "cnn-default-v1",
    "augmentationProfileName": "digits-light-v1",
    "benchmarkName": "sudoku-benchmark-v1",
    "seed": 1234
  },
  "output": {
    "runDirectoryPath": "/opt/sudoku/shared/trainings/runs/train-20260429-143000-cnn-mnist-baseline-sudokuDigitsV1",
    "reportsDirectoryPath": "/opt/sudoku/shared/trainings/reports/train-20260429-143000-cnn-mnist-baseline-sudokuDigitsV1",
    "workingDirectoryPath": "/opt/sudoku/shared/tmp/trainings/train-20260429-143000-cnn-mnist-baseline-sudokuDigitsV1",
    "producedModelName": "train-20260429-143000-cnn-mnist-baseline-sudokuDigitsV1",
    "producedModelArtifactsDirectoryPath": "/opt/sudoku/shared/models/registry/train-20260429-143000-cnn-mnist-baseline-sudokuDigitsV1/artifacts"
  },
  "callbacks": {
    "eventsPath": "/internal/ml/trainings/train-20260429-143000-cnn-mnist-baseline-sudokuDigitsV1/events"
  }
}
```

Uwaga: powyższe ścieżki są przykładem kontraktu runtime. W kodzie i planie konfiguracji nie wolno hardcodować `/opt/sudoku/...`; wartości pochodzą z `appsettings.{environment}.json`.

### 3.4 ML -> BE
- Sam `POST /api/trainings` nie obsługuje jeszcze eventów końcowych, ale musi utworzyć metadata zgodne z późniejszym `POST /internal/ml/trainings/{runName}/events`.
- Eventy `ML -> BE` będą idempotentnie aktualizować ten sam rekord `trainings/metadata/{runName}.json`.

## 4) Zachowanie per warstwa

### API (`Sudoku`)
- Cienki kontroler:
  - autoryzuje żądanie,
  - binduje `CreateTrainingRunApiEntry`,
  - wywołuje `CreateTrainingRunCommand`,
  - mapuje DTO aplikacyjne na `TrainingRunApiResponse`,
  - mapuje wyjątki domenowe/aplikacyjne na `ErrorApiResponse`.
- Brak skanowania katalogów, brak generowania `runName`, brak wywołań `HttpClient` do `ML` w kontrolerze.
- Logi w API tylko na granicy żądania: start obsługi, konflikt aktywnego runu, sukces `202`, błąd mapowany na status HTTP.

### Application (`Application`)
- Use-case komendowy `CreateTrainingRunCommand`.
- Odpowiedzialność:
  - walidacja wejścia przez `FluentValidation`,
  - odczyt aktywnych runów przez `ITrainingRunsGateway`,
  - sprawdzenie invariantu pojedynczego aktywnego runu,
  - pobranie modelu bazowego przez `IModelsRegistryGateway.GetByNameAsync`,
  - pobranie datasetu przez `IProcessedDatasetsGateway.GetByNameAsync` albo listę z filtrowaniem, jeśli port nie zostanie jeszcze rozszerzony,
  - walidacja `canStartTraining`, kompletności metadanych i zgodności profili,
  - wygenerowanie `runName` i `producedModelName`,
  - zbudowanie rekordu metadanych runu,
  - zapis/rezerwacja metadanych przez port `ITrainingRunsGateway`,
  - zbudowanie requestu do `ML` z resolved ścieżkami przekazanymi przez porty/DTO,
  - wywołanie `IMlTrainingsGateway.StartTrainingAsync`,
  - finalne ustawienie statusu publicznego na `queued` i zwrot DTO.
- `Application` decyduje, co znaczy poprawny start treningu. `Infrastructure` tylko realizuje odczyt/zapis plików i HTTP.

### Domain / Models (`Models`)
- W MVP można utrzymać statusy i metadane jako DTO w `Application/Trainings`, ale lepszy kierunek dla workflow treningów to neutralne modele:
  - `TrainingRunStatus` - kanoniczne statusy (`starting`, `queued`, `running`, `cancelling`, `succeeded`, `failed`, `cancelled`),
  - `TrainingRunName` albo helper walidacji nazwy, jeśli nazwa zacznie być współdzielona przez start, cancel, eventy i szczegóły.
- Modele domenowe nie znają HTTP, `MediatR`, filesystem, `HttpClient`, `appsettings` ani kontraktów `ML`.

### Infrastructure (`Infrastructure`)
- Implementuje porty:
  - storage metadanych treningu,
  - odczyt rejestru modeli,
  - odczyt metadanych datasetów,
  - klient `ML` do startu treningu.
- Reuse istniejących adapterów:
  - `IFileStorageGateway` / `LocalFileStorageGateway` do operacji plikowych,
  - `ModelsRegistryGateway` do manifestów modeli,
  - `ProcessedDatasetsGateway` do metadanych `.npz`,
  - `TrainingRunsGateway` do metadanych runów.
- Jeśli brakuje operacji `Save`, `Update`, `Delete` albo `GetByName`, rozszerzyć istniejące porty generycznie i reużywalnie, zamiast tworzyć osobne klasy specyficzne tylko dla startu.
- Klient `ML` mapuje błędy transportowe i kontraktowe na wyjątki aplikacyjne/infrastrukturalne, ale nie decyduje o biznesowej walidacji runu.

## 5) Pliki per warstwa i odpowiedzialności

### API (`src/Backend/Sudoku/Sudoku`)
- `[MODYFIKACJA]` `Controllers/TrainingsController.cs`
  - dodać `POST /api/trainings`,
  - przyjąć `CreateTrainingRunApiEntry`,
  - wywołać `CreateTrainingRunCommand`,
  - zwrócić `202 Accepted` + `TrainingRunApiResponse`,
  - mapować błędy na `ErrorApiResponse`.
- `[NOWY]` `Contracts/CreateTrainingRunApiEntry.cs`
  - publiczny request FE: `BaseModelName`, `ProcessedDatasetName`.
- `[REUSE]` `Contracts/TrainingRunApiResponse.cs`
  - publiczna odpowiedź zgodna z `GET /api/trainings/active`.
- `[REUSE]` `Contracts/ErrorApiResponse.cs`
  - publiczny model błędu `errorType`, `message`.
- `[MODYFIKACJA]` `Program.cs`
  - bind i walidacja nowych options: `TrainingDefaultsOptions`,
  - walidacja nowych pól `MlServiceOptions` dla startu treningu,
  - walidacja absolutnych ścieżek pozostaje w typed options.
- `[MODYFIKACJA]` `appsettings.local.json`
  - lokalne, twarde wartości dla `TrainingDefaults`,
  - lokalne `MlService.StartTrainingPath`,
  - ewentualnie `MlService.TrainingEventsPathTemplate`, jeśli callback path ma być konfigurowalny.
- `[MODYFIKACJA]` `appsettings.production.json`
  - placeholdery nadpisywane w workflow dla `TrainingDefaults` i `MlService.StartTrainingPath`.

### Application (`src/Backend/Sudoku/Application`)
- `[NOWY]` `Trainings/CreateTrainingRunCommand.cs`
  - komenda MediatR z `BaseModelName`, `ProcessedDatasetName`.
- `[NOWY]` `Trainings/CreateTrainingRunCommandValidator.cs`
  - walidacja body: wymagane pola, dozwolone znaki, długości nazw.
- `[NOWY]` `Trainings/CreateTrainingRunCommandHandler.cs`
  - główna orkiestracja startu runu.
- `[NOWY]` `Trainings/CreateTrainingRunCommandResultDto.cs`
  - DTO odpowiedzi aplikacyjnej mapowane do `TrainingRunApiResponse`.
- `[NOWY]` `Trainings/CreateTrainingRunErrorTypes.cs`
  - stałe: `training_run_already_active`, `base_model_not_found`, `processed_dataset_not_found`, `base_model_cannot_start_training`, `training_profile_mismatch`, `ml_training_start_unavailable`, `ml_training_start_timeout`, `training_run_start_failed`.
- `[NOWY]` `Trainings/TrainingDefaultsOptions.cs`
  - typed options: `TrainingMode`, `TrainingProfileName`, `AugmentationProfileName`, `BenchmarkName`, `Seed`, `RunNamePrefix`.
- `[NOWY]` `Trainings/TrainingRunNameGenerator.cs` albo `ITrainingRunNameGenerator`
  - deterministyczny, testowalny generator nazw z datą UTC i sanitizowanymi segmentami.
- `[MODYFIKACJA]` `Trainings/TrainingRunMetadataDto.cs`
  - rozszerzyć o pola potrzebne do źródła prawdy: `UpdatedAtUtc`, `SourceRevision`, `ReportStatus`, `Warnings`, referencje do artefaktów raportu/modelu, opcjonalnie `MlJobId` jeśli `ML` go zwraca.
- `[MODYFIKACJA]` `Abstractions/ITrainingRunsGateway.cs`
  - dodać `TryCreateAsync(metadata)`, `UpdateAsync(metadata)`, `DeleteAsync(runName)` albo `MarkFailedAsync`, `GetByRunNameAsync(runName)`.
- `[MODYFIKACJA]` `Abstractions/IProcessedDatasetsGateway.cs`
  - dodać `GetByNameAsync(name)`, żeby start treningu nie listował i nie filtrował ręcznie w kilku use-case'ach.
- `[NOWY]` `Abstractions/IMlTrainingsGateway.cs`
  - port aplikacyjny do startu treningu w `ML`.
- `[NOWY]` `Trainings/StartMlTrainingRequestDto.cs`
  - DTO wewnętrzne dla portu `IMlTrainingsGateway`.
- `[NOWY]` `Trainings/StartMlTrainingResultDto.cs`
  - wynik przyjęcia startu przez `ML`, np. `AcceptedAtUtc`, opcjonalnie `MlJobId`.
- `[NOWY]` wyjątki aplikacyjne:
  - `ActiveTrainingRunAlreadyExistsException`,
  - `BaseModelNotFoundException`,
  - `ProcessedDatasetNotFoundException`,
  - `BaseModelCannotStartTrainingException`,
  - `TrainingProfileMismatchException`,
  - `TrainingRunReservationException`,
  - `MlTrainingStartRejectedException`.

### Domain / Models (`src/Backend/Sudoku/Models`)
- `[OPCJONALNIE NOWY]` `Trainings/TrainingRunStatus.cs`
  - kanoniczne statusy jako enum albo stałe, bez zależności od HTTP.
- `[OPCJONALNIE NOWY]` `Trainings/TrainingRunStatusExtensions.cs`
  - `IsActive()`, `IsTerminal()` jeśli ta logika będzie współdzielona przez start, active, cancel i events.
- `[OPCJONALNIE NOWY]` `Trainings/TrainingRunIdentity.cs`
  - tylko jeśli walidacja/generowanie nazw zacznie być używane w wielu miejscach.
- Guardrail: nie przenosić `CreateTrainingRunApiEntry`, `TrainingRunApiResponse` ani requestów `ML` do `Models`.

### Infrastructure (`src/Backend/Sudoku/Infrastructure`)
- `[NOWY]` `Ml/MlTrainingsHttpClient.cs`
  - implementacja `IMlTrainingsGateway`,
  - `POST` do `MlService.StartTrainingPath`,
  - serializacja `StartMlTrainingRequestDto` w `camelCase`,
  - obsługa `202 Accepted` / `200 OK` jako potwierdzenia przyjęcia,
  - mapowanie `4xx`, `5xx`, timeoutów i błędów kontraktu.
- `[MODYFIKACJA]` `Configuration/MlServiceOptions.cs`
  - dodać `StartTrainingPath` z domyślnym `/ml/trainings`,
  - opcjonalnie `TrainingEventsPathTemplate`,
  - ewentualnie osobny `TrainingStartTimeoutSeconds`, jeśli start ma inny timeout niż przygotowanie datasetu.
- `[MODYFIKACJA]` `Storage/TrainingRunsGateway.cs`
  - dodać zapis atomowy metadanych `trainings/metadata/{runName}.json`,
  - dodać aktualizację statusu i rollback/usunięcie rekordu startowego,
  - dodać `GetByRunNameAsync`,
  - zachować listowanie dla `GET /api/trainings/active`.
- `[MODYFIKACJA]` `Storage/ProcessedDatasetsGateway.cs`
  - dodać `GetByNameAsync` z odczytem `{name}.metadata.json` i potwierdzeniem istnienia `{name}.npz`.
- `[REUSE]` `Storage/ModelsRegistryGateway.cs`
  - użyć istniejącego `GetByNameAsync`,
  - w razie potrzeby rozszerzyć DTO o resolved path przez osobny DTO techniczny, ale nie zwracać tych ścieżek do `FE`.
- `[MODYFIKACJA]` `Storage/LocalFileStorageGateway.cs`
  - tylko jeśli potrzebne będą generyczne operacje `DeleteAsync`, `ReplaceAsync` albo `ExistsAsync`.
  - Operacje mają pozostać ogólne, nie treningowe.
- `[MODYFIKACJA]` `DependencyInjection.cs`
  - rejestracja `IMlTrainingsGateway -> MlTrainingsHttpClient`.

### Workflow (`.github/workflows`)
- `[MODYFIKACJA]` `.github/workflows/backend-cd.yml`
  - dodać zmienne dla `MlService.StartTrainingPath`,
  - dodać zmienne dla `TrainingDefaults`,
  - walidować je razem z pozostałymi zmiennymi środowiska `main`,
  - generator `appsettings.production.json` ma nadpisywać wartości produkcyjne.
- `[BEZ ZMIAN LUB OPCJONALNIE]` `.github/workflows/ml-cd.yml`
  - jeśli kontrakt `ML` wymaga nowych zmiennych po swojej stronie, opisać analogiczne wartości w planie `ML`; endpoint `BE` nie powinien jednak zależeć od zmian workflow `ML` poza spójnym adresem/path.

## 6) Weryfikacja usług Infrastructure i antyduplikacja
- Istnieje `IFileStorageGateway` / `LocalFileStorageGateway` z `SaveAsync`, `OpenReadAsync`, `ListFilesAsync`, `ListDirectoriesAsync`.
- Istnieje `ITrainingRunsGateway` i `TrainingRunsGateway` do listowania metadanych runów; należy je rozszerzyć, nie tworzyć `CreateTrainingRunFileWriter`.
- Istnieje `IModelsRegistryGateway.GetByNameAsync`; użyć go do walidacji `baseModelName`.
- Istnieje `IProcessedDatasetsGateway.ListAsync`; rozszerzyć port o `GetByNameAsync`, żeby start treningu i przyszłe szczegóły runu korzystały z jednej implementacji.
- Istnieje `MlServiceOptions` i wzorzec klientów HTTP `Infrastructure/Ml/*`; nowy klient `MlTrainingsHttpClient` powinien trzymać się tego samego stylu.
- Jeśli potrzebne są operacje delete/replace/exists w plikach, dodać je do `IFileStorageGateway` jako generyczne metody, bo będą potrzebne też dla cancel/events/finalizacji modelu.

## 7) Przepływ w obrębie BE
1. `FE` wysyła `POST /api/trainings` z tokenem admin i body `baseModelName`, `processedDatasetName`.
2. `TrainingsController` binduje `CreateTrainingRunApiEntry` i wysyła `CreateTrainingRunCommand`.
3. Pipeline `FluentValidation` odrzuca puste albo niepoprawne nazwy.
4. Handler pobiera metadane runów przez `ITrainingRunsGateway.ListAsync`.
5. Handler sprawdza, czy istnieje aktywny run (`starting`, `queued`, `running`, `cancelling`).
6. Jeśli aktywny run istnieje, handler rzuca `ActiveTrainingRunAlreadyExistsException`; API zwraca `409`.
7. Handler pobiera model przez `IModelsRegistryGateway.GetByNameAsync(baseModelName)`.
8. Handler pobiera dataset przez `IProcessedDatasetsGateway.GetByNameAsync(processedDatasetName)`.
9. Handler waliduje `canStartTraining`, brak ostrzeżeń blokujących, istnienie datasetu `.npz`, zgodność profili.
10. Handler rozwiązuje domyślne profile z `TrainingDefaultsOptions`.
11. Handler generuje `runName` i `producedModelName`, retry-ując kolizje nazw plikowych wewnętrznie.
12. Handler buduje rekord `TrainingRunMetadataDto` ze statusem technicznym `starting`.
13. Handler zapisuje rekord przez `ITrainingRunsGateway.TryCreateAsync`.
14. Handler buduje request do `ML`, używając wyłącznie ścieżek z typed options i danych portów.
15. `IMlTrainingsGateway.StartTrainingAsync` wysyła `POST /ml/trainings`.
16. Jeśli `ML` potwierdzi start, handler aktualizuje metadata do `queued` i zwraca `CreateTrainingRunCommandResultDto`.
17. Kontroler mapuje wynik na `TrainingRunApiResponse` i zwraca `202 Accepted`.
18. `FE` przechodzi do `/ws/trainings/{runName}` albo odpyta `GET /api/trainings/active`.

## 8) Główne funkcje
- `TrainingsController.CreateAsync(...)`
- `CreateTrainingRunCommandValidator.Validate(...)`
- `CreateTrainingRunCommandHandler.Handle(...)`
- `CreateTrainingRunCommandHandler.EnsureNoActiveRun(...)`
- `CreateTrainingRunCommandHandler.ResolveBaseModelAsync(...)`
- `CreateTrainingRunCommandHandler.ResolveProcessedDatasetAsync(...)`
- `CreateTrainingRunCommandHandler.ValidateProfileCompatibility(...)`
- `TrainingRunNameGenerator.Generate(...)`
- `ITrainingRunsGateway.TryCreateAsync(...)`
- `ITrainingRunsGateway.UpdateAsync(...)`
- `ITrainingRunsGateway.DeleteAsync(...)`
- `IModelsRegistryGateway.GetByNameAsync(...)`
- `IProcessedDatasetsGateway.GetByNameAsync(...)`
- `IMlTrainingsGateway.StartTrainingAsync(...)`
- `MlTrainingsHttpClient.StartTrainingAsync(...)`

## 9) Wyjątki, fallbacki i zachowanie błędowe

### 9.1 Publiczne statusy
- `202 Accepted`:
  - run został zarezerwowany w `BE`, a `ML` potwierdził przyjęcie zlecenia.
- `400 Bad Request`:
  - puste lub niepoprawne `baseModelName` / `processedDatasetName`,
  - profil modelu i datasetu nie pasują.
- `404 Not Found`:
  - brak modelu bazowego w `models/registry`,
  - brak metadanych albo artefaktu `.npz` datasetu.
- `409 Conflict`:
  - istnieje aktywny run; odpowiedź powinna mieć `errorType = training_run_already_active`.
- `422 Unprocessable Entity`:
  - model ma `canStartTraining = false`,
  - dataset ma niespójne metadane lub zerowe próbki treningowe.
- `502 Bad Gateway`:
  - `ML` odpowiedział niepoprawnym JSON albo statusem/kontraktem spoza uzgodnionych przypadków.
- `503 Service Unavailable`:
  - brak połączenia z `ML`, DNS/socket/refused connection.
- `504 Gateway Timeout`:
  - `ML` nie potwierdził startu w czasie skonfigurowanego timeoutu.
- `500 Internal Server Error`:
  - błąd I/O podczas zapisu metadata,
  - nieudany rollback,
  - wykryto wiele aktywnych runów,
  - nie da się wygenerować unikalnego `runName` po kilku próbach.

### 9.2 Fallbacki
- Brak fallbacku do `FE` cache.
- Brak fallbacku do `ML` jako źródła aktywnego runu; aktywność runu jest ustalana z backendowych metadanych.
- Brak automatycznej kolejki. Drugi start kończy się `409`.
- Brak automatycznego wyboru innego modelu/datasetu. Jeśli wskazany zasób nie istnieje albo nie pasuje profilowo, żądanie kończy się błędem.
- Jeśli `ML` nie potwierdzi startu:
  - preferowany fallback: usunąć prowizoryczny rekord `starting` i zwrócić `503`/`504`/`502`,
  - jeśli usunięcie rekordu nie powiedzie się, oznaczyć go jako `failed` z ostrzeżeniem operacyjnym i zwrócić `500`.

### 9.3 Scenariusze graniczne
- Pusty katalog metadata -> można startować.
- Istnieją wyłącznie runy terminalne -> można startować.
- Więcej niż jeden aktywny run -> `500`, bo naruszony jest invariant systemu.
- Model bootstrap bez `sourceRunName` -> legalny, jeśli `canStartTraining = true`.
- Model z brakującymi artefaktami i `canStartTraining = true` -> błąd walidacji rejestru lub `422`.
- Dataset bez `.metadata.json` albo bez `.npz` -> `404` albo `422`, zależnie od tego, który element istnieje.
- Kolizja `runName` / `producedModelName` -> wewnętrzny retry z nowym suffixem; nie zwracać normalnego `409`.
- Timeout `ML` po faktycznym przyjęciu zlecenia jest najtrudniejszy: ponieważ `BE` nie ma potwierdzenia, powinien usunąć rekord `starting` i logować ostrzeżenie z `runName`; późniejsze eventy z nieznanego runu muszą być odrzucone albo obsłużone przez endpoint eventów jako `404`.

## 10) Pseudokod specyficznej logiki

```text
handleCreateTrainingRun(command):
  activeRuns = trainingRunsGateway.list()
    .where(status in ["starting", "queued", "running", "cancelling"])

  if activeRuns.count > 1:
    logError("Multiple active training runs detected", activeRuns.runNames)
    throw InvariantViolationException

  if activeRuns.count == 1:
    throw ActiveTrainingRunAlreadyExistsException(activeRuns.single.runName)

  baseModel = modelsRegistryGateway.getByName(command.baseModelName)
  if baseModel is null:
    throw BaseModelNotFoundException

  if not baseModel.canStartTraining:
    throw BaseModelCannotStartTrainingException

  dataset = processedDatasetsGateway.getByName(command.processedDatasetName)
  if dataset is null:
    throw ProcessedDatasetNotFoundException

  if baseModel.inputProfile != dataset.preprocessingProfile:
    throw TrainingProfileMismatchException

  defaults = trainingDefaultsOptions.value
  runIdentity = runNameGenerator.generate(
    utcNow,
    baseModel.name,
    dataset.name,
    prefix = defaults.runNamePrefix)

  metadata = TrainingRunMetadata(
    runName = runIdentity.runName,
    status = "starting",
    createdAtUtc = utcNow,
    updatedAtUtc = utcNow,
    baseModelName = baseModel.name,
    producedModelName = runIdentity.producedModelName,
    processedDatasetName = dataset.name,
    trainingMode = "fineTuning",
    trainingProfileName = defaults.trainingProfileName,
    augmentationProfileName = defaults.augmentationProfileName,
    benchmarkName = defaults.benchmarkName,
    seed = defaults.seed,
    sourceRevision = null,
    progressChannelUrl = "/ws/trainings/{runName}"
  )

  trainingRunsGateway.tryCreate(metadata)

  try:
    mlRequest = buildMlStartRequest(metadata, baseModel, dataset, options)
    mlResult = mlTrainingsGateway.startTraining(mlRequest)

    metadata.status = "queued"
    metadata.updatedAtUtc = utcNow
    metadata.mlJobId = mlResult.mlJobId
    trainingRunsGateway.update(metadata)

    return metadata
  catch MlStartValidationException ex:
    trainingRunsGateway.delete(metadata.runName)
    throw mapToPublic4xx(ex)
  catch MlUnavailableException:
    trainingRunsGateway.delete(metadata.runName)
    throw
  catch MlTimeoutException:
    trainingRunsGateway.delete(metadata.runName)
    throw
  catch Exception:
    markFailedOrDeleteBestEffort(metadata.runName)
    throw
```

```text
generateRunName(utcNow, baseModelName, datasetName):
  timestamp = utcNow.format("yyyyMMdd-HHmmss")
  baseSegment = slug(baseModelName, max = 32)
  datasetSegment = slug(datasetName, max = 32)
  candidate = "train-" + timestamp + "-" + baseSegment + "-" + datasetSegment

  for attempt in 0..9:
    name = candidate if attempt == 0 else candidate + "-" + attempt
    if metadata file does not exist and registry directory does not exist:
      return name

  throw TrainingRunReservationException
```

## 11) Workflow GitHub i konfiguracja runtime
- Lokalnie:
  - wartości w `appsettings.local.json` są wpisane na sztywno i wskazują lokalne katalogi projektu,
  - `MlService.StartTrainingPath` może mieć `/ml/trainings`,
  - `TrainingDefaults` powinno mieć jeden preset MVP.
- Produkcyjnie:
  - workflow `backend-cd.yml` generuje `appsettings.production.json` w publish output,
  - workflow nadpisuje ścieżki i ustawienia produkcyjne zmiennymi GitHub Environment,
  - trwałe katalogi `data`, `models`, `trainings`, `tmp` nie są czyszczone przez deploy.

### 11.1 Nowa sekcja `TrainingDefaults`

```json
{
  "TrainingDefaults": {
    "RunNamePrefix": "train",
    "TrainingMode": "fineTuning",
    "TrainingProfileName": "cnn-default-v1",
    "AugmentationProfileName": "digits-light-v1",
    "BenchmarkName": "sudoku-benchmark-v1",
    "Seed": 1234
  }
}
```

### 11.2 Rozszerzenie `MlService`

```json
{
  "MlService": {
    "StartTrainingPath": "/ml/trainings",
    "TrainingEventsPathTemplate": "/internal/ml/trainings/{runName}/events",
    "TimeoutSeconds": 60
  }
}
```

### 11.3 Zmiany w `backend-cd.yml`
- Dodać env:
  - `BE_ML_START_TRAINING_PATH`,
  - `BE_TRAINING_DEFAULT_RUN_NAME_PREFIX`,
  - `BE_TRAINING_DEFAULT_MODE`,
  - `BE_TRAINING_DEFAULT_PROFILE_NAME`,
  - `BE_TRAINING_DEFAULT_AUGMENTATION_PROFILE_NAME`,
  - `BE_TRAINING_DEFAULT_BENCHMARK_NAME`,
  - `BE_TRAINING_DEFAULT_SEED`.
- Dodać walidację obecności wartości.
- Sparsować `BE_TRAINING_DEFAULT_SEED` jako integer.
- W generatorze konfiguracji ustawić:
  - `config["MlService"]["StartTrainingPath"]`,
  - `config["TrainingDefaults"]["RunNamePrefix"]`,
  - `config["TrainingDefaults"]["TrainingMode"]`,
  - `config["TrainingDefaults"]["TrainingProfileName"]`,
  - `config["TrainingDefaults"]["AugmentationProfileName"]`,
  - `config["TrainingDefaults"]["BenchmarkName"]`,
  - `config["TrainingDefaults"]["Seed"]`.

## 12) Logging
- Cel: umożliwić odtworzenie błędów startu bez spamowania logów i bez zapisywania dużych payloadów.
- `Information`:
  - przyjęto żądanie startu z `baseModelName`, `processedDatasetName`,
  - zarezerwowano `runName`,
  - `ML` potwierdził przyjęcie runu,
  - zwrócono `202 Accepted`.
- `Warning`:
  - odrzucono start przez istniejący aktywny run (`activeRunName`, `requestedBaseModelName`, `requestedDatasetName`),
  - mismatch profili model/dataset,
  - rollback rekordu po błędzie `ML`,
  - timeout startu `ML` dla konkretnego `runName`.
- `Error`:
  - wiele aktywnych runów,
  - błąd zapisu/aktualizacji/usunięcia metadata,
  - niepoprawny kontrakt odpowiedzi `ML`,
  - nieudany rollback po niepotwierdzonym starcie.
- Guardrail logowania:
  - nie logować tokenów admina,
  - nie logować pełnych manifestów `model.json`,
  - nie logować pełnych payloadów request/response `ML`,
  - w odpowiedzi API nie zwracać absolutnych ścieżek,
  - w logach technicznych wystarczą `runName`, `baseModelName`, `processedDatasetName`, `errorType`, status HTTP `ML` i krótki powód.

## 13) Inne istotne reguły
- `POST /api/trainings` nie przygotowuje datasetu i nie uruchamia preprocessingu; używa gotowego `.npz` z `UC-12`.
- `POST /api/trainings` nie finalizuje modelu; finalizacja następuje po eventach końcowych `ML -> BE`.
- `producedModelName` w MVP może być równe `runName`, ale semantycznie pozostaje osobnym polem.
- `sourceRevision` w MVP istnieje w metadata, ale ma wartość `null`.
- `trainingProfileName` i `augmentationProfileName` nie są dziedziczone z modelu bazowego w MVP.
- `trainingMode` wysyłane przez `FE` nie istnieje w request body; `BE` ustawia `fineTuning`.
- Nie eksponować do `FE`: `manifestPath`, `artifactPath`, katalogów `trainings/*`, `tmp/*`, `models/registry/*`.
- `409` rezerwować wyłącznie dla aktywnego runu; kolizje nazw obsługiwać retry albo jako `500`.

## 14) Kolejność implementacji kodu dla historyjki
1. Dodać `CreateTrainingRunApiEntry` w `Sudoku/Contracts`.
2. Dodać `TrainingDefaultsOptions` i konfigurację `TrainingDefaults` w `appsettings.local.json` oraz `appsettings.production.json`.
3. Rozszerzyć `MlServiceOptions` o `StartTrainingPath` i ewentualny template callbacku.
4. Zaktualizować `Program.cs` o bind/walidację nowych options.
5. Rozszerzyć `IProcessedDatasetsGateway` i `ProcessedDatasetsGateway` o `GetByNameAsync`.
6. Rozszerzyć `ITrainingRunsGateway` i `TrainingRunsGateway` o atomowe `TryCreateAsync`, `UpdateAsync`, `DeleteAsync`, `GetByRunNameAsync`.
7. Jeśli potrzebne, rozszerzyć `IFileStorageGateway` o generyczne `DeleteAsync`, `ReplaceAsync`, `ExistsAsync`.
8. Dodać `IMlTrainingsGateway` oraz DTO request/result dla startu `ML`.
9. Dodać `MlTrainingsHttpClient` i rejestrację w `Infrastructure/DependencyInjection.cs`.
10. Dodać `CreateTrainingRunCommand`, validator, result DTO, error types i wyjątki aplikacyjne.
11. Zaimplementować `TrainingRunNameGenerator`.
12. Zaimplementować `CreateTrainingRunCommandHandler`.
13. Dodać `POST /api/trainings` do `TrainingsController`.
14. Zaktualizować `.github/workflows/backend-cd.yml` o nowe zmienne i generator `appsettings.production.json`.
15. Dodać testy Application: sukces, aktywny run, brak modelu, `canStartTraining=false`, brak datasetu, mismatch profili, rollback po błędzie `ML`.
16. Dodać testy Infrastructure: zapis metadata, kolizja pliku, update, delete, `GetByNameAsync` datasetu, mapowanie odpowiedzi `ML`.
17. Dodać testy API/integracyjne: `202`, `400`, `401`, `404`, `409`, `422`, `503`, `504`.

## 15) Guardraile implementacyjne
- Kontroler bez logiki workflow, bez `File.*`, `Directory.*`, `JsonSerializer` i bez bezpośredniego `HttpClient`.
- `Application` orkiestruje i podejmuje decyzje biznesowe; `Infrastructure` wykonuje I/O i HTTP.
- Nie dodawać minimal API `MapPost`; użyć ASP.NET Controller.
- Nie hardcodować ścieżek serwerowych w kodzie.
- Nie tworzyć bazy danych ani drugiego rejestru runów.
- Nie robić fallbacku do `ML` jako źródła prawdy dla aktywnego runu.
- Nie przekazywać do `FE` ścieżek systemowych ani technicznych nazw artefaktów.
- Nie przyjmować z `FE` profili treningu w MVP.
- Nie tworzyć kolejki treningów.
- Operacje zapisu metadanych powinny być odporne na kolizje i możliwie atomowe.
- Rollback po błędzie startu `ML` musi być best-effort i logowany.
- DTO `ML` i API publiczne trzymać rozdzielone.
- Publiczne błędy zawsze przez `ErrorApiResponse`.

## 16) Zależności pomiędzy historyjkami
- Wejściowe:
  - `UC-13` - autoryzacja admin token dla startu treningu.
  - `UC-12` - przygotowany dataset `.npz` i metadane `preprocessingProfile`.
  - `INF-08` - standard manifestu modelu i bootstrap rejestru.
  - `GET /api/models/registry` - wspólny port rejestru modeli i capability.
  - `GET /api/trainings/active` - wspólny port metadanych i reguła aktywnego runu.
- Równoległe:
  - `ML UC-06` - implementacja `POST /ml/trainings` i wykonywanie joba w tle.
  - `UC-07` - SignalR i eventy postępu korzystają z tego samego `runName`.
  - `POST /api/trainings/{runName}/cancel` - wymaga statusów `queued/running/cancelling`.
- Wyjściowe:
  - `UC-08` - lista treningów i modeli odczytuje metadata utworzone tutaj.
  - `UC-09` - szczegóły runu i metryki opierają się o pełną konfigurację zapisaną przy starcie.
  - `UC-10` - wybór aktywnego modelu będzie używał `producedModelName` po sukcesie runu.

## 17) Model API wejściowy i wyjściowy w komunikacji z FE i ML
- FE -> BE:
  - `CreateTrainingRunApiEntry`
  - `baseModelName: string`
  - `processedDatasetName: string`
- BE -> FE:
  - `TrainingRunApiResponse`
  - `ErrorApiResponse`
- BE -> ML:
  - `StartMlTrainingRequestDto`
  - dane modelu bazowego: nazwa, manifest, główny artefakt, input profile,
  - dane datasetu: nazwa, ścieżka `.npz`, preprocessing profile,
  - konfiguracja treningu: mode, profile, augmentacja, benchmark, seed,
  - output paths: run, reports, working, model artifacts,
  - callback path dla eventów.
- ML -> BE jako odpowiedź synchroniczna na start:
  - `StartMlTrainingResultDto`
  - minimalnie `accepted: true`, opcjonalnie `acceptedAtUtc`, `mlJobId`.
- ML -> BE później:
  - eventy statusu/progressu do `POST /internal/ml/trainings/{runName}/events`, poza zakresem samego startu, ale metadata musi być z nimi zgodne.
