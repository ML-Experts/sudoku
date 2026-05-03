# UC-10-BE - Plan implementacyjny dla `GET /api/models/active`

## 1) Przeznaczenie endpointa
- Endpoint `GET /api/models/active` zwraca aktualnie wybrany model inferencyjny, aby `FE` mogło zaznaczyć bieżący wybór na ekranie modeli.
- Backend pozostaje `source of truth`: odczyt bazuje na lekkim wskaźniku `models/active/inference.json` oraz manifeście `models/registry/{modelName}/model.json`.
- Endpoint niczego nie zapisuje, nie tworzy fallbackowego modelu i nie pyta `ML` o aktywny stan.
- Jeśli wskaźnik nie istnieje, endpoint zwraca `204 No Content`, bo brak aktywnego modelu jest stanem bootstrapowym albo awaryjnym, ale nie błędem odczytu samego endpointa.

## 2) Zakres i założenia
- Plan dotyczy wyłącznie części BE dla `GET /api/models/active`.
- Nie sugerować się bieżącą implementacją `FE` ani `ML`; źródłem kontraktu są `PRD`, `UC-10`, istniejące kontrakty UC-06/UC-08/UC-09/UC-13 oraz zasady architektury backendu.
- Endpoint jest chroniony tokenem administracyjnym z `UC-13`, tak samo jak `GET /api/models/registry` i `PUT /api/models/active`.
- Nie zmieniać istniejących nazw klas i pól dodanych dla `PUT /api/models/active`: `ActiveModelApiResponse`, `SetActiveModelApiEntry`, `SetActiveModelCommand*`, `ActiveModelPointerDto`, `ModelsActiveStorageOptions`.
- Reużyć istniejące porty i adaptery:
  - `IActiveModelPointerGateway` / `ActiveModelPointerGateway`,
  - `IModelsRegistryGateway` / `ModelsRegistryGateway`,
  - `IFileStorageGateway` / `LocalFileStorageGateway`.
- Dodać tylko brakujące elementy do odczytu wskaźnika i orkiestracji query; nie tworzyć równoległego readera pliku aktywnego modelu.

## 3) Kontrakty API FE i ML

### 3.1 FE -> BE (`GET /api/models/active`)
- Request body: brak.
- Autoryzacja: token administracyjny (`Bearer`).
- Publiczny JSON: `camelCase`.

### 3.2 Odpowiedzi publiczne
- `200 OK` -> `ActiveModelApiResponse`, jeśli wskaźnik istnieje i wskazuje poprawny, nadal aktywowalny model.
- `204 No Content` -> brak pliku `models/active/inference.json`.
- `401 Unauthorized` -> brak albo niepoprawny token.
- `409 Conflict` -> wskaźnik istnieje, ale jest niespójny: ma niepoprawny `modelName`, wskazuje brakujący model, model ma `canUseForInference = false` albo manifest/artefakt nie pozwala na inferencję.
- `500 Internal Server Error` -> błąd odczytu storage, uprawnień albo niespodziewany błąd I/O.
- Wszystkie błędy zwracają `ErrorApiResponse` z polami `errorType` i `message`.

### 3.3 Model wyjściowy FE
- Wyjście BE -> FE:
  - `ActiveModelApiResponse`,
  - `modelName: string`,
  - `displayName: string`,
  - `sourceType: string`,
  - `sourceRunName: string | null`,
  - `parentModelName: string | null`,
  - `inputProfile: string`,
  - `canUseForInference: boolean`,
  - `activatedAtUtc: string`.

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
- `GET /api/models/active` nie dodaje nowej komunikacji `BE -> ML`.
- `ML` nie jest źródłem prawdy dla aktywnego modelu; wspólnym kontraktem runtime pozostaje plik `models/active/inference.json`.
- Endpoint nie powinien wykonywać "ping/reload" do ML ani zwracać stanu pamięci procesu ML. Jeśli w przyszłości będzie potrzebna diagnostyka reloadu modelu, powinna powstać osobna historyjka/endpoint techniczny.

### 3.5 Plikowy kontrakt wejściowy
`models/active/inference.json`:

```json
{
  "modelName": "train-20260503-112233",
  "registryRelativePath": "../registry/train-20260503-112233",
  "setBy": "backend",
  "updatedAtUtc": "2026-05-03T11:05:00Z"
}
```

Reguły:
- `modelName` jest jedynym wymaganym identyfikatorem biznesowym.
- `registryRelativePath` jest informacyjne i nie powinno sterować odczytem rejestru po stronie BE.
- `updatedAtUtc` mapujemy na `activatedAtUtc`.
- Dla plików bootstrapowych bez `updatedAtUtc` można rozważyć fallback na `LastModifiedUtc` pliku, ale lepszy kontrakt BE to wymagać `updatedAtUtc` po zapisie przez `PUT`. Jeśli obecny bootstrap operacyjny może nie mieć daty, decyzję opisać jawnie w testach i nie ukrywać uszkodzonego wskaźnika jako sukcesu.

## 4) Zachowanie per warstwa

### API (`Sudoku`)
- Cienki kontroler:
  - wymusza `[Authorize]`,
  - obsługuje `[HttpGet("active")]`,
  - wywołuje `GetActiveModelQuery` przez MediatR,
  - zwraca `204`, jeśli query nie znalazło wskaźnika,
  - mapuje DTO aplikacyjne na istniejący `ActiveModelApiResponse`,
  - mapuje wyjątki na `ErrorApiResponse`.
- Brak `File.*`, `Directory.*`, parsowania JSON wskaźnika albo manifestu w kontrolerze.

### Application (`Application`)
- Właściwa logika use-case'u:
  - odczyt aktywnego wskaźnika przez `IActiveModelPointerGateway.GetAsync`,
  - jeśli wskaźnika nie ma, zwrot wyniku `HasActiveModel = false`,
  - walidacja `modelName` z pliku wskaźnika tak samo restrykcyjna jak przy `PUT`,
  - pobranie manifestu przez `IModelsRegistryGateway.GetByNameAsync`,
  - sprawdzenie, czy model nadal istnieje i `canUseForInference = true`,
  - sprawdzenie minimalnej kompletności manifestu oraz bezpiecznej ścieżki artefaktu,
  - zwrot publicznie bezpiecznego DTO do API.
- Application decyduje, czy aktualny wskaźnik jest biznesowo poprawny. Infrastructure tylko odczytuje plik i manifest.

### Domain / Models (`Models`)
- Dla tego endpointa nie dodawać nowego modelu domenowego.
- Rejestr i aktywny model są na obecnym etapie plikowymi rekordami systemowymi obsługiwanymi przez DTO w `Application`.
- Jeśli capability modeli zacznie być współdzielone przez wiele niezależnych use-case'ów, dopiero wtedy rozważyć neutralny model w `Models`, bez przenoszenia kontraktów HTTP.

### Infrastructure (`Infrastructure`)
- Implementuje techniczny odczyt wskaźnika:
  - `ActiveModelPointerGateway.GetAsync` otwiera `inference.json` z katalogu `ModelsActiveStorage.ActiveDirectoryPath`,
  - jeśli plik nie istnieje, zwraca `null`,
  - parsuje JSON przez `JsonSerializerDefaults.Web`,
  - mapuje payload na `ActiveModelPointerDto`,
  - nie decyduje, czy wskazany model wolno użyć do inferencji.
- `ModelsRegistryGateway` pozostaje jedynym adapterem odczytu manifestu i technicznej kompletności rejestru.
- `LocalFileStorageGateway` zapewnia generyczny odczyt i bezpieczny zapis plików; jeśli trzeba dodać pomocniczą metodę, powinna być generyczna, a nie specyficzna dla aktywnego modelu.

## 5) Pliki per warstwa i odpowiedzialności

### API (`src/Backend/Sudoku/Sudoku`)
- `[REUSE/ROZSZERZENIE]` `Controllers/ModelsController.cs`
  - dodać akcję `GetActiveAsync` dla `GET /api/models/active`,
  - `[Authorize]`, `[HttpGet("active")]`,
  - `200` -> `ActiveModelApiResponse`,
  - `204` -> brak body,
  - `409` -> `ErrorApiResponse` dla niespójnego wskaźnika,
  - `500` -> `ErrorApiResponse` dla błędów odczytu.
- `[REUSE]` `Contracts/ActiveModelApiResponse.cs`
  - ten sam model odpowiedzi co dla `PUT /api/models/active`; nie tworzyć `GetActiveModelApiResponse`.
- `[REUSE]` `Contracts/ErrorApiResponse.cs`
  - wspólny model błędu HTTP.
- `[REUSE]` `Program.cs`
  - już binduje `ModelsActiveStorageOptions` i `ModelsRegistryStorageOptions` z walidacją absolutnych ścieżek.
- `[REUSE]` `appsettings.local.json`
  - lokalna, absolutna ścieżka `ModelsActiveStorage.ActiveDirectoryPath`.
- `[REUSE]` `appsettings.production.json`
  - placeholder `ModelsActiveStorage.ActiveDirectoryPath` podstawiany przez workflow.

### Application (`src/Backend/Sudoku/Application`)
- `[ADD]` `ModelsActive/GetActiveModelQuery.cs`
  - query MediatR bez parametrów.
- `[ADD]` `ModelsActive/GetActiveModelQueryHandler.cs`
  - orkiestruje odczyt wskaźnika, walidację rejestru i mapowanie do wyniku.
- `[ADD]` `ModelsActive/GetActiveModelQueryResultDto.cs`
  - wynik query, np. `ActiveModel: ActiveModelDto?` albo pola `HasActiveModel` + dane odpowiedzi.
- `[ADD]` `ModelsActive/ActiveModelDto.cs`
  - aplikacyjny DTO aktywnego modelu, jeśli nie chcemy zwracać bezpośrednio `GetActiveModelQueryResultDto` z wieloma polami.
- `[ADD]` `ModelsActive/GetActiveModelErrorTypes.cs`
  - np. `active_model_pointer_invalid`, `active_model_read_failed`, `active_model_conflict`.
- `[ADD]` `ModelsActive/ActiveModelPointerInvalidException.cs`
  - wskaźnik istnieje, ale jest pusty, uszkodzony albo zawiera niebezpieczny `modelName`.
- `[ADD]` `ModelsActive/ActiveModelPointerReadException.cs`
  - opakowanie błędów I/O/uprawnień przy odczycie wskaźnika, jeśli warto odróżnić je od konfliktów biznesowych.
- `[REUSE]` `ModelsActive/ActiveModelNotFoundException.cs`
  - wskaźnik wskazuje model, którego nie ma w rejestrze.
- `[REUSE]` `ModelsActive/ActiveModelCannotUseForInferenceException.cs`
  - wskazany model istnieje, ale nie może być użyty do inferencji.
- `[REUSE]` `ModelsActive/ActiveModelManifestInvalidException.cs`
  - manifest wskazanego modelu nie jest poprawny do inferencji.
- `[REUSE/ROZSZERZENIE]` `Abstractions/IActiveModelPointerGateway.cs`
  - dodać `Task<ActiveModelPointerDto?> GetAsync(CancellationToken cancellationToken = default)`.
- `[REUSE]` `Abstractions/IModelsRegistryGateway.cs`
  - użyć `GetByNameAsync(modelName)`.
- `[REUSE]` `ModelsRegistry/RegistryModelManifestDto.cs`
  - manifest używany do zbudowania odpowiedzi.

### Domain / Models (`src/Backend/Sudoku/Models`)
- `[BRAK NOWEGO PLIKU]`
  - endpoint nie wymaga nowych modeli domenowych.
- `[REUSE POŚREDNI]` istniejące modele/statusy treningów
  - semantyka `sourceRunName`, `parentModelName`, capability i raportów musi pozostać zgodna z UC-06/UC-08/UC-09.

### Infrastructure (`src/Backend/Sudoku/Infrastructure`)
- `[REUSE/ROZSZERZENIE]` `Storage/ActiveModelPointerGateway.cs`
  - dodać `GetAsync`,
  - czytać `inference.json`,
  - zwracać `null` dla braku pliku,
  - parsować JSON do `ActiveModelPointerDto`,
  - nie walidować capability.
- `[REUSE]` `Storage/ModelsRegistryGateway.cs`
  - odczyt `models/registry/{modelName}/model.json`,
  - techniczna kompletność manifestu i artefaktów.
- `[REUSE]` `Storage/LocalFileStorageGateway.cs`
  - `OpenReadAsync`, `FileExistsAsync`, `ReplaceAsync`.
- `[REUSE]` `DependencyInjection.cs`
  - rejestracje obecnych gatewayów powinny wystarczyć; brak nowego adaptera DI.

### Workflow (`.github/workflows`)
- `[REUSE/ZWERYFIKOWAĆ]` `.github/workflows/backend-cd.yml`
  - workflow już ma `BE_MODELS_ACTIVE_DIRECTORY_PATH`,
  - waliduje jej obecność,
  - podstawia ją do `ModelsActiveStorage.ActiveDirectoryPath`,
  - nie powinien czyścić ani nadpisywać `models/active`.
- Dla `GET` nie ma potrzeby dodawać nowej zmiennej GitHub, jeśli `PUT` i `GET` korzystają z tego samego katalogu active.

## 6) Weryfikacja usług Infrastructure i antyduplikacja
- Istnieje `IActiveModelPointerGateway`, więc dodać do niego odczyt `GetAsync`, zamiast tworzyć `IActiveModelReader`, `ActiveModelFileReader` albo helper w kontrolerze.
- Istnieje `IModelsRegistryGateway.GetByNameAsync`, więc nie dodawać osobnego readera manifestu na potrzeby `GET`.
- Istnieje `IFileStorageGateway.OpenReadAsync`; odczyt pliku wskaźnika ma przechodzić przez ten generyczny port.
- Jeśli format odczytu wskaźnika wymaga obsługi `LastModifiedUtc`, najpierw sprawdzić, czy `IFileStorageGateway.ListFilesAsync` zwraca metadane pliku i użyć tego generycznie, bez tworzenia adaptera specyficznego dla UC-10.
- Nie dodawać cache aktywnego modelu w pamięci procesu BE; plik jest lekkim źródłem prawdy i powinien być czytany na żądanie.

## 7) Przepływ w obrębie BE
1. `FE` wysyła `GET /api/models/active` z tokenem admin.
2. Middleware autoryzacji weryfikuje token z `UC-13`.
3. `ModelsController.GetActiveAsync` wysyła `GetActiveModelQuery`.
4. Handler wywołuje `IActiveModelPointerGateway.GetAsync`.
5. `ActiveModelPointerGateway` próbuje odczytać `models/active/inference.json`.
6. Jeśli pliku nie ma, gateway zwraca `null`, handler zwraca brak aktywnego modelu, a kontroler odpowiada `204 No Content`.
7. Jeśli wskaźnik istnieje, handler waliduje `pointer.ModelName`.
8. Handler pobiera manifest przez `IModelsRegistryGateway.GetByNameAsync(pointer.ModelName)`.
9. Jeśli manifest nie istnieje albo nie jest aktywowalny, handler rzuca wyjątek konfliktu/niespójności.
10. Handler mapuje manifest + `pointer.UpdatedAtUtc` do DTO aktywnego modelu.
11. Kontroler mapuje DTO na `ActiveModelApiResponse` i zwraca `200 OK`.

## 8) Główne funkcje
- `ModelsController.GetActiveAsync(...)`
- `GetActiveModelQueryHandler.Handle(...)`
- `GetActiveModelQueryHandler.ResolvePointerAsync(...)`
- `GetActiveModelQueryHandler.EnsurePointerModelNameIsValid(...)`
- `GetActiveModelQueryHandler.ResolveModelAsync(...)`
- `GetActiveModelQueryHandler.EnsureCanUseForInference(...)`
- `GetActiveModelQueryHandler.EnsureActivatableManifest(...)`
- `IActiveModelPointerGateway.GetAsync(...)`
- `ActiveModelPointerGateway.GetAsync(...)`
- `IModelsRegistryGateway.GetByNameAsync(...)`
- `ModelsRegistryGateway.GetByNameAsync(...)`
- `IFileStorageGateway.OpenReadAsync(...)`

## 9) Wyjątki, fallbacki i zachowanie błędowe

### 9.1 Publiczne statusy
- `200 OK`:
  - `inference.json` istnieje,
  - zawiera poprawny `modelName`,
  - model istnieje w rejestrze,
  - manifest i artefakt inferencyjny są kompletne,
  - `canUseForInference = true`.
- `204 No Content`:
  - `models/active/inference.json` nie istnieje.
- `401 Unauthorized`:
  - brak albo niepoprawny token administracyjny.
- `409 Conflict`:
  - wskaźnik istnieje, ale jest uszkodzony,
  - `modelName` jest pusty lub niebezpieczny,
  - wskazany model nie istnieje,
  - wskazany model ma `canUseForInference = false`,
  - manifest albo główny artefakt nie spełniają reguł aktywowalności.
- `500 Internal Server Error`:
  - błąd odczytu pliku,
  - brak uprawnień do `models/active` albo `models/registry`,
  - niespodziewany błąd storage poza walidowalną niespójnością stanu.

### 9.2 Fallbacki
- Brak fallbacku do ostatnio znanego modelu z pamięci procesu.
- Brak fallbacku do pierwszego modelu z rejestru.
- Brak fallbacku do `ML`.
- Brak automatycznego utworzenia `inference.json` przy `GET`.
- Brak próby naprawiania wskaźnika przez `GET`; naprawa odbywa się przez `PUT /api/models/active` albo operacyjny bootstrap.

### 9.3 Scenariusze graniczne
- Brak wskaźnika:
  - `204 No Content`.
- Wskaźnik wskazuje model usunięty z rejestru:
  - `409 active_model_pointer_invalid` albo podobny `errorType`.
- Wskaźnik wskazuje model z `canUseForInference = false`:
  - `409 model_cannot_use_for_inference`.
- Manifest modelu jest uszkodzony:
  - `409 model_manifest_invalid`, ponieważ aktywny wybór jest niespójny z rejestrem.
- Brak raportu treningowego:
  - nie blokuje odpowiedzi `200`, jeśli manifest i artefakty inferencyjne są kompletne.
- Bootstrap bez `sourceRunName`:
  - poprawny, jeśli manifest i artefakty inferencyjne są kompletne.
- `updatedAtUtc` w pliku wskaźnika jest brakujące albo nieparsowalne:
  - preferowane zachowanie: `409 active_model_pointer_invalid`; ewentualny fallback na `LastModifiedUtc` wymaga jawnej decyzji i testu.

## 10) Pseudokod specyficznej logiki

```text
handleGetActiveModel():
  pointer = activeModelPointerGateway.get()

  if pointer is null:
    return result(activeModel = null)

  ensurePointerModelNameIsValid(pointer.modelName)

  model = modelsRegistryGateway.getByName(pointer.modelName)

  if model is null:
    throw ActiveModelNotFoundException(pointer.modelName)

  if model.canUseForInference is false:
    throw ActiveModelCannotUseForInferenceException(model.name)

  ensureActivatableManifest(model)

  return result(activeModel = ActiveModelDto(
    modelName = model.name,
    displayName = model.displayName,
    sourceType = model.sourceType,
    sourceRunName = model.sourceRunName,
    parentModelName = model.parentModelName,
    inputProfile = model.inputProfile,
    canUseForInference = model.canUseForInference,
    activatedAtUtc = pointer.updatedAtUtc
  ))
```

```text
activeModelPointerGateway.get():
  try open modelsActiveStorage.activeDirectoryPath / "inference.json"
  catch file not found:
    return null

  parse json using web camelCase options

  return ActiveModelPointerDto(
    modelName = json.modelName,
    registryRelativePath = json.registryRelativePath,
    setBy = json.setBy,
    updatedAtUtc = json.updatedAtUtc
  )
```

```text
ensurePointerModelNameIsValid(modelName):
  require non-empty after trim
  reject path separators "/" and "\"
  reject ".." segment
  reject ":" and control characters
  reject names longer than validator limit used by PUT
```

## 11) Workflow GitHub i konfiguracja runtime
- Lokalnie:
  - `appsettings.local.json` ma mieć twardo ustawioną absolutną ścieżkę `ModelsActiveStorage.ActiveDirectoryPath`.
  - lokalny plik `models/active/inference.json` jest runtime state, a nie plik do wersjonowania.
- Produkcyjnie:
  - `appsettings.production.json` ma placeholder `ModelsActiveStorage.ActiveDirectoryPath`,
  - `.github/workflows/backend-cd.yml` podstawia `BE_MODELS_ACTIVE_DIRECTORY_PATH`,
  - wartość powinna wskazywać trwały katalog współdzielony, np. odpowiednik `/opt/sudoku/shared/models/active`, ale kod nie może znać tej ścieżki.
- Deploy:
  - zwykły deploy BE publikuje aplikację i konfigurację,
  - nie czyści `models/active`, `models/registry`, `trainings`, `data` ani `examples`,
  - bootstrap pierwszego modelu aktywnego jest osobnym krokiem operacyjnym, nie efektem `GET`.
- Dla tej historyjki nie trzeba dodawać nowych zmiennych do workflow, ale trzeba zweryfikować, że `BE_MODELS_ACTIVE_DIRECTORY_PATH` istnieje w GitHub Environment.

## 12) Logging
- Cel: diagnoza niespójnego wskaźnika bez spamowania i bez ujawniania ścieżek systemowych.
- `Information`:
  - rozpoczęto odczyt aktywnego modelu,
  - zwrócono aktywny model z `ModelName`.
- `Debug` albo brak logu:
  - brak wskaźnika i odpowiedź `204`; to może być normalny stan bootstrapowy, więc nie logować jako `Warning` za każdym razem.
- `Warning`:
  - wskaźnik istnieje, ale jest niepoprawny,
  - wskaźnik wskazuje brakujący model,
  - model utracił `canUseForInference`,
  - manifest jest nieaktywowalny.
- `Error`:
  - błąd I/O albo uprawnień przy odczycie wskaźnika lub manifestu.
- Guardrail:
  - nie logować pełnego `inference.json`,
  - nie logować pełnego `model.json`,
  - nie logować tokenów,
  - nie zwracać absolutnych ścieżek w `ErrorApiResponse`,
  - logować `modelName` i `errorType`, a nie payloady plików.

## 13) Kolejność implementacji kodu dla historyjki
1. Zweryfikować istniejący `PUT /api/models/active`, `ActiveModelApiResponse`, `ActiveModelPointerDto`, `IActiveModelPointerGateway` i `ActiveModelPointerGateway`.
2. Rozszerzyć `IActiveModelPointerGateway` o `GetAsync`.
3. Dodać implementację `ActiveModelPointerGateway.GetAsync` z obsługą braku `inference.json` jako `null`.
4. Dodać `GetActiveModelQuery`, `GetActiveModelQueryResultDto` i ewentualny `ActiveModelDto`.
5. Dodać wyjątki i `GetActiveModelErrorTypes` dla niespójnego wskaźnika oraz błędów odczytu.
6. Zaimplementować `GetActiveModelQueryHandler`, reużywając walidacji aktywowalności z `SetActiveModelCommandHandler`; jeśli pojawia się duplikacja, wydzielić mały helper w `Application/ModelsActive`, a nie w `Infrastructure`.
7. Dodać `ModelsController.GetActiveAsync`.
8. Zweryfikować mapowanie statusów: `200`, `204`, `401`, `409`, `500`.
9. Zweryfikować `Program.cs`, `appsettings.local.json`, `appsettings.production.json` i `backend-cd.yml` dla `ModelsActiveStorage`.
10. Dodać testy jednostkowe gatewaya odczytu: brak pliku, poprawny JSON, uszkodzony JSON, brak pól.
11. Dodać testy handlera: brak wskaźnika, sukces, model nie istnieje, `canUseForInference = false`, manifest invalid, niebezpieczny `modelName`.
12. Dodać testy API/integracyjne: `200`, `204`, `401`, `409`, `500`.
13. Uruchomić build/testy backendu.

## 14) Guardraile implementacyjne
- Kontroler pozostaje cienki; żadnych operacji filesystem ani parsowania JSON w API.
- `Application` zawiera decyzje use-case'u i walidację aktywnego wyboru.
- `Infrastructure` tylko czyta/zapisuje pliki i mapuje payloady techniczne.
- Nie tworzyć minimal API `MapGet`; użyć kontrolera ASP.NET.
- Nie hardcodować `/opt/sudoku/...` ani lokalnych ścieżek w kodzie.
- Nie kopiować modelu z `models/registry` do `models/active`.
- Nie zwracać do `FE` ścieżek systemowych, `primaryArtifactRelativePath`, `registryRelativePath` ani pełnego manifestu.
- Nie dodawać cache aktywnego modelu w BE.
- Nie traktować `ML` jako źródła prawdy dla aktywnego modelu.
- Zachować `camelCase`, `ApiEntry`, `ApiResponse`, `Dto` i `ErrorApiResponse`.
- Nie zmieniać kontraktu `ActiveModelApiResponse`, bo jest już używany przez `PUT /api/models/active`.

## 15) Zależności pomiędzy historyjkami
- Wejściowe:
  - `UC-13` - autoryzacja endpointu tokenem administracyjnym.
  - `INF-08` - standard manifestów, bootstrap rejestru i wskaźnik `models/active/inference.json`.
  - `UC-06 GET /api/models/registry` - rejestr modeli i `IModelsRegistryGateway`.
  - `UC-06 POST /api/trainings` - tworzenie modeli wynikowych w `models/registry`.
  - `UC-08` / `UC-09` - metryki i dane pomagające operatorowi wybrać model, bez zmiany kontraktu aktywnego wskaźnika.
  - `UC-10 PUT /api/models/active` - zapisuje wskaźnik odczytywany przez ten endpoint.
- Konsumujące:
  - `FE UC-10` - zaznacza aktualny model w UI.
  - `UC-05` - inferencja używa modelu wskazanego w `models/active/inference.json`.
  - `ML UC-10` - reload/hot swap modelu bazuje na tym samym wskaźniku, bez osobnego źródła prawdy.

## 16) Inne istotne reguły
- `GET` jest odczytem i nie powinien naprawiać ani nadpisywać pliku aktywnego modelu.
- `204` oznacza brak wskaźnika, a nie brak modeli w rejestrze.
- `409` oznacza, że wskaźnik istnieje, ale stan systemu jest niespójny i wymaga ponownego `PUT` albo interwencji operacyjnej.
- `activatedAtUtc` pochodzi z `inference.json.updatedAtUtc`.
- Wskaźnik może wskazywać model bootstrap albo model wytrenowany, jeśli manifest i artefakty są kompletne.
- Brak raportu treningowego nie blokuje odczytu aktywnego modelu.
- `registryRelativePath` w `inference.json` nie jest używane do rozwiązywania ścieżki rejestru po stronie BE; BE używa `ModelsRegistryStorage.RegistryDirectoryPath` i `modelName`.

## 17) Model API wejściowy i wyjściowy w komunikacji z FE i ML
- FE -> BE:
  - `GET /api/models/active`,
  - brak body,
  - token administracyjny.
- BE -> FE:
  - `ActiveModelApiResponse` dla `200`,
  - puste body dla `204`,
  - `ErrorApiResponse` dla błędów.
- BE -> ML:
  - brak nowego HTTP call.
  - wspólny kontrakt runtime to odczytywany plik `models/active/inference.json`.
- ML -> BE:
  - brak komunikacji inicjowanej przez ten endpoint.
- Plikowe kontrakty wejściowe dla BE:
  - `models/active/inference.json`,
  - `models/registry/{modelName}/model.json`,
  - `models/registry/{modelName}/{primaryArtifactRelativePath}`.
- Plikowe kontrakty wyjściowe BE:
  - brak; endpoint niczego nie zapisuje.

