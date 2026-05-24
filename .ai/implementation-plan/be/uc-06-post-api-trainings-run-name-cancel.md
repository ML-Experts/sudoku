# UC-06-BE - Plan implementacyjny dla `POST /api/trainings/{runName}/cancel`

## 1) Przeznaczenie endpointa
- Endpoint `POST /api/trainings/{runName}/cancel` zleca kooperacyjne anulowanie aktywnego runu treningowego.
- Endpoint jest chroniony tokenem administracyjnym z `UC-13`; bez tokenu nie wolno anulować runu ani wywoływać `ML`.
- Publicznym identyfikatorem jest `runName`, czyli nazwa rekordu `trainings/metadata/{runName}.json` utworzona przez `POST /api/trainings`.
- Anulowanie jest idempotentne i dla uproszczenia publicznie zawsze zwraca `202 Accepted`, jeżeli żądanie jest poprawnie obsłużone przez `BE`.
- Odpowiedź nie obiecuje natychmiastowego stanu terminalnego. Zwraca bieżący status dopasowanego runu albo `null`, a faktyczny koniec `cancelled` przychodzi później przez `POST /internal/ml/trainings/{runName}/events` i `SignalR /ws/trainings/{runName}`.
- Backend pozostaje `source of truth`: to `BE` weryfikuje aktywny run, zapisuje status `cancelling`, wywołuje `ML`, utrzymuje metadane i publikuje snapshot do `FE`.

## 2) Zakres i założenia
- Plan opiera się na `PRD`, `UC-06`, dokumentacji deployu/runtime oraz istniejących planach dla:
  - `POST /api/trainings`,
  - `GET /api/trainings/active`,
  - `POST /internal/ml/trainings/{runName}/events`,
  - `SignalR /ws/trainings/{runName}`.
- Nie sugerować się aktualnym stanem `FE` i `ML`; kontrakt wynika z odpowiedzialności Backendu jako właściciela workflow.
- System dopuszcza dokładnie jeden aktywny run jednocześnie. Cancel dotyczy tylko runu aktywnego i dopasowanego po `runName`.
- Aktywne statusy do anulowania: `starting`, `queued`, `running`, `cancelling`.
- Terminalne statusy: `succeeded`, `failed`, `cancelled`.
- `starting` może wystąpić tylko w krótkim oknie między rezerwacją metadanych a potwierdzeniem startu przez `ML`. Cancel dla `starting` nie powinien tworzyć niespójnego rollbacku startu; szczegóły w sekcji wyjątków.
- `cancelled` jako stan końcowy jest zapisywany dopiero po evencie `ML -> BE`. Sam endpoint publiczny zwykle ustawia status `cancelling`.
- Po końcowym `cancelled` techniczne artefakty runtime są czyszczone przez istniejący mechanizm cleanup używany również dla `failed`, a `trainings/metadata/{runName}.json` zostaje zachowany.
- Publiczny JSON ma klucze `camelCase`; modele wejściowe HTTP mają sufiks `ApiEntry`, wyjściowe `ApiResponse`, a DTO warstwy aplikacyjnej mają sufiks `Dto`.

## 3) Kontrakty API FE i ML

### 3.1 FE -> BE (`POST /api/trainings/{runName}/cancel`)
- Route param:
  - `runName: string` - wymagany, walidowany jak nazwa runu treningowego.
- Request body:
  - brak w MVP.
- Autoryzacja:
  - `Bearer` token administracyjny.
- Odpowiedzi:
  - `202 Accepted` -> `CancelTrainingRunApiResponse`,
  - `400 Bad Request` -> `ErrorApiResponse`, gdy `runName` ma niepoprawny format,
  - `401 Unauthorized` -> brak albo niepoprawny token,
  - `502 Bad Gateway` -> `ML` zwrócił nieoczekiwany kontrakt albo odrzucił poprawne zlecenie w sposób kontraktowy,
  - `503 Service Unavailable` -> `ML` niedostępny,
  - `504 Gateway Timeout` -> timeout potwierdzenia anulowania przez `ML`,
  - `500 Internal Server Error` -> błąd zapisu metadanych, niespójność plikowego stanu aktywnego runu albo inny błąd techniczny `BE`.

Uwaga: brak dopasowanego aktywnego runu nie jest `404`, ponieważ endpoint ma być idempotentny i zwracać `202 Accepted` z `requestDisposition = "not_found"` albo `requestDisposition = "not_active"`.

Przykład nowo przyjętego anulowania:

```json
{
  "runName": "train-20260429-143000-cnn-mnist-baseline-sudokuDigitsV1",
  "status": "cancelling",
  "requestDisposition": "accepted",
  "message": "Anulowanie runu zostało przyjęte.",
  "progressChannelUrl": "/ws/trainings/train-20260429-143000-cnn-mnist-baseline-sudokuDigitsV1"
}
```

Przykład duplikatu:

```json
{
  "runName": "train-20260429-143000-cnn-mnist-baseline-sudokuDigitsV1",
  "status": "cancelling",
  "requestDisposition": "duplicate",
  "message": "Run jest już w trakcie anulowania.",
  "progressChannelUrl": "/ws/trainings/train-20260429-143000-cnn-mnist-baseline-sudokuDigitsV1"
}
```

Przykład no-op dla runu terminalnego:

```json
{
  "runName": "train-20260429-143000-cnn-mnist-baseline-sudokuDigitsV1",
  "status": "succeeded",
  "requestDisposition": "already_finished",
  "message": "Run jest już zakończony i nie może zostać anulowany.",
  "progressChannelUrl": "/ws/trainings/train-20260429-143000-cnn-mnist-baseline-sudokuDigitsV1"
}
```

Przykład braku dopasowania:

```json
{
  "runName": "train-unknown",
  "status": null,
  "requestDisposition": "not_found",
  "message": "Nie znaleziono aktywnego runu o podanej nazwie.",
  "progressChannelUrl": null
}
```

### 3.2 BE -> ML (`POST /ml/trainings/{runName}/cancel`)
- `BE` wywołuje `ML` tylko wtedy, gdy istnieje dopasowany aktywny run w statusie pozwalającym na zlecenie anulowania.
- Route:
  - `/ml/trainings/{runName}/cancel`.
- Request body w MVP:

```json
{
  "runName": "train-20260429-143000-cnn-mnist-baseline-sudokuDigitsV1",
  "requestedAtUtc": "2026-04-29T14:35:00Z",
  "reason": "user_requested"
}
```

- `requestedAtUtc` pochodzi z `TimeProvider` po stronie `BE`.
- `reason` jest krótkim kodem diagnostycznym, nie tekstem od użytkownika.
- Payload nie zawiera ścieżek systemowych, bo cancel dotyczy istniejącego joba/runu po `runName`.

### 3.3 ML -> BE
- Sam endpoint publiczny nie zapisuje finalnego `cancelled`.
- Oczekiwane domknięcie:
  - `ML` przyjmuje cancel,
  - worker treningowy kończy możliwie szybko i sprząta własne uchwyty/proces,
  - `ML` wysyła terminalny event `cancelled` do `POST /internal/ml/trainings/{runName}/events`,
  - `BE` aktualizuje `trainings/metadata/{runName}.json`, uruchamia cleanup artefaktów runtime i publikuje terminalny snapshot przez SignalR.
- Jeśli `ML` zwróci `404` dla joba, `BE` nie może samodzielnie oznaczyć runu jako `cancelled`. W MVP mapujemy to jako błąd integracji `502`, chyba że `ML` zwróci jawny kontrakt idempotentny opisany niżej.

### 3.4 BE -> ML - odpowiedź cancel
- Akceptowane statusy:
  - `202 Accepted` - cancel przyjęty,
  - `200 OK` - cancel już był przyjęty albo job jest już w stanie anulowania po stronie `ML`.
- Opcjonalny payload:

```json
{
  "accepted": true,
  "runName": "train-20260429-143000-cnn-mnist-baseline-sudokuDigitsV1",
  "status": "cancelling",
  "disposition": "accepted"
}
```

- `disposition` po stronie `ML` może mieć wartości:
  - `accepted`,
  - `duplicate`,
  - `already_finished`.
- `BE` nie ufa `ML` jako źródłu prawdy statusu biznesowego, ale może użyć `disposition` do logów diagnostycznych. Publiczna odpowiedź dla `FE` wynika z metadanych `BE`.

## 4) Modele wejściowe i wyjściowe

### 4.1 `CancelTrainingRunApiResponse`
- `runName: string` - `runName` z route.
- `status: string | null` - bieżący status runu znany przez `BE`; `null` przy braku dopasowanego runu.
- `requestDisposition: string`:
  - `accepted` - `BE` zapisał przejście do `cancelling` i `ML` przyjął zlecenie,
  - `duplicate` - run był już w `cancelling`; request został potwierdzony bez ponownego zapisu statusu,
  - `already_finished` - run istnieje, ale ma status terminalny,
  - `not_found` - brak rekordu o `runName`,
  - `not_active` - rekord istnieje, ale nie jest aktywnym runem możliwym do anulowania,
  - `start_not_confirmed` - rekord jest w krótkim stanie `starting`, w którym anulowanie nie może bezpiecznie wyprzedzić rollbacku/startu.
- `message: string` - krótka informacja dla UI, bez stack trace i bez ścieżek.
- `progressChannelUrl: string | null` - `/ws/trainings/{runName}` dla znanego runu, inaczej `null`.

### 4.2 `CancelTrainingRunCommand`
- `RunName: string?`.

### 4.3 `CancelTrainingRunCommandResultDto`
- `RunName: string`.
- `Status: string?`.
- `RequestDisposition: string`.
- `Message: string`.
- `ProgressChannelUrl: string?`.

### 4.4 `CancelMlTrainingRequestDto`
- `RunName: string`.
- `RequestedAtUtc: DateTimeOffset`.
- `Reason: string`.

### 4.5 `CancelMlTrainingResultDto`
- `Accepted: bool`.
- `RunName: string`.
- `Status: string?`.
- `Disposition: string?`.

## 5) Zachowanie per warstwa

### API (`Sudoku`)
- Kontroler pozostaje cienki:
  - binduje `runName` z route,
  - wywołuje `CancelTrainingRunCommand`,
  - mapuje DTO aplikacyjne na `CancelTrainingRunApiResponse`,
  - dla poprawnie obsłużonych no-opów zawsze zwraca `202 Accepted`,
  - mapuje walidację i błędy techniczne na `ErrorApiResponse`.
- Kontroler nie skanuje katalogów, nie sprawdza statusów i nie wywołuje `HttpClient` do `ML`.
- Endpoint powinien być w istniejącym `TrainingsController`, obok `POST /api/trainings` i `GET /api/trainings/active`.
- Logi w API tylko na granicy żądania:
  - `Information`: przyjęto żądanie anulowania i końcowa `requestDisposition`,
  - `Warning`: błąd walidacji, niedostępne `ML`, timeout,
  - `Error`: niespójność plików lub błąd zapisu.

### Application (`Application`)
- Warstwa aplikacyjna jest właścicielem reguł anulowania:
  - waliduje `runName`,
  - odczytuje metadane runu przez `ITrainingRunsGateway`,
  - rozróżnia brak rekordu, status aktywny, `cancelling`, status terminalny i nieaktywny,
  - pilnuje invariantów pojedynczego aktywnego runu,
  - decyduje, kiedy przejść do `cancelling`,
  - zapisuje metadane przed komunikacją zwrotną do `FE`,
  - zleca cancel przez `IMlTrainingsGateway.CancelTrainingAsync`,
  - publikuje snapshot do SignalR przez istniejący `ITrainingRunEventPublisher` albo analogiczny publisher snapshotu po zmianie statusu.
- `Application` nie wykonuje operacji filesystem bezpośrednio i nie zna URL-a `ML`.
- `Application` nie czyści artefaktów w momencie żądania cancel. Cleanup następuje po terminalnym evencie `cancelled` w przepływie `POST /internal/ml/trainings/{runName}/events`.

### Domain / Models (`Models`)
- Reuse istniejącego `TrainingRunStatus`:
  - `Starting`,
  - `Queued`,
  - `Running`,
  - `Cancelling`,
  - `Succeeded`,
  - `Failed`,
  - `Cancelled`.
- Dodać helper, jeżeli go brakuje i jest współdzielony w wielu handlerach:
  - `IsActive(status)` dla `starting`, `queued`, `running`, `cancelling`,
  - `CanRequestCancellation(status)` dla `queued`, `running` i ewentualnie `cancelling`,
  - `IsTerminal(status)` już istnieje i powinien zostać użyty.
- Modele domenowe nie znają HTTP, MediatR, filesystem, `HttpClient`, `appsettings` ani kontraktów `ML`.
- Jeżeli statusy pozostają stringami, walidatory i handler muszą korzystać ze stałych `TrainingRunStatus`, a nie z literalnych stringów rozsianych po kodzie.

### Infrastructure (`Infrastructure`)
- Reuse istniejących adapterów:
  - `TrainingRunsGateway` do odczytu i zapisu metadanych,
  - `MlTrainingsHttpClient` jako klient `ML` dla treningów,
  - `TrainingArtifactsCleanupGateway` pozostaje odpowiedzialny za cleanup po terminalnym `cancelled`,
  - `LocalFileStorageGateway` pozostaje generycznym adapterem plikowym.
- Nie tworzyć osobnego `MlCancelTrainingHttpClient` tylko dla jednego endpointa. Rozszerzyć istniejący `IMlTrainingsGateway` i `MlTrainingsHttpClient` o metodę `CancelTrainingAsync`.
- Jeżeli trzeba dodać path template do `ML`, rozszerzyć istniejące `MlServiceOptions` o `CancelTrainingPathTemplate`, zamiast hardcodować `/ml/trainings/{runName}/cancel` w kliencie.
- Implementacja infrastruktury mapuje transport:
  - timeout -> `MlServiceTimeoutException`,
  - `HttpRequestException` / brak połączenia -> `MlServiceUnavailableException`,
  - 4xx/nieoczekiwany payload -> `MlOperationFailedException`,
  - 5xx -> `MlServiceUnavailableException`.
- Infrastructure nie decyduje, czy status runu pozwala na anulowanie. To jest logika aplikacyjna.

## 6) Pliki per warstwa i odpowiedzialności

### API (`src/Backend/Sudoku/Sudoku`)
- `[MODYFIKACJA]` `Controllers/TrainingsController.cs`
  - dodać `[Authorize] [HttpPost("{runName}/cancel")]`,
  - wywołać `CancelTrainingRunCommand`,
  - zwrócić `202 Accepted` z `CancelTrainingRunApiResponse`,
  - mapować walidację na `400`,
  - mapować błędy `ML` na `502/503/504`,
  - mapować błędy storage na `500`.
- `[NOWY]` `Contracts/CancelTrainingRunApiResponse.cs`
  - publiczna odpowiedź dla `FE`.
- `[REUSE]` `Contracts/ErrorApiResponse.cs`
  - publiczny model błędu `errorType`, `message`.
- `[MODYFIKACJA]` `Program.cs`
  - bind i walidacja `MlServiceOptions.CancelTrainingPathTemplate`,
  - upewnić się, że `ITrainingRunEventPublisher` jest zarejestrowany dla publikacji snapshotu po przejściu do `cancelling`.
- `[MODYFIKACJA]` `appsettings.local.json`
  - dodać lokalne, jawne `"CancelTrainingPathTemplate": "/ml/trainings/{runName}/cancel"`.
- `[MODYFIKACJA]` `appsettings.production.json`
  - dodać placeholder `"CancelTrainingPathTemplate": "__SET_BY_GITHUB_VARIABLE_BE_ML_CANCEL_TRAINING_PATH_TEMPLATE__"`.

### Application (`src/Backend/Sudoku/Application`)
- `[NOWY]` `Trainings/CancelTrainingRunCommand.cs`
  - komenda MediatR z `RunName`.
- `[NOWY]` `Trainings/CancelTrainingRunCommandValidator.cs`
  - wymagany `runName`,
  - długość i dozwolone znaki zgodne z generatorami nazw runu,
  - błąd walidacji z kodem `invalid_training_run_name`.
- `[NOWY]` `Trainings/CancelTrainingRunCommandHandler.cs`
  - główna orkiestracja anulowania.
- `[NOWY]` `Trainings/CancelTrainingRunCommandResultDto.cs`
  - DTO odpowiedzi aplikacyjnej mapowane do `CancelTrainingRunApiResponse`.
- `[NOWY]` `Trainings/CancelTrainingRunErrorTypes.cs`
  - stałe:
    - `invalid_training_run_name`,
    - `training_cancel_ml_rejected`,
    - `training_cancel_ml_unavailable`,
    - `training_cancel_ml_timeout`,
    - `training_cancel_persistence_failed`,
    - `training_cancel_invariant_violation`.
- `[NOWY]` `Trainings/CancelTrainingRunDispositions.cs`
  - stałe:
    - `accepted`,
    - `duplicate`,
    - `already_finished`,
    - `not_found`,
    - `not_active`,
    - `start_not_confirmed`.
- `[MODYFIKACJA]` `Abstractions/IMlTrainingsGateway.cs`
  - dodać `CancelTrainingAsync(CancelMlTrainingRequestDto request, CancellationToken cancellationToken = default)`.
- `[NOWY]` `Trainings/CancelMlTrainingRequestDto.cs`
  - DTO requestu aplikacyjnego do portu `IMlTrainingsGateway`.
- `[NOWY]` `Trainings/CancelMlTrainingResultDto.cs`
  - DTO wyniku anulowania po stronie `ML`.
- `[MODYFIKACJA OPCJONALNA]` `Abstractions/ITrainingRunsGateway.cs`
  - jeżeli handler potrzebuje atomowości, dodać generyczne `UpdateIfCurrentStatusAsync(runName, allowedStatuses, updateFactory)` albo `TryUpdateAsync(metadata, expectedStatus)`.
  - Nie dodawać metody specyficznej `CancelAsync`, jeżeli można zachować generyczny gateway metadanych.
- `[MODYFIKACJA OPCJONALNA]` `Trainings/ITrainingRunEventLockProvider.cs`
  - reuse locka per `runName` z eventów ML, żeby cancel i callback terminalny nie nadpisały sobie metadanych w wyścigu.
- `[MODYFIKACJA OPCJONALNA]` `Models/Trainings/TrainingRunStatus.cs`
  - dodać helpery `IsActive` i `CanRequestCancellation`, jeżeli statusy są używane w wielu handlerach.

### Domain / Models (`src/Backend/Sudoku/Models`)
- `[MODYFIKACJA OPCJONALNA]` `Trainings/TrainingRunStatus.cs`
  - dodać wspólne helpery statusów.
- Brak nowych modeli zależnych od HTTP albo storage.

### Infrastructure (`src/Backend/Sudoku/Infrastructure`)
- `[MODYFIKACJA]` `Ml/MlTrainingsHttpClient.cs`
  - zaimplementować `CancelTrainingAsync`,
  - zbudować URL przez path template z `MlServiceOptions`,
  - wysłać `POST` JSON z `CancelMlTrainingRequestDto`,
  - akceptować `200 OK` i `202 Accepted`,
  - mapować błędy przez ten sam styl co `StartTrainingAsync`.
- `[MODYFIKACJA]` `Configuration/MlServiceOptions.cs`
  - dodać `[Required] public string CancelTrainingPathTemplate { get; init; } = "/ml/trainings/{runName}/cancel";`.
- `[MODYFIKACJA OPCJONALNA]` `Storage/TrainingRunsGateway.cs`
  - tylko jeśli potrzebna będzie generyczna atomowa aktualizacja statusu.
- `[REUSE]` `Storage/TrainingArtifactsCleanupGateway.cs`
  - bez zmian w momencie endpointa cancel; cleanup działa po terminalnym evencie `cancelled`.
- `[REUSE]` `Storage/LocalFileStorageGateway.cs`
  - bez dedykowanej logiki cancel.
- `[MODYFIKACJA]` `DependencyInjection.cs`
  - zwykle bez zmian, jeśli rozszerzamy istniejące `IMlTrainingsGateway`;
  - jeśli dodany zostanie nowy serwis pomocniczy, zarejestrować go jako port aplikacyjny, nie jako zależność kontrolera.

### Testy backendu
- `[NOWY/MODYFIKACJA]` testy handlera `CancelTrainingRunCommandHandler`:
  - brak rekordu -> `202`/`not_found`,
  - status `queued` -> zapis `cancelling`, wywołanie `ML`, wynik `accepted`,
  - status `running` -> zapis `cancelling`, wywołanie `ML`, wynik `accepted`,
  - status `cancelling` -> bez ponownej zmiany statusu, wynik `duplicate`,
  - status terminalny -> bez wywołania `ML`, wynik `already_finished`,
  - błędy `ML` po zapisie `cancelling` -> patrz fallback w sekcji 8,
  - callback `cancelled` przychodzący równolegle z cancel requestem -> brak regresji statusu.
- `[NOWY/MODYFIKACJA]` testy `MlTrainingsHttpClient`:
  - poprawna ścieżka po template,
  - `202` i `200` jako sukces,
  - `503` -> `MlServiceUnavailableException`,
  - timeout -> `MlServiceTimeoutException`,
  - niepoprawny JSON -> `MlOperationFailedException`.
- `[NOWY/MODYFIKACJA]` testy kontrolera:
  - route `POST /api/trainings/{runName}/cancel`,
  - autoryzacja,
  - mapowanie wyniku aplikacyjnego na `202`,
  - mapowanie walidacji na `400`.

## 7) Główne funkcje
- `TrainingsController.CancelAsync(string runName, CancellationToken cancellationToken)`.
- `CancelTrainingRunCommandHandler.Handle(CancelTrainingRunCommand request, CancellationToken cancellationToken)`.
- `CancelTrainingRunCommandValidator`.
- `IMlTrainingsGateway.CancelTrainingAsync(CancelMlTrainingRequestDto request, CancellationToken cancellationToken)`.
- `MlTrainingsHttpClient.CancelTrainingAsync(...)`.
- `TrainingRunStatus.CanRequestCancellation(status)` albo lokalny odpowiednik w handlerze.
- `ITrainingRunEventLockProvider.AcquireAsync(runName, cancellationToken)` do ochrony przed wyścigiem z eventami `ML`.
- `ITrainingRunEventPublisher.PublishAsync(metadata, cancellationToken)` po zapisaniu statusu `cancelling`, jeżeli chcemy natychmiast pokazać zmianę w kanale SignalR.

## 8) Wyjątki, fallbacki i idempotencja

### Brak rekordu
- `BE` zwraca `202 Accepted`:
  - `status = null`,
  - `requestDisposition = "not_found"`,
  - nie wywołuje `ML`.
- Log poziomu `Information` albo `Debug`, bez stack trace.

### Rekord istnieje, ale nie jest aktywny
- Jeżeli status terminalny: `requestDisposition = "already_finished"`.
- Jeżeli status nieznany albo nieobsługiwany: traktować jako niespójność `500 training_cancel_invariant_violation`, bo to problem źródła prawdy.
- `ML` nie jest wywoływany.

### Run już jest `cancelling`
- Zwrócić `202 Accepted` z `requestDisposition = "duplicate"`.
- Nie trzeba ponownie zapisywać metadanych.
- Co do wywołania `ML`:
  - rekomendacja MVP: nie wywoływać ponownie `ML`, jeśli `BE` ma już status `cancelling`;
  - `FE` i tak monitoruje finalny event przez SignalR.

### Run jest `queued` albo `running`
- Ustawić `status = "cancelling"` i `updatedAtUtc`.
- Zapisać metadata przed odpowiedzią do `FE`.
- Wywołać `ML` przez `IMlTrainingsGateway.CancelTrainingAsync`.
- Po sukcesie zwrócić `202 Accepted` z `requestDisposition = "accepted"`.
- Opublikować snapshot `cancelling` przez SignalR po trwałym zapisie metadanych.

### Run jest `starting`
- To najtrudniejszy stan, bo `POST /api/trainings` może być jeszcze przed potwierdzeniem `ML` i ma własny rollback.
- Rekomendacja MVP:
  - nie wysyłać cancel do `ML`,
  - zwrócić `202 Accepted` z `requestDisposition = "start_not_confirmed"` i aktualnym `status = "starting"`,
  - `FE` powinno odczekać snapshot/active run i ponowić cancel po przejściu do `queued` albo po zniknięciu rollbackowanego rekordu.
- Alternatywa późniejsza:
  - wprowadzić serializowany lock dla startu i cancel tego samego runu, a cancel w `starting` wykonać dopiero po potwierdzonym `queued`.

### `ML` niedostępny po zapisaniu `cancelling`
- Nie wolno automatycznie oznaczyć runu jako `cancelled`, bo brak terminalnego potwierdzenia.
- Dwie dopuszczalne strategie:
  - preferowana: zostawić `cancelling`, zwrócić `503/504`, zapisać warning `cancel_request_delivery_failed`, pozwolić operatorowi albo ponownemu requestowi naprawić dostarczenie cancel,
  - bardziej agresywna: rollback statusu do poprzedniego (`queued`/`running`) tylko jeśli zapis `cancelling` był jedyną zmianą i mamy bezpieczny expected-status update.
- Rekomendacja MVP: zostawić `cancelling` i zwrócić błąd transportowy. Dzięki temu nie ukrywamy problemu integracji, a FE może pokazać "anulowanie zlecone, czekamy na potwierdzenie" dopiero po udanym requestcie.
- Jeżeli chcemy zachować ścisłą semantykę "accepted tylko po przyjęciu przez ML", wtedy zapis statusu należy wykonać po sukcesie `ML`. To jednak otwiera wyścig z eventami i mniej dobrze komunikuje zamiar. Dla BE jako source of truth rekomendowany jest zapis zamiaru cancel przed publikacją.

### `ML` zwraca `404` albo `already_finished`
- `404` bez kontraktu idempotentnego mapować na `502`, bo `BE` ma aktywny run, a `ML` nie zna joba.
- `200/202` z `disposition = "already_finished"` traktować jako sukces dostarczenia cancel, ale nie zmieniać statusu terminalnego po stronie `BE` bez eventu callbacka.
- Jeśli po stronie `ML` job już zakończył się chwilę wcześniej, terminalny event powinien dotrzeć do `BE`; do tego czasu `BE` może pozostać w `cancelling`.

### Cleanup
- Endpoint cancel nie usuwa katalogów samodzielnie.
- Cleanup `trainings/runs/{runName}`, `trainings/reports/{runName}`, `tmp/trainings/{runName}` i częściowo utworzonego `models/registry/{producedModelName}` następuje po terminalnym evencie `cancelled`.
- Jeżeli cleanup się nie powiedzie, zapisać `cleanupWarnings`, ale pozostawić metadata ze statusem `cancelled`.

## 9) Specyficzna logika jako pseudokod

```csharp
handle CancelTrainingRun(runName):
    validate(runName)

    using lock = await lockProvider.AcquireAsync(runName)
    metadata = await trainingRuns.GetByRunNameAsync(runName)

    if metadata is null:
        return Result(runName, null, "not_found")

    if IsTerminal(metadata.Status):
        return Result(runName, metadata.Status, "already_finished", metadata.ProgressChannelUrl)

    if metadata.Status == "cancelling":
        return Result(runName, metadata.Status, "duplicate", metadata.ProgressChannelUrl)

    if metadata.Status == "starting":
        return Result(runName, metadata.Status, "start_not_confirmed", metadata.ProgressChannelUrl)

    if metadata.Status not in ["queued", "running"]:
        throw invariantViolation

    previousStatus = metadata.Status
    cancellingMetadata = metadata with
    {
        Status = "cancelling",
        UpdatedAtUtc = clock.GetUtcNow(),
        Warnings = metadata.Warnings
    }

    await trainingRuns.UpdateAsync(cancellingMetadata)
    await publisher.PublishAsync(cancellingMetadata) // best effort albo obsłużony warning

    try:
        await mlTrainings.CancelTrainingAsync(new CancelMlTrainingRequestDto(
            runName,
            requestedAtUtc,
            "user_requested"))
    catch transport/timeout/contract:
        // Nie ustawiamy cancelled. Terminalny stan wymaga callbacka ML.
        // Opcjonalnie dopisać warning i zostawić cancelling.
        await appendWarning("cancel_request_delivery_failed")
        throw

    return Result(runName, "cancelling", "accepted", metadata.ProgressChannelUrl)
```

Wariant z publikacją SignalR:

```csharp
try:
    await publisher.PublishAsync(cancellingMetadata)
catch Exception ex:
    log warning
    // Nie cofamy zapisu metadanych i nie blokujemy cancel.
```

## 10) Logowanie
- `Information`:
  - rozpoczęcie anulowania dla znanego runu,
  - zapis statusu `cancelling`,
  - sukces wywołania `ML`,
  - dyspozycje `accepted`, `duplicate`, `already_finished`.
- `Warning`:
  - `not_found` i `not_active` tylko jeśli pojawiają się często albo z podejrzanym `runName`,
  - timeout/niedostępność `ML`,
  - nieudane best-effort publish do SignalR.
- `Error`:
  - błąd zapisu `trainings/metadata`,
  - naruszenie invariantu statusu,
  - błąd serializacji/deserializacji metadanych.
- Nie logować:
  - tokenów administracyjnych,
  - pełnych payloadów z sekretnymi danymi,
  - dużych logów treningowych,
  - pełnych ścieżek w odpowiedziach publicznych.
- W logach można używać `runName`, `status`, `requestDisposition`, HTTP statusu `ML` i krótkiego kodu błędu.

## 11) Workflow GitHub i konfiguracja runtime
- Endpoint wymaga konfiguracji ścieżki `BE -> ML`:
  - lokalnie w `appsettings.local.json` ustawić na sztywno:
    - `MlService.CancelTrainingPathTemplate = "/ml/trainings/{runName}/cancel"`.
  - produkcyjnie w `appsettings.production.json` trzymać placeholder nadpisywany przez workflow:
    - `__SET_BY_GITHUB_VARIABLE_BE_ML_CANCEL_TRAINING_PATH_TEMPLATE__`.
- W `.github/workflows/backend-cd.yml` dodać zmienną:
  - `BE_ML_CANCEL_TRAINING_PATH_TEMPLATE: ${{ vars.BE_ML_CANCEL_TRAINING_PATH_TEMPLATE }}`.
- W walidacji workflow dodać sprawdzenie, że `BE_ML_CANCEL_TRAINING_PATH_TEMPLATE` nie jest puste.
- W kroku generowania `appsettings.production.json` ustawić:

```python
ml_service["CancelTrainingPathTemplate"] = os.environ["BE_ML_CANCEL_TRAINING_PATH_TEMPLATE"]
```

- Przy okazji zweryfikować spójność istniejącego workflow z obecnymi placeholderami dla UC-06:
  - `BE_ML_START_TRAINING_PATH`,
  - `BE_ML_TRAINING_EVENTS_PATH_TEMPLATE`,
  - `BE_TRAINING_DEFAULT_RUN_NAME_PREFIX`,
  - `BE_TRAINING_DEFAULT_MODE`,
  - `BE_TRAINING_DEFAULT_PROFILE_NAME`,
  - `BE_TRAINING_DEFAULT_AUGMENTATION_PROFILE_NAME`,
  - `BE_TRAINING_DEFAULT_BENCHMARK_NAME`,
  - `BE_TRAINING_DEFAULT_SEED`.
- Workflow backendu nie może czyścić ani nadpisywać:
  - `models/registry`,
  - `models/active`,
  - `trainings`,
  - `data`,
  - `examples`.
- Deploy `BE` dostarcza tylko release i `appsettings*.json`; runtime state pozostaje w `/opt/sudoku/shared`.

## 12) Opis przepływu w obrębie BE
1. `FE` wysyła `POST /api/trainings/{runName}/cancel` z tokenem admin.
2. `TrainingsController` binduje `runName` i wysyła `CancelTrainingRunCommand`.
3. Validator sprawdza format `runName`.
4. Handler zakłada lock per `runName`, żeby nie ścigać się z callbackiem `ML`.
5. Handler odczytuje `trainings/metadata/{runName}.json` przez `ITrainingRunsGateway`.
6. Handler wybiera dyspozycję:
   - brak rekordu -> `not_found`,
   - terminalny -> `already_finished`,
   - `cancelling` -> `duplicate`,
   - `starting` -> `start_not_confirmed`,
   - `queued/running` -> właściwe anulowanie.
7. Dla `queued/running` handler zapisuje status `cancelling`.
8. Handler publikuje snapshot do `SignalR` jako informację, że cancel został zainicjowany.
9. Handler wywołuje `IMlTrainingsGateway.CancelTrainingAsync`.
10. Kontroler zwraca `202 Accepted` z `CancelTrainingRunApiResponse`.
11. `ML` kończy job kooperacyjnie i wysyła event `cancelled`.
12. `POST /internal/ml/trainings/{runName}/events` zapisuje status `cancelled`, uruchamia cleanup i publikuje terminalny snapshot.

## 13) Kolejność implementacji kodu dla historyjki
1. Dodać kontrakty i stałe w `Application`: command, result DTO, dispositions, error types, request/response DTO do `ML`.
2. Dodać helpery statusów w `Models/Trainings/TrainingRunStatus.cs`, jeśli będą współdzielone.
3. Rozszerzyć `IMlTrainingsGateway` o `CancelTrainingAsync`.
4. Rozszerzyć `MlServiceOptions` o `CancelTrainingPathTemplate`.
5. Zaimplementować `MlTrainingsHttpClient.CancelTrainingAsync` z mapowaniem błędów spójnym ze startem treningu.
6. Zaimplementować `CancelTrainingRunCommandValidator`.
7. Zaimplementować `CancelTrainingRunCommandHandler` z lockiem per `runName`, idempotencją i zapisem `cancelling`.
8. Dodać `CancelTrainingRunApiResponse`.
9. Dodać akcję w `TrainingsController`.
10. Uzupełnić `appsettings.local.json` i `appsettings.production.json`.
11. Uzupełnić `.github/workflows/backend-cd.yml` o nową zmienną produkcyjną i walidację.
12. Dodać testy jednostkowe handlera i klienta `ML`.
13. Dodać test kontrolera / integration smoke dla autoryzacji i `202`.
14. Uruchomić build/test backendu.

## 14) Guardraile implementacyjne
- Kontroler nie może zawierać logiki workflow ani wywołań `HttpClient`.
- `Application` decyduje o statusach i dyspozycji requestu; `Infrastructure` tylko realizuje storage i HTTP.
- Nie hardcodować ścieżek `/opt/sudoku/...` ani endpointu `ML` w kodzie.
- Nie tworzyć kolejki treningów.
- Nie oznaczać runu jako `cancelled` bez terminalnego eventu `ML -> BE`.
- Nie usuwać metadanych `trainings/metadata/{runName}.json` po anulowaniu.
- Nie usuwać artefaktów w publicznym endpointcie cancel; cleanup zostaje po stronie handlera eventu terminalnego.
- Nie tworzyć nowego, jednorazowego klienta infrastruktury tylko dla cancel; rozszerzyć istniejący `IMlTrainingsGateway`.
- `202 Accepted` dla no-opów jest celowy; nie zmieniać go na `404/409` dla `not_found`, `duplicate` albo `already_finished`.
- `401` pozostaje standardową odpowiedzią dla braku tokenu; nie zwracać `202`, jeśli użytkownik nie jest autoryzowany.
- Publiczne odpowiedzi nie eksponują absolutnych ścieżek systemowych.
- SignalR jest best-effort transportem UI; trwały zapis metadanych ma pierwszeństwo.
- W przypadku wyścigu cancel vs terminalny event nie wolno robić regresji z `succeeded/failed/cancelled` do `cancelling`.

## 15) Zależności pomiędzy historyjkami
- Zależy od `UC-13`, bo endpoint jest chroniony tokenem administracyjnym.
- Zależy od `POST /api/trainings`, bo cancel operuje na rekordzie utworzonym przy starcie.
- Zależy od `GET /api/trainings/active`, bo `FE` może najpierw odzyskać aktywny run i jego `runName`.
- Zależy od `POST /internal/ml/trainings/{runName}/events`, bo końcowe `cancelled` jest potwierdzane eventem z `ML`.
- Zależy od `SignalR /ws/trainings/{runName}`, bo `FE` obserwuje przejście `cancelling -> cancelled`.
- Korzysta z `GET /api/models/registry` i `GET /api/datasets/processed` tylko pośrednio przez workflow startu, nie bezpośrednio w cancel.
- `UC-07` reuse'uje te statusy w UI postępu.
- `UC-08/UC-09` powinny później widzieć metadata runu ze statusem `cancelled` i ewentualnymi `cleanupWarnings`.

## 16) Inne istotne reguły
- `runName` jest jedynym identyfikatorem publicznym; nie dodawać `trainingId`.
- `requestDisposition` jest kontraktem dla `FE`; nie zastępować go samym statusem HTTP.
- `status = null` jest dozwolone tylko dla braku dopasowanego runu.
- `cancel` jest kooperacyjny, więc nie zabija procesu po stronie `BE`. Twarde przerwanie procesu, jeśli kiedykolwiek będzie potrzebne, należy do operacyjnego mechanizmu `ML`, nie publicznego API.
- `ML` może wykonać cleanup własnych uchwytów/procesów, ale biznesowy cleanup artefaktów runtime pozostaje sterowany przez `BE` po evencie terminalnym.
- Jeśli raport końcowy nie powstanie przy anulowaniu, nie jest to błąd. `cancelled` nie wymaga metryk ani modelu wynikowego.
- Częściowo utworzony katalog modelu wynikowego musi zostać usunięty po `cancelled`, ale brak tego katalogu nie powinien psuć finalizacji anulowania.

