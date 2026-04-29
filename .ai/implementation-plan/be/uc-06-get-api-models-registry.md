# UC-06-BE - Plan implementacyjny dla `GET /api/models/registry`

## 1) Przeznaczenie endpointa
- Endpoint `GET /api/models/registry` zwraca chronioną listę wpisów rejestru modeli możliwych do pokazania w ekranie uruchamiania treningu i później w widokach porównywania modeli.
- Dla `UC-06` lista służy przede wszystkim do wyboru modelu bazowego. `FE` widzi wyłącznie logiczne metadane modelu i capability (`canStartTraining`, `canUseForInference`), bez ścieżek systemowych i bez technicznych nazw artefaktów.
- Backend jest `source of truth` dla listy widocznej dla `FE`: źródłem jest skan `models/registry/*/model.json`, a nie aktualny stan `FE` ani niezależny rejestr po stronie `ML`.
- Endpoint nie uruchamia treningu, nie komunikuje się z `ML` i nie sprawdza aktywnego modelu. To lekki odczyt rejestru modeli.

## 2) Zakres i założenia
- Plan opiera się na `PRD`, `UC-06`, zasadach runtime/deployu i `INF-08`; nie sugeruje się bieżącą implementacją `FE` ani `ML`.
- Endpoint jest chroniony tokenem administracyjnym z `UC-13`.
- Rejestr modeli jest katalogiem `models/registry`, gdzie każdy wpis ma katalog `{modelName}`, obowiązkowy `model.json` i katalog `artifacts/`.
- Model bootstrap bez `sourceRunName` jest poprawnym wpisem i może zostać zwrócony na liście.
- Wpis uszkodzony, archiwalny albo niekompatybilny nie musi być ukrywany, jeśli manifest da się odczytać; jego capability powinno wynikać z manifestu, np. `canStartTraining = false` i/lub `canUseForInference = false`.
- Publiczny JSON pozostaje w `camelCase`, modele HTTP mają sufiks `ApiResponse`, a DTO warstwy aplikacyjnej sufiks `Dto`.

## 3) Kontrakty API FE i ML

### 3.1 FE -> BE (`GET /api/models/registry`)
- Request body: brak.
- Query params: brak w MVP.
- Autoryzacja: token administracyjny (`Bearer`).

### 3.2 Odpowiedzi publiczne
- `200 OK` -> `RegistryModelsListApiResponse`.
- `401 Unauthorized` -> brak albo niepoprawny token.
- `500 Internal Server Error` -> błąd odczytu rejestru, parsowania manifestu albo niespójność uniemożliwiająca zbudowanie odpowiedzi.

### 3.3 Model wejściowy/wyjściowy FE
- Wejście FE -> BE:
  - brak body.
- Wyjście BE -> FE (`RegistryModelsListApiResponse`):
  - `items: RegistryModelListItemApiResponse[]`
  - `totalCount: number`
- `RegistryModelListItemApiResponse`:
  - `name: string`
  - `displayName: string`
  - `sourceType: string` (`bootstrap` | `training` | inne przyszłe wartości manifestu)
  - `sourceRunName: string | null`
  - `parentModelName: string | null`
  - `trainingMode: string`
  - `inputProfile: string`
  - `trainingProfileName: string | null`
  - `augmentationProfileName: string | null`
  - `createdAtUtc: string | null`
  - `canStartTraining: boolean`
  - `canUseForInference: boolean`
  - `warnings: string[]`

Przykład:

```json
{
  "items": [
    {
      "name": "cnn-mnist-baseline",
      "displayName": "CNN MNIST Baseline",
      "sourceType": "bootstrap",
      "sourceRunName": null,
      "parentModelName": null,
      "trainingMode": "externalBaseline",
      "inputProfile": "default-28x28-v1",
      "trainingProfileName": "cnn-default-v1",
      "augmentationProfileName": "digits-light-v1",
      "createdAtUtc": "2026-04-11T12:00:00Z",
      "canStartTraining": true,
      "canUseForInference": true,
      "warnings": []
    }
  ],
  "totalCount": 1
}
```

### 3.4 BE <-> ML dla tego endpointa
- Brak komunikacji `BE -> ML`.
- Brak komunikacji `ML -> BE`.
- `ML` może wcześniej utworzyć artefakty bootstrap przez `INF-08` albo artefakty modelu wynikowego w workflow treningu, ale endpoint odczytuje tylko backendowy rejestr na dysku.

## 4) Zachowanie per warstwa

### API (`Sudoku`)
- Cienki kontroler:
  - autoryzacja,
  - wywołanie query MediatR,
  - mapowanie DTO aplikacyjnych na `RegistryModelsListApiResponse`,
  - mapowanie wyjątków na `ErrorApiResponse`.
- Brak skanowania katalogów, brak parsowania `model.json`, brak reguł capability.

### Application (`Application`)
- Use-case odczytowy `ListRegistryModelsQuery`.
- Logika aplikacyjna:
  - pobranie manifestów z portu `IModelsRegistryGateway`,
  - walidacja minimalnych invariantów publicznej listy,
  - normalizacja nazwy z katalogu i nazwy z manifestu,
  - sortowanie deterministyczne,
  - wyliczenie `totalCount`,
  - mapowanie do DTO listy.
- Decyzja, które pola pokazujemy `FE`, należy do `Application`. Szczegóły systemu plików i JSON należą do `Infrastructure`.

### Domain / Models (`Models`)
- W MVP brak dedykowanego modelu domenowego, jeśli zespół utrzymuje prosty wzorzec DTO w `Application`.
- Jeżeli pojawi się potrzeba współdzielenia semantyki manifestu między wieloma use-case'ami, można dodać neutralne modele w `Models/ModelsRegistry`, ale bez zależności od HTTP, filesystem i klienta ML.
- Guardrail: nie przenosić kontraktów `RegistryModel*ApiResponse` do `Models`.

### Infrastructure (`Infrastructure`)
- Implementuje port rejestru modeli:
  - listuje katalogi bezpośrednio pod `ModelsRegistryStorage.RegistryDirectoryPath`,
  - otwiera `model.json` w każdym katalogu,
  - deserializuje manifest,
  - technicznie sprawdza istnienie katalogu `artifacts/` i głównego artefaktu, jeśli manifest wskazuje `primaryArtifactRelativePath`,
  - zwraca DTO aplikacyjne.
- Infrastructure nie decyduje, czy model jest biznesowo dobrym kandydatem do startu treningu; przekazuje dane z manifestu i techniczne ostrzeżenia.

## 5) Pliki per warstwa i odpowiedzialności

### API (`src/Backend/Sudoku/Sudoku`)
- `[NOWY]` `Controllers/ModelsController.cs`
  - kontroler z `[ApiController]`, `[Route("api/models")]`.
  - akcja `ListRegistryAsync` dla `GET /api/models/registry`.
  - mapowanie `ListRegistryModelsQueryResultDto` -> `RegistryModelsListApiResponse`.
  - mapowanie błędów listowania na `500` z `ErrorApiResponse`.
- `[NOWY]` `Contracts/RegistryModelsListApiResponse.cs`
  - publiczny model listy: `items`, `totalCount`.
- `[NOWY]` `Contracts/RegistryModelListItemApiResponse.cs`
  - publiczny model elementu listy.
- `[REUSE]` `Contracts/ErrorApiResponse.cs`
  - wspólny model błędów `errorType`, `message`.
- `[REUSE/MODYFIKACJA]` `Program.cs`
  - bind i walidacja `ModelsRegistryStorageOptions`.
- `[MODYFIKACJA]` `appsettings.local.json`
  - dodać lokalną, absolutną ścieżkę do `ModelsRegistryStorage.RegistryDirectoryPath`.
- `[MODYFIKACJA]` `appsettings.production.json`
  - dodać placeholder dla `ModelsRegistryStorage.RegistryDirectoryPath` nadpisywany przez workflow.

### Application (`src/Backend/Sudoku/Application`)
- `[NOWY]` `ModelsRegistry/ListRegistryModelsQuery.cs`
  - query MediatR bez parametrów.
- `[NOWY]` `ModelsRegistry/ListRegistryModelsQueryHandler.cs`
  - orkiestracja odczytu, sortowanie i budowanie wyniku listy.
- `[NOWY]` `ModelsRegistry/ListRegistryModelsQueryResultDto.cs`
  - DTO wyniku: `Items`, `TotalCount`.
- `[NOWY]` `ModelsRegistry/RegistryModelListItemDto.cs`
  - DTO elementu listy przekazywane do API.
- `[NOWY]` `ModelsRegistry/RegistryModelManifestDto.cs`
  - DTO manifestu odczytywanego z `model.json`; zawiera pola manifestu potrzebne nie tylko temu endpointowi, ale też `POST /api/trainings`.
- `[NOWY]` `ModelsRegistry/ModelsRegistryStorageOptions.cs`
  - typed options z `SectionName = "ModelsRegistryStorage"` i `RegistryDirectoryPath`.
- `[NOWY]` `ModelsRegistry/ListRegistryModelsErrorTypes.cs`
  - stałe błędów, np. `models_registry_list_read_failed`.
- `[NOWY]` `Abstractions/IModelsRegistryGateway.cs`
  - port aplikacyjny do listowania modeli oraz przyszłego pobierania modelu po nazwie.
  - Warto od razu przewidzieć `GetByNameAsync(modelName)` dla `POST /api/trainings`, żeby nie tworzyć później drugiego adaptera.

### Domain / Models (`src/Backend/Sudoku/Models`)
- `[BRAK WYMAGANEGO NOWEGO PLIKU W MVP]`
  - DTO manifestu i listy mogą pozostać w `Application/ModelsRegistry`, bo są częścią use-case'ów backendowych.
- `[OPCJONALNIE PÓŹNIEJ]` `ModelsRegistry/ModelCapability.cs`
  - tylko jeśli capability zacznie być współdzielone przez wiele modułów jako pojęcie domenowe.

### Infrastructure (`src/Backend/Sudoku/Infrastructure`)
- `[NOWY]` `Storage/ModelsRegistryGateway.cs`
  - implementacja `IModelsRegistryGateway`.
  - skan `models/registry/*/model.json`.
  - deserializacja manifestu przez `JsonSerializerDefaults.Web`.
  - techniczna walidacja katalogu wpisu i artefaktów.
  - używa `IFileStorageGateway`, nie własnych helperów do standardowego list/open.
- `[REUSE]` `Storage/LocalFileStorageGateway.cs`
  - generyczne operacje `ListDirectoriesAsync`, `ListFilesAsync`, `OpenReadAsync`.
  - Jeśli potrzebny jest odczyt pliku z podkatalogu modelu, używać bezpiecznego `OpenReadAsync(entryDirectory, "model.json")`.
- `[MODYFIKACJA]` `DependencyInjection.cs`
  - rejestracja `IModelsRegistryGateway -> ModelsRegistryGateway`.
- `[BRAK ZMIAN]` `Ml/*`
  - endpoint nie wywołuje ML.

### Workflow (`.github/workflows`)
- `[MODYFIKACJA]` `.github/workflows/backend-cd.yml`
  - dodać zmienną `BE_MODELS_REGISTRY_DIRECTORY_PATH`.
  - walidować ją razem z pozostałymi zmiennymi produkcyjnymi.
  - w generatorze `appsettings.production.json` ustawić `ModelsRegistryStorage.RegistryDirectoryPath`.

## 6) Weryfikacja usług Infrastructure i antyduplikacja
- Sprawdzone w aktualnym BE: istnieje `IFileStorageGateway` z `ListDirectoriesAsync`, `ListFilesAsync`, `OpenReadAsync` oraz implementacja `LocalFileStorageGateway`.
- Wniosek: nie tworzyć osobnego `DirectoryScanner`, `ModelManifestFileReader` ani statycznych helperów z bezpośrednim `Directory.*` w `Application`.
- Nowy `ModelsRegistryGateway` powinien być generyczny dla rejestru modeli:
  - `ListAsync()` dla tego endpointa,
  - opcjonalnie `GetByNameAsync()` dla startu treningu,
  - opcjonalnie później `SaveManifestAsync()` dla finalizacji modelu po `completed`.
- Jeśli obecny `IFileStorageGateway` okaże się niewystarczający do sprawdzenia podkatalogu `artifacts`, najpierw rozszerzyć go generycznie, zamiast dodawać logikę specyficzną dla rejestru w kilku miejscach.

## 7) Przepływ w obrębie BE
1. `FE` wysyła `GET /api/models/registry` z tokenem admin.
2. `ModelsController` wywołuje `ListRegistryModelsQuery`.
3. Handler wywołuje `IModelsRegistryGateway.ListAsync`.
4. `ModelsRegistryGateway` listuje katalogi bezpośrednio w `ModelsRegistryStorage.RegistryDirectoryPath`.
5. Dla każdego katalogu próbuje odczytać `model.json`.
6. Gateway deserializuje manifest i zwraca rekordy aplikacyjne z technicznymi ostrzeżeniami.
7. Handler sprawdza minimalne invarianty listy, sortuje wyniki i wylicza `totalCount`.
8. Kontroler mapuje DTO na `RegistryModelsListApiResponse`.
9. `FE` używa listy do pokazania modeli i pozwala wybrać do startu treningu tylko wpisy z `canStartTraining = true`.

## 8) Główne funkcje
- `ModelsController.ListRegistryAsync(...)`
- `ListRegistryModelsQueryHandler.Handle(...)`
- `IModelsRegistryGateway.ListAsync(...)`
- `IModelsRegistryGateway.GetByNameAsync(...)` jeśli dodane od razu pod `POST /api/trainings`
- `ModelsRegistryGateway.ListAsync(...)`
- `ModelsRegistryGateway.ReadManifestAsync(...)`
- `ModelsRegistryGateway.ValidateTechnicalCompleteness(...)`
- `IFileStorageGateway.ListDirectoriesAsync(...)`
- `IFileStorageGateway.OpenReadAsync(...)`

## 9) Wyjątki, fallbacki i zachowanie błędowe

### 9.1 Publiczne statusy
- `200 OK`:
  - rejestr odczytany poprawnie; pusta lista jest poprawna w świeżym środowisku przed bootstrapem.
- `401 Unauthorized`:
  - brak albo niepoprawny token administracyjny.
- `500 Internal Server Error`:
  - brak dostępu do katalogu rejestru,
  - uszkodzony JSON manifestu,
  - manifest bez wymaganych pól minimalnych,
  - duplikat logicznej nazwy modelu,
  - błąd I/O podczas odczytu.

### 9.2 Fallbacki
- Brak fallbacku do `ML`.
- Brak fallbacku do aktywnego wskaźnika `models/active/inference.json`.
- Brak fallbacku do cache `FE`.
- Pusty katalog registry zwraca `200` z `items=[]`, bo to poprawny stan przed `INF-08` albo w środowisku testowym.
- Brak katalogu registry:
  - preferowane zachowanie MVP: `200` z pustą listą, jeśli `IFileStorageGateway.ListDirectoriesAsync` zwraca pusty wynik dla nieistniejącego katalogu.
  - Jeśli aplikacja ma wymagać utworzonego katalogu na starcie, wtedy walidację operacyjną robi deploy/init, a nie endpoint.

### 9.3 Scenariusze graniczne
- `model.json` nie istnieje w katalogu wpisu:
  - fail fast `500`, bo katalog wygląda jak wpis rejestru, ale nie spełnia kontraktu `INF-08`.
- `modelName` w manifeście różni się od nazwy katalogu:
  - `500` i log `Error`; to niespójność rejestru.
- Brak `artifacts/` albo brak głównego artefaktu:
  - jeśli manifest ma `canStartTraining = true` lub `canUseForInference = true`, zwrócić `500`, bo capability nie zgadza się z techniczną kompletnością.
  - jeśli oba capability są `false`, można zwrócić wpis z ostrzeżeniem `model_artifacts_missing`.
- Duplikat nazw po normalizacji:
  - `500`, bo publiczne API używa `name` jako identyfikatora.
- Pojedynczy uszkodzony manifest:
  - decyzja MVP: fail fast całej listy, żeby operator nie przeoczył uszkodzonego rejestru.

## 10) Pseudokod specyficznej logiki

```text
handleListRegistryModels():
  manifests = modelsRegistryGateway.list()

  ensureNoDuplicateNames(manifests)

  items = manifests
    .orderByDescending(createdAtUtc ?? DateTimeOffset.MinValue)
    .thenBy(name)
    .map(m => RegistryModelListItemDto(
      name = m.name,
      displayName = m.displayName ?? m.name,
      sourceType = m.sourceType,
      sourceRunName = m.sourceRunName,
      parentModelName = m.parentModelName,
      trainingMode = m.trainingMode,
      inputProfile = m.inputProfile,
      trainingProfileName = m.trainingProfileName,
      augmentationProfileName = m.augmentationProfileName,
      createdAtUtc = m.createdAtUtc,
      canStartTraining = m.canStartTraining,
      canUseForInference = m.canUseForInference,
      warnings = m.warnings
    ))

  return RegistryModelsListDto(items, totalCount = items.count)
```

```text
modelsRegistryGateway.list():
  entries = fileStorage.listDirectories(registryDirectory)

  for entry in entries:
    manifest = readJson(entry.path, "model.json")

    if manifest.modelName != entry.name:
      throw InvalidDataException("Manifest modelName differs from registry directory name.")

    warnings = []
    if manifest.primaryArtifactRelativePath is not empty:
      if not fileExists(entry.path, manifest.primaryArtifactRelativePath):
        warnings.add("primary_artifact_missing")

    if warnings contains artifact problem and (manifest.canStartTraining or manifest.canUseForInference):
      throw InvalidDataException("Model capability requires complete artifacts.")

    yield manifest with warnings
```

## 11) Workflow GitHub i konfiguracja runtime
- Lokalnie:
  - `appsettings.local.json` ma zawierać twardą, absolutną ścieżkę, np. `/home/wojtek/projects/sudoku/data/models/registry`.
- Produkcyjnie:
  - `appsettings.production.json` ma zawierać placeholder nadpisywany przez `.github/workflows/backend-cd.yml`.
  - Workflow nie powinien czyścić ani nadpisywać `models/registry`; to trwały katalog w `/opt/sudoku/shared/models/registry`.

### 11.1 Nowa sekcja konfiguracji BE

```json
{
  "ModelsRegistryStorage": {
    "RegistryDirectoryPath": "/home/wojtek/projects/sudoku/data/models/registry"
  }
}
```

### 11.2 Zmiany w `backend-cd.yml`
- Dodać env:
  - `BE_MODELS_REGISTRY_DIRECTORY_PATH: ${{ vars.BE_MODELS_REGISTRY_DIRECTORY_PATH }}`
- Dodać walidację:
  - brak wartości kończy workflow przed publikacją release.
- Dodać do listy `required_env_vars` w generatorze konfiguracji.
- Ustawić w Pythonowym generatorze:
  - `config["ModelsRegistryStorage"]["RegistryDirectoryPath"] = os.environ["BE_MODELS_REGISTRY_DIRECTORY_PATH"]`
- Zmienna powinna wskazywać produkcyjnie na trwały katalog współdzielony, np. `/opt/sudoku/shared/models/registry`, ale tej ścieżki nie hardcodujemy w kodzie.

## 12) Logging
- Cel: diagnostyka uszkodzonego rejestru bez spamowania i bez dumpowania pełnych manifestów.
- `Information`:
  - rozpoczęto listowanie rejestru modeli,
  - zakończono listowanie z liczbą zwróconych modeli.
- `Warning`:
  - wpis ma capability `false` z powodu ostrzeżeń technicznych,
  - pominięto plik/katalog niebędący wpisem rejestru, jeśli taka tolerancja zostanie przyjęta.
- `Error`:
  - manifest niepoprawny JSON,
  - brak wymaganego `model.json`,
  - `modelName` różny od nazwy katalogu,
  - duplikat nazwy modelu,
  - capability wymaga artefaktów, których fizycznie brakuje.
- Guardrail:
  - nie logować pełnej treści `model.json`,
  - nie logować absolutnych ścieżek w odpowiedzi API; w logach technicznych można logować nazwę modelu i nazwę brakującego pliku względnego.

## 13) Inne istotne reguły
- `GET` jest read-only i nie tworzy brakujących katalogów ani manifestów.
- Endpoint nie filtruje modeli wyłącznie do `canStartTraining = true`; FE może potrzebować pokazać także modele tylko do inferencji albo wpisy archiwalne w późniejszym `UC-08/UC-10`.
- `trainingMode` w liście opisuje istniejący wpis modelu, a nie parametr nowego treningu.
- `inputProfile` musi być zwracany, bo `POST /api/trainings` będzie walidował zgodność z `ProcessedDataset.preprocessingProfile`.
- Nie eksponować `primaryArtifactRelativePath`, `registryDirectoryPath`, `manifestPath`, `artifactsDirectoryPath` ani innych ścieżek technicznych do `FE`.
- Sortowanie ma być deterministyczne: `createdAtUtc` malejąco, potem `name` rosnąco.
- Publiczne błędy zawsze przez `ErrorApiResponse`.

## 14) Kolejność implementacji kodu dla historyjki
1. Dodać `ModelsRegistryStorageOptions` i konfigurację `ModelsRegistryStorage` w `appsettings.local.json` oraz `appsettings.production.json`.
2. Zaktualizować `Program.cs` o bind i walidację absolutnej ścieżki `RegistryDirectoryPath`.
3. Dodać DTO i query w `Application/ModelsRegistry`.
4. Dodać port `IModelsRegistryGateway` z `ListAsync` i najlepiej `GetByNameAsync`.
5. Zaimplementować `ModelsRegistryGateway` w `Infrastructure/Storage` z reuse `IFileStorageGateway`.
6. Zarejestrować gateway w `Infrastructure/DependencyInjection.cs`.
7. Dodać kontrakty API `RegistryModelsListApiResponse` i `RegistryModelListItemApiResponse`.
8. Dodać `ModelsController` z `GET /api/models/registry`.
9. Dodać mapowanie wyjątków na `ErrorApiResponse`.
10. Zaktualizować `.github/workflows/backend-cd.yml` o `BE_MODELS_REGISTRY_DIRECTORY_PATH`.
11. Dodać testy handlera: pusta lista, sortowanie, `totalCount`, bootstrap bez `sourceRunName`.
12. Dodać testy gatewaya: poprawny manifest, brak `model.json`, niezgodna nazwa katalogu, brak artefaktu przy capability `true`.
13. Dodać testy integracyjne kontrolera: `200`, `401`, `500`.

## 15) Guardraile implementacyjne
- Kontroler ma być cienki; żadnych `Directory.*`, `File.*` ani `JsonSerializer.Deserialize` w `Api`.
- `Application` decyduje o publicznym kształcie listy i sortowaniu; `Infrastructure` tylko adaptuje storage.
- Nie dodawać minimal API `MapGet`; użyć kontrolera ASP.NET.
- Nie hardcodować `/opt/sudoku/...` ani lokalnych ścieżek w kodzie.
- Nie tworzyć osobnego źródła prawdy w bazie danych ani cache dla listy modeli.
- Nie wywoływać `ML` z tego endpointa.
- Nie ufać nazwie katalogu bez porównania z `model.json`.
- Nie zwracać do `FE` ścieżek systemowych ani sekretów.
- Zachować `camelCase` w JSON i sufiksy `ApiResponse`/`Dto`.

## 16) Zależności pomiędzy historyjkami
- Wejściowe:
  - `UC-13` - autoryzacja endpointu.
  - `INF-08` - standard manifestów oraz bootstrap wpisów w `models/registry`.
  - `UC-12` - przygotowane datasety, które później są sprawdzane względem `inputProfile` modelu.
- Równoległe / konsumujące:
  - `UC-06 POST /api/trainings` - użyje `IModelsRegistryGateway.GetByNameAsync` do walidacji `baseModelName`.
  - `GET /api/trainings/active` - ekran treningu najpierw odzyskuje aktywny run, a dopiero przy `204` pobiera modele.
- Wyjściowe:
  - `UC-08` - lista treningów i modeli reuse'uje publiczną listę rejestru.
  - `UC-10` - wybór aktywnego modelu użyje tych samych manifestów, ale z regułą `canUseForInference`.
  - `UC-09` - szczegóły runu mogą linkować do `producedModelName` obecnego w rejestrze.

## 17) Model API wejściowy i wyjściowy w komunikacji z FE i ML
- FE -> BE:
  - `GET /api/models/registry`
  - brak body.
- BE -> FE:
  - `RegistryModelsListApiResponse`
  - `RegistryModelListItemApiResponse[]`
  - `ErrorApiResponse` dla błędów.
- BE -> ML:
  - brak komunikacji dla tego endpointa.
- ML -> BE:
  - brak komunikacji dla tego endpointa.
- Plikowy kontrakt wejściowy dla BE:
  - `models/registry/{modelName}/model.json`
  - `models/registry/{modelName}/artifacts/`

