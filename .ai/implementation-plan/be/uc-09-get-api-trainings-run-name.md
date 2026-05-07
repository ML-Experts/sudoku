# UC-09-BE - Plan implementacyjny dla `GET /api/trainings/{runName}`

## 1) Przeznaczenie endpointa
- Endpoint `GET /api/trainings/{runName}` zwraca chronione szczegóły pojedynczego runu treningowego.
- Dane mają zasilać widok `UC-09`: konfigurację eksperymentu, status, postęp, model bazowy, model wynikowy, dataset, benchmark, metryki, historię treningu i confusion matrix.
- Backend pozostaje `source of truth` dla publicznego stanu runu. `FE` nie czyta plików runtime i nie komunikuje się z `ML`.
- Endpoint jest read-only: nie startuje treningu, nie anuluje runu, nie finalizuje modelu i nie próbuje naprawiać stanu plikowego.
- `runName` jest jedynym identyfikatorem runu i musi pozostać zgodny z kontraktami z `UC-06`, `UC-07` i `UC-08`.

## 2) Zakres i założenia
- Plan dotyczy wyłącznie części BE dla endpointa `GET /api/trainings/{runName}`.
- Nie opierać kontraktu ani reguł na bieżącej implementacji `FE` lub `ML`; źródłem są `PRD`, `UC-09`, kontrakty `UC-06`, reguły architektury backendu i dokumentacja deployu/runtime.
- Endpoint jest chroniony tokenem administracyjnym z `UC-13`.
- Źródłem głównym jest rekord `trainings/metadata/{runName}.json` utrzymywany przez Backend.
- Raporty `ML` są plikowym kontraktem technicznym czytanym przez Backend tylko przez skonfigurowany katalog `TrainingsStorage.ReportsDirectoryPath`.
- Backend nie ujawnia `FE` absolutnych ścieżek, nazw plików raportów ani technicznych lokalizacji artefaktów.
- Jeśli podstawowy odczyt runu istnieje po `UC-06`, `UC-09` rozszerza go o manifesty modeli, metadata datasetu i raporty.
- Na obecnym stanie repo część elementów jest już gotowa i należy je reużyć: `ITrainingRunsGateway`, `TrainingRunsGateway`, `IModelsRegistryGateway`, `ModelsRegistryGateway`, `IProcessedDatasetsGateway`, `TrainingsStorageOptions`, `ModelsRegistryStorageOptions`, `ProcessedDatasetMetadataDto`, `RegistryModelManifestDto`, `TrainingRunMetadataDto`, `TrainingReportStatus`.
- Na obecnym stanie repo w `TrainingsController` widać zarys akcji `GetByRunNameAsync`, ale klasy typu `GetTrainingRunDetailsQuery`, `TrainingRunDetailsDto` i publiczne kontrakty szczegółów nie są jeszcze kompletne. Traktować to jako pracę do domknięcia, nie jako powód do zmiany nazw uzgodnionych w kontrakcie.

## 3) Kontrakty API FE i ML

### 3.1 FE -> BE (`GET /api/trainings/{runName}`)
- Request body: brak.
- Route param:
  - `runName: string`.
- Autoryzacja: token administracyjny (`Bearer`).
- Publiczny JSON: `camelCase`.

### 3.2 Odpowiedzi publiczne
- `200 OK` -> `TrainingRunDetailsApiResponse`.
- `400 Bad Request` -> `ErrorApiResponse`, jeśli `runName` jest pusty albo ma niedozwolony format.
- `401 Unauthorized` -> brak albo niepoprawny token.
- `404 Not Found` -> brak `trainings/metadata/{runName}.json`.
- `409 Conflict` -> rekord istnieje, ale wskazuje niespójne lub niebezpieczne referencje, np. `baseModelName` pusty, `producedModelName` sprzeczny ze statusem, referencja raportu wychodzi poza katalog runu.
- `422 Unprocessable Entity` -> raport istnieje, ale nie spełnia kontraktu publicznego, np. niepoprawny JSON metryk, macierz o złych wymiarach, brak wymaganego pola metryki w raporcie oznaczonym jako `ready`.
- `500 Internal Server Error` -> błąd I/O, uprawnień, deserializacji metadanych albo nieoczekiwana niespójność storage.

### 3.3 Model wejściowy/wyjściowy FE
- Wejście FE -> BE:
  - brak body,
  - `runName` w ścieżce.
- Wyjście BE -> FE:
  - `TrainingRunDetailsApiResponse`.

Przykład odpowiedzi:

```json
{
  "runName": "train-20260503-112233",
  "status": "succeeded",
  "stage": "finished",
  "createdAtUtc": "2026-05-03T09:22:33Z",
  "startedAtUtc": "2026-05-03T09:23:02Z",
  "finishedAtUtc": "2026-05-03T09:40:12Z",
  "baseModel": {
    "name": "cnn-bootstrap",
    "displayName": "CNN bootstrap",
    "sourceType": "bootstrap",
    "sourceRunName": null,
    "parentModelName": null,
    "inputProfile": "default-28x28-v1",
    "canUseForInference": true,
    "canStartTraining": true
  },
  "producedModel": {
    "name": "train-20260503-112233",
    "displayName": "train-20260503-112233",
    "sourceType": "training",
    "sourceRunName": "train-20260503-112233",
    "parentModelName": "cnn-bootstrap",
    "inputProfile": "default-28x28-v1",
    "canUseForInference": true,
    "canStartTraining": true
  },
  "dataset": {
    "processedDatasetName": "sudokuDigitsV1",
    "preprocessingProfile": "default-28x28-v1",
    "sampleCounts": {
      "train": 9657,
      "val": 2657,
      "test": 1000
    }
  },
  "configuration": {
    "trainingMode": "fineTuning",
    "trainingProfileName": "cnn-default-v1",
    "augmentationProfileName": "digits-light-v1",
    "benchmarkName": "sudoku-benchmark-v1",
    "seed": 1234,
    "sourceRevision": null
  },
  "progress": {
    "percent": 100,
    "epoch": 10,
    "totalEpochs": 10,
    "trainLoss": 0.08,
    "validationLoss": 0.11,
    "trainAccuracy": 0.98,
    "validationAccuracy": 0.96
  },
  "report": {
    "status": "ready",
    "summary": {
      "accuracy": 0.96,
      "precisionMacro": 0.95,
      "recallMacro": 0.95,
      "f1Macro": 0.95,
      "trainingDurationSeconds": 1050,
      "averageInferenceTimeMs": 12.4
    },
    "perClassMetrics": [
      {
        "label": "1",
        "precision": 0.97,
        "recall": 0.96,
        "f1": 0.96,
        "support": 120
      }
    ],
    "history": [
      {
        "epoch": 1,
        "trainLoss": 0.42,
        "validationLoss": 0.39,
        "trainAccuracy": 0.84,
        "validationAccuracy": 0.86
      }
    ],
    "confusionMatrix": {
      "classNames": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
      "matrix": [
        [100, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 118, 1, 0, 0, 0, 0, 1, 0, 0]
      ]
    }
  },
  "warnings": []
}
```

### 3.4 BE <-> ML dla tego endpointa
- Brak nowego endpointu `BE -> ML`.
- Brak nowego endpointu `ML -> BE`.
- `GET /api/trainings/{runName}` korzysta wyłącznie z danych zapisanych wcześniej przez workflow `UC-06`:
  - `POST /api/trainings`,
  - `POST /internal/ml/trainings/{runName}/events`,
  - finalizacja modelu wynikowego w `models/registry`.
- Pliki raportów zapisane przez `ML` są czytane przez Backend jako runtime state, ale nie są wystawiane jako pliki do pobrania.

## 4) Zachowanie per warstwa

### API (`Sudoku`)
- Kontroler pozostaje cienki:
  - wymusza `[Authorize]`,
  - binduje `runName` z trasy,
  - wysyła `GetTrainingRunDetailsQuery` przez MediatR,
  - mapuje DTO aplikacyjne na `TrainingRunDetailsApiResponse`,
  - mapuje wyjątki aplikacyjne na `ErrorApiResponse`.
- API nie czyta plików, nie parsuje JSON, nie waliduje manifestów modeli i nie składa ścieżek raportów.
- API nie zwraca absolutnych ścieżek ani pełnych manifestów modeli.

### Application (`Application`)
- Właściwa logika use-case'u:
  - waliduje `runName` przez FluentValidation,
  - pobiera metadane runu przez `ITrainingRunsGateway.GetByRunNameAsync`,
  - odrzuca brak runu jako `404`,
  - waliduje minimalne pola rekordu potrzebne do szczegółów,
  - pobiera model bazowy przez `IModelsRegistryGateway.GetByNameAsync`,
  - pobiera model wynikowy przez `IModelsRegistryGateway.GetByNameAsync`, jeśli `ProducedModelName` istnieje i run może mieć model wynikowy,
  - pobiera metadata datasetu przez `IProcessedDatasetsGateway.GetByNameAsync`,
  - na podstawie `ReportStatus` i `ReportArtifacts` decyduje, czy czytać raporty przez `ITrainingReportsGateway`,
  - mapuje metadane, manifesty, dataset i raporty na `TrainingRunDetailsDto`.
- Application decyduje o semantyce braków:
  - brak runu to `404`,
  - brak dataset metadata przy istniejącym runie nie musi blokować odpowiedzi; może dać `dataset.preprocessingProfile = null`, `sampleCounts = null` i ostrzeżenie,
  - brak modelu bazowego zwykle oznacza niespójny stan i `409`,
  - brak modelu wynikowego dla runu `succeeded` z `canUseProducedModelForInference = true` oznacza `409`,
  - brak raportu przy `reportStatus = missing | corrupted | pending` nie jest `500`.
- Application nie zna technicznych API filesystem i nie używa `File.*`, `Directory.*` ani `JsonDocument`.

### Domain / Models (`Models`)
- Reużyć neutralne modele statusów, jeśli są potrzebne do spójnej semantyki:
  - `Models/Trainings/TrainingReportStatus.cs`,
  - istniejące modele statusów runu, jeśli są obecne.
- Dla `UC-09` nie trzeba dodawać nowych modeli domenowych, jeśli logika pozostaje orkiestracją odczytu rekordów systemowych.
- Nie przenosić kontraktów HTTP ani DTO raportów do `Models`.

### Infrastructure (`Infrastructure`)
- Implementuje techniczne porty:
  - `ITrainingRunsGateway` odczytuje `trainings/metadata/{runName}.json`,
  - `IModelsRegistryGateway` odczytuje `models/registry/{modelName}/model.json`,
  - `IProcessedDatasetsGateway` odczytuje metadata przygotowanych datasetów,
  - `ITrainingReportsGateway` czyta pliki raportów z `TrainingsStorage.ReportsDirectoryPath`.
- Infrastructure może walidować techniczną kompletność i bezpieczeństwo ścieżek względnych, ale nie decyduje, czy brak metryk jest biznesowo dopuszczalny.
- Jeśli brakuje operacji odczytu raportów, dodać ją jako generyczny port `ITrainingReportsGateway`, nie jako kod w kontrolerze ani handlerze.
- Nie tworzyć osobnych adapterów typu `TrainingDetailsFileReader`, jeśli istniejące gatewaye można rozszerzyć generycznie.

## 5) Pliki per warstwa i odpowiedzialności

### API (`src/Backend/Sudoku/Sudoku`)
- `[REUSE/UTWARDZENIE]` `Controllers/TrainingsController.cs`
  - akcja `GetByRunNameAsync` dla `GET /api/trainings/{runName}`,
  - `[Authorize]`, `[HttpGet("{runName}")]`,
  - wywołanie `GetTrainingRunDetailsQuery`,
  - mapowanie `TrainingRunDetailsDto` -> `TrainingRunDetailsApiResponse`,
  - mapowanie `ValidationException` -> `400`,
  - mapowanie `TrainingRunDetailsNotFoundException` -> `404`,
  - mapowanie `TrainingRunDetailsConflictException` -> `409`,
  - mapowanie `TrainingRunReportInvalidException` -> `422`,
  - mapowanie błędów I/O/deserializacji -> `500`,
  - lekkie logi rozpoczęcia, sukcesu i błędów.
- `[DODAĆ]` `Contracts/TrainingRunDetailsApiResponse.cs`
  - publiczny model odpowiedzi endpointa.
- `[DODAĆ]` `Contracts/TrainingRunModelReferenceApiResponse.cs`
  - publiczny skrót manifestu modelu bez ścieżek i artefaktów.
- `[DODAĆ]` `Contracts/TrainingRunDatasetDetailsApiResponse.cs`
  - nazwa datasetu, profil preprocessingu i sample counts.
- `[DODAĆ]` `Contracts/TrainingDatasetSampleCountsApiResponse.cs`
  - `train`, `val`, `test`.
- `[DODAĆ]` `Contracts/TrainingRunConfigurationApiResponse.cs`
  - `trainingMode`, profile, benchmark, `seed`, `sourceRevision`.
- `[DODAĆ]` `Contracts/TrainingRunReportApiResponse.cs`
  - `status`, `summary`, `perClassMetrics`, `history`, `confusionMatrix`.
- `[DODAĆ]` `Contracts/TrainingReportSummaryApiResponse.cs`
  - accuracy, precision/recall/F1 macro, czasy treningu i inferencji.
- `[DODAĆ]` `Contracts/TrainingClassMetricApiResponse.cs`
  - metryki per klasa.
- `[DODAĆ]` `Contracts/TrainingMetricHistoryPointApiResponse.cs`
  - historia metryk po epokach.
- `[DODAĆ]` `Contracts/TrainingConfusionMatrixApiResponse.cs`
  - `classNames` i `matrix`.
- `[REUSE]` `Contracts/TrainingRunProgressApiResponse.cs`
  - publiczny model postępu już używany przez listę i eventy.
- `[REUSE]` `Contracts/ErrorApiResponse.cs`
  - wspólny kontrakt błędu `errorType`, `message`.
- `[REUSE]` `Program.cs`
  - rejestracja kontrolerów, autoryzacji, MediatR, FluentValidation i options.
- `[REUSE]` `appsettings.local.json`
  - lokalne, absolutne ścieżki `TrainingsStorage.*`, `ModelsRegistryStorage.*`, `DatasetsPreparation.ProcessedDatasetsDirectoryPath`.
- `[REUSE]` `appsettings.production.json`
  - placeholdery produkcyjne podstawiane przez workflow.

### Application (`src/Backend/Sudoku/Application`)
- `[DODAĆ]` `Trainings/GetTrainingRunDetailsQuery.cs`
  - query MediatR z `RunName`.
- `[DODAĆ]` `Trainings/GetTrainingRunDetailsQueryValidator.cs`
  - walidacja `runName`: wymagane, rozsądna długość, brak separatorów ścieżek, brak `..`, brak znaków kontrolnych.
- `[DODAĆ]` `Trainings/GetTrainingRunDetailsQueryHandler.cs`
  - orkiestracja odczytu metadanych, manifestów, datasetu i raportów.
- `[DODAĆ]` `Trainings/GetTrainingRunDetailsErrorTypes.cs`
  - stałe `errorType` dla błędów publicznych.
- `[DODAĆ]` `Trainings/TrainingRunDetailsDto.cs`
  - główny DTO szczegółów runu dla API.
- `[DODAĆ]` `Trainings/TrainingRunModelReferenceDto.cs`
  - bezpieczny skrót manifestu modelu.
- `[DODAĆ]` `Trainings/TrainingRunDatasetDetailsDto.cs`
  - dane datasetu użytego w runie.
- `[DODAĆ]` `Trainings/TrainingDatasetSampleCountsDto.cs`
  - próbki `train`, `val`, `test`, jeśli nie można bezpośrednio reużyć `SplitSampleCountsDto`.
- `[DODAĆ]` `Trainings/TrainingRunConfigurationDto.cs`
  - konfiguracja runu.
- `[DODAĆ]` `Trainings/TrainingRunReportDto.cs`
  - publicznie bezpieczny agregat raportu.
- `[DODAĆ]` `Trainings/TrainingReportSummaryDto.cs`
  - skrót raportu końcowego.
- `[DODAĆ]` `Trainings/TrainingClassMetricDto.cs`
  - metryki per klasa.
- `[DODAĆ]` `Trainings/TrainingMetricHistoryPointDto.cs`
  - historia metryk.
- `[DODAĆ]` `Trainings/TrainingConfusionMatrixDto.cs`
  - macierz pomyłek.
- `[DODAĆ]` `Trainings/TrainingRunDetailsNotFoundException.cs`
  - brak rekordu metadanych runu.
- `[DODAĆ]` `Trainings/TrainingRunDetailsConflictException.cs`
  - niespójność metadanych, modeli, datasetu lub referencji.
- `[DODAĆ]` `Trainings/TrainingRunReportInvalidException.cs`
  - raport istnieje, ale nie spełnia kontraktu.
- `[DODAĆ/REUSE]` `Abstractions/ITrainingReportsGateway.cs`
  - jeśli istnieje w kodzie, rozbudować; jeśli nie, dodać port odczytu raportów.
- `[REUSE]` `Abstractions/ITrainingRunsGateway.cs`
  - `GetByRunNameAsync`.
- `[REUSE]` `Abstractions/IModelsRegistryGateway.cs`
  - `GetByNameAsync`.
- `[REUSE]` `Abstractions/IProcessedDatasetsGateway.cs`
  - `GetByNameAsync`.
- `[REUSE]` `Trainings/TrainingRunMetadataDto.cs`
  - główny rekord stanu runu; nie zmieniać nazw istniejących pól z `UC-06`.
- `[REUSE]` `Trainings/TrainingRunProgressDto.cs`
  - postęp runu.
- `[REUSE]` `Trainings/TrainingMetricsSummaryDto.cs`
  - skrót metryk z metadanych.
- `[REUSE]` `Trainings/TrainingsStorageOptions.cs`
  - ścieżki runtime dla `metadata`, `reports`, `runs`, `working`.
- `[REUSE]` `ModelsRegistry/RegistryModelManifestDto.cs`
  - skrót manifestu modelu.
- `[REUSE]` `Datasets/ProcessedDatasetMetadataDto.cs`
  - metadata przygotowanego datasetu.
- `[REUSE]` `Datasets/SplitSampleCountsDto.cs`
  - sample counts, jeśli pasuje do publicznego mapowania.

### Domain / Models (`src/Backend/Sudoku/Models`)
- `[REUSE]` `Trainings/TrainingReportStatus.cs`
  - kanoniczne wartości `ready`, `missing`, `corrupted`, `pending`; przy implementacji nie wprowadzać alternatywnych nazw.
- `[REUSE POŚREDNI]` istniejące modele statusów runu, jeśli są obecne.
- `[BRAK NOWEGO PLIKU]`
  - dla `GET /api/trainings/{runName}` nie dodawać nowych modeli domenowych, dopóki nie pojawi się realna logika domenowa niezależna od odczytu rekordów systemowych.

### Infrastructure (`src/Backend/Sudoku/Infrastructure`)
- `[REUSE]` `Storage/TrainingRunsGateway.cs`
  - odczyt `trainings/metadata/{runName}.json`,
  - deserializacja `TrainingRunMetadataDto`,
  - brak reguł biznesowych.
- `[REUSE]` `Storage/ModelsRegistryGateway.cs`
  - odczyt manifestów modelu bazowego i wynikowego,
  - walidacja techniczna manifestu i bezpiecznych ścieżek artefaktów,
  - brak decyzji, czy model ma być pokazany jako wynik runu.
- `[REUSE]` `Storage/ProcessedDatasetsGateway.cs`
  - `GetByNameAsync` dla metadanych datasetu przetworzonego.
- `[DODAĆ/UTWARDZIĆ]` `Storage/TrainingReportsGateway.cs`
  - odczyt `summary.json`, `metrics.json`, `confusion_matrix.json` przez referencje względne,
  - użycie `TrainingsStorage.ReportsDirectoryPath`,
  - blokada path traversal i ścieżek absolutnych,
  - deserializacja do DTO technicznych albo neutralnych DTO aplikacyjnych,
  - rzucanie `InvalidDataException` dla niepoprawnego kontraktu pliku.
- `[REUSE]` `Storage/LocalFileStorageGateway.cs`
  - generyczny odczyt/listowanie plików; nie dodawać bezpośrednich `File.*` w handlerze.
- `[REUSE/UTWARDZENIE]` `DependencyInjection.cs`
  - rejestracja `ITrainingReportsGateway -> TrainingReportsGateway`, jeśli nie jest jeszcze gotowa,
  - istniejące rejestracje `ITrainingRunsGateway`, `IModelsRegistryGateway`, `IProcessedDatasetsGateway`.
- `[BRAK ZMIAN]` `Ml/*`
  - endpoint szczegółów nie wywołuje `ML`.

### Workflow (`.github/workflows`)
- `[REUSE/ZWERYFIKOWAĆ]` `.github/workflows/backend-cd.yml`
  - dla tego endpointa nie trzeba dodawać nowych zmiennych, jeśli istnieją:
    - `BE_TRAININGS_METADATA_DIRECTORY_PATH`,
    - `BE_TRAININGS_REPORTS_DIRECTORY_PATH`,
    - `BE_MODELS_REGISTRY_DIRECTORY_PATH`,
    - `BE_DATASETS_PREP_PROCESSED_DIRECTORY_PATH`.
  - workflow ma podstawiać `appsettings.production.json`, a local ma mieć wartości wpisane na sztywno w `appsettings.local.json`.
  - workflow nie może czyścić ani nadpisywać `/opt/sudoku/shared/trainings`, `/opt/sudoku/shared/models` ani `/opt/sudoku/shared/data`.
  - ponieważ `MlServiceOptions` waliduje całą sekcję przy starcie aplikacji, niezależnie od `UC-09` należy zweryfikować, czy workflow po `UC-06` podstawia też istniejące wartości `BE_ML_START_TRAINING_PATH`, `BE_ML_CANCEL_TRAINING_PATH_TEMPLATE` i `BE_ML_TRAINING_EVENTS_PATH_TEMPLATE`; `UC-09` ich nie używa, ale błędny overlay produkcyjny może zatrzymać Backend przy starcie.

## 6) Weryfikacja usług Infrastructure i antyduplikacja
- Istnieje `ITrainingRunsGateway` i `TrainingRunsGateway`; używać ich jako jedynego adaptera metadanych runów.
- Istnieje `IModelsRegistryGateway` i `ModelsRegistryGateway`; nie tworzyć osobnego readera manifestów dla szczegółów treningu.
- Istnieje `IProcessedDatasetsGateway`; używać `GetByNameAsync` do metadata datasetu zamiast skanowania katalogu w handlerze.
- Jeśli `ITrainingReportsGateway` już istnieje, rozbudować go o brakujące metody odczytu raportu; jeśli nie istnieje, dodać jeden generyczny adapter raportów treningowych.
- Nie dodawać klas typu `TrainingDetailsStorage`, `TrainingReportFileReader` albo `ModelManifestReader`, jeśli dublują istniejące porty.
- Jeśli potrzeba nowej operacji plikowej, najpierw rozszerzyć generycznie `IFileStorageGateway`.

## 7) Przepływ w obrębie BE
1. `FE` wysyła `GET /api/trainings/{runName}` z tokenem admin.
2. Middleware autoryzacji weryfikuje token z `UC-13`.
3. `TrainingsController.GetByRunNameAsync` loguje rozpoczęcie odczytu i wysyła `GetTrainingRunDetailsQuery`.
4. Pipeline FluentValidation waliduje `runName`.
5. `GetTrainingRunDetailsQueryHandler` pobiera metadane przez `ITrainingRunsGateway.GetByRunNameAsync`.
6. Jeśli metadata nie istnieją, handler rzuca `TrainingRunDetailsNotFoundException`.
7. Handler waliduje minimalne pola: `runName`, `status`, `createdAtUtc`, `baseModelName`, `producedModelName`, `processedDatasetName`, profile i `benchmarkName`.
8. Handler pobiera model bazowy przez `IModelsRegistryGateway.GetByNameAsync`.
9. Handler pobiera model wynikowy, jeśli `ProducedModelName` wskazuje realny model wynikowy.
10. Handler pobiera metadata datasetu przez `IProcessedDatasetsGateway.GetByNameAsync`.
11. Handler buduje sekcję `configuration` z rekordu runu.
12. Handler buduje sekcję `progress` z ostatniego znanego postępu w metadata.
13. Handler rozstrzyga `report.status` z `metadata.ReportStatus` albo `pending`, jeśli pole jest puste i run jest aktywny.
14. Jeśli `report.status = ready`, handler odczytuje pliki wskazane w `ReportArtifacts` przez `ITrainingReportsGateway`.
15. `TrainingReportsGateway` waliduje referencje względne względem `trainings/reports/{runName}` i deserializuje raporty.
16. Handler mapuje raporty do DTO publicznego i dodaje ostrzeżenia z metadata oraz z braków opcjonalnych.
17. Kontroler mapuje `TrainingRunDetailsDto` na `TrainingRunDetailsApiResponse`.
18. `FE` otrzymuje dane do widoku szczegółów bez dostępu do plików runtime.

## 8) Główne funkcje
- `TrainingsController.GetByRunNameAsync(...)`
- `TrainingsController.ToTrainingRunDetailsApiResponse(...)`
- `TrainingsController.ToTrainingRunModelReferenceApiResponse(...)`
- `TrainingsController.ToTrainingRunReportApiResponse(...)`
- `GetTrainingRunDetailsQueryValidator.ValidateRunName(...)`
- `GetTrainingRunDetailsQueryHandler.Handle(...)`
- `GetTrainingRunDetailsQueryHandler.LoadMetadataAsync(...)`
- `GetTrainingRunDetailsQueryHandler.LoadBaseModelAsync(...)`
- `GetTrainingRunDetailsQueryHandler.LoadProducedModelAsync(...)`
- `GetTrainingRunDetailsQueryHandler.LoadDatasetDetailsAsync(...)`
- `GetTrainingRunDetailsQueryHandler.LoadReportAsync(...)`
- `GetTrainingRunDetailsQueryHandler.EnsureConsistentDetails(...)`
- `ITrainingRunsGateway.GetByRunNameAsync(...)`
- `IModelsRegistryGateway.GetByNameAsync(...)`
- `IProcessedDatasetsGateway.GetByNameAsync(...)`
- `ITrainingReportsGateway.GetReportAsync(...)`
- `TrainingReportsGateway.GetReportAsync(...)`
- `TrainingReportsGateway.EnsureSafeRelativePath(...)`

## 9) Wyjątki, fallbacki i zachowanie błędowe

### 9.1 Publiczne statusy
- `200 OK`:
  - metadata istnieją,
  - minimalne pola są spójne,
  - odpowiedź może zostać zbudowana nawet bez kompletnego raportu, jeśli `reportStatus` to `pending`, `missing` albo `corrupted`.
- `400 Bad Request`:
  - `runName` pusty,
  - `runName` zawiera `/`, `\`, `..`, `:`, znak kontrolny albo przekracza limit długości.
- `401 Unauthorized`:
  - brak albo niepoprawny token administracyjny.
- `404 Not Found`:
  - brak pliku metadanych dla `runName`.
- `409 Conflict`:
  - model bazowy wskazany w metadata nie istnieje,
  - run `succeeded` wskazuje model wynikowy, którego manifest nie istnieje,
  - `sourceRunName` modelu wynikowego nie zgadza się z `runName`,
  - `parentModelName` modelu wynikowego nie zgadza się z `baseModelName`, jeśli manifest podaje tę wartość,
  - referencje raportów są absolutne albo zawierają path traversal,
  - metadata wskazują stan niemożliwy do bezpiecznego pokazania.
- `422 Unprocessable Entity`:
  - raport oznaczony jako `ready` istnieje, ale nie spełnia kontraktu,
  - `metrics.json.classes` nie jest tablicą,
  - `history` ma ujemne epoki lub wartości niemożliwe do zmapowania,
  - confusion matrix nie jest prostokątną macierzą liczb albo liczba wierszy nie pasuje do `classNames`.
- `500 Internal Server Error`:
  - błąd I/O,
  - brak uprawnień,
  - uszkodzony JSON metadanych runu,
  - błąd deserializacji manifestu lub dataset metadata w istniejącym gatewayu,
  - nieoczekiwany wyjątek storage.

### 9.2 Fallbacki
- Brak fallbacku do `ML`.
- Brak fallbacku do katalogu `trainings/runs/{runName}` dla metryk końcowych.
- Brak fallbacku do `models/registry/{modelName}/artifacts` dla raportu.
- Brak fallbacku do cache po stronie `FE`.
- Brak metadata datasetu:
  - endpoint może zwrócić `dataset.preprocessingProfile = null` i `dataset.sampleCounts = null` z warningiem `processed_dataset_metadata_missing`, bo główny rekord runu nadal istnieje.
- `reportStatus = pending`:
  - nie czytać raportów; zwrócić `report.summary = null`, puste listy metryk i `confusionMatrix = null`.
- `reportStatus = missing`:
  - nie traktować jako `failed`; zwrócić ostrzeżenie i brak metryk końcowych.
- `reportStatus = corrupted`:
  - jeśli metadata już oznaczają raport jako uszkodzony, nie próbować agresywnego parsowania; zwrócić status i ostrzeżenie.
- `reportStatus = ready`, ale plik raportu zniknął:
  - zwrócić `422` albo `409` zależnie od miejsca wykrycia; nie udawać `missing`, bo Backendowy rekord deklarował gotowość.

### 9.3 Scenariusze graniczne
- Run aktywny:
  - zwrócić konfigurację, model bazowy, dataset, progress i `report.status = pending`; `producedModel` może być `null`, jeśli manifest modelu wynikowego nie istnieje jeszcze.
- Run `cancelled`:
  - raport zwykle nie istnieje; zwrócić status runu, konfigurację i ostrzeżenia bez metryk.
- Run `failed`:
  - raport może nie istnieć, bo cleanup usuwa artefakty runtime; zwrócić dane z metadata oraz `report.status` zgodnie z metadata, bez wymuszania metryk.
- Run `succeeded` z `reportStatus = missing | corrupted`:
  - odpowiedź `200`, jeśli model wynikowy i metadata są spójne; UI widzi ostrzeżenie.
- Model bootstrap jako base model:
  - poprawny nawet bez własnego `sourceRunName`.
- `warnings = null` w metadata:
  - Application normalizuje do pustej listy.
- `sourceRevision = null`:
  - poprawne w MVP.

## 10) Pseudokod specyficznej logiki

```c#
handleGetTrainingRunDetails(runName):
  ensure runName validated by FluentValidation

  metadata = trainingRunsGateway.getByRunName(runName)
  if metadata is null:
    throw TrainingRunDetailsNotFoundException(runName)

  ensureRequiredMetadataForDetails(metadata)

  baseModel = modelsRegistryGateway.getByName(metadata.baseModelName)
  if baseModel is null:
    throw TrainingRunDetailsConflictException("base_model_missing")

  producedModel = null
  if shouldLoadProducedModel(metadata):
    producedModel = modelsRegistryGateway.getByName(metadata.producedModelName)
    ensureProducedModelConsistent(metadata, producedModel)

  dataset = processedDatasetsGateway.getByName(metadata.processedDatasetName)
  datasetDetails = mapDatasetOrWarning(metadata.processedDatasetName, dataset)

  reportStatus = metadata.reportStatus ?? resolveDefaultReportStatus(metadata.status)
  report = buildEmptyReport(reportStatus)

  if reportStatus == "ready":
    ensure report artifact refs are present
    report = trainingReportsGateway.getReport(
      runName = metadata.runName,
      summaryRelativePath = metadata.reportArtifacts.summaryRelativePath,
      metricsRelativePath = metadata.reportArtifacts.metricsRelativePath,
      confusionMatrixRelativePath = metadata.reportArtifacts.confusionMatrixRelativePath)

  warnings = normalize(metadata.warnings) + datasetDetails.warnings

  return TrainingRunDetailsDto(
    runName = metadata.runName,
    status = metadata.status,
    stage = metadata.stage,
    dates = metadata.dates,
    baseModel = mapModel(baseModel),
    producedModel = mapOptionalModel(producedModel),
    dataset = datasetDetails,
    configuration = mapConfiguration(metadata),
    progress = metadata.progress,
    report = report,
    warnings = warnings)
```

```c#
trainingReportsGateway.getReport(runName, summaryRelativePath, metricsRelativePath, confusionMatrixRelativePath):
  reportDirectory = combine(reportsDirectoryPath, runName)

  summary = readJson(reportDirectory, ensureSafe(summaryRelativePath))
  metrics = readJson(reportDirectory, ensureSafe(metricsRelativePath))
  confusion = readJson(reportDirectory, ensureSafe(confusionMatrixRelativePath))

  ensure summary.metricsSummary has accuracy, precisionMacro, recallMacro, f1Macro
  ensure metrics.classes is array
  ensure metrics.history is array
  ensure confusion.matrix is rectangular
  ensure confusion.classNames.count == confusion.matrix.rowCount

  return TrainingRunReportDto(...)
```

```c#
ensureSafeRelativePath(path):
  if path is null or whitespace:
    throw TrainingRunDetailsConflictException
  if path is rooted:
    throw TrainingRunDetailsConflictException
  if path contains ".." segment after splitting by "/" and "\\":
    throw TrainingRunDetailsConflictException
  return path
```

## 11) Workflow GitHub i konfiguracja runtime
- Lokalnie:
  - `appsettings.local.json` przechowuje twarde, absolutne ścieżki runtime,
  - dla `UC-09` potrzebne są co najmniej:
    - `TrainingsStorage.MetadataDirectoryPath`,
    - `TrainingsStorage.ReportsDirectoryPath`,
    - `ModelsRegistryStorage.RegistryDirectoryPath`,
    - `DatasetsPreparation.ProcessedDatasetsDirectoryPath`.
- Produkcyjnie:
  - `appsettings.production.json` zawiera placeholdery,
  - `.github/workflows/backend-cd.yml` podstawia wartości z GitHub Variables do produkcyjnego overlayu,
  - workflow nie powinien tworzyć ani czyścić raportów treningowych; są trwałym runtime state.
- Dla tego endpointa nie dodawać nowych zmiennych workflow, jeśli istnieją już zmienne dla `TrainingsStorage`, `ModelsRegistryStorage` i processed datasets.
- Zweryfikować, czy workflow po poprzednich historyjkach nadal podstawia wszystkie opcje walidowane przy starcie Backendu. Nawet jeśli `UC-09` nie wywołuje `ML`, `ValidateOnStart` może zatrzymać aplikację przy brakujących placeholderach z sekcji `MlService`.
- Deploy BE ma publikować kod i `appsettings*.json`, ale nie nadpisywać:
  - `/opt/sudoku/shared/trainings`,
  - `/opt/sudoku/shared/models`,
  - `/opt/sudoku/shared/data`.

## 12) Logging
- Cel: ułatwić diagnozę niespójnych metadanych i raportów bez spamowania i bez ujawniania ścieżek.
- `Information`:
  - rozpoczęto odczyt szczegółów runu z `RunName`,
  - zakończono odczyt z `RunName`, `Status`, `ReportStatus`.
- `Warning`:
  - run nie istnieje,
  - brak modelu bazowego,
  - brak modelu wynikowego dla runu zakończonego sukcesem,
  - brak metadata datasetu przy istniejącym runie,
  - raport oznaczony jako `missing` albo `corrupted`.
- `Error`:
  - raport `ready` nie spełnia kontraktu,
  - błąd odczytu metadanych lub manifestów,
  - niespójne referencje raportów.
- Guardrail:
  - nie logować pełnych treści `metadata.json`, `model.json`, `summary.json`, `metrics.json` ani macierzy pomyłek,
  - nie logować tokenów,
  - nie zwracać absolutnych ścieżek w `ErrorApiResponse`,
  - w logach preferować `runName`, `modelName`, `reportStatus`, `errorType` i nazwę logicznej operacji.

## 13) Kolejność implementacji kodu dla historyjki
1. Zweryfikować istniejący `TrainingsController.GetByRunNameAsync`; jeśli jest tylko szkicem, dopasować go do finalnych klas z tego planu.
2. Dodać publiczne kontrakty `TrainingRunDetailsApiResponse` i powiązane `ApiResponse` w `Sudoku/Contracts`.
3. Dodać `GetTrainingRunDetailsQuery`, validator, handler, DTO i wyjątki w `Application/Trainings`.
4. Spiąć handler z istniejącymi portami `ITrainingRunsGateway`, `IModelsRegistryGateway`, `IProcessedDatasetsGateway`.
5. Zweryfikować lub dodać `ITrainingReportsGateway` i `TrainingReportsGateway` jako generyczny odczyt raportów treningowych.
6. Dodać bezpieczne sprawdzanie referencji względnych raportów.
7. Dodać mapowanie manifestów modeli na `TrainingRunModelReferenceDto`.
8. Dodać mapowanie dataset metadata na `TrainingRunDatasetDetailsDto` z łagodnym warningiem dla braku metadata.
9. Dodać mapowanie raportów `summary`, `metrics`, `confusionMatrix` na publiczny kontrakt.
10. Zarejestrować nowy gateway w `Infrastructure/DependencyInjection.cs`, jeśli jeszcze nie jest zarejestrowany.
11. Zweryfikować `Program.cs`, binding options i `ValidateOnStart`.
12. Zweryfikować `appsettings.local.json` i `appsettings.production.json` dla `TrainingsStorage`, `ModelsRegistryStorage` i processed datasets.
13. Zweryfikować `.github/workflows/backend-cd.yml`, czy podstawia potrzebne wartości produkcyjne.
14. Dodać testy walidatora `runName`.
15. Dodać testy handlera: sukces z pełnym raportem, aktywny run bez raportu, `missing`, `corrupted`, brak runu, brak base model, brak produced model, brak dataset metadata.
16. Dodać testy gatewaya raportów: poprawne pliki, path traversal, brak pliku, uszkodzony JSON, niepoprawna confusion matrix.
17. Dodać testy API/integracyjne dla `200`, `400`, `401`, `404`, `409`, `422`, `500`.

## 14) Guardraile implementacyjne
- Kontroler ma pozostać cienki; bez `Directory.*`, `File.*`, `JsonSerializer.Deserialize` i reguł workflow.
- `Application` zawiera logikę use-case'u i decyzje semantyczne, ale nie implementuje adapterów plikowych.
- `Infrastructure` implementuje odczyt storage i walidację techniczną, ale nie decyduje o publicznym znaczeniu statusów.
- Nie dodawać minimal API `MapGet`; używać kontrolera ASP.NET.
- Nie hardcodować `/opt/sudoku/...` ani lokalnych ścieżek w kodzie.
- Nie wywoływać `ML` podczas odczytu szczegółów.
- Nie czytać raportów z `trainings/runs/{runName}`.
- Nie przenosić raportów do `models/registry/{modelName}`.
- Nie zmieniać istniejących nazw pól kontraktów `UC-06`, szczególnie `runName`, `baseModelName`, `producedModelName`, `processedDatasetName`, `reportStatus`, `summaryRelativePath`, `metricsRelativePath`, `confusionMatrixRelativePath`.
- Nie zwracać do `FE` ścieżek systemowych, nazw plików raportów ani `primaryArtifactRelativePath`.
- Publiczny JSON ma pozostać w `camelCase`.
- Modele HTTP wejściowe mają sufiks `ApiEntry`, wyjściowe `ApiResponse`, DTO aplikacyjne `Dto`.
- Brak raportu nie może automatycznie zmieniać statusu runu na `failed`.
- Endpoint GET nie wykonuje cleanupu i nie finalizuje modelu.

## 15) Zależności pomiędzy historyjkami
- Wejściowe:
  - `UC-13` - autoryzacja tokenem administracyjnym.
  - `UC-06 POST /api/trainings` - tworzy `trainings/metadata/{runName}.json`.
  - `UC-06 POST /internal/ml/trainings/{runName}/events` - aktualizuje status, progress, `reportStatus`, referencje raportów i metryki skrótowe.
  - `UC-06 GET /api/models/registry` - ustala standard manifestów modeli i port rejestru.
  - `UC-12 GET /api/datasets/processed` - dostarcza metadata gotowego datasetu `.npz`.
  - `INF-08` - standard `models/registry/{modelName}/model.json`.
- Równoległe / konsumujące:
  - `UC-07` - monitoring realtime korzysta z tego samego rekordu metadata i progressu.
  - `UC-08 GET /api/trainings` - lista linkuje do szczegółów po `runName`.
  - `UC-10 PUT /api/models/active` - operator może wybrać model po analizie metryk z `UC-09`.
  - `UC-05` - inferencja później używa aktywnego modelu wybranego m.in. na podstawie szczegółów treningu.

## 16) Inne istotne reguły
- `runName` nie jest identyfikatorem z bazy danych; to nazwa runu spójna z plikiem metadata i katalogami runtime.
- `producedModelName` w MVP może być równe `runName`, ale semantycznie pozostaje nazwą modelu wynikowego.
- Model bootstrap może występować jako `baseModel` i mieć `sourceRunName = null`.
- `producedModel` może być `null` dla runu aktywnego, anulowanego albo nieudanego.
- `report.status = pending` jest poprawny dla aktywnego runu.
- `report.status = missing | corrupted` jest poprawny dla sukcesu z ostrzeżeniem, jeśli artefakty modelu są kompletne.
- `sourceRevision = null` jest poprawne w MVP.
- Pełne metryki porównawcze pozostają w `trainings/reports/{runName}`, a nie w `model.json`.
- Endpoint nie paginuje i nie filtruje; dotyczy jednego runu.

## 17) Model API wejściowy i wyjściowy w komunikacji z FE i ML
- FE -> BE:
  - `GET /api/trainings/{runName}`,
  - brak body,
  - `runName` w ścieżce.
- BE -> FE:
  - `TrainingRunDetailsApiResponse`,
  - `TrainingRunModelReferenceApiResponse`,
  - `TrainingRunDatasetDetailsApiResponse`,
  - `TrainingRunConfigurationApiResponse`,
  - `TrainingRunProgressApiResponse | null`,
  - `TrainingRunReportApiResponse`,
  - `ErrorApiResponse` dla błędów.
- BE -> ML:
  - brak komunikacji dla tego endpointa.
- ML -> BE:
  - brak komunikacji inicjowanej przez ten endpoint.
  - dane raportowe pochodzą historycznie z eventu `POST /internal/ml/trainings/{runName}/events` i z plików zapisanych przez `ML` w `trainings/reports/{runName}`.
- Plikowe kontrakty wejściowe dla BE:
  - `trainings/metadata/{runName}.json`,
  - `models/registry/{baseModelName}/model.json`,
  - `models/registry/{producedModelName}/model.json`, jeśli istnieje,
  - metadata processed datasetu z mechanizmu `UC-12`,
  - `trainings/reports/{runName}/{summaryRelativePath}`,
  - `trainings/reports/{runName}/{metricsRelativePath}`,
  - `trainings/reports/{runName}/{confusionMatrixRelativePath}`.
