# UC-06-BE - Plan implementacyjny dla `SignalR /ws/trainings/{runName}`

## 1) Przeznaczenie endpointa
- Kanał `SignalR /ws/trainings/{runName}` służy do monitorowania postępu konkretnego runu treningowego przez `FE`.
- Kanał jest chroniony tym samym tokenem administracyjnym co `POST /api/trainings`, `GET /api/trainings/active` i pozostałe operacje treningowe.
- Po zestawieniu połączenia `BE` wysyła snapshot aktualnego publicznego stanu runu znanego z `trainings/metadata/{runName}.json`.
- Kolejne komunikaty pochodzą wyłącznie z eventów `ML -> BE` przyjętych przez `POST /internal/ml/trainings/{runName}/events`, zapisanych w metadanych i dopiero potem opublikowanych do `SignalR`.
- Utrata połączenia `SignalR` albo błąd wysyłki do klienta nie zatrzymuje treningu i nie może powodować utraty eventu po stronie `BE`.
- Szczególnie ważne: nawet bez EF i bez transakcji bazodanowej awaria publikacji `SignalR` nie może "zniszczyć pętli zdarzeń". Prawidłowa kolejność to `zapis metadata -> best-effort publish -> ack dla ML`; błąd publishowania jest logowany i ignorowany względem trwałego workflow.

## 2) Zakres i założenia
- Plan opiera się na `PRD`, `UC-06`, dokumentacji deployu/runtime oraz istniejących planach:
  - `GET /api/trainings/active`,
  - `GET /api/models/registry`,
  - `POST /api/trainings`,
  - `POST /internal/ml/trainings/{runName}/events`.
- Nie sugerować się aktualnym stanem `FE` i `ML`; kanał wynika z odpowiedzialności Backendu jako właściciela workflow.
- Backend pozostaje `source of truth`; `SignalR` jest wyłącznie transportem aktualnego snapshotu do `FE`.
- Kanał nie komunikuje się bezpośrednio z `ML`.
- Nie wprowadzamy kolejki, brokera ani EF tylko dla realtime MVP. Źródłem odtworzenia stanu po reconnect jest plik metadata.
- `FE` może ignorować spóźnione komunikaty z niższym `sequence`; `BE` i tak publikuje najnowszy zapisany snapshot.
- Dla runu terminalnego hub może wysłać snapshot terminalny i pozwolić klientowi zamknąć połączenie. Backend nie musi utrzymywać specjalnej sesji po terminalnym snapshotcie.
- Publiczny JSON i payloady SignalR pozostają w `camelCase`; modele wyjściowe dla klienta mają sufiks `ApiResponse`, DTO warstwy aplikacyjnej mają sufiks `Dto`.

## 3) Kontrakty komunikacji FE i ML

### 3.1 FE -> BE (`SignalR /ws/trainings/{runName}`)
- Transport: SignalR WebSocket/Long Polling zgodnie z mechanizmem ASP.NET Core SignalR.
- Route:
  - `/ws/trainings/{runName}`
  - `runName` to nazwa runu utworzona przez `POST /api/trainings`.
- Autoryzacja:
  - preferowane: token administracyjny przekazany przez `accessTokenFactory`;
  - po stronie `BE` `JwtBearerOptions.Events.OnMessageReceived` odczytuje `access_token` tylko dla ścieżek zaczynających się od `/ws/trainings`;
  - nadal można wspierać standardowy nagłówek `Authorization: Bearer ...` dla transportów, które go użyją.
- Body HTTP: brak, połączenie SignalR.
- Query poza `access_token`: brak w MVP.

Przykład po stronie klienta:

```ts
new HubConnectionBuilder()
  .withUrl(`/ws/trainings/${runName}`, {
    accessTokenFactory: () => adminToken
  })
  .withAutomaticReconnect()
  .build()
```

### 3.2 BE -> FE - komunikaty SignalR
- Hub wysyła komunikaty przez nazwane metody klienta:
  - `trainingSnapshot` - wysyłany po `OnConnectedAsync` i opcjonalnie przy reconnect,
  - `trainingEvent` - wysyłany po każdym zaakceptowanym evencie `ML -> BE`.
- Payload obu metod ma ten sam kształt `TrainingRunRealtimeApiResponse`, żeby `FE` mogło traktować snapshot i event jako "najnowszy stan".
- `messageKind` pozwala rozróżnić źródło komunikatu bez zmiany modelu.

Przykład `trainingSnapshot`:

```json
{
  "messageKind": "snapshot",
  "runName": "train-20260429-143000-cnn-mnist-baseline-sudokuDigitsV1",
  "status": "running",
  "createdAtUtc": "2026-04-29T14:30:00Z",
  "updatedAtUtc": "2026-04-29T14:35:00Z",
  "startedAtUtc": "2026-04-29T14:31:10Z",
  "finishedAtUtc": null,
  "baseModelName": "cnn-mnist-baseline",
  "producedModelName": "train-20260429-143000-cnn-mnist-baseline-sudokuDigitsV1",
  "processedDatasetName": "sudokuDigitsV1",
  "trainingMode": "fineTuning",
  "trainingProfileName": "cnn-default-v1",
  "augmentationProfileName": "digits-light-v1",
  "benchmarkName": "sudoku-benchmark-v1",
  "seed": 1234,
  "lastAcceptedSequence": 12,
  "lastEventType": "progress",
  "progress": {
    "percent": 15.0,
    "epoch": 3,
    "totalEpochs": 20,
    "trainLoss": 0.42,
    "validationLoss": 0.51,
    "trainAccuracy": 0.88,
    "validationAccuracy": 0.84
  },
  "metricsSummary": null,
  "reportStatus": null,
  "reportRelativePath": null,
  "warnings": [],
  "cleanupWarnings": [],
  "failureReason": null
}
```

Przykład terminalnego `trainingEvent`:

```json
{
  "messageKind": "event",
  "runName": "train-20260429-143000-cnn-mnist-baseline-sudokuDigitsV1",
  "status": "succeeded",
  "createdAtUtc": "2026-04-29T14:30:00Z",
  "updatedAtUtc": "2026-04-29T15:45:01Z",
  "startedAtUtc": "2026-04-29T14:31:10Z",
  "finishedAtUtc": "2026-04-29T15:45:00Z",
  "baseModelName": "cnn-mnist-baseline",
  "producedModelName": "train-20260429-143000-cnn-mnist-baseline-sudokuDigitsV1",
  "processedDatasetName": "sudokuDigitsV1",
  "trainingMode": "fineTuning",
  "trainingProfileName": "cnn-default-v1",
  "augmentationProfileName": "digits-light-v1",
  "benchmarkName": "sudoku-benchmark-v1",
  "seed": 1234,
  "lastAcceptedSequence": 98,
  "lastEventType": "completed",
  "progress": {
    "percent": 100.0,
    "epoch": 20,
    "totalEpochs": 20,
    "trainLoss": 0.08,
    "validationLoss": 0.13,
    "trainAccuracy": 0.98,
    "validationAccuracy": 0.95
  },
  "metricsSummary": {
    "accuracy": 0.95,
    "macroF1": 0.94
  },
  "reportStatus": "missing",
  "reportRelativePath": null,
  "warnings": ["training_report_missing"],
  "cleanupWarnings": [],
  "failureReason": null
}
```

### 3.3 BE -> ML
- Brak komunikacji `BE -> ML` dla samego kanału `/ws/trainings/{runName}`.
- `BE -> ML` przy starcie treningu nadal przekazuje `callbacks.eventsPath` z `POST /api/trainings`.

### 3.4 ML -> BE
- Brak bezpośredniego wywołania kanału SignalR przez `ML`.
- `ML` raportuje eventy tylko przez `POST /internal/ml/trainings/{runName}/events`.
- Po zapisaniu eventu handler wywołuje `ITrainingRunEventPublisher.PublishAsync(...)`; docelowa implementacja publikuje snapshot do grupy SignalR runu.

## 4) Modele wejściowe i wyjściowe

### 4.1 Wejście FE -> BE
- `runName: string` w ścieżce huba.
- Token admin:
  - `access_token` query string dla WebSocket/SSE,
  - albo standardowy `Authorization` header, jeżeli transport go obsługuje.
- Brak request body.

### 4.2 `TrainingRunRealtimeApiResponse`
- `messageKind: string` - `snapshot` albo `event`.
- `runName: string`.
- `status: string` - `starting`, `queued`, `running`, `cancelling`, `succeeded`, `failed`, `cancelled`.
- `createdAtUtc: DateTimeOffset`.
- `updatedAtUtc: DateTimeOffset | null`.
- `startedAtUtc: DateTimeOffset | null`.
- `finishedAtUtc: DateTimeOffset | null`.
- `baseModelName: string`.
- `producedModelName: string`.
- `processedDatasetName: string`.
- `trainingMode: string`.
- `trainingProfileName: string`.
- `augmentationProfileName: string`.
- `benchmarkName: string`.
- `seed: int`.
- `lastAcceptedSequence: long | null`.
- `lastEventType: string | null`.
- `progress: TrainingRunProgressApiResponse | null`.
- `metricsSummary: TrainingMetricsSummaryApiResponse | null`.
- `reportStatus: string | null`.
- `reportRelativePath: string | null`.
- `warnings: string[]`.
- `cleanupWarnings: string[]`.
- `failureReason: string | null`.

### 4.3 `TrainingRunProgressApiResponse`
- `percent: decimal | null`.
- `epoch: int | null`.
- `totalEpochs: int | null`.
- `trainLoss: decimal | null`.
- `validationLoss: decimal | null`.
- `trainAccuracy: decimal | null`.
- `validationAccuracy: decimal | null`.

### 4.4 Uwagi do kontraktu
- `TrainingRunProgressApiResponse` może reuse'ować strukturę analogiczną do istniejącego `TrainingRunProgressApiEntry`, ale nie powinien używać modelu wejściowego jako modelu wyjściowego.
- `TrainingMetricsSummaryApiResponse` może reuse'ować istniejący model, jeśli został już zdefiniowany jako wyjściowy; jeżeli obecny typ jest wejściowy, dodać osobny response.
- Nie wysyłać do `FE` ścieżek absolutnych, `MlJobId`, katalogów runtime ani tokenów.
- `reportRelativePath` jest referencją logiczną/względną do przyszłych endpointów szczegółów z `UC-09`, nie ścieżką systemową.

## 5) Zachowanie per warstwa

### API (`Sudoku`)
- Rejestruje SignalR (`AddSignalR`) i mapuje hub `MapHub<TrainingRunHub>("/ws/trainings/{runName}")`.
- Rozszerza konfigurację JWT o odczyt tokenu z `access_token` wyłącznie dla ścieżki `/ws/trainings`.
- Hub pozostaje cienki:
  - pobiera `runName` z route values,
  - sprawdza autoryzację przez `[Authorize]`,
  - wywołuje query aplikacyjne o snapshot runu,
  - dołącza connection do grupy runu,
  - wysyła `trainingSnapshot`.
- Hub nie czyta plików bezpośrednio, nie finalizuje modelu, nie mapuje eventów ML i nie decyduje o statusach workflow.
- API zawiera implementację `ITrainingRunEventPublisher` opartą o `IHubContext<TrainingRunHub>`.

### Application (`Application`)
- Dostarcza use-case odczytowy snapshotu runu po `runName`.
- Decyduje, czy run może być monitorowany:
  - run istnieje -> zwraca snapshot,
  - run nie istnieje -> błąd aplikacyjny mapowany w hubie na odrzucenie połączenia,
  - run terminalny -> nadal zwraca snapshot terminalny.
- Utrzymuje port `ITrainingRunEventPublisher` jako abstrakcję publikacji eventów treningowych.
- Handler `RecordTrainingRunEventCommandHandler` musi zapisywać metadata przed publikacją i nie może uzależniać przyjęcia eventu od sukcesu transportu realtime.
- Jeśli obecne wywołanie publishera może rzucić wyjątek po udanym zapisie metadanych, należy je zabezpieczyć w `Application` albo w implementacji publishera tak, aby nie zmieniało wyniku callbacka ML na `500`.

### Domain / Models (`Models`)
- Reuse istniejące neutralne statusy i typy treningu:
  - `Trainings/TrainingRunStatus.cs`,
  - `Trainings/TrainingRunEventType.cs`,
  - `Trainings/TrainingReportStatus.cs`.
- Nie dodawać typów zależnych od SignalR, ASP.NET, `Hub`, `IHubContext` ani kontraktów HTTP do `Models`.
- Jeśli potrzeba wspólnego modelu snapshotu, preferować DTO w `Application/Trainings`, bo jest to publiczny widok use-case'u, nie domenowy byt niezależny od aplikacji.

### Infrastructure (`Infrastructure`)
- Dla samego SignalR nie tworzyć nowej usługi infrastruktury plikowej ani klienta ML.
- Reuse istniejących adapterów:
  - `ITrainingRunsGateway` / `TrainingRunsGateway` do odczytu metadata,
  - `IFileStorageGateway` / `LocalFileStorageGateway` jako generyczne I/O plikowe.
- Jeśli okaże się potrzebny cache albo buforowanie eventów, najpierw opisać port w `Application`, a implementację umieścić w `Infrastructure`; w MVP nie jest to wymagane.
- Nie przenosić implementacji SignalR do `Infrastructure`, bo zależy od warstwy ASP.NET/API i publicznego transportu do `FE`.

## 6) Pliki per warstwa i odpowiedzialności

### API (`src/Backend/Sudoku/Sudoku`)
- `[NOWY]` `Hubs/TrainingRunHub.cs`
  - hub `[Authorize]` dla `/ws/trainings/{runName}`,
  - `OnConnectedAsync`: odczyt `runName`, dołączenie do grupy, pobranie snapshotu przez MediatR, wysłanie `trainingSnapshot`,
  - walidacja braku `runName` jako błąd połączenia.
- `[NOWY]` `Realtime/SignalRTrainingRunEventPublisher.cs`
  - implementacja `ITrainingRunEventPublisher`,
  - mapowanie `TrainingRunMetadataDto` -> `TrainingRunRealtimeApiResponse`,
  - publikacja przez `IHubContext<TrainingRunHub>` do grupy runu,
  - złapanie i zalogowanie wyjątków z SignalR bez rzucania dalej.
- `[NOWY]` `Realtime/TrainingRunHubGroups.cs`
  - centralny helper nazwy grupy, np. `training-run:{runName}`,
  - używany przez hub i publisher, żeby uniknąć rozjazdu stringów.
- `[NOWY]` `Contracts/TrainingRunRealtimeApiResponse.cs`
  - publiczny payload SignalR dla snapshotu i eventu.
- `[NOWY]` `Contracts/TrainingRunProgressApiResponse.cs`
  - publiczny model postępu wysyłany do `FE`, bez sufiksu `Entry`.
- `[MODYFIKACJA/REUSE]` `Contracts/TrainingMetricsSummaryApiResponse.cs`
  - upewnić się, że typ jest sensowny jako response; jeśli obecnie jest używany wyłącznie jako wejście callbacka, rozważyć osobny model wyjściowy.
- `[MODYFIKACJA]` `Configuration/AdminAuthenticationExtensions.cs`
  - dodać `OnMessageReceived`,
  - odczytywać `access_token` tylko gdy `Request.Path.StartsWithSegments("/ws/trainings")`,
  - zachować obecne `OnAuthenticationFailed` i `OnChallenge`.
- `[MODYFIKACJA]` `Program.cs`
  - `builder.Services.AddSignalR()`,
  - rejestracja docelowego publishera SignalR, jeżeli nie trafi do `AddApplication`,
  - `app.MapHub<TrainingRunHub>("/ws/trainings/{runName}")` po `UseAuthorization()`,
  - zostawić kontrolery przez `MapControllers()`, bez minimal API dla endpointów HTTP.
- `[OPCJONALNIE]` `Contracts/ErrorApiResponse.cs`
  - reuse; SignalR nie musi wysyłać tego modelu jako normalnego komunikatu, ale błędy negocjacji/autoryzacji nadal korzystają z istniejącej konfiguracji JWT.

### Application (`src/Backend/Sudoku/Application`)
- `[NOWY]` `Trainings/GetTrainingRunRealtimeSnapshotQuery.cs`
  - query z `RunName`.
- `[NOWY]` `Trainings/GetTrainingRunRealtimeSnapshotQueryHandler.cs`
  - pobiera metadata przez `ITrainingRunsGateway.GetByRunNameAsync`,
  - mapuje na DTO snapshotu,
  - nie czyta filesystem bezpośrednio.
- `[NOWY]` `Trainings/GetTrainingRunRealtimeSnapshotResultDto.cs`
  - wynik query z pełnym publicznym stanem runu.
- `[NOWY]` `Trainings/TrainingRunRealtimeSnapshotDto.cs`
  - DTO snapshotu mapowane w API na `TrainingRunRealtimeApiResponse`.
- `[NOWY]` `Trainings/GetTrainingRunRealtimeSnapshotErrorTypes.cs`
  - np. `training_run_not_found`, `training_run_snapshot_read_failed`.
- `[NOWY]` `Trainings/TrainingRunNotFoundForRealtimeException.cs`
  - czytelny wyjątek aplikacyjny dla nieistniejącego runu.
- `[MODYFIKACJA]` `Trainings/RecordTrainingRunEventCommandHandler.cs`
  - zabezpieczyć wywołanie `ITrainingRunEventPublisher.PublishAsync` przed propagacją błędów transportowych po udanym zapisie metadata,
  - albo wymagać, że implementacja publishera nigdy nie rzuca; bezpieczniejsza opcja to `try/catch` w handlerze z logowaniem przez port/ILogger, jeśli zespół akceptuje logowanie w Application.
- `[MODYFIKACJA]` `Abstractions/ITrainingRunEventPublisher.cs`
  - pozostawić generyczny port publikacji snapshotu,
  - nie dodawać zależności na SignalR ani typy API.
- `[MODYFIKACJA]` `DependencyInjection.cs`
  - usunąć albo warunkowo zastąpić `NoOpTrainingRunEventPublisher`,
  - docelowy binding może być w `Sudoku/Program.cs`, bo implementacja SignalR żyje w API.
- `[REUSE]` `Trainings/TrainingRunMetadataDto.cs`
  - źródło danych snapshotu; nie dodawać do niego pól transportowych typu `messageKind`.
- `[REUSE]` `Trainings/TrainingRunProgressDto.cs`
  - mapowanie do response.
- `[REUSE]` `Trainings/TrainingMetricsSummaryDto.cs`
  - mapowanie do response.

### Domain / Models (`src/Backend/Sudoku/Models`)
- `[REUSE]` `Trainings/TrainingRunStatus.cs`
  - statusy aktywne i terminalne, helper `IsTerminal`.
- `[REUSE]` `Trainings/TrainingRunEventType.cs`
  - wartości `progress`, `statusChanged`, `completed`, `failed`, `cancelled`.
- `[REUSE]` `Trainings/TrainingReportStatus.cs`
  - wartości raportu `ok`, `missing`, `corrupted`.
- `[BRAK NOWYCH PLIKÓW WYMAGANYCH]`
  - SignalR jest transportem API, więc nie tworzyć domenowego `SignalRMessage`, `HubEvent` ani podobnych typów.

### Infrastructure (`src/Backend/Sudoku/Infrastructure`)
- `[REUSE]` `Storage/TrainingRunsGateway.cs`
  - `GetByRunNameAsync` używane przez query snapshotu.
- `[REUSE]` `Storage/LocalFileStorageGateway.cs`
  - generyczne operacje odczytu metadanych.
- `[REUSE]` `DependencyInjection.cs`
  - bez nowego klienta ML i bez nowego adaptera plikowego.
- `[BRAK NOWEGO PLIKU SIGNALR]`
  - implementacja SignalR należy do API, nie do Infrastructure.

### Workflow (`.github/workflows`)
- `[MODYFIKACJA]` `.github/workflows/backend-cd.yml`
  - zwykle brak nowych zmiennych środowiskowych tylko dla SignalR, bo ścieżka `/ws/trainings` jest publicznym routingiem aplikacji.
  - jeśli reverse proxy/nginx jest generowane przez workflow lub skrypt deployowy, dopisać routing websocketów dla `/ws/`.
  - nie zmieniać runtime state w `shared`.
- `[BRAK ZMIAN]` `appsettings.local.json`
  - local ma sztywny `Kestrel.Url` i obecne ścieżki; SignalR nie wymaga osobnych ścieżek plikowych.
  - jeśli dodany będzie dedykowany limit SignalR, np. `Realtime:ClientTimeoutSeconds`, w local wpisać konkretną wartość.
- `[BRAK ZMIAN LUB MAŁA MODYFIKACJA]` `appsettings.production.json`
  - workflow nadal generuje overlay produkcyjny.
  - jeśli pojawi się sekcja `Realtime`, workflow ma ją uzupełniać tak jak inne typed options.

## 7) Weryfikacja usług Infrastructure i antyduplikacja
- Sprawdzone w BE: istnieje `ITrainingRunsGateway.GetByRunNameAsync` oraz implementacja `TrainingRunsGateway`, więc snapshot huba nie potrzebuje nowego readera plików.
- Sprawdzone w BE: istnieje `ITrainingRunEventPublisher` z implementacją `NoOpTrainingRunEventPublisher`; należy podmienić implementację, a nie tworzyć równoległego mechanizmu publikacji poza handlerem eventów.
- Nie tworzyć:
  - `SignalRTrainingMetadataReader`,
  - `TrainingRunDirectoryScanner`,
  - osobnego cache jako drugiego źródła prawdy,
  - klienta HTTP do `ML` na potrzeby snapshotu.
- Jeśli potrzebne są dodatkowe operacje storage, rozszerzyć istniejący `ITrainingRunsGateway` albo `IFileStorageGateway` generycznie, bo te porty będą używane także przez `UC-07/08/09`.

## 8) Przepływ w obrębie BE
1. `FE` uruchamia trening przez `POST /api/trainings` albo odzyskuje aktywny run przez `GET /api/trainings/active`.
2. `FE` bierze `runName` i otwiera `SignalR /ws/trainings/{runName}` z tokenem admin.
3. Middleware JWT waliduje token; dla WebSocket token może pochodzić z query `access_token`.
4. `TrainingRunHub.OnConnectedAsync` pobiera `runName` z route values.
5. Hub wywołuje `GetTrainingRunRealtimeSnapshotQuery(runName)`.
6. Handler pobiera metadata przez `ITrainingRunsGateway.GetByRunNameAsync`.
7. Jeśli metadata istnieje, handler buduje snapshot DTO.
8. Hub dodaje connection do grupy `training-run:{runName}`.
9. Hub wysyła do tej connection `trainingSnapshot`.
10. W trakcie treningu `ML` wysyła event do `POST /internal/ml/trainings/{runName}/events`.
11. `RecordTrainingRunEventCommandHandler` waliduje event, aktualizuje metadata i zapisuje `trainings/metadata/{runName}.json`.
12. Dopiero po udanym zapisie handler woła `ITrainingRunEventPublisher.PublishAsync(nextMetadata)`.
13. `SignalRTrainingRunEventPublisher` mapuje metadata na `TrainingRunRealtimeApiResponse(messageKind = "event")`.
14. Publisher wysyła `trainingEvent` do grupy runu.
15. Jeśli wysyłka SignalR się nie powiedzie, publisher loguje warning i kończy bez wyjątku.
16. Callback `ML -> BE` nadal dostaje `200 OK`, jeśli metadata zostało zapisane poprawnie.
17. Po reconnect `FE` ponownie dostaje snapshot z pliku metadata, więc nie potrzebujemy niezawodnej kolejki komunikatów SignalR w MVP.

## 9) Główne funkcje
- `TrainingRunHub.OnConnectedAsync()`
- `TrainingRunHub.ResolveRunName()`
- `GetTrainingRunRealtimeSnapshotQueryHandler.Handle(...)`
- `ITrainingRunsGateway.GetByRunNameAsync(...)`
- `SignalRTrainingRunEventPublisher.PublishAsync(...)`
- `SignalRTrainingRunEventPublisher.ToRealtimeApiResponse(...)`
- `TrainingRunHubGroups.ForRun(runName)`
- `AdminAuthenticationExtensions.AddAdminAuthentication(...)` z obsługą `OnMessageReceived`
- `Program.cs` rejestrujące `AddSignalR()` i `MapHub<TrainingRunHub>(...)`

## 10) Wyjątki, fallbacki i zachowanie błędowe

### 10.1 Autoryzacja i połączenie
- Brak tokenu albo nieważny token:
  - handshake/negocjacja kończy się `401`,
  - nie wysyłać własnego eventu SignalR z błędem autoryzacji.
- Token wygasły:
  - zgodnie z istniejącą konfiguracją `AdminAuthErrorTypes.AdminTokenExpired`.
- Brak `runName` w ścieżce:
  - hub przerywa połączenie,
  - log `Warning` bez tokenu i bez danych wrażliwych.
- Nieistniejący `runName`:
  - hub nie dołącza klienta do grupy,
  - połączenie może zostać zamknięte po zalogowaniu `Information/Warning`,
  - `FE` powinien odświeżyć stan przez `GET /api/trainings/active`.

### 10.2 Odczyt snapshotu
- Uszkodzony JSON metadata:
  - połączenie nie dostaje snapshotu,
  - log `Error`,
  - nie próbować pytać `ML` o stan, bo `ML` nie jest source of truth.
- Run terminalny:
  - wysłać terminalny snapshot,
  - nie traktować jako błąd.
- Brak aktywnego runu, ale runName wskazuje historyczny terminalny rekord:
  - wysłać snapshot, jeśli metadata istnieje.

### 10.3 Publikacja eventów
- Błąd `IHubContext.Clients.Group(...).SendAsync(...)`:
  - log `Warning`,
  - nie rzucać dalej,
  - nie zmieniać statusu runu,
  - nie powodować `500` w `POST /internal/ml/trainings/{runName}/events`.
- Brak klientów w grupie:
  - to nie jest błąd i nie wymaga logu per event.
- Rozłączenie klienta w trakcie wysyłki:
  - traktować jak normalny błąd transportowy albo no-op.
- Duplikat eventu z `ML`:
  - obsługuje istniejący handler eventów; jeśli metadata nie jest aktualizowana, nie trzeba publikować nowego eventu do SignalR.

### 10.4 Fallbacki
- Jedyny fallback realtime to reconnect klienta i pobranie snapshotu z metadata.
- Brak fallbacku do cache FE jako źródła prawdy.
- Brak fallbacku do `ML`.
- Brak buforowania historii eventów w pamięci w MVP; po reconnect klient widzi najnowszy snapshot, nie pełną historię.

## 11) Specyficzna logika (pseudokod)

### 11.1 Hub connect

```text
onConnected():
  runName = routeValues["runName"]
  if runName is empty:
    logWarning("SignalR training connection without runName")
    abort connection

  snapshot = sender.send(GetTrainingRunRealtimeSnapshotQuery(runName))
  if snapshot not found:
    logInformation("SignalR training connection for unknown run", runName)
    abort connection

  groupName = TrainingRunHubGroups.forRun(runName)
  groups.addToGroup(connectionId, groupName)

  clients.caller.send("trainingSnapshot", map(snapshot, messageKind="snapshot"))
```

### 11.2 Bezpieczne publishowanie po evencie ML

```text
handleMlTrainingEvent(event):
  nextMetadata = applyEvent(event)

  trainingRunsGateway.update(nextMetadata)

  try:
    eventPublisher.publish(nextMetadata)
  catch Exception ex:
    logWarning(ex, "Realtime publish failed after metadata persisted", runName, sequence)
    // Nie wolno rzucić dalej: ML ma dostać ack, bo source-of-truth został zapisany.

  return ack(disposition="accepted", status=nextMetadata.status)
```

### 11.3 Publisher SignalR

```text
publish(metadata):
  response = mapMetadataToRealtimeResponse(metadata, messageKind="event")
  groupName = TrainingRunHubGroups.forRun(metadata.runName)

  try:
    hubContext.clients.group(groupName).sendAsync("trainingEvent", response)
  catch OperationCanceledException when application is stopping:
    logInformation("Realtime publish cancelled by shutdown", metadata.runName)
  catch Exception ex:
    logWarning(ex, "Realtime publish failed", metadata.runName, metadata.lastAcceptedSequence)
```

## 12) Logi
- `Information`:
  - zestawienie połączenia dla poprawnego `runName` bez logowania tokenu,
  - wysłanie snapshotu terminalnego,
  - terminalny event opublikowany do grupy.
- `Debug`:
  - wysłanie zwykłego snapshotu/progress eventu,
  - reconnect klienta, jeśli łatwo wykrywalny.
- `Warning`:
  - brak albo niepoprawny `runName`,
  - próba monitorowania nieistniejącego runu,
  - błąd wysyłki SignalR po zapisaniu metadata.
- `Error`:
  - odczyt/parsing metadata uniemożliwia wysłanie snapshotu,
  - błąd konfiguracji huba albo DI.
- Nie logować:
  - tokenów JWT,
  - query string z `access_token`,
  - pełnych payloadów metryk per event,
  - dużych komunikatów z `ML`.
- Żeby nie spamować dysku:
  - progress eventy logować na `Debug`, nie `Information`,
  - przy błędach publishowania logować runName i sequence, nie pełny snapshot,
  - rozważyć throttling dopiero, jeśli ML zacznie wysyłać bardzo częste eventy.

## 13) Kolejność implementacji kodu
1. Dodać kontrakty response dla realtime (`TrainingRunRealtimeApiResponse`, `TrainingRunProgressApiResponse`, ewentualnie metryki response).
2. Dodać query i DTO snapshotu w `Application/Trainings`.
3. Zaimplementować handler snapshotu z użyciem `ITrainingRunsGateway.GetByRunNameAsync`.
4. Dodać `TrainingRunHubGroups`.
5. Dodać `TrainingRunHub` z `[Authorize]`, `OnConnectedAsync`, grupą i `trainingSnapshot`.
6. Rozszerzyć `AdminAuthenticationExtensions` o `OnMessageReceived` dla `/ws/trainings`.
7. Dodać `SignalRTrainingRunEventPublisher`.
8. Podmienić DI z `NoOpTrainingRunEventPublisher` na publisher SignalR.
9. Zabezpieczyć handler eventów albo publisher przed propagacją błędów wysyłki.
10. Dodać `AddSignalR()` i `MapHub<TrainingRunHub>("/ws/trainings/{runName}")` w `Program.cs`.
11. Uzupełnić testy jednostkowe handlera snapshotu.
12. Uzupełnić testy publishera: błąd SignalR nie rzuca dalej.
13. Uzupełnić test integracyjny/autoryzacyjny dla tokenu query, jeśli projekt ma już wzorzec testów API.
14. Zweryfikować workflow/nginx pod kątem routingu `/ws/` i websocket upgrade.

## 14) Guardraile implementacyjne
- Nie używać minimal API `Map*Endpoints` dla publicznych HTTP endpointów; `MapHub` jest dopuszczalne dla SignalR.
- Nie czytać plików w hubie bezpośrednio.
- Nie publikować do SignalR przed zapisem metadata.
- Nie pozwolić, żeby błąd SignalR zmienił wynik callbacka `ML -> BE` na `500`.
- Nie traktować SignalR jako trwałej kolejki eventów.
- Nie wprowadzać drugiego źródła prawdy w pamięci.
- Nie wysyłać do `FE` ścieżek absolutnych ani technicznych katalogów.
- Nie logować `access_token` z query string.
- Nie tworzyć nowego adaptera plikowego, jeśli wystarcza `ITrainingRunsGateway`.
- Nie przenosić implementacji `IHubContext` do `Application` ani `Infrastructure`.
- Nie używać tokenu admin do endpointu wewnętrznego `ML -> BE`; SignalR jest kanałem `FE -> BE`.
- Nie zmieniać kontraktu eventów `ML -> BE` tylko po to, żeby dopasować UI; realtime mapuje backendowy snapshot.

## 15) Zależności pomiędzy historyjkami
- Wymaga `UC-13`, bo kanał jest chroniony tokenem administracyjnym.
- Wymaga `POST /api/trainings`, bo runName i metadata powstają przy starcie runu.
- Wymaga `GET /api/trainings/active` jako ścieżki odzyskania runu przed połączeniem i po błędach.
- Wymaga `POST /internal/ml/trainings/{runName}/events`, bo to on zasila snapshoty postępem.
- Korzysta z `GET /api/models/registry` i `UC-12` pośrednio przez metadata zapisane przy starcie.
- Jest fundamentem dla `UC-07`, który rozwija UI postępu, ale nie powinien zmieniać transportowego kontraktu `runName`.
- Przygotowuje dane dla `UC-08/UC-09`, bo snapshot realtime ma być zgodny ze stanem później odczytywanym historycznie.
- Jest powiązany z `POST /api/trainings/{runName}/cancel`, bo status `cancelling/cancelled` powinien zostać opublikowany tym samym kanałem.

## 16) Workflow GitHub i runtime
- Backend workflow nadal generuje produkcyjny `appsettings.production.json`; dla SignalR zwykle nie ma nowych ścieżek runtime.
- `appsettings.local.json` nie musi dostać nowych pól, chyba że implementujemy typed options dla realtime timeoutów. Wtedy local zawiera konkretne wartości na sztywno.
- Jeśli produkcyjny nginx jest częścią repo/workflow/skryptów, trzeba upewnić się, że `/ws/` jest proxy do BE z nagłówkami:

```nginx
location /ws/ {
  proxy_pass http://127.0.0.1:5000;
  proxy_http_version 1.1;
  proxy_set_header Upgrade $http_upgrade;
  proxy_set_header Connection "upgrade";
  proxy_set_header Host $host;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto $scheme;
}
```

- Jeśli workflow nie zarządza nginx, opisać tę zmianę w dokumentacji deployu lub zadaniu infrastrukturalnym, nie w `appsettings`.
- Deploy backendu nie może czyścić `shared/trainings`, bo snapshot po reconnect zależy od metadanych zapisanych w runtime.
- `BE` nadal słucha na `127.0.0.1:5000`, a publiczny dostęp idzie przez nginx.

## 17) Testy i weryfikacja
- Unit:
  - `GetTrainingRunRealtimeSnapshotQueryHandler` zwraca snapshot dla istniejącego runu.
  - Handler zwraca błąd/not found dla nieistniejącego runu.
  - Mapowanie progress/metrics/warnings nie gubi pól.
- Unit:
  - `SignalRTrainingRunEventPublisher.PublishAsync` wysyła `trainingEvent` do grupy `training-run:{runName}`.
  - Publisher łapie wyjątek z `SendAsync` i nie rzuca dalej.
- Unit/Application:
  - `RecordTrainingRunEventCommandHandler` po zapisaniu metadata nie zwraca błędu, gdy publisher realtime zawiedzie.
- Integration/API:
  - połączenie bez tokenu jest odrzucane.
  - połączenie z tokenem w `access_token` przechodzi autoryzację.
  - po connect klient dostaje `trainingSnapshot`.
- Manual smoke:
  - uruchomić trening,
  - połączyć klienta z `/ws/trainings/{runName}`,
  - wysłać przykładowy event ML do `/internal/ml/trainings/{runName}/events`,
  - sprawdzić, że klient dostaje `trainingEvent`,
  - rozłączyć klienta, wysłać kolejny event, po reconnect sprawdzić aktualny snapshot.

## 18) Inne istotne reguły
- Nazwy metod SignalR (`trainingSnapshot`, `trainingEvent`) traktować jako część kontraktu FE.
- `runName` w URL musi być walidowany tak samo restrykcyjnie jak w endpointach HTTP, żeby nie pozwalać na dziwne znaki w group name.
- W MVP nie musimy wysyłać osobnego `ping/pong`; SignalR ma własne keep-alive.
- Jeśli później powstanie skalowanie na wiele instancji BE, obecny in-memory SignalR wymaga backplane albo sticky sessions. To poza MVP, ale nie projektować API tak, żeby to blokowało.
- Snapshot powinien być kompletny i samowystarczalny, żeby `FE` po reconnect nie musiało odtwarzać historii eventów.
