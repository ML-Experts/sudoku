# UC-06-BE - Plan implementacyjny dla `POST /internal/ml/trainings/{runName}/events`

## 1) Przeznaczenie endpointa
- Endpoint `POST /internal/ml/trainings/{runName}/events` jest wewnętrznym callbackiem `ML -> BE` używanym do raportowania postępu, zmian statusu, anulowania oraz końcowego wyniku treningu.
- Endpoint nie jest wywoływany przez `FE` i nie należy do publicznego API administracyjnego. `FE` widzi stan runu przez `GET /api/trainings/active`, późniejsze `GET /api/trainings/{runName}` oraz kanał `SignalR /ws/trainings/{runName}`.
- Backend pozostaje `source of truth`: przyjmuje event, waliduje go względem istniejącego rekordu `trainings/metadata/{runName}.json`, aktualizuje własny snapshot runu, finalizuje `model.json` dla modelu wynikowego po `completed` i dopiero potem publikuje stan dalej.
- Endpoint ma potwierdzać idempotentnie duplikaty eventów, bo `ML` powtarza wysyłkę końcowego eventu z tym samym `sequence` aż do otrzymania odpowiedzi `2xx`.
- Publicznym identyfikatorem procesu pozostaje `runName`; nie wprowadzamy osobnego `training_id`.

## 2) Zakres i założenia
- Plan opiera się na `PRD`, `UC-06`, zasadach deployu/runtime oraz obecnych planach dla `POST /api/trainings`, `GET /api/trainings/active` i `GET /api/models/registry`.
- Nie sugerować się aktualnym stanem `FE` i `ML`; kontrakt callbacka wynika z odpowiedzialności Backendu jako właściciela workflow.
- `ML` jest usługą wewnętrzną, niewystawioną do internetu. Endpoint `/internal/...` nie powinien być routowany przez nginx publicznie.
- W MVP ochroną endpointu jest topologia sieciowa: `BE` słucha na `127.0.0.1:5000`, `ML` działa na tym samym hoście i wywołuje `BE` po localhost. Nie używamy tokenu admin z `UC-13`, bo to token dla `FE -> BE`.
- Jeżeli później będzie potrzeba dodatkowego zabezpieczenia callbacków, dodać osobny internal callback secret/header w konfiguracji, a nie reuse tokenu użytkownika administracyjnego.
- Eventy nie muszą mieć ciągłej numeracji. Backend odrzuca regresję stanu po `sequence`, ale nie wymaga kompletności `1..N`.
- Dla eventów terminalnych `completed`, `failed`, `cancelled` najważniejsze jest trwałe zapisanie stanu w `trainings/metadata/{runName}.json`; dopiero po tym endpoint zwraca `2xx`.
- Brakujący albo uszkodzony raport nie unieważnia modelu, jeżeli event `completed` wskazuje kompletne artefakty inferencyjne. Taki przypadek zapisujemy jako sukces z ostrzeżeniem.

## 3) Kontrakty API FE i ML

### 3.1 FE -> BE
- Brak bezpośredniego kontraktu FE dla tego endpointa.
- `FE` pośrednio korzysta z wyniku eventów przez:
  - `GET /api/trainings/active`,
  - `SignalR /ws/trainings/{runName}`,
  - późniejsze `GET /api/trainings/{runName}` z `UC-09`.

### 3.2 ML -> BE (`POST /internal/ml/trainings/{runName}/events`)
- Route param:
  - `runName: string` - nazwa runu utworzona wcześniej przez `POST /api/trainings`.
- Request body: `TrainingRunEventApiEntry`.
- Autoryzacja:
  - brak tokenu admin,
  - endpoint dostępny tylko lokalnie/operacyjnie przez brak publicznego routingu `/internal`.

Przykład eventu postępu:

```json
{
  "sequence": 12,
  "eventType": "progress",
  "status": "running",
  "occurredAtUtc": "2026-04-29T15:04:10Z",
  "message": "Epoch 3/20 finished.",
  "progress": {
    "percent": 15.0,
    "epoch": 3,
    "totalEpochs": 20,
    "trainLoss": 0.42,
    "validationLoss": 0.51,
    "trainAccuracy": 0.88,
    "validationAccuracy": 0.84
  },
  "warnings": []
}
```

Przykład eventu końcowego `completed` z ostrzeżeniem raportu:

```json
{
  "sequence": 98,
  "eventType": "completed",
  "status": "succeeded",
  "occurredAtUtc": "2026-04-29T15:45:00Z",
  "message": "Training completed. Report is missing, model artifacts are complete.",
  "progress": {
    "percent": 100.0,
    "epoch": 20,
    "totalEpochs": 20,
    "trainLoss": 0.08,
    "validationLoss": 0.13,
    "trainAccuracy": 0.98,
    "validationAccuracy": 0.95
  },
  "result": {
    "producedModelName": "train-20260429-143000-cnn-mnist-baseline-sudokuDigitsV1",
    "primaryArtifactRelativePath": "artifacts/model.keras",
    "reportStatus": "missing",
    "reportRelativePath": null,
    "metricsSummary": {
      "accuracy": 0.95,
      "macroF1": 0.94
    }
  },
  "warnings": [
    "training_report_missing"
  ]
}
```

### 3.3 BE -> ML
- `200 OK` -> `TrainingRunEventAckApiResponse` dla eventu przyjętego, duplikatu albo eventu bezpiecznie zignorowanego.
- `400 Bad Request` -> niepoprawny payload, niedozwolony `eventType`, niedozwolony `status`, mismatch `runName` w ścieżce/body jeśli body będzie zawierało `runName`.
- `404 Not Found` -> brak rekordu runu w metadanych BE.
- `409 Conflict` -> event nie może być jeszcze przyjęty, np. `completed` wskazuje artefakt, którego nie da się odczytać. To celowo nie jest `2xx`, żeby `ML` mogło ponowić callback.
- `422 Unprocessable Entity` -> event jest poprawny składniowo, ale łamie kontrakt workflow, np. `completed` bez `result.producedModelName`.
- `500 Internal Server Error` -> błąd zapisu metadanych, parsowania istniejącego rekordu, finalizacji manifestu modelu albo inny błąd techniczny.

Przykład `200 OK`:

```json
{
  "accepted": true,
  "runName": "train-20260429-143000-cnn-mnist-baseline-sudokuDigitsV1",
  "status": "running",
  "lastAcceptedSequence": 12,
  "disposition": "accepted"
}
```

Przykład duplikatu:

```json
{
  "accepted": true,
  "runName": "train-20260429-143000-cnn-mnist-baseline-sudokuDigitsV1",
  "status": "succeeded",
  "lastAcceptedSequence": 98,
  "disposition": "duplicate"
}
```

## 4) Modele wejściowe i wyjściowe

### 4.1 `TrainingRunEventApiEntry`
- `sequence: long` - wymagane, `>= 1`, monotoniczne dla danego runu.
- `eventType: string` - `progress`, `statusChanged`, `completed`, `failed`, `cancelled`.
- `status: string` - aktualny status po stronie ML mapowany do statusu BE:
  - dla `progress`: zwykle `running`,
  - dla `statusChanged`: `queued`, `running`, `cancelling`,
  - dla `completed`: `succeeded`,
  - dla `failed`: `failed`,
  - dla `cancelled`: `cancelled`.
- `occurredAtUtc: DateTimeOffset` - czas zdarzenia po stronie ML.
- `message: string | null` - krótki opis diagnostyczny, bez dużych logów.
- `progress: TrainingRunProgressApiEntry | null` - snapshot postępu.
- `result: TrainingRunEventResultApiEntry | null` - wymagany dla `completed`, opcjonalny dla `failed`.
- `warnings: string[]` - krótkie kody ostrzeżeń.

### 4.2 `TrainingRunProgressApiEntry`
- `percent: decimal | null` - zakres `0..100`.
- `epoch: int | null`.
- `totalEpochs: int | null`.
- `trainLoss: decimal | null`.
- `validationLoss: decimal | null`.
- `trainAccuracy: decimal | null`.
- `validationAccuracy: decimal | null`.

### 4.3 `TrainingRunEventResultApiEntry`
- `producedModelName: string | null` - dla MVP musi odpowiadać `TrainingRunMetadataDto.ProducedModelName`.
- `primaryArtifactRelativePath: string | null` - ścieżka względna w katalogu `models/registry/{producedModelName}`.
- `reportStatus: string | null` - `ok`, `missing`, `corrupted`.
- `reportRelativePath: string | null` - ścieżka względna w `trainings/reports/{runName}` albo `null`.
- `metricsSummary: TrainingMetricsSummaryApiEntry | null`.

### 4.4 `TrainingRunEventAckApiResponse`
- `accepted: bool`.
- `runName: string`.
- `status: string`.
- `lastAcceptedSequence: long`.
- `disposition: string`:
  - `accepted`,
  - `duplicate`,
  - `ignored_terminal_state`.

## 5) Zachowanie per warstwa

### API (`Sudoku`)
- Dodać cienki kontroler wewnętrzny dla `/internal/ml/trainings`.
- Kontroler:
  - binduje `runName` i `TrainingRunEventApiEntry`,
  - wywołuje `RecordTrainingRunEventCommand`,
  - mapuje wynik aplikacyjny na `TrainingRunEventAckApiResponse`,
  - mapuje walidację i wyjątki na `ErrorApiResponse`.
- Kontroler nie finalizuje modelu, nie zapisuje plików, nie czyści katalogów i nie publikuje `SignalR` bezpośrednio.
- Logi w API są lekkie: start obsługi callbacka na `Debug`, zaakceptowany event terminalny na `Information`, błędy mapowane na `Warning`/`Error`.

### Application (`Application`)
- Główna logika trafia do `RecordTrainingRunEventCommandHandler`.
- Handler:
  - waliduje, czy run istnieje,
  - przetwarza eventy per `runName` sekwencyjnie, żeby uniknąć race condition przy read-modify-write metadanych,
  - sprawdza `sequence` i idempotencję,
  - mapuje `eventType` + `status` na kanoniczny status BE,
  - aktualizuje snapshot postępu i pola diagnostyczne w metadanych,
  - dla `completed` waliduje artefakty modelu i finalizuje manifest `models/registry/{producedModelName}/model.json`,
  - dla `failed` i `cancelled` oznacza stan terminalny i zleca cleanup artefaktów runtime,
  - publikuje zdarzenie do portu notyfikacji treningów, który później może być implementowany przez `SignalR`.
- `Application` decyduje, czy event oznacza dozwoloną zmianę stanu. `Infrastructure` tylko zapisuje/odczytuje pliki, sprawdza artefakty i wykonuje cleanup.

### Domain / Models (`Models`)
- Wprowadzić neutralne typy statusów/eventów, jeśli zespół nie chce dalej powielać stringów:
  - `TrainingRunStatus`,
  - `TrainingRunEventType`,
  - `TrainingReportStatus`.
- Modele domenowe nie znają ASP.NET, JSON, MediatR, filesystem ani klienta ML.
- Jeżeli zespół utrzymuje aktualny prostszy styl DTO w `Application`, minimum to przeniesienie kanonicznych nazw statusów do jednego miejsca, żeby `POST /api/trainings`, active run, cancel i event callback nie rozjechały się słownikami.

### Infrastructure (`Infrastructure`)
- Reuse istniejących elementów:
  - `ITrainingRunsGateway` / `TrainingRunsGateway` do odczytu i aktualizacji `trainings/metadata/{runName}.json`,
  - `IFileStorageGateway` / `LocalFileStorageGateway` do generycznego I/O,
  - `IModelsRegistryGateway` / `ModelsRegistryGateway` jako baza do pracy z rejestrem modeli,
  - `TrainingsStorageOptions`, `ModelsRegistryStorageOptions`, `MlServiceOptions`.
- Rozszerzyć istniejące porty generycznie:
  - `IModelsRegistryGateway.SaveAsync(...)` albo osobny `FinalizeModelManifestAsync(...)`, ale odpowiedzialność ma być reużywalna dla `UC-08/09/10`, nie zaszyta tylko pod callback eventu,
  - `IFileStorageGateway.DeleteDirectoryAsync(...)` / `DirectoryExistsAsync(...)` / `FileExistsAsync(...)` jako operacje ogólne, jeżeli są potrzebne do walidacji artefaktów i cleanupu.
- Jeśli dodajemy port cleanupu, nazwać go aplikacyjnie, np. `ITrainingArtifactsCleanupGateway`, a implementację w `Infrastructure` oprzeć o generyczne operacje storage. Nie dodawać bezpośrednich `Directory.Delete(...)` w handlerze.

## 6) Pliki per warstwa i odpowiedzialności

### API (`src/Backend/Sudoku/Sudoku`)
- `[NOWY]` `Controllers/InternalMlTrainingsController.cs`
  - `[ApiController]`, `[Route("internal/ml/trainings")]`.
  - `POST "{runName}/events"`.
  - Wywołuje `RecordTrainingRunEventCommand`.
  - Zwraca `TrainingRunEventAckApiResponse`.
  - Mapuje wyjątki na `ErrorApiResponse`.
- `[NOWY]` `Contracts/TrainingRunEventApiEntry.cs`
  - Payload eventu `ML -> BE`.
- `[NOWY]` `Contracts/TrainingRunProgressApiEntry.cs`
  - Snapshot postępu treningu.
- `[NOWY]` `Contracts/TrainingRunEventResultApiEntry.cs`
  - Wynik eventu terminalnego: artefakty, raport, metryki.
- `[NOWY]` `Contracts/TrainingMetricsSummaryApiEntry.cs`
  - Skrócone metryki końcowe, bez pełnego raportu.
- `[NOWY]` `Contracts/TrainingRunEventAckApiResponse.cs`
  - Potwierdzenie eventu do `ML`.
- `[REUSE]` `Contracts/ErrorApiResponse.cs`
  - Wspólny błąd HTTP `errorType`, `message`.
- `[REUSE/MODYFIKACJA]` `Program.cs`
  - Nie dodawać minimal API.
  - Jeżeli dodany będzie `SignalR`, zarejestrować `AddSignalR()` i mapowanie huba w ramach planu `UC-07`; dla samego callbacka wystarczy port notyfikacji z implementacją no-op albo późniejszą.

### Application (`src/Backend/Sudoku/Application`)
- `[NOWY]` `Trainings/RecordTrainingRunEventCommand.cs`
  - Komenda MediatR z `RunName`, `Sequence`, `EventType`, `Status`, `OccurredAtUtc`, `Progress`, `Result`, `Warnings`, `Message`.
- `[NOWY]` `Trainings/RecordTrainingRunEventCommandValidator.cs`
  - Walidacja wymaganych pól, zakresów i dozwolonych wartości.
- `[NOWY]` `Trainings/RecordTrainingRunEventCommandHandler.cs`
  - Główna orkiestracja eventu i finalizacji.
- `[NOWY]` `Trainings/RecordTrainingRunEventResultDto.cs`
  - Wynik dla API: `Accepted`, `RunName`, `Status`, `LastAcceptedSequence`, `Disposition`.
- `[NOWY]` `Trainings/TrainingRunEventDto.cs`
  - DTO eventu po mapowaniu z API, niezależne od HTTP.
- `[NOWY]` `Trainings/TrainingRunProgressDto.cs`
  - Snapshot postępu w metadanych.
- `[NOWY]` `Trainings/TrainingRunEventResultDto.cs`
  - Wynik terminalny po stronie aplikacji.
- `[NOWY]` `Trainings/TrainingMetricsSummaryDto.cs`
  - Skrócone metryki końcowe.
- `[NOWY]` `Trainings/RecordTrainingRunEventErrorTypes.cs`
  - Stałe `errorType`, np. `training_run_event_invalid`, `training_run_not_found`, `training_run_event_conflict`, `training_run_artifact_not_ready`, `training_run_event_persist_failed`.
- `[MODYFIKACJA]` `Trainings/TrainingRunMetadataDto.cs`
  - Dodać pola:
    - `LastAcceptedSequence: long?`,
    - `LastEventType: string?`,
    - `StartedAtUtc: DateTimeOffset?`,
    - `FinishedAtUtc: DateTimeOffset?`,
    - `Progress: TrainingRunProgressDto?`,
    - `ReportRelativePath: string?`,
    - `MetricsSummary: TrainingMetricsSummaryDto?`,
    - `FailureReason: string?`,
    - `CleanupWarnings: IReadOnlyList<string>?`.
- `[MODYFIKACJA]` `Abstractions/ITrainingRunsGateway.cs`
  - Reuse `GetByRunNameAsync` i `UpdateAsync`.
  - Jeżeli potrzebna będzie bezpieczna aktualizacja, dodać generyczne `UpdateAsync(metadata, expectedLastAcceptedSequence)` albo obsłużyć blokadę per run w Application.
- `[NOWY]` `Abstractions/IModelsRegistryWriterGateway.cs` albo `[MODYFIKACJA] IModelsRegistryGateway`
  - Finalizacja `model.json` dla modelu wynikowego.
  - Preferowane rozszerzenie istniejącego `IModelsRegistryGateway`, jeśli nie rozmyje odpowiedzialności.
- `[NOWY]` `Abstractions/ITrainingArtifactsCleanupGateway.cs`
  - Cleanup katalogów runtime dla `failed` i `cancelled`.
- `[NOWY]` `Abstractions/ITrainingRunEventPublisher.cs`
  - Port do publikowania snapshotu/eventu po aktualizacji metadanych; w MVP może mieć implementację no-op, a `UC-07` podmieni ją na `SignalR`.
- `[NOWY]` `Trainings/ITrainingRunEventLockProvider.cs` + implementacja w Application
  - Per-run `SemaphoreSlim` dla pojedynczej instancji BE.
  - Chroni sekwencję read-modify-write dla metadanych.
- `[NOWE]` wyjątki aplikacyjne:
  - `TrainingRunNotFoundException`,
  - `TrainingRunEventConflictException`,
  - `TrainingRunEventArtifactNotReadyException`,
  - `TrainingRunEventInvalidTransitionException`,
  - `TrainingRunEventPersistenceException`.

### Domain / Models (`src/Backend/Sudoku/Models`)
- `[NOWY/OPCJONALNIE]` `Trainings/TrainingRunStatus.cs`
  - Kanoniczne statusy: `starting`, `queued`, `running`, `cancelling`, `succeeded`, `failed`, `cancelled`.
- `[NOWY/OPCJONALNIE]` `Trainings/TrainingRunEventType.cs`
  - Kanoniczne typy eventów: `progress`, `statusChanged`, `completed`, `failed`, `cancelled`.
- `[NOWY/OPCJONALNIE]` `Trainings/TrainingReportStatus.cs`
  - `ok`, `missing`, `corrupted`.
- Guardrail: nie przenosić `TrainingRunEventApiEntry`, `ErrorApiResponse`, `JsonSerializerOptions`, `IOptions` ani klas storage do `Models`.

### Infrastructure (`src/Backend/Sudoku/Infrastructure`)
- `[MODYFIKACJA]` `Storage/TrainingRunsGateway.cs`
  - Obsłużyć nowe pola `TrainingRunMetadataDto`.
  - Zachować `JsonSerializerDefaults.Web`.
  - Nie dodawać reguł biznesowych przejść statusów.
- `[MODYFIKACJA]` `Storage/ModelsRegistryGateway.cs`
  - Dodać zapis/finalizację manifestu `model.json` dla `producedModelName`.
  - Sprawdzać technicznie, że `primaryArtifactRelativePath` jest względne i istnieje.
  - Tworzyć manifest zgodny ze standardem rejestru:
    - `name`,
    - `displayName`,
    - `sourceType = "training"`,
    - `sourceRunName`,
    - `parentModelName`,
    - `trainingMode`,
    - `architecture.inputProfile`,
    - `training.defaultTrainingProfileName`,
    - `training.defaultAugmentationProfileName`,
    - `artifacts.primaryArtifactRelativePath`,
    - `capabilities.canStartTraining`,
    - `capabilities.canUseForInference`,
    - `metadata.createdAtUtc`.
- `[NOWY]` `Storage/TrainingArtifactsCleanupGateway.cs`
  - Implementacja `ITrainingArtifactsCleanupGateway`.
  - Czyści tylko runtime artefakty danego runu:
    - `trainings/runs/{runName}`,
    - `trainings/reports/{runName}`,
    - `tmp/trainings/{runName}`,
    - częściowo utworzony `models/registry/{producedModelName}` dla `failed/cancelled`.
  - Nie usuwa `trainings/metadata/{runName}.json`.
- `[MODYFIKACJA]` `Storage/LocalFileStorageGateway.cs`
  - Dodać generyczne operacje katalogowe, jeśli cleanup/finalizacja ich wymaga:
    - `DirectoryExistsAsync`,
    - `FileExistsAsync`,
    - `DeleteDirectoryAsync`.
  - Wszystkie operacje muszą pilnować, że ścieżka docelowa pozostaje wewnątrz katalogu bazowego.
- `[MODYFIKACJA]` `DependencyInjection.cs`
  - Rejestracja nowych gatewayów i publishera.
  - Jeśli publisher jest no-op w tej historyjce, zarejestrować jawnie `NoOpTrainingRunEventPublisher`.
- `[BRAK NOWEGO KLIENTA ML]`
  - Endpoint jest kierunkiem `ML -> BE`, więc nie tworzyć nowego `HttpClient`.
  - Istniejący `MlTrainingEventsPathProvider` jest reuse'owany przez `POST /api/trainings` do przekazania callback path do `ML`.

### Configuration / Workflow
- `[MODYFIKACJA]` `src/Backend/Sudoku/Sudoku/appsettings.local.json`
  - Lokalnie pozostawić twardą wartość:
    - `MlService.TrainingEventsPathTemplate = "/internal/ml/trainings/{runName}/events"`.
  - Jeżeli dodany będzie internal callback secret, lokalnie wpisać wartość developerską.
- `[MODYFIKACJA]` `src/Backend/Sudoku/Sudoku/appsettings.production.json`
  - Utrzymywać `MlService.TrainingEventsPathTemplate` jako wartość produkcyjną nadpisywaną przez workflow.
- `[MODYFIKACJA]` `.github/workflows/backend-cd.yml`
  - Dodać zmienną `BE_ML_TRAINING_EVENTS_PATH_TEMPLATE`.
  - Walidować ją razem z pozostałymi zmiennymi środowiska.
  - Ustawić w generatorze `appsettings.production.json`:
    - `MlService.TrainingEventsPathTemplate`.
  - Jeżeli nie zostało jeszcze zrobione przez plan `POST /api/trainings`, dopiąć także `BE_ML_START_TRAINING_PATH -> MlService.StartTrainingPath`.
- `[BRAK PUBLICZNEGO ROUTINGU NGINX]`
  - Nie dodawać publicznego proxy dla `/internal/...`.
  - Publiczne `/api/...` pozostaje oddzielne od wewnętrznego callbacka.

## 7) Weryfikacja usług Infrastructure i antyduplikacja
- Sprawdzone w obecnym BE:
  - istnieje `ITrainingRunsGateway` z `ListAsync`, `GetByRunNameAsync`, `TryCreateAsync`, `UpdateAsync`, `DeleteAsync`,
  - istnieje `TrainingRunsGateway` zapisujący metadane w `trainings/metadata`,
  - istnieje `IFileStorageGateway` / `LocalFileStorageGateway`,
  - istnieje `IModelsRegistryGateway` / `ModelsRegistryGateway`,
  - istnieje `MlTrainingEventsPathProvider`,
  - istnieją `TrainingsStorageOptions`, `ModelsRegistryStorageOptions`, `MlServiceOptions`.
- Nie tworzyć nowego czytnika metadanych runów ani osobnego storage tylko dla eventów, jeśli wystarczy rozszerzyć aktualne gatewaye.
- Nie dodawać bezpośrednich operacji `File.*` / `Directory.*` w Application.
- Finalizacja manifestu modelu powinna być reużywalna dla późniejszych `UC-08`, `UC-09`, `UC-10`, a nie nazwana i zaprojektowana wyłącznie pod jeden callback.
- Cleanup katalogów ma być generycznie parametryzowany przez `TrainingsStorageOptions` i `ModelsRegistryStorageOptions`; żadnych hardcodowanych `/opt/sudoku/...`.

## 8) Przepływ w obrębie BE
1. `ML` kończy etap treningu albo epokę i wysyła `POST /internal/ml/trainings/{runName}/events`.
2. `InternalMlTrainingsController` binduje route/body i wysyła `RecordTrainingRunEventCommand`.
3. Validator sprawdza składnię payloadu.
4. Handler bierze per-run lock dla `runName`.
5. Handler odczytuje `TrainingRunMetadataDto` przez `ITrainingRunsGateway.GetByRunNameAsync`.
6. Jeśli run nie istnieje, zwraca `404`.
7. Jeśli `sequence <= LastAcceptedSequence`, handler zwraca `200 duplicate` bez zmiany stanu.
8. Handler sprawdza dozwoloną zmianę statusu:
   - `starting/queued -> running`,
   - `running -> running`,
   - `running/cancelling -> cancelled`,
   - `running -> failed`,
   - `running -> succeeded`.
9. Handler aktualizuje snapshot postępu, `UpdatedAtUtc`, `LastAcceptedSequence`, `LastEventType`, `Warnings`.
10. Dla `completed`:
    - sprawdza zgodność `producedModelName`,
    - sprawdza istnienie głównego artefaktu,
    - finalizuje `models/registry/{producedModelName}/model.json`,
    - zapisuje `status = succeeded`, `FinishedAtUtc`, `ReportStatus`, metryki i ostrzeżenia.
11. Dla `failed`:
    - zapisuje `status = failed`, `FailureReason`, `FinishedAtUtc`,
    - czyści runtime artefakty i częściowy katalog modelu.
12. Dla `cancelled`:
    - zapisuje `status = cancelled`, `FinishedAtUtc`,
    - czyści runtime artefakty i częściowy katalog modelu.
13. Handler zapisuje metadata przez `ITrainingRunsGateway.UpdateAsync`.
14. Po udanym zapisie handler publikuje snapshot przez `ITrainingRunEventPublisher`.
15. Kontroler zwraca `200 OK` z `TrainingRunEventAckApiResponse`.

## 9) Główne funkcje
- `InternalMlTrainingsController.RecordEventAsync(...)`
- `RecordTrainingRunEventCommandValidator.Validate(...)`
- `RecordTrainingRunEventCommandHandler.Handle(...)`
- `RecordTrainingRunEventCommandHandler.ApplyProgressEvent(...)`
- `RecordTrainingRunEventCommandHandler.ApplyTerminalCompletedEvent(...)`
- `RecordTrainingRunEventCommandHandler.ApplyTerminalFailedEvent(...)`
- `RecordTrainingRunEventCommandHandler.ApplyTerminalCancelledEvent(...)`
- `ITrainingRunsGateway.GetByRunNameAsync(...)`
- `ITrainingRunsGateway.UpdateAsync(...)`
- `IModelsRegistryGateway.SaveAsync(...)` albo `IModelsRegistryWriterGateway.SaveAsync(...)`
- `ITrainingArtifactsCleanupGateway.CleanupFailedOrCancelledRunAsync(...)`
- `ITrainingRunEventPublisher.PublishAsync(...)`

## 10) Wyjątki, fallbacki i zachowanie błędowe

### 10.1 Publiczne statusy dla ML
- `200 OK`:
  - event przyjęty i zapisany,
  - event jest duplikatem,
  - event przyszedł po terminalnym stanie i jest bezpiecznie ignorowany bez regresji.
- `400 Bad Request`:
  - `sequence < 1`,
  - nieznany `eventType`,
  - nieznany `status`,
  - `percent` poza `0..100`,
  - `runName` nie spełnia reguł nazwy.
- `404 Not Found`:
  - brak `trainings/metadata/{runName}.json`.
- `409 Conflict`:
  - `completed` wskazuje artefakt, który nie jest jeszcze widoczny,
  - próba niedozwolonego przejścia z terminalnego statusu na inny stan z wyższym `sequence`.
- `422 Unprocessable Entity`:
  - `completed` bez `result`,
  - `completed` bez `primaryArtifactRelativePath`,
  - `result.producedModelName` różny od metadanych runu,
  - `reportStatus` spoza `ok/missing/corrupted`.
- `500 Internal Server Error`:
  - nie można odczytać/zapisać metadanych,
  - nie można finalizować manifestu modelu,
  - cleanup rzuca błąd, którego nie udało się zapisać jako ostrzeżenie.

### 10.2 Fallbacki
- Brak fallbacku do `ML` jako źródła prawdy.
- Brak fallbacku do cache `FE`.
- Brak zgadywania statusu na podstawie katalogów `trainings/runs` albo `models/registry`; one są artefaktami technicznymi, nie źródłem stanu workflow.
- Dla duplikatu eventu terminalnego zwracamy `200 duplicate`, żeby przerwać retry po stronie `ML`.
- Dla eventu po terminalnym stanie:
  - jeżeli `sequence <= LastAcceptedSequence`, `200 duplicate`,
  - jeżeli `sequence > LastAcceptedSequence`, nie zmieniamy statusu terminalnego; preferowane `200 ignored_terminal_state` dla eventów nieterminalnych, żeby nie generować retry loop,
  - dla konfliktowego innego terminalnego eventu z wyższym `sequence` zwrócić `409` i zalogować `Warning`.
- Cleanup po `failed/cancelled`:
  - jeśli cleanup częściowo się nie uda, status terminalny pozostaje zapisany,
  - dopisać `cleanup_failed` do `CleanupWarnings`,
  - logować `Error`, ale nie cofać statusu do `running`.

### 10.3 Zachowanie raportu i artefaktów
- `completed + reportStatus = ok`:
  - zapisać `succeeded`,
  - zapisać `reportRelativePath`,
  - finalizować model.
- `completed + reportStatus = missing/corrupted`:
  - jeśli główny artefakt modelu istnieje, zapisać `succeeded` z `Warnings`,
  - finalizować model z capability do inferencji/treningu zgodnie z kontraktem.
- `completed`, ale brak głównego artefaktu:
  - zwrócić `409 training_run_artifact_not_ready`,
  - nie finalizować manifestu,
  - nie potwierdzać eventu jako przyjętego.

## 11) Specyficzna logika (pseudokod)

```text
handleTrainingRunEvent(runName, event):
  validate(event)

  using lockProvider.acquire(runName):
    metadata = trainingRunsGateway.getByRunName(runName)
    if metadata is null:
      throw TrainingRunNotFound

    if metadata.lastAcceptedSequence != null
       and event.sequence <= metadata.lastAcceptedSequence:
      return ack(disposition = "duplicate", status = metadata.status)

    if isTerminal(metadata.status):
      if event.eventType in ["progress", "statusChanged"]:
        logInfo("Ignoring late non-terminal event", runName, event.sequence)
        return ack(disposition = "ignored_terminal_state", status = metadata.status)
      throw TrainingRunEventConflict

    nextMetadata = metadata with:
      lastAcceptedSequence = event.sequence
      lastEventType = event.eventType
      updatedAtUtc = now()
      warnings = merge(metadata.warnings, event.warnings)
      progress = mergeProgress(metadata.progress, event.progress)

    switch event.eventType:
      case "progress":
        nextMetadata.status = event.status ?? "running"

      case "statusChanged":
        nextMetadata.status = normalizeStatus(event.status)

      case "completed":
        ensure event.result exists
        ensure event.result.producedModelName == metadata.producedModelName
        ensurePrimaryArtifactExists(metadata.producedModelName, event.result.primaryArtifactRelativePath)
        modelsRegistryGateway.saveManifest(buildModelManifest(metadata, event.result))
        nextMetadata.status = "succeeded"
        nextMetadata.finishedAtUtc = event.occurredAtUtc
        nextMetadata.reportStatus = event.result.reportStatus
        nextMetadata.reportRelativePath = event.result.reportRelativePath
        nextMetadata.metricsSummary = event.result.metricsSummary

      case "failed":
        nextMetadata.status = "failed"
        nextMetadata.finishedAtUtc = event.occurredAtUtc
        nextMetadata.failureReason = event.message
        cleanupWarnings = cleanupGateway.cleanupRuntimeArtifacts(metadata)
        nextMetadata.cleanupWarnings = cleanupWarnings

      case "cancelled":
        nextMetadata.status = "cancelled"
        nextMetadata.finishedAtUtc = event.occurredAtUtc
        cleanupWarnings = cleanupGateway.cleanupRuntimeArtifacts(metadata)
        nextMetadata.cleanupWarnings = cleanupWarnings

    trainingRunsGateway.update(nextMetadata)
    eventPublisher.publish(nextMetadata)

    return ack(disposition = "accepted", status = nextMetadata.status)
```

## 12) Logi diagnostyczne
- `Debug`:
  - odebrano event nieterminalny: `runName`, `sequence`, `eventType`, `status`.
- `Information`:
  - run przeszedł do `running`,
  - run zakończył się `succeeded/failed/cancelled`,
  - duplikat terminalnego eventu został potwierdzony.
- `Warning`:
  - event z niższym `sequence`,
  - event po terminalnym statusie,
  - `completed` z `reportStatus = missing/corrupted`,
  - cleanup częściowo nieudany.
- `Error`:
  - błąd zapisu metadanych,
  - błąd finalizacji manifestu,
  - niespójność `producedModelName`,
  - nie da się potwierdzić eventu terminalnego.
- Nie logować pełnych metryk per epoka jako dużych payloadów. Logi mają zawierać identyfikatory i krótkie kody błędów, a szczegóły metryk trafią do metadanych/raportów.

## 13) Workflow GitHub i konfiguracja runtime
- `local`:
  - `appsettings.local.json` ma twardą wartość `MlService.TrainingEventsPathTemplate`.
  - Callback działa po lokalnym adresie BE, bez publicznego nginx.
- `production`:
  - workflow `backend-cd.yml` generuje `appsettings.production.json`.
  - Dodać `BE_ML_TRAINING_EVENTS_PATH_TEMPLATE`, np. `/internal/ml/trainings/{runName}/events`.
  - Nie dodawać routingu `/internal` do nginx.
  - Upewnić się, że `BE` i `ML` działają na localhost oraz mają dostęp do wspólnych katalogów runtime zgodnie z dokumentacją deployu.
- Katalogi `shared/trainings`, `shared/models`, `shared/data` nie są częścią release'u i nie mogą być czyszczone przez deploy.

## 14) Kolejność implementacji kodu
1. Dodać/uzgodnić kanoniczne statusy i typy eventów (`Models` albo wspólne stałe w `Application`).
2. Rozszerzyć `TrainingRunMetadataDto` o pola sekwencji, postępu, wyniku, metryk i diagnostyki.
3. Dodać modele API `TrainingRunEvent*ApiEntry` i `TrainingRunEventAckApiResponse`.
4. Dodać command, validator, DTO i wyjątki dla `RecordTrainingRunEvent`.
5. Rozszerzyć `IModelsRegistryGateway` albo dodać writer gateway dla finalizacji `model.json`.
6. Dodać generyczne operacje storage potrzebne do `FileExists`/`DirectoryExists`/`DeleteDirectory`.
7. Dodać `TrainingArtifactsCleanupGateway`.
8. Dodać per-run lock provider dla sekwencyjnej obsługi eventów.
9. Zaimplementować `RecordTrainingRunEventCommandHandler`.
10. Dodać no-op publisher eventów albo docelową integrację z `SignalR`, jeśli `UC-07` jest implementowany równolegle.
11. Dodać `InternalMlTrainingsController`.
12. Dodać rejestrację DI.
13. Uzupełnić `appsettings.local.json`, `appsettings.production.json` i `backend-cd.yml`.
14. Dodać testy jednostkowe handlera i testy integracyjne kontrolera/storage.

## 15) Guardraile implementacyjne
- Nie tworzyć minimal API `MapPost`; użyć kontrolera ASP.NET.
- Nie mieszać kontraktów API z DTO aplikacyjnymi.
- Nie robić finalizacji modelu w `Infrastructure`; `Infrastructure` zapisuje manifest, ale decyzję kiedy i z jakimi danymi podejmuje `Application`.
- Nie robić cleanupu przez hardcodowane ścieżki.
- Nie używać `/opt/sudoku/...` w kodzie.
- Nie wymagać pełnej sekwencji eventów; wystarczy monotoniczność przyjętego snapshotu.
- Nie nadpisywać terminalnego statusu runu eventem spóźnionym.
- Nie traktować brakującego raportu jako `failed`, jeśli artefakty modelu są kompletne.
- Nie publikować do `FE` eventu przed trwałym zapisem metadanych.
- Nie logować pełnych payloadów eventów ani dużych metryk.
- Nie wystawiać `/internal/...` publicznie przez nginx.

## 16) Zależności pomiędzy historyjkami
- Wymaga `UC-13` tylko pośrednio: publiczne operacje startu i monitoringu są chronione tokenem admin, ale sam callback nie używa tokenu FE.
- Wymaga wcześniejszego `POST /api/trainings`, bo callback aktualizuje rekord utworzony przy starcie runu.
- Korzysta z `GET /api/trainings/active`, bo po eventach aktywny run ma odzwierciedlać aktualny status.
- Korzysta z rejestru modeli z `GET /api/models/registry` / `INF-08`, bo po `completed` finalizuje wpis modelu wynikowego.
- Korzysta z datasetów przygotowanych w `UC-12` tylko przez metadane zapisane przy starcie runu.
- Jest fundamentem dla `UC-07`, bo `SignalR` powinien publikować stan pochodzący z eventów zapisanych przez ten endpoint.
- Przygotowuje dane dla `UC-08` i `UC-09`, bo utrzymuje historię statusów, metryki skrócone, raport i powiązanie `run -> producedModelName`.
- Jest powiązany z `UC-10`, bo model wynikowy po `completed` może później zostać ustawiony jako aktywny model inferencyjny.

## 17) Testy i weryfikacja
- Testy walidatora:
  - brak `sequence`,
  - `sequence < 1`,
  - nieznany `eventType`,
  - `completed` bez `result`,
  - `percent` poza zakresem.
- Testy handlera:
  - event `progress` aktualizuje snapshot i `LastAcceptedSequence`,
  - duplikat eventu zwraca `duplicate` bez zapisu,
  - event z niższym `sequence` nie cofa stanu,
  - `completed` z kompletnym artefaktem tworzy manifest modelu i ustawia `succeeded`,
  - `completed` z `reportStatus = missing` nadal ustawia `succeeded`, jeśli artefakt istnieje,
  - `completed` bez artefaktu zwraca konflikt i nie zapisuje `succeeded`,
  - `failed` i `cancelled` czyszczą runtime artefakty i zostawiają metadata,
  - event po terminalnym statusie nie nadpisuje wyniku.
- Testy API:
  - `POST /internal/ml/trainings/{runName}/events` zwraca poprawne statusy HTTP i `ErrorApiResponse`,
  - JSON jest w `camelCase`,
  - route `/internal/...` działa niezależnie od `/api/trainings`.
- Testy storage:
  - `LocalFileStorageGateway.DeleteDirectoryAsync` nie pozwala wyjść poza katalog bazowy,
  - finalizacja manifestu zapisuje `model.json` w poprawnym katalogu.
