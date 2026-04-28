# UC-12-BE - Plan implementacyjny dla `POST /api/datasets/processed`

## 1) Przeznaczenie endpointa
- Endpoint `POST /api/datasets/processed` realizuje przygotowanie jednego, spójnego artefaktu treningowego `{name}.npz` na podstawie listy logicznych źródeł z `UC-11`.
- Backend pozostaje orkiestratorem i `source of truth`: waliduje żądanie, mapuje `splits -> splitPolicy`, wywołuje `ML`, zapisuje finalny plik i zwraca raport publiczny do `FE`.
- Endpoint jest operacją administracyjną, więc wymaga tokenu z `UC-13`.

## 2) Zakres historyjki (BE)
- W zakresie: `POST /api/datasets/processed` oraz niezbędne elementy wspierające ten workflow (`Application`, `Infrastructure`, `Api`, konfiguracja, workflow deploy).
- Poza zakresem tego planu: logika UI, implementacja szczegółowego preprocessingu w Pythonie, start treningu (`UC-06`), SignalR (`UC-07`).

## 3) Kontrakty API (wejście/wyjście) w komunikacji FE i ML

### 3.1 FE -> BE (`POST /api/datasets/processed`)
`CreateProcessedDatasetApiEntry`:
- `name: string`
- `sources: SelectedRawDatasetSourceApiEntry[]`

`SelectedRawDatasetSourceApiEntry`:
- `name: string`
- `type: string` (`board` | `digit`)
- `splits: string[]` (`train` | `val` | `test` | `mix`)

Sukces `201 Created` -> `ProcessedDatasetApiResponse`:
- `name: string`
- `fileName: string`
- `preprocessingProfile: string`
- `createdAtUtc: string` (`ISO-8601 UTC`)
- `sources: SelectedRawDatasetSourceApiEntry[]`
- `sampleCounts: SplitSampleCountsApiResponse`
- `sourceReports: ProcessedDatasetSourceReportApiResponse[]`
- `warnings: string[]`

`SplitSampleCountsApiResponse`:
- `train: number`
- `val: number`
- `test: number`

`ProcessedDatasetSourceReportApiResponse`:
- `name: string`
- `type: string`
- `processedSampleCount: number`
- `includedSampleCount: number`
- `emptyCellCount: number`
- `rejectedSampleCount: number`
- `warnings: string[]`

Błędy:
- `400` (`invalid_dataset_split_selection`, `invalid_request`)
- `401` (`unauthorized`)
- `404` (`raw_dataset_not_found`)
- `409` (`processed_dataset_name_conflict`)
- `422` (`dataset_source_invalid`, `raw_dataset_type_mismatch`, `no_samples_prepared`)
- `503` (`ml_unavailable`)
- `504` (`ml_timeout`)

### 3.2 BE -> ML (`POST /ml/datasets/prepare`)
`PrepareDatasetArtifactApiEntry`:
- `datasetName: string`
- `sources: PrepareDatasetSourceApiEntry[]`
- `preprocessingProfile: string`

`PrepareDatasetSourceApiEntry`:
- `name: string`
- `type: string` (`board` | `digit`)
- `splitPolicy: DatasetSplitPolicyApiEntry`

`DatasetSplitPolicyApiEntry`:
- `mode: string` (`mix` | `selected`)
- `ratios: SplitRatiosApiEntry`
- `groupBy: string` (`sample` | `board`)

`SplitRatiosApiEntry`:
- `train: number`
- `val: number`
- `test: number`

Sukces `200 OK` -> `PreparedDatasetArtifactApiResponse`:
- `sampleCounts: SplitSampleCountsApiResponse`
- `sources: PreparedDatasetSourceReportApiResponse[]`
- `warnings: string[]`

`PreparedDatasetSourceReportApiResponse`:
- `name: string`
- `requestedType: string`
- `detectedType: string`
- `processedSampleCount: number`
- `includedSampleCount: number`
- `emptyCellCount: number`
- `rejectedSampleCount: number`
- `warnings: string[]`

## 4) Architektura i odpowiedzialności warstw

### API
- Tylko transport HTTP: autoryzacja, binding requestu, mapowanie odpowiedzi i wyjątków na statusy HTTP.
- Brak logiki biznesowej splitów, brak operacji plikowych, brak bezpośredniej semantyki `board`/`digit`.

### Application
- Właściwa logika use case: walidacja, reguły splitów, weryfikacja zgodności z kandydatami z `UC-11`, orkiestracja BE->ML->storage, mapowanie raportu.
- To tutaj jest workflow przygotowania datasetu i reguły biznesowo-aplikacyjne.

### Domain (`Models`)
- Modele neutralne biznesowo/technicznie używane między warstwami (`ImageContent`, `CellsGrid` już istnieją; dla UC-12 dodajemy analogiczne DTO/rekordy specyficzne dla dataset preparation po stronie Application/Contracts, nie w kontrolerze).
- Brak zależności od HTTP i infrastruktury.

### Infrastructure
- Implementacja portów: filesystem, klient HTTP do `ML`.
- Zero logiki orkiestracyjnej use-case; tylko wykonanie operacji technicznych parametryzowanych przez Application.

## 5) Pliki per warstwa i odpowiedzialności

## API (`src/Backend/Sudoku/Sudoku`)
- `Controllers/DatasetsController.cs` (modyfikacja)  
  - dodać akcję `POST /api/datasets/processed`.
  - mapowanie wyjątków aplikacyjnych na `400/401/404/409/422/503/504`.
- `Contracts/CreateProcessedDatasetApiEntry.cs` (nowy)  
  - model wejścia HTTP.
- `Contracts/SelectedRawDatasetSourceApiEntry.cs` (nowy)  
  - model źródła z polami `name`, `type`, `splits`.
- `Contracts/ProcessedDatasetApiResponse.cs` (nowy)  
  - model wyjścia `201`.
- `Contracts/ProcessedDatasetSourceReportApiResponse.cs` (nowy)  
  - raport per źródło.
- `Contracts/SplitSampleCountsApiResponse.cs` (nowy)  
  - liczności splitów.
- `Contracts/ErrorApiResponse.cs` (istnieje, reuse)  
  - wspólny kontrakt błędów.

## Application (`src/Backend/Sudoku/Application`)
- `Datasets/CreateProcessedDatasetCommand.cs` (nowy)  
  - wejście use-case.
- `Datasets/CreateProcessedDatasetCommandValidator.cs` (nowy)  
  - walidacje: `name`, `sources`, unikalność źródeł, reguły `mix`.
- `Datasets/CreateProcessedDatasetCommandHandler.cs` (nowy)  
  - główna orkiestracja use-case.
- `Datasets/CreateProcessedDatasetCommandResultDto.cs` (nowy)  
  - wynik use-case do API.
- `Datasets/CreateProcessedDatasetErrorTypes.cs` (nowy)  
  - stałe `errorType`.
- `Datasets/ProcessedDatasetSourceReportDto.cs` (nowy)  
  - raport źródła w warstwie aplikacyjnej.
- `Datasets/SplitSampleCountsDto.cs` (nowy)  
  - liczności splitów.
- `Datasets/PrepareDatasetArtifactRequestDto.cs` (nowy)  
  - DTO requestu do gateway ML.
- `Datasets/PrepareDatasetArtifactSourceDto.cs` (nowy)  
  - źródło + split policy do ML.
- `Datasets/DatasetSplitPolicyDto.cs` (nowy)  
  - `mode`, `ratios`, `groupBy`.
- `Datasets/PrepareDatasetArtifactResultDto.cs` (nowy)  
  - odpowiedź z ML zmapowana do Application.
- `Datasets/PreparedDatasetSourceReportDto.cs` (nowy)  
  - raport źródła z ML.
- `Datasets/DatasetsPreparationOptions.cs` (nowy)  
  - absolutne ścieżki i domyślne ratio/profil.
- `Datasets/DatasetsPreparationDefaults.cs` (nowy, opcjonalny)  
  - wartości i normalizacja domyślnych ustawień.
- `Abstractions/IMlDatasetsPreparationGateway.cs` (nowy)  
  - port `BE -> ML` dla `POST /ml/datasets/prepare`.
- `Abstractions/IProcessedDatasetsGateway.cs` (nowy)  
  - port do zapisu/odczytu finalnych artefaktów i metadanych.
- `Abstractions/IFileStorageGateway.cs` (istnieje, reuse)  
  - potwierdzone: wystarczające do operacji plikowych; nie tworzyć duplikatu usług storage.
- `Datasets/ListRawDatasetCandidatesQuery*.cs` (istnieją, reuse)  
  - źródło prawdy kandydatów z `UC-11`.

## Domain (`src/Backend/Sudoku/Models`)
- Obecnie brak dedykowanych modeli dataset preparation; dla UC-12 preferowane są DTO use-case w `Application/Datasets`.
- Guardrail: nie przenosić kontraktów HTTP do `Models`; `Models` pozostają niezależne od transportu.

## Infrastructure (`src/Backend/Sudoku/Infrastructure`)
- `Ml/MlDatasetsPreparationHttpClient.cs` (nowy)  
  - implementacja `IMlDatasetsPreparationGateway`.
  - mapowanie statusów i błędów (`422`, `503`, `504`, payload `errorType/message`).
- `Storage/ProcessedDatasetsGateway.cs` (nowy)  
  - implementacja `IProcessedDatasetsGateway`.
  - zapis finalnego `{name}.npz`, odczyt metadanych przygotowania.
- `Storage/LocalFileStorageGateway.cs` (istnieje, reuse)  
  - już generyczny; użyć przez nowy gateway, nie duplikować kodu I/O.
- `Configuration/MlServiceOptions.cs` (modyfikacja)  
  - dodać `PrepareDatasetPath`.
- `DependencyInjection.cs` (modyfikacja)  
  - rejestracja nowych gatewayów i HttpClient.

## Composition root / config (`src/Backend/Sudoku/Sudoku`)
- `Program.cs` (modyfikacja)  
  - bind i walidacja `DatasetsPreparationOptions` (ścieżki absolutne, ratio sum = 1.0).
- `appsettings.local.json` (modyfikacja)  
  - twarde lokalne ścieżki absolutne dla `boards`, `digits`, `processed`, `tmp/datasets`, profile i ratio.
- `appsettings.production.json` (modyfikacja)  
  - placeholdery dla wartości nadpisywanych przez workflow.

## Workflow (`.github/workflows`)
- `backend-cd.yml` (modyfikacja)  
  - rozszerzyć walidację zmiennych i generator `appsettings.production.json` o sekcję `DatasetsPreparation` dla UC-12.

## 6) Weryfikacja istniejących usług Infrastructure (anti-duplication)
- Sprawdzone: `IFileStorageGateway` + `LocalFileStorageGateway` już istnieją i są generyczne (`SaveAsync`, `OpenReadAsync`, `ListFilesAsync`, `ListDirectoriesAsync`).
- Wniosek: nie tworzymy nowego adaptera lokalnego storage tylko dla UC-12.
- Nowe gatewaye w Infrastructure mają być cienkimi adapterami orkiestrującymi operacje przez istniejące generyczne porty, tak aby reuse był możliwy w kolejnych UC.

## 7) Przepływ BE (end-to-end)
1. `API` odbiera `POST /api/datasets/processed` (token wymagany).
2. Request mapowany do `CreateProcessedDatasetCommand`.
3. `Validator` sprawdza format i reguły (`mix` vs jawne splity, duplikaty, name).
4. Handler pobiera kandydatów z mechanizmu `UC-11` (nie ufa bezpośrednio `type` z FE).
5. Handler buduje `splitPolicy` per źródło:
   - `mix` -> ratio z konfiguracji;
   - jawne splity -> ratio wyliczone dla wskazanych partycji;
   - `groupBy = board` dla `board`, `sample` dla `digit`.
6. Handler wywołuje `IMlDatasetsPreparationGateway`.
7. `ML` odkłada artefakt tymczasowy `tmp/{datasetName}.npz` i zwraca raport.
8. Handler zleca `IProcessedDatasetsGateway` skopiowanie/utrwalenie finalnego pliku `{name}.npz` do `processedDatasetsDirectoryPath`.
9. Handler zapisuje metadane przygotowania (co najmniej: `preprocessingProfile`, `sampleCounts`, `sourceReports`, `warnings`, `createdAtUtc`).
10. API zwraca `201` z `ProcessedDatasetApiResponse`.

## 8) Główne funkcje do zaimplementowania
- `CreateProcessedDatasetCommandHandler.Handle(...)`
- `CreateProcessedDatasetCommandValidator.Validate(...)`
- `BuildSplitPolicy(...)`
- `ValidateSelectedSourcesAgainstRawCandidates(...)`
- `EnsureProcessedDatasetNameIsAvailable(...)`
- `PrepareDatasetWithMlAsync(...)`
- `PersistPreparedDatasetArtifactAsync(...)`
- `MapPreparedArtifactToPublicResponse(...)`
- `MlDatasetsPreparationHttpClient.PrepareAsync(...)`
- `ProcessedDatasetsGateway.SavePreparedDatasetAsync(...)`

## 9) Wyjątki i fallbacki

### Walidacja wejścia
- `name` puste / whitespace -> `400 invalid_request`.
- `sources` puste -> `400 invalid_request`.
- `splits` zawiera `mix` + inne wartości -> `400 invalid_dataset_split_selection`.
- duplikat `source.name + type` -> `400 invalid_request`.

### Spójność źródeł
- źródło zniknęło od czasu `UC-11` -> `404 raw_dataset_not_found`.
- `type` niezgodny z aktualnie wykrytym kandydatem -> `422 raw_dataset_type_mismatch`.

### Konflikty zapisu
- `{name}.npz` już istnieje -> `409 processed_dataset_name_conflict`.
- fallback: brak automatycznego nadpisania; użytkownik wybiera inną nazwę.

### Integracja ML
- `503/5xx` z ML -> `503 ml_unavailable`.
- timeout requestu do ML -> `504 ml_timeout`.
- `422` z ML -> `422 dataset_source_invalid` (lub bardziej szczegółowy `errorType` z ML).
- fallback: brak retry automatycznego w API request-response; klient FE może ponowić ręcznie.

### Artefakt tymczasowy/finalny
- brak artefaktu tymczasowego po sukcesie ML -> `503` (niespójność transport/storage).
- błąd kopiowania do finalnego katalogu -> `500` lub `503` zależnie od typu błędu I/O.
- fallback: best-effort cleanup artefaktu tymczasowego, bez pozostawiania pół-zapisu finalnego.

## 10) Pseudokod kluczowej logiki (specyficznej)

```text
handle(command):
  validate(command)
  ensureAdminScope()

  candidates = loadRawCandidatesFromUc11()
  ensureSourcesMatchCandidates(command.sources, candidates)
  ensureNoNameConflict(command.name)

  preprocessingProfile = options.defaultPreprocessingProfile
  mlRequest.sources = []

  for source in command.sources:
    policy = buildSplitPolicy(source.splits, source.type, options.defaultMixSplitRatios)
    mlRequest.sources.add({name: source.name, type: source.type, splitPolicy: policy})

  mlResult = mlGateway.prepareDataset({
    datasetName: command.name,
    sources: mlRequest.sources,
    preprocessingProfile: preprocessingProfile
  })

  if (sum(mlResult.sampleCounts) == 0):
    throw 422 no_samples_prepared

  finalFileName = command.name + ".npz"
  processedGateway.promoteTempArtifactToProcessed(command.name, finalFileName)
  processedGateway.saveMetadata(...)

  return mapResult(finalFileName, preprocessingProfile, mlResult, command.sources)
```

## 11) Reguły implementacyjne (guardraile)
- `Infrastructure` implementuje technikalia; `Application` trzyma logikę use-case.
- Nie hardkodować ścieżek runtime; wyłącznie typed options (`appsettings` + env override).
- Nie ufać `type` z FE bez weryfikacji względem bieżących kandydatów z `UC-11`.
- `mix` jest wykluczające wobec jawnych splitów dla pojedynczego źródła.
- Dla `board` wymuszać `groupBy=board` (ochrona przed data leakage między splitami).
- Nie przepisywać kontraktów FE na bazie aktualnego stanu FE; źródłem jest PRD + feature spec UC-12.
- JSON w `camelCase`, nazewnictwo modeli: `ApiEntry`/`ApiResponse`, DTO: `Dto`.
- Logować błędy integracyjne (`ML`, `I/O`) z kontekstem `datasetName`, bez logowania sekretów.

## 12) Inne istotne reguły
- Idempotencja biznesowa przez nazwę: ten sam `name` drugi raz -> `409`, brak nadpisania.
- `createdAtUtc` generowane przez backend (`TimeProvider`), nie z wejścia FE.
- Metadane raportowe przechowywać po stronie BE dla późniejszego `GET /api/datasets/processed`.
- Zachować deterministyczne mapowanie `sources` i raportów (kolejność zgodna z requestem).
- Komunikaty błędów dla FE zawsze przez `ErrorApiResponse` (`errorType`, `message`).

## 13) Zależności między historyjkami
- Zrealizowane i wymagane wejściowo:
  - `UC-13` (autoryzacja admin) - wymagane.
  - `UC-11` (lista raw candidates) - wymagane.
- Wykorzystane pośrednio:
  - `UC-01`, `UC-02`, `UC-04` - dają gotowe wzorce storage + ML client + error mapping.
- Zależność wyjściowa:
  - `UC-12` dostarcza artefakty wejściowe dla `UC-06` (`POST /api/trainings`).

## 14) Kolejność implementacji kodu
1. Dodać kontrakty API (`ApiEntry/ApiResponse`) dla `POST /api/datasets/processed`.
2. Dodać DTO, command i validator w `Application`.
3. Dodać porty `IMlDatasetsPreparationGateway` i `IProcessedDatasetsGateway`.
4. Zaimplementować handler use-case z pełną logiką splitów i walidacją źródeł.
5. Dodać implementację `MlDatasetsPreparationHttpClient` w `Infrastructure`.
6. Dodać `ProcessedDatasetsGateway` (promocja artefaktu tymczasowego + metadane).
7. Rozszerzyć `DatasetsController` o nową akcję `POST`.
8. Rozszerzyć `MlServiceOptions` + `Program.cs` + `appsettings*` o UC-12 options.
9. Rozszerzyć `backend-cd.yml` o zmienne i generację produkcyjnych wartości sekcji UC-12.
10. Testy jednostkowe validatora/handlera + testy integracyjne endpointa.

## 15) Workflow GitHub i konfiguracja środowiskowa
- Zgodnie z zasadą projektu:
  - lokalnie wartości wpisujemy na sztywno do `appsettings.local.json`,
  - produkcyjnie wartości są wstrzykiwane przez workflow i wpisywane do `appsettings.production.json`.
- Do dodania/utrzymania w `backend-cd.yml` (env `main`):
  - `BE_DATASETS_PREP_BOARDS_SUBDIRECTORY`
  - `BE_DATASETS_PREP_DIGITS_SUBDIRECTORY`
  - `BE_DATASETS_PREP_PROCESSED_DIRECTORY_PATH`
  - `BE_DATASETS_PREP_TEMPORARY_ARTIFACTS_DIRECTORY_PATH`
  - `BE_DATASETS_PREP_DEFAULT_PREPROCESSING_PROFILE`
  - `BE_DATASETS_PREP_DEFAULT_MIX_TRAIN_RATIO`
  - `BE_DATASETS_PREP_DEFAULT_MIX_VAL_RATIO`
  - `BE_DATASETS_PREP_DEFAULT_MIX_TEST_RATIO`
  - opcjonalnie `BE_ML_PREPARE_DATASET_PATH`
- Generator `appsettings.production.json` musi ustawić finalnie sekcje:
  - `DatasetsPreparation.*`
  - `MlService.PrepareDatasetPath`
- Runtime produkcyjny pozostaje uruchamiany z `SUDOKU_ENVIRONMENT=production`.

## 16) Plan testów akceptacyjnych (BE)
- `201`: poprawny request mieszany (`board` + `digit`) i poprawne raporty.
- `400`: niepoprawne `splits` (`mix` + `train`).
- `401`: brak tokenu.
- `404`: źródło nie istnieje.
- `409`: konflikt nazwy `{name}.npz`.
- `422`: `type` mismatch oraz przypadek `no_samples_prepared`.
- `503/504`: niedostępność i timeout ML.
- Walidacja side-effect: finalny plik `{name}.npz` w `processed`, metadane zapisane, brak uszkodzonych pół-produktów po błędach.
