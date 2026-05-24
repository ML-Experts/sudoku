# UC-06-BE - Plan implementacyjny dla `GET /api/trainings/active`

## 1) Przeznaczenie endpointa
- Endpoint `GET /api/trainings/active` zwraca aktualnie aktywny run treningowy (`queued`, `running`, `cancelling`; wyjątkowo przejściowo `starting`) albo `204 No Content`, gdy aktywnego runu nie ma.
- Endpoint służy do odzyskania stanu po odświeżeniu strony, reconnect i scenariuszu konfliktu przy starcie (`409 training_run_already_active` z `POST /api/trainings`).
- To lekki odczyt stanu systemowego utrzymywanego przez backend; endpoint nie uruchamia treningu i nie komunikuje się bezpośrednio z ML.

## 2) Zakres i założenia
- Plan opiera się na `PRD` i specyfikacji `UC-06`, bez sugerowania się bieżącym stanem FE/ML.
- `Backend` pozostaje `source of truth` dla statusu runu.
- Endpoint jest chroniony (`UC-13`) i dostępny tylko dla tokenu administracyjnego.
- Kontrakt HTTP pozostaje stabilny i w `camelCase`.
- W MVP system utrzymuje dokładnie jeden aktywny run naraz.

## 3) Kontrakty API (FE i ML)

### 3.1 FE -> BE (`GET /api/trainings/active`)
- Request body: brak.
- Query params: brak (MVP).
- Autoryzacja: token administracyjny (`Bearer`).

### 3.2 Odpowiedzi publiczne
- `200 OK` -> `TrainingRunApiResponse` (aktywny run znaleziony).
- `204 No Content` -> brak aktywnego runu.
- `401 Unauthorized` -> brak/niepoprawny token.
- `500 Internal Server Error` -> błąd odczytu/parsowania metadanych.

### 3.3 Model wejściowy/wyjściowy FE
- Wejście FE -> BE:
  - brak modelu body (HTTP GET).
- Wyjście BE -> FE (`TrainingRunApiResponse`):
  - `runName: string`
  - `status: string`
  - `createdAtUtc: string` (ISO-8601 UTC)
  - `baseModelName: string`
  - `producedModelName: string`
  - `processedDatasetName: string`
  - `trainingMode: string`
  - `trainingProfileName: string`
  - `augmentationProfileName: string`
  - `benchmarkName: string`
  - `seed: number`
  - `progressChannelUrl: string`

### 3.4 BE <-> ML dla tego endpointa
- Dla `GET /api/trainings/active` brak ruchu `BE -> ML`.
- Dla `GET /api/trainings/active` brak ruchu `ML -> BE`.
- Źródłem odpowiedzi jest wyłącznie rekord runu backendu (`trainings/metadata`).

## 4) Zachowanie per warstwa

### API (`Sudoku`)
- Cienki kontroler:
  - autoryzacja,
  - wywołanie query MediatR,
  - mapowanie DTO na `TrainingRunApiResponse`,
  - mapowanie błędów na `ErrorApiResponse`.
- Brak logiki wyboru aktywnego runu i brak I/O plikowego.

### Application (`Application`)
- Use-case odczytowy `GetActiveTrainingRunQuery`.
- Logika biznesowa:
  - pobranie kandydatów runów z portu,
  - identyfikacja aktywnego runu,
  - reguła pojedynczego aktywnego runu,
  - normalizacja stanu odpowiedzi do kontraktu FE.
- Brak szczegółów technicznych filesystem i JSON parsera.

### Domain (`Models`)
- Definicje neutralnych modeli stanu treningu (status/stage) i rekordu runu jako modele domenowe/DTO.
- Brak typów HTTP i brak zależności od ASP.NET.

### Infrastructure (`Infrastructure`)
- Implementacja adaptera odczytu metadanych runów.
- Techniczne odpowiedzialności:
  - listowanie plików metadata,
  - odczyt i deserializacja JSON,
  - mapowanie na DTO aplikacyjne,
  - obsługa błędów I/O/parsowania.
- Brak reguł biznesowych "co jest aktywne" poza ewentualną walidacją techniczną rekordu.

## 5) Pliki per warstwa i odpowiedzialności

## API (`src/Backend/Sudoku/Sudoku`)
- `[NOWY]` `Controllers/TrainingsController.cs`
  - `GET /api/trainings/active`,
  - mapowanie `GetActiveTrainingRunQueryResultDto` -> `TrainingRunApiResponse`,
  - mapowanie błędów na `500` z `ErrorApiResponse`.
- `[NOWY]` `Contracts/TrainingRunApiResponse.cs`
  - publiczny model odpowiedzi endpointu.
- `[REUSE]` `Contracts/ErrorApiResponse.cs`
  - wspólny model błędu HTTP.

## Application (`src/Backend/Sudoku/Application`)
- `[NOWY]` `Trainings/GetActiveTrainingRunQuery.cs`
  - query MediatR.
- `[NOWY]` `Trainings/GetActiveTrainingRunQueryHandler.cs`
  - orkiestracja use-case i selekcja aktywnego runu.
- `[NOWY]` `Trainings/GetActiveTrainingRunQueryResultDto.cs`
  - wynik query (`HasActiveRun` + dane runu).
- `[NOWY]` `Trainings/ActiveTrainingRunDto.cs`
  - DTO aktywnego runu mapowane do API.
- `[NOWY]` `Trainings/GetActiveTrainingRunErrorTypes.cs`
  - stałe `errorType`, np. `active_training_run_read_failed`.
- `[NOWY]` `Abstractions/ITrainingRunsGateway.cs`
  - port odczytu metadanych runów (np. `ListAsync()` + opcjonalnie `GetByRunNameAsync()` pod przyszłe UC).

## Domain / Models (`src/Backend/Sudoku/Models`)
- `[NOWY]` `Trainings/TrainingRunStatus.cs`
  - kanoniczne statusy runu.
- `[NOWY]` `Trainings/TrainingRunMetadata.cs` (lub rekord DTO po stronie Application, jeśli zespół utrzymuje prostszy model)
  - reprezentacja rekordu metadanych niezależna od HTTP.
- Uwaga: jeżeli utrzymujemy podejście jak w UC-12 (DTO w Application, bez dedykowanego domain model), to ten punkt może zostać ograniczony do Application DTO. Decyzję należy utrzymać spójnie w całym module `Trainings`.

## Infrastructure (`src/Backend/Sudoku/Infrastructure`)
- `[NOWY]` `Storage/TrainingRunsGateway.cs`
  - implementacja `ITrainingRunsGateway`,
  - odczyt `trainings/metadata/*.json`.
- `[REUSE]` `Storage/LocalFileStorageGateway.cs`
  - generyczne I/O plikowe (`ListFilesAsync`, `OpenReadAsync`).
- `[REUSE]` `DependencyInjection.cs`
  - rejestracja nowego gateway (`ITrainingRunsGateway` -> `TrainingRunsGateway`).

## Configuration / Composition root (`src/Backend/Sudoku/Sudoku`)
- `[NOWY]` `Application/Trainings/TrainingsStorageOptions.cs`
  - typed options dla:
    - `RunsDirectoryPath`,
    - `ReportsDirectoryPath`,
    - `MetadataDirectoryPath`,
    - `WorkingDirectoryPath`.
- `[REUSE + MODYFIKACJA]` `Program.cs`
  - bind + walidacja `TrainingsStorageOptions` (`absolute paths`, `ValidateOnStart`).
- `[REUSE + MODYFIKACJA]` `appsettings.local.json`
  - stałe lokalne ścieżki `TrainingsStorage.*`.
- `[REUSE + MODYFIKACJA]` `appsettings.production.json`
  - placeholdery pod workflow dla `TrainingsStorage.*`.

## Workflow (`.github/workflows`)
- `[REUSE + MODYFIKACJA]` `.github/workflows/backend-cd.yml`
  - walidacja nowych zmiennych środowiskowych,
  - podmiana `TrainingsStorage.*` w `appsettings.production.json`,
  - podmiana nowych ścieżek ML związanych z treningiem (jeżeli dokładane równolegle przez UC-06).

## 6) Weryfikacja usług Infrastructure (antyduplikacja)
- Istnieje generyczny adapter plikowy `IFileStorageGateway` / `LocalFileStorageGateway` i należy go reuse'ować.
- Nie tworzyć nowej klasy typu "TrainingMetadataFileReader" duplikującej listowanie/otwieranie plików.
- `TrainingRunsGateway` ma być generyczny względem odczytu metadanych runów (przydatny także dla `UC-07/08/09`), a nie zaszyty wyłącznie pod jeden endpoint.
- Reguła: Infrastructure implementuje technikalia, Application decyduje co oznacza "aktywny".

## 7) Przepływ w obrębie BE (`GET /api/trainings/active`)
1. FE wysyła żądanie z tokenem admin.
2. `TrainingsController` wywołuje `GetActiveTrainingRunQuery`.
3. Handler pobiera listę metadanych z `ITrainingRunsGateway`.
4. Infrastructure odczytuje i deserializuje rekordy z `TrainingsStorage.MetadataDirectoryPath`.
5. Handler wybiera rekord aktywny wg statusu (`queued`/`starting`/`running`/`cancelling`) i reguł spójności.
6. Jeśli brak aktywnego runu -> wynik typu `NoActiveRun`.
7. Jeśli aktywny run jest znaleziony -> mapowanie do `ActiveTrainingRunDto`.
8. Kontroler:
   - zwraca `204`, gdy brak aktywnego,
   - zwraca `200` + `TrainingRunApiResponse`, gdy aktywny istnieje.

## 8) Główne funkcje
- `TrainingsController.GetActiveAsync(...)`
- `GetActiveTrainingRunQueryHandler.Handle(...)`
- `ITrainingRunsGateway.ListAsync(...)`
- `TrainingRunsGateway.ListAsync(...)`
- `LocalFileStorageGateway.ListFilesAsync(...)`
- `LocalFileStorageGateway.OpenReadAsync(...)`

## 9) Wyjątki, fallbacki i zachowanie błędowe

### 9.1 Publiczne zachowanie błędowe
- `401 Unauthorized`:
  - brak tokenu lub token nieważny.
- `500 Internal Server Error`:
  - brak dostępu do katalogu metadata,
  - uszkodzony JSON,
  - niespójność rekordu uniemożliwiająca mapowanie.

### 9.2 Fallbacki
- Brak fallbacku do ML (to endpoint read-only oparty na backendowym source-of-truth).
- Brak fallbacku do FE cache.
- Jedyny dopuszczalny fallback biznesowy:
  - brak aktywnego runu zwracamy jako `204`, a nie błąd.

### 9.3 Scenariusze graniczne
- Pusty katalog metadata -> `204`.
- Istnieją wyłącznie runy terminalne (`succeeded`, `failed`, `cancelled`) -> `204`.
- Jednocześnie >1 rekord aktywny (niespójność stanu) -> `500` + log ostrzegawczo-błędowy, bo łamie invariant pojedynczego aktywnego runu.
- Rekord statusu `starting`:
  - endpoint może go zwrócić wyłącznie w krótkim oknie przejściowym.

## 10) Specyficzna logika (pseudokod)

```text
handleGetActiveTrainingRun():
  metadataItems = trainingRunsGateway.list()

  activeCandidates = metadataItems
    .where(item.status in ["queued", "starting", "running", "cancelling"])
    .orderByDescending(item.createdAtUtc)

  if activeCandidates.count == 0:
    return NoActiveRun

  if activeCandidates.count > 1:
    logError("Multiple active training runs detected", runNames)
    throw InvariantViolationException

  active = activeCandidates.single

  return ActiveTrainingRunDto(
    runName = active.runName,
    status = active.status,
    createdAtUtc = active.createdAtUtc,
    baseModelName = active.baseModelName,
    producedModelName = active.producedModelName,
    processedDatasetName = active.processedDatasetName,
    trainingMode = active.trainingMode,
    trainingProfileName = active.trainingProfileName,
    augmentationProfileName = active.augmentationProfileName,
    benchmarkName = active.benchmarkName,
    seed = active.seed,
    progressChannelUrl = active.progressChannelUrl
  )
```

## 11) Workflow GitHub i konfiguracja runtime (local vs production)
- `local`:
  - ścieżki `TrainingsStorage.*` wpisane na sztywno w `appsettings.local.json`.
- `production`:
  - workflow `backend-cd.yml` podmienia `appsettings.production.json`.

### 11.1 Zmiany wymagane w `backend-cd.yml`
- Dodać i walidować zmienne:
  - `BE_TRAININGS_RUNS_DIRECTORY_PATH`
  - `BE_TRAININGS_REPORTS_DIRECTORY_PATH`
  - `BE_TRAININGS_METADATA_DIRECTORY_PATH`
  - `BE_TRAININGS_WORKING_DIRECTORY_PATH`
- Podmieniać nimi sekcję `TrainingsStorage` w `appsettings.production.json`.

### 11.2 Uwaga o UC-06 całościowo
- Jeśli równolegle dokładane są endpointy start/cancel/events, workflow powinien także podmieniać:
  - ścieżki i endpointy `MlService.StartTrainingPath`,
  - `MlService.CancelTrainingPath`,
  - sekret techniczny `MlService.TrainingEventsSharedSecret` (lub równoważny).

## 12) Logging (lekki, diagnostyczny)
- Cel: śledzenie błędów i niespójności bez spamu.
- Proponowane logi:
  - `Information`:
    - `GET /api/trainings/active` -> znaleziono aktywny run (`runName`, `status`),
    - `GET /api/trainings/active` -> brak aktywnego runu.
  - `Warning`:
    - podejrzany rekord metadata pominięty przez błąd walidacji technicznej (bez dumpu payloadu).
  - `Error`:
    - błąd I/O/parsowania,
    - wykryto więcej niż jeden aktywny run.
- Guardrail:
  - nie logować pełnych treści plików JSON,
  - nie logować sekretów, tokenów i ścieżek wrażliwych,
  - logi powinny zawierać `runName` i `errorType` jako klucze diagnostyczne.

## 13) Kolejność implementacji dla historyjki
1. Dodać kontrakt API `TrainingRunApiResponse` i nowy `TrainingsController`.
2. Dodać query/handler/DTO w `Application/Trainings`.
3. Dodać port `ITrainingRunsGateway`.
4. Dodać typed options `TrainingsStorageOptions` + walidację w `Program.cs`.
5. Zaimplementować `TrainingRunsGateway` z reuse `IFileStorageGateway`.
6. Podpiąć DI (`Infrastructure/DependencyInjection.cs`).
7. Dodać mapowanie wyjątków -> `ErrorApiResponse` w kontrolerze.
8. Uzupełnić `appsettings.local.json` i `appsettings.production.json` o `TrainingsStorage`.
9. Rozszerzyć `backend-cd.yml` o nowe zmienne i podmianę sekcji.
10. Dodać testy (Application + API integracyjne).

## 14) Guardraile implementacyjne
- Kontroler ma pozostać cienki; zero logiki biznesowej i zero I/O.
- `Application` decyduje o statusach aktywnych; `Infrastructure` nie koduje reguł workflow.
- Nie hardkodować ścieżek (`/opt/sudoku/...`) w kodzie; wszystko przez typed options.
- Kontrakty HTTP (`*ApiResponse`) i DTO aplikacyjne (`*Dto`) muszą być rozdzielone.
- Publiczny JSON ma mieć klucze `camelCase`.
- Infrastructure ma być generyczne i reużywalne dla kolejnych endpointów treningowych.

## 15) Zależności pomiędzy historyjkami
- Wejściowe (musi istnieć wcześniej):
  - `UC-13` (autoryzacja admin token),
  - `UC-12` (lista datasetów i metadane używane przez run),
  - `UC-11` pośrednio (źródła danych do przygotowania datasetów).
- Równoległe / kolejne:
  - `UC-06 POST /api/trainings` (tworzy aktywne runy),
  - `UC-06 POST /api/trainings/{runName}/cancel` (zmienia stan aktywnego runu),
  - `UC-07` (monitoring SignalR),
  - `UC-08/UC-09` (lista/szczegóły runów).

## 16) Inne istotne reguły
- Endpoint jest tylko odczytem i nie modyfikuje stanu.
- `204` jest poprawnym i częstym przypadkiem biznesowym.
- `500` oznacza problem techniczny backendu, nie brak aktywnego runu.
- Wykrycie wielu aktywnych runów to naruszenie invariantu i sygnał do analizy operacyjnej.
- Implementacja ma być gotowa pod rozszerzenie o `GET /api/trainings/{runName}` bez przebudowy warstw.
