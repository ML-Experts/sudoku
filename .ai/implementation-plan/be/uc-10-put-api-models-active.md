# UC-10-BE - Plan implementacyjny dla `PUT /api/models/active`

## 1) Przeznaczenie endpointa
- Endpoint `PUT /api/models/active` pozwala operatorowi administracyjnemu wybrać model używany później w ścieżce inferencji.
- Backend pozostaje `source of truth` dla aktywnego modelu: wybór jest utrwalany jako lekki wskaźnik `models/active/inference.json`.
- Endpoint nie kopiuje katalogu `models/registry/{modelName}` do `models/active` i nie tworzy osobnego rejestru po stronie `FE` ani `ML`.
- Wybór aktywnego modelu ma być możliwy tylko dla wpisu z rejestru, którego manifest jest kompletny, bezpieczny i deklaruje `canUseForInference = true`.

## 2) Zakres i założenia
- Plan dotyczy wyłącznie części BE dla `PUT /api/models/active`.
- Nie opierać kontraktu ani reguł na bieżącej implementacji `FE` lub `ML`; źródłem są `PRD`, `UC-10`, reguły architektury backendu i dokumentacja runtime/deployu.
- Endpoint jest chroniony tokenem administracyjnym z `UC-13`.
- Źródłem walidacji modelu jest `models/registry/{modelName}/model.json`, odczytywany przez istniejący port rejestru modeli.
- Wynikowy stan jest zapisywany w `models/active/inference.json`, w katalogu wskazanym przez `ModelsActiveStorage.ActiveDirectoryPath`.
- Na obecnym stanie repo wiele elementów jest już dodanych po wcześniejszych historyjkach i należy je reużyć, a nie tworzyć równoległe adaptery.

## 3) Kontrakty API FE i ML

### 3.1 FE -> BE (`PUT /api/models/active`)
- Request body: `SetActiveModelApiEntry`.
- Autoryzacja: token administracyjny (`Bearer`).
- Publiczny JSON: `camelCase`.

```json
{
  "modelName": "train-20260503-112233"
}
```

### 3.2 Odpowiedzi publiczne
- `200 OK` -> `ActiveModelApiResponse`.
- `400 Bad Request` -> `ErrorApiResponse`, gdy `modelName` jest pusty albo ma niedozwolony format.
- `401 Unauthorized` -> brak albo niepoprawny token.
- `404 Not Found` -> brak `models/registry/{modelName}/model.json`.
- `409 Conflict` -> model istnieje, ale `canUseForInference = false`.
- `422 Unprocessable Entity` -> manifest albo ścieżka artefaktu są niekompletne lub niebezpieczne.
- `500 Internal Server Error` -> nie udało się zapisać wskaźnika albo wystąpił błąd I/O.

### 3.3 Model wejściowy/wyjściowy FE
- Wejście FE -> BE:
  - `SetActiveModelApiEntry`
  - `modelName: string`
- Wyjście BE -> FE:
  - `ActiveModelApiResponse`
  - `modelName: string`
  - `displayName: string`
  - `sourceType: string`
  - `sourceRunName: string | null`
  - `parentModelName: string | null`
  - `inputProfile: string`
  - `canUseForInference: boolean`
  - `activatedAtUtc: string`

Przykład:

```json
{
  "modelName": "train-20260503-112233",
  "displayName": "train-20260503-112233",
  "sourceType": "training",
  "sourceRunName": "train-20260503-112233",
  "parentModelName": "cnn-bootstrap",
  "inputProfile": "default-28x28-v1",
  "canUseForInference": true,
  "activatedAtUtc": "2026-05-03T11:05:00Z"
}
```

### 3.4 BE <-> ML dla tego endpointa
- `PUT /api/models/active` nie powinien dodawać nowej publicznej komunikacji `FE -> ML`.
- W MVP nie jest wymagany osobny call `BE -> ML`, jeśli `ML` przeładowuje model przez odczyt wskaźnika przy kolejnej inferencji albo własny mechanizm hot reload.
- Kontraktem współdzielonym z `ML` jest plik `models/active/inference.json`:

```json
{
  "modelName": "train-20260503-112233",
  "registryRelativePath": "../registry/train-20260503-112233",
  "setBy": "backend",
  "updatedAtUtc": "2026-05-03T11:05:00Z"
}
```

- Jeśli później powstanie jawny endpoint reload po stronie `ML`, dodać go jako osobną decyzję kontraktową i port w `Application`; nie zaszywać klienta ML bezpośrednio w kontrolerze.

## 4) Zachowanie per warstwa

### API (`Sudoku`)
- Cienki kontroler:
  - wymusza `[Authorize]`,
  - bindowanie `SetActiveModelApiEntry`,
  - utworzenie `SetActiveModelCommand`,
  - wywołanie MediatR,
  - mapowanie DTO aplikacyjnego na `ActiveModelApiResponse`,
  - mapowanie wyjątków na `ErrorApiResponse`.
- Brak parsowania `model.json`, brak operacji `File.*` / `Directory.*`, brak decyzji capability w kontrolerze.

### Application (`Application`)
- Właściwa logika use-case'u:
  - walidacja `modelName` przez FluentValidation,
  - pobranie manifestu z `IModelsRegistryGateway.GetByNameAsync`,
  - odrzucenie braku modelu,
  - sprawdzenie `canUseForInference`,
  - sprawdzenie minimalnych pól manifestu wymaganych do aktywacji,
  - sprawdzenie, że `PrimaryArtifactRelativePath` jest względny i bez path traversal,
  - zbudowanie `ActiveModelPointerDto`,
  - zapis przez `IActiveModelPointerGateway.ReplaceAsync`,
  - zwrot publicznie bezpiecznego DTO do API.
- Application decyduje, czy model można aktywować. Infrastructure tylko dostarcza manifest i zapisuje wskaźnik.

### Domain / Models (`Models`)
- Dla tego endpointa nie trzeba dodawać nowego modelu domenowego.
- Reużyć istniejące neutralne modele, jeśli są potrzebne do wspólnej semantyki statusów lub raportów, ale nie przenosić kontraktów HTTP do `Models`.
- Jeśli capability modeli rozrośnie się w kilku use-case'ach, dopiero wtedy rozważyć neutralny model domenowy, np. `Models/ModelsRegistry/ModelCapability`.

### Infrastructure (`Infrastructure`)
- Implementuje techniczne porty:
  - `IModelsRegistryGateway` odczytuje manifesty z `models/registry`,
  - `IActiveModelPointerGateway` zapisuje `models/active/inference.json`,
  - `IFileStorageGateway` wykonuje generyczne operacje storage.
- Infrastructure nie decyduje, czy model biznesowo wolno aktywować; może wykryć techniczne niespójności manifestu i artefaktów.
- Nie dodawać dedykowanych helperów typu `ActiveModelFileWriter` ani bezpośredniego zapisu pliku w `Application`.

## 5) Pliki per warstwa i odpowiedzialności

### API (`src/Backend/Sudoku/Sudoku`)
- `[REUSE/UTWARDZENIE]` `Controllers/ModelsController.cs`
  - akcja `SetActiveAsync` dla `PUT /api/models/active`,
  - `[Authorize]`, `[HttpPut("active")]`,
  - mapowanie `SetActiveModelCommandResultDto` -> `ActiveModelApiResponse`,
  - mapowanie wyjątków na `400`, `404`, `409`, `422`, `500`,
  - lekkie logi rozpoczęcia, sukcesu i błędów.
- `[REUSE]` `Contracts/SetActiveModelApiEntry.cs`
  - publiczny model wejściowy z `ModelName`.
- `[REUSE]` `Contracts/ActiveModelApiResponse.cs`
  - publiczny model odpowiedzi po ustawieniu aktywnego modelu.
- `[REUSE]` `Contracts/ErrorApiResponse.cs`
  - wspólny model błędu HTTP `errorType`, `message`.
- `[REUSE]` `Program.cs`
  - bind i walidacja `ModelsRegistryStorageOptions` oraz `ModelsActiveStorageOptions`,
  - rejestracja kontrolerów, autoryzacji i MediatR.
- `[REUSE]` `appsettings.local.json`
  - lokalna, absolutna ścieżka `ModelsActiveStorage.ActiveDirectoryPath`.
- `[REUSE]` `appsettings.production.json`
  - placeholder `ModelsActiveStorage.ActiveDirectoryPath` podstawiany przez workflow.

### Application (`src/Backend/Sudoku/Application`)
- `[REUSE]` `ModelsActive/SetActiveModelCommand.cs`
  - komenda MediatR z `ModelName`.
- `[REUSE/UTWARDZENIE]` `ModelsActive/SetActiveModelCommandValidator.cs`
  - walidacja niepustej nazwy, długości i zakazu separatorów ścieżek / znaków kontrolnych.
- `[REUSE/UTWARDZENIE]` `ModelsActive/SetActiveModelCommandHandler.cs`
  - orkiestracja całego use-case'u ustawienia aktywnego modelu.
- `[REUSE]` `ModelsActive/SetActiveModelCommandResultDto.cs`
  - wynik use-case'u mapowany potem na API.
- `[REUSE]` `ModelsActive/ActiveModelPointerDto.cs`
  - aplikacyjny model plikowego wskaźnika.
- `[REUSE]` `ModelsActive/ModelsActiveStorageOptions.cs`
  - typed options dla katalogu `models/active`.
- `[REUSE]` `ModelsActive/SetActiveModelErrorTypes.cs`
  - stałe `errorType`.
- `[REUSE]` `ModelsActive/ActiveModelNotFoundException.cs`
  - brak wpisu w rejestrze.
- `[REUSE]` `ModelsActive/ActiveModelCannotUseForInferenceException.cs`
  - model z `canUseForInference = false`.
- `[REUSE]` `ModelsActive/ActiveModelManifestInvalidException.cs`
  - manifest niekompletny, niespójny albo niebezpieczny.
- `[REUSE]` `ModelsActive/ActiveModelPointerWriteException.cs`
  - opakowanie błędów zapisu wskaźnika.
- `[REUSE]` `Abstractions/IActiveModelPointerGateway.cs`
  - port zapisu wskaźnika aktywnego modelu.
- `[REUSE]` `Abstractions/IModelsRegistryGateway.cs`
  - port odczytu manifestu przez `GetByNameAsync`.
- `[REUSE]` `ModelsRegistry/RegistryModelManifestDto.cs`
  - DTO manifestu modelu używane do walidacji aktywacji.

### Domain / Models (`src/Backend/Sudoku/Models`)
- `[BRAK NOWEGO PLIKU]`
  - dla `PUT /api/models/active` obecne DTO aplikacyjne wystarczają.
- `[REUSE POŚREDNI]` istniejące modele treningów, np. `Models/Trainings/TrainingRunStatus.cs`
  - nie są bezpośrednio używane przez endpoint, ale rejestr modeli i metadane treningów muszą pozostać semantycznie spójne z UC-06/UC-08/UC-09.

### Infrastructure (`src/Backend/Sudoku/Infrastructure`)
- `[REUSE]` `Storage/ActiveModelPointerGateway.cs`
  - serializacja `ActiveModelPointerDto` przez `JsonSerializerDefaults.Web`,
  - zapis `inference.json` w `ModelsActiveStorage.ActiveDirectoryPath`,
  - użycie `IFileStorageGateway.ReplaceAsync`.
- `[REUSE]` `Storage/ModelsRegistryGateway.cs`
  - `GetByNameAsync(modelName)` odczytuje `models/registry/{modelName}/model.json`,
  - waliduje spójność nazwy manifestu z katalogiem,
  - sprawdza techniczną kompletność `artifacts/` i głównego artefaktu,
  - zwraca `RegistryModelManifestDto`.
- `[REUSE]` `Storage/LocalFileStorageGateway.cs`
  - generyczne operacje plikowe, w tym odczyt, listowanie i atomowy/bezpieczny replace, zależnie od istniejącego kontraktu.
- `[REUSE]` `DependencyInjection.cs`
  - rejestracja `IModelsRegistryGateway -> ModelsRegistryGateway`,
  - rejestracja `IActiveModelPointerGateway -> ActiveModelPointerGateway`,
  - rejestracja `IFileStorageGateway -> LocalFileStorageGateway`.
- `[BRAK ZMIAN]` `Ml/*`
  - ten endpoint nie wymaga nowego klienta ML, dopóki kontrakt reload nie zostanie jawnie ustalony.

### Workflow (`.github/workflows`)
- `[REUSE/ZWERYFIKOWAĆ]` `.github/workflows/backend-cd.yml`
  - workflow ma już zmienną `BE_MODELS_ACTIVE_DIRECTORY_PATH`,
  - waliduje jej obecność,
  - podstawia ją do `ModelsActiveStorage.ActiveDirectoryPath`,
  - nie powinien czyścić ani nadpisywać `models/active` jako części zwykłego release'u.

## 6) Weryfikacja usług Infrastructure i antyduplikacja
- Istnieje `IActiveModelPointerGateway` oraz `ActiveModelPointerGateway`; używać ich jako jedynego adaptera zapisu wskaźnika.
- Istnieje `IModelsRegistryGateway` oraz `ModelsRegistryGateway`; nie tworzyć osobnego `ActiveModelManifestReader`.
- Istnieje `IFileStorageGateway` oraz `LocalFileStorageGateway`; nie używać `File.WriteAllText`, `Directory.CreateDirectory` ani `JsonDocument` poza adapterem infrastrukturalnym.
- Jeśli zapis wskaźnika wymaga poprawy atomowości, rozszerzyć generycznie `IFileStorageGateway.ReplaceAsync`, aby mogły skorzystać z tego także inne use-case'y zapisujące pliki JSON.
- Jeśli później dojdzie odczyt aktywnego modelu (`GET /api/models/active`), rozważyć rozszerzenie `IActiveModelPointerGateway` o `GetAsync`, zamiast tworzyć drugi reader tego samego pliku.

## 7) Przepływ w obrębie BE
1. `FE` wysyła `PUT /api/models/active` z tokenem admin i `modelName`.
2. Middleware autoryzacji weryfikuje token z `UC-13`.
3. `ModelsController.SetActiveAsync` tworzy `SetActiveModelCommand`.
4. Pipeline FluentValidation uruchamia `SetActiveModelCommandValidator`.
5. Handler normalizuje `modelName` przez `Trim`.
6. Handler wywołuje `IModelsRegistryGateway.GetByNameAsync(modelName)`.
7. `ModelsRegistryGateway` odczytuje `models/registry/{modelName}/model.json` i sprawdza techniczną kompletność manifestu.
8. Handler sprawdza `canUseForInference` oraz minimalne pola wymagane do aktywacji.
9. Handler buduje `ActiveModelPointerDto` z `setBy = backend`, `updatedAtUtc` i względnym `registryRelativePath`.
10. Handler zapisuje wskaźnik przez `IActiveModelPointerGateway.ReplaceAsync`.
11. `ActiveModelPointerGateway` zapisuje `inference.json` w katalogu `models/active`.
12. Kontroler zwraca `ActiveModelApiResponse`.
13. Kolejna inferencja używa modelu wskazanego przez `models/active/inference.json`; `FE` nie przechowuje własnego źródła prawdy.

## 8) Główne funkcje
- `ModelsController.SetActiveAsync(...)`
- `SetActiveModelCommandValidator.ValidateModelName(...)`
- `SetActiveModelCommandHandler.Handle(...)`
- `SetActiveModelCommandHandler.ResolveModelAsync(...)`
- `SetActiveModelCommandHandler.EnsureCanUseForInference(...)`
- `SetActiveModelCommandHandler.EnsureActivatableManifest(...)`
- `SetActiveModelCommandHandler.ReplacePointerAsync(...)`
- `IModelsRegistryGateway.GetByNameAsync(...)`
- `ModelsRegistryGateway.GetByNameAsync(...)`
- `IActiveModelPointerGateway.ReplaceAsync(...)`
- `ActiveModelPointerGateway.ReplaceAsync(...)`
- `IFileStorageGateway.ReplaceAsync(...)`

## 9) Wyjątki, fallbacki i zachowanie błędowe

### 9.1 Publiczne statusy
- `200 OK`:
  - model istnieje,
  - manifest jest aktywowalny,
  - wskaźnik został zapisany.
- `400 Bad Request`:
  - brak body lub `modelName`,
  - `modelName` puste,
  - `modelName` za długie,
  - `modelName` zawiera separator ścieżki, path traversal, `:` albo znaki kontrolne.
- `401 Unauthorized`:
  - brak albo niepoprawny token administracyjny.
- `404 Not Found`:
  - brak wpisu `models/registry/{modelName}/model.json`.
- `409 Conflict`:
  - manifest istnieje, ale `canUseForInference = false`.
- `422 Unprocessable Entity`:
  - manifest nie zawiera wymaganych pól,
  - `primaryArtifactRelativePath` jest pusty, absolutny albo zawiera `..`,
  - manifest ma ostrzeżenia blokujące aktywację, np. brak artefaktu.
- `500 Internal Server Error`:
  - błąd zapisu `models/active/inference.json`,
  - brak uprawnień do katalogu active,
  - błąd I/O lub niespodziewana niespójność storage.

### 9.2 Fallbacki
- Brak fallbacku do `FE`.
- Brak fallbacku do cache.
- Brak fallbacku do `ML`.
- Brak fallbacku do poprzedniego aktywnego modelu w odpowiedzi. Jeśli zapis nowego wskaźnika się nie uda, endpoint zwraca błąd i nie deklaruje sukcesu.
- Nie tworzyć automatycznie modelu bootstrap przy żądaniu `PUT`; bootstrap rejestru jest osobnym krokiem operacyjnym z `INF-08`.

### 9.3 Scenariusze graniczne
- Ponowne ustawienie tego samego `modelName`:
  - traktować jako idempotentny sukces i odświeżyć `updatedAtUtc`.
- Model bootstrap bez `sourceRunName`:
  - poprawny, jeśli manifest deklaruje `canUseForInference = true` i ma kompletne artefakty.
- Model po treningu z brakującym raportem:
  - nie blokować aktywacji, jeśli manifest i artefakty inferencyjne są kompletne.
- Model z brakującym głównym artefaktem:
  - odrzucić jako `422` albo jako manifest invalid, bo capability inferencyjne byłoby fałszywe.
- Uszkodzony JSON manifestu:
  - nie aktywować; mapować na błąd manifestu albo błąd techniczny zgodnie z tym, gdzie wyjątek zostanie złapany.
- Częściowy zapis `inference.json`:
  - nie może być akceptowany jako sukces; preferowany zapis przez temp file + replace w generycznym storage, jeśli obecny adapter tego nie gwarantuje.

## 10) Pseudokod specyficznej logiki

```c#
handleSetActiveModel(command):
  ensure command was validated

  modelName = trim(command.modelName)
  model = modelsRegistryGateway.getByName(modelName)

  if model is null:
    throw ActiveModelNotFoundException(modelName)

  if model.canUseForInference is false:
    throw ActiveModelCannotUseForInferenceException(modelName)

  ensureActivatableManifest(model)

  now = timeProvider.getUtcNow()
  pointer = ActiveModelPointerDto(
    modelName = model.name,
    registryRelativePath = "../registry/" + model.name,
    setBy = "backend",
    updatedAtUtc = now
  )

  activeModelPointerGateway.replace(pointer)

  return SetActiveModelCommandResultDto(
    modelName = model.name,
    displayName = model.displayName,
    sourceType = model.sourceType,
    sourceRunName = model.sourceRunName,
    parentModelName = model.parentModelName,
    inputProfile = model.inputProfile,
    canUseForInference = model.canUseForInference,
    activatedAtUtc = now
  )
```

```c#
ensureActivatableManifest(model):
  require model.name
  require model.displayName
  require model.sourceType
  require model.inputProfile
  require model.primaryArtifactRelativePath

  if primaryArtifactRelativePath is rooted:
    throw ActiveModelManifestInvalidException

  if primaryArtifactRelativePath contains ".." segment:
    throw ActiveModelManifestInvalidException

  if warnings contain artifact problem:
    throw ActiveModelManifestInvalidException
```

## 11) Workflow GitHub i konfiguracja runtime
- Lokalnie:
  - `appsettings.local.json` ma mieć twardo ustawioną absolutną ścieżkę `ModelsActiveStorage.ActiveDirectoryPath`, np. `/home/wojtek/projects/sudoku/data/models/active`.
  - katalog lokalny jest runtime state i nie powinien być wersjonowany jako stan aktywnego modelu.
- Produkcyjnie:
  - `appsettings.production.json` zawiera placeholder `ModelsActiveStorage.ActiveDirectoryPath`.
  - `.github/workflows/backend-cd.yml` podstawia `BE_MODELS_ACTIVE_DIRECTORY_PATH` podczas przygotowania release'u.
  - wartość produkcyjna powinna wskazywać trwały katalog współdzielony, np. odpowiednik `/opt/sudoku/shared/models/active`, ale ścieżka nie może być hardcodowana w kodzie.
- Deploy:
  - workflow BE publikuje aplikację i appsettings,
  - deploy nie czyści `models/active`, `models/registry`, `trainings`, `data` ani `examples`,
  - bootstrap pierwszego aktywnego modelu pozostaje osobnym krokiem operacyjnym, nie skutkiem zwykłego deployu BE.
- Aktualny `backend-cd.yml` ma już `BE_MODELS_ACTIVE_DIRECTORY_PATH`; przy implementacji tylko zweryfikować, czy zmienna jest ustawiona w GitHub Environment.

## 12) Logging
- Cel: ułatwić diagnozę nieudanej aktywacji bez spamowania i bez ujawniania ścieżek lub manifestów.
- `Information`:
  - rozpoczęto ustawianie aktywnego modelu z `ModelName`,
  - zapisano aktywny wskaźnik modelu z `ModelName`.
- `Warning`:
  - model nie istnieje,
  - model ma `canUseForInference = false`,
  - manifest jest nieaktywowalny.
- `Error`:
  - nie udało się zapisać wskaźnika,
  - błąd I/O, uprawnień lub storage przy aktywacji.
- Guardrail:
  - nie logować pełnej treści `model.json`,
  - nie logować tokenów,
  - nie zwracać absolutnych ścieżek w `ErrorApiResponse`,
  - używać `modelName` i `errorType` jako głównego kontekstu diagnostycznego.

## 13) Kolejność implementacji kodu dla historyjki
1. Zweryfikować istniejące pliki `ModelsActive/*`, `IActiveModelPointerGateway`, `ActiveModelPointerGateway`, `ModelsController.SetActiveAsync`.
2. Sprawdzić, czy `SetActiveModelCommandValidator` blokuje wszystkie niedozwolone warianty `modelName`.
3. Sprawdzić, czy `SetActiveModelCommandHandler` używa `IModelsRegistryGateway.GetByNameAsync` i nie odczytuje plików bezpośrednio.
4. Sprawdzić, czy handler odrzuca `canUseForInference = false`.
5. Sprawdzić, czy handler odrzuca manifest z pustym lub niebezpiecznym `PrimaryArtifactRelativePath`.
6. Sprawdzić, czy `ActiveModelPointerGateway` zapisuje wyłącznie `inference.json` w katalogu z `ModelsActiveStorageOptions`.
7. Zweryfikować `Program.cs`: `ModelsActiveStorageOptions` jest zbindowane, waliduje absolutną ścieżkę i ma `ValidateOnStart`.
8. Zweryfikować `appsettings.local.json` i `appsettings.production.json` dla `ModelsActiveStorage`.
9. Zweryfikować `.github/workflows/backend-cd.yml`, czy waliduje i podstawia `BE_MODELS_ACTIVE_DIRECTORY_PATH`.
10. Dodać testy jednostkowe walidatora: pusty `modelName`, separator ścieżki, `..`, za długa nazwa, poprawna nazwa.
11. Dodać testy handlera: sukces, brak modelu, `canUseForInference = false`, brak artefaktu, path traversal w artefakcie, błąd zapisu wskaźnika.
12. Dodać testy gatewaya wskaźnika: zapisuje `inference.json` w `camelCase`, używa `setBy = backend`, nie zapisuje pełnego manifestu.
13. Dodać testy API/integracyjne: `200`, `400`, `401`, `404`, `409`, `422`, `500`.

## 14) Guardraile implementacyjne
- Kontroler ma pozostać cienki; żadnego filesystem, parserów JSON manifestu ani reguł capability w `Api`.
- `Application` zawiera logikę use-case'u; nie implementuje adapterów plikowych.
- `Infrastructure` implementuje storage i klienty zewnętrzne, ale nie decyduje o regułach aktywacji poza techniczną spójnością odczytu.
- Nie dodawać minimal API `MapPut`; używać kontrolera ASP.NET.
- Nie hardcodować `/opt/sudoku/...` ani lokalnych ścieżek w kodzie.
- Nie kopiować katalogu `models/registry/{modelName}` do `models/active`.
- Nie zwracać do `FE` ścieżek systemowych, `primaryArtifactRelativePath` ani pełnego manifestu.
- Nie tworzyć bazy danych ani cache dla aktywnego modelu.
- Nie traktować filtrowania w `FE` jako walidacji bezpieczeństwa.
- Zachować `camelCase`, `ApiEntry`, `ApiResponse`, `Dto` i `ErrorApiResponse`.

## 15) Zależności pomiędzy historyjkami
- Wejściowe:
  - `UC-13` - autoryzacja endpointu tokenem administracyjnym.
  - `INF-08` - standard manifestów i bootstrap rejestru modeli.
  - `UC-06 GET /api/models/registry` - źródło listy modeli oraz `IModelsRegistryGateway`.
  - `UC-06 POST /api/trainings` - tworzy modele wynikowe w `models/registry`.
  - `UC-08` / `UC-09` - dostarczają kontekst metryk i porównania modeli, które pomagają operatorowi wybrać model.
- Równoległe / konsumujące:
  - `GET /api/models/active` z `UC-10` - odczyt bieżącego wskaźnika, jeśli jest implementowany jako osobny endpoint.
  - `UC-05` - inferencja powinna używać modelu wskazanego przez `models/active/inference.json`.
  - `ML UC-10` - mechanizm hot reload albo reload przy inferencji po stronie ML korzysta z tego samego wskaźnika.

## 16) Inne istotne reguły
- `modelName` jest publicznym identyfikatorem wpisu rejestru i musi odpowiadać nazwie katalogu.
- `registryRelativePath` w `inference.json` jest informacyjne; komponenty powinny rozwiązywać model względem skonfigurowanego katalogu rejestru.
- Brak raportu treningowego nie blokuje aktywacji, jeśli manifest i artefakty inferencyjne są kompletne.
- Model archiwalny może pozostać w rejestrze, ale jeśli `canUseForInference = false`, endpoint musi go odrzucić.
- Aktywacja modelu nie zmienia manifestu rejestru ani metadanych treningu.
- `activatedAtUtc` w odpowiedzi odpowiada czasowi zapisu wskaźnika, a nie czasowi utworzenia modelu.
- Ponowienie tego samego żądania jest dozwolone i powinno zakończyć się sukcesem, jeśli stan rejestru nadal jest poprawny.

## 17) Model API wejściowy i wyjściowy w komunikacji z FE i ML
- FE -> BE:
  - `PUT /api/models/active`
  - `SetActiveModelApiEntry`
  - `modelName`.
- BE -> FE:
  - `ActiveModelApiResponse`,
  - `ErrorApiResponse` dla błędów.
- BE -> ML:
  - brak nowego HTTP call w MVP dla tego endpointa.
  - wspólny kontrakt runtime to zapisany plik `models/active/inference.json`.
- ML -> BE:
  - brak komunikacji inicjowanej przez ten endpoint.
  - przy późniejszej inferencji ML powinien użyć wskaźnika i manifestu rejestru, a nie własnego publicznego wyboru aktywnego modelu.
- Plikowe kontrakty wejściowe dla BE:
  - `models/registry/{modelName}/model.json`,
  - `models/registry/{modelName}/{primaryArtifactRelativePath}`.
- Plikowy kontrakt wyjściowy BE:
  - `models/active/inference.json`.

