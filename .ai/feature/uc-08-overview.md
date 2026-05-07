# UC-08 — Lista treningów i wytrenowanych modeli

## Cel
- Pokazać użytkownikowi katalog treningów oraz rejestr modeli dostępnych w systemie.
- Połączyć w UI informacje z rekordów runów (`trainings/metadata/{runName}.json`) i manifestów modeli (`models/registry/{modelName}/model.json`).
- Zachować Backend jako `source of truth`; `FE` nie czyta plików ani nie woła `ML`, a `ML` nie udostępnia osobnej listy treningów lub modeli.

## Diagram przepływu
```mermaid
flowchart TD
    A[FE: otwiera widok katalogu treningów i modeli] -->|FE -> BE<br/>GET /api/trainings| B[BE: listuje treningi<br/>read trainings/metadata/*.json]
    A -->|FE -> BE<br/>GET /api/models/registry| C[BE: listuje modele<br/>read models/registry/*/model.json]

    B --> D[BE: mapuje rekordy runów<br/>TrainingRunListItemApiResponse]
    C --> E[BE: mapuje manifesty modeli<br/>RegistryModelListItemApiResponse]

    D -->|BE -> FE<br/>TrainingRunsListApiResponse| F[FE: renderuje listę treningów]
    E -->|BE -> FE<br/>RegistryModelsListApiResponse| G[FE: renderuje listę modeli]

    F --> H[FE: pokazuje status, datę, dataset, model bazowy i model wynikowy]
    G --> I[FE: pokazuje modele bootstrap i modele z treningu]

    J[ML: wykonuje trening w UC-06] -->|ML -> BE<br/>POST /internal/ml/trainings/{runName}/events| K[BE: aktualizuje metadata runu]
    K --> L[BE: po completed finalizuje manifest modelu<br/>write models/registry/{producedModelName}/model.json]
    L --> C
    K --> B

    %% FE -> BE
    linkStyle 0,1 stroke:#2563eb,stroke-width:2px

    %% BE -> FE
    linkStyle 4,5 stroke:#16a34a,stroke-width:2px

    %% ML -> BE
    linkStyle 8 stroke:#ca8a04,stroke-width:2px

    %% Internal
    linkStyle 2,3,6,7,9,10,11 stroke:#7c3aed,stroke-width:1.5px
```

## Role warstw
### `FE`
- Pobiera listę treningów przez `GET /api/trainings`.
- Pobiera listę modeli przez `GET /api/models/registry`.
- Łączy dane wizualnie po `runName`, `producedModelName` i `sourceRunName`, ale nie wylicza stanu systemowego samodzielnie.
- Pokazuje również model bootstrap, który nie ma powiązanego `runName`.

### `BE`
- Jest właścicielem publicznych endpointów katalogowych.
- Czyta metadane runów z `trainings/metadata/{runName}.json`.
- Czyta manifesty modeli z `models/registry/{modelName}/model.json`.
- Dba o spójne mapowanie statusów, dat, capability i relacji `run -> producedModelName -> model.json`.
- Nie odpytuje `ML` przy każdym wejściu na listę; dane katalogowe wynikają z zapisanych rekordów systemowych.

### `ML`
- Nie dostarcza endpointu listującego treningi lub modele dla `FE`.
- Aktualizuje katalog pośrednio przez kontrakty z `UC-06`: eventy `ML -> BE` oraz artefakty/raporty, które pozwalają Backendowi zapisać końcowy stan runu i manifest modelu.
- Dla modeli bootstrap dostarcza zgodny `model.json` przez proces inicjalizacji rejestru, ale źródłem publicznej listy pozostaje Backend.

## Kontrakty `FE -> BE`
### `GET /api/trainings`
- Endpoint chroniony tokenem administracyjnym z `UC-13`.
- `200 OK` -> `TrainingRunsListApiResponse`.
- Lista zawiera runy aktywne i terminalne.
- Domyślne sortowanie: najnowsze `createdAtUtc` jako pierwsze.

```json
{
  "items": [
    {
      "runName": "train-20260503-112233",
      "status": "succeeded",
      "createdAtUtc": "2026-05-03T09:22:33Z",
      "updatedAtUtc": "2026-05-03T09:40:12Z",
      "startedAtUtc": "2026-05-03T09:23:02Z",
      "finishedAtUtc": "2026-05-03T09:40:12Z",
      "baseModelName": "cnn-bootstrap",
      "producedModelName": "train-20260503-112233",
      "processedDatasetName": "sudokuDigitsV1",
      "trainingMode": "fineTuning",
      "trainingProfileName": "default-finetune-v1",
      "augmentationProfileName": "default-augment-v1",
      "benchmarkName": "sudoku-benchmark-v1",
      "reportStatus": "ready",
      "progress": {
        "percent": 100,
        "epochCurrent": 10,
        "epochTotal": 10,
        "etaSeconds": 0
      },
      "metricsSummary": {
        "accuracy": 0.96,
        "macroF1": 0.95
      },
      "warnings": []
    },
    {
      "runName": "train-20260503-120000",
      "status": "running",
      "createdAtUtc": "2026-05-03T10:00:00Z",
      "updatedAtUtc": "2026-05-03T10:05:00Z",
      "startedAtUtc": "2026-05-03T10:00:10Z",
      "finishedAtUtc": null,
      "baseModelName": "train-20260503-112233",
      "producedModelName": "train-20260503-120000",
      "processedDatasetName": "sudokuDigitsV2",
      "trainingMode": "fineTuning",
      "trainingProfileName": "default-finetune-v1",
      "augmentationProfileName": "default-augment-v1",
      "benchmarkName": "sudoku-benchmark-v1",
      "reportStatus": null,
      "progress": {
        "percent": 42,
        "epochCurrent": 4,
        "epochTotal": 10,
        "etaSeconds": 480
      },
      "metricsSummary": null,
      "warnings": []
    }
  ],
  "totalCount": 2
}
```

### `GET /api/models/registry`
- Endpoint chroniony tokenem administracyjnym z `UC-13`.
- `200 OK` -> `RegistryModelsListApiResponse`.
- Ten endpoint istnieje już jako część `UC-06`, a `UC-08` używa go katalogowo i doprecyzowuje relację z listą treningów.

```json
{
  "items": [
    {
      "name": "cnn-bootstrap",
      "displayName": "CNN bootstrap",
      "sourceType": "bootstrap",
      "sourceRunName": null,
      "parentModelName": null,
      "trainingMode": "externalBaseline",
      "inputProfile": "default-28x28-v1",
      "trainingProfileName": "default-finetune-v1",
      "augmentationProfileName": "default-augment-v1",
      "createdAtUtc": "2026-05-01T10:00:00Z",
      "canStartTraining": true,
      "canUseForInference": true,
      "warnings": []
    },
    {
      "name": "train-20260503-112233",
      "displayName": "train-20260503-112233",
      "sourceType": "training",
      "sourceRunName": "train-20260503-112233",
      "parentModelName": "cnn-bootstrap",
      "trainingMode": "fineTuning",
      "inputProfile": "default-28x28-v1",
      "trainingProfileName": "default-finetune-v1",
      "augmentationProfileName": "default-augment-v1",
      "createdAtUtc": "2026-05-03T09:40:12Z",
      "canStartTraining": true,
      "canUseForInference": true,
      "warnings": []
    }
  ],
  "totalCount": 2
}
```

## Kontrakty `BE <-> ML` istotne dla `UC-08`
`UC-08` nie dodaje nowego endpointu `BE -> ML`. Lista katalogowa korzysta z danych powstałych wcześniej w `UC-06`.

### Event końcowy `ML -> BE`
- Kanał: `POST /internal/ml/trainings/{runName}/events`.
- Event końcowy nie jest trwałą bazą danych sam w sobie; jest mechanizmem aktualizacji rekordów utrzymywanych przez Backend.
- Po przyjęciu eventu Backend aktualizuje `trainings/metadata/{runName}.json`, a po sukcesie finalizuje `models/registry/{producedModelName}/model.json`.
- Dla `UC-08` najważniejsze są pola końcowego wyniku:

```json
{
  "eventType": "completed",
  "sequence": 42,
  "runName": "train-20260503-112233",
  "status": "succeeded",
  "stage": "finished",
  "occurredAtUtc": "2026-05-03T09:40:12Z",
  "message": "Training completed.",
  "progress": null,
  "warnings": [],
  "result": {
    "producedModelName": "train-20260503-112233",
    "reportStatus": "ready",
    "canUseProducedModelForInference": true,
    "primaryArtifactRelativePath": "artifacts/model.pt",
    "summaryRelativePath": "summary.json",
    "metricsRelativePath": "metrics.json",
    "confusionMatrixRelativePath": "confusion-matrix.json"
  },
  "failure": null
}
```

### Plik manifestu modelu `models/registry/{modelName}/model.json`
- Jest plikowym kontraktem współdzielonym przez `BE` i `ML`.
- Jest trwałym rekordem modelu w rejestrze i częścią plikowej bazy systemu.
- Backend używa go do listowania modeli, walidacji wyborów użytkownika i ustawiania aktywnego modelu.
- ML używa go do odnalezienia artefaktu modelu oraz technicznego profilu wejścia.

Minimalny kształt istotny dla katalogu:

```json
{
  "name": "train-20260503-112233",
  "displayName": "train-20260503-112233",
  "sourceType": "training",
  "sourceRunName": "train-20260503-112233",
  "parentModelName": "cnn-bootstrap",
  "trainingMode": "fineTuning",
  "framework": "pytorch",
  "architecture": {
    "type": "cnn",
    "family": "sudoku-digit-classifier",
    "numClasses": 10,
    "inputChannels": 1,
    "inputHeight": 28,
    "inputWidth": 28,
    "inputProfile": "default-28x28-v1"
  },
  "training": {
    "defaultTrainingProfileName": "default-finetune-v1",
    "defaultAugmentationProfileName": "default-augment-v1"
  },
  "artifacts": {
    "primaryArtifactRelativePath": "artifacts/model.pt",
    "format": "pytorch"
  },
  "capabilities": {
    "canStartTraining": true,
    "canUseForInference": true
  },
  "metadata": {
    "createdAtUtc": "2026-05-03T09:40:12Z"
  }
}
```

## Plikowe źródła danych katalogowych
Te pliki są częścią runtime'owej bazy systemu i powinny być traktowane jako kontrakt danych, a nie jako szczegół implementacji warstw.

### `trainings/metadata/{runName}.json`
- Zasila `GET /api/trainings`.
- Jest głównym rekordem runu treningowego po stronie Backendu.
- Istnieje od momentu przyjęcia startu treningu, dlatego lista może pokazać również runy aktywne.
- Jest aktualizowany na podstawie eventów `ML -> BE`.
- Spina listę treningów z listą modeli przez `producedModelName`.

Minimalny zakres potrzebny dla `UC-08`:

```json
{
  "runName": "train-20260503-112233",
  "status": "succeeded",
  "createdAtUtc": "2026-05-03T09:22:33Z",
  "updatedAtUtc": "2026-05-03T09:40:12Z",
  "startedAtUtc": "2026-05-03T09:23:02Z",
  "finishedAtUtc": "2026-05-03T09:40:12Z",
  "baseModelName": "cnn-bootstrap",
  "producedModelName": "train-20260503-112233",
  "processedDatasetName": "sudokuDigitsV1",
  "trainingMode": "fineTuning",
  "trainingProfileName": "default-finetune-v1",
  "augmentationProfileName": "default-augment-v1",
  "benchmarkName": "sudoku-benchmark-v1",
  "reportStatus": "ready",
  "progress": {
    "percent": 100,
    "epochCurrent": 10,
    "epochTotal": 10,
    "etaSeconds": 0
  },
  "metricsSummary": {
    "accuracy": 0.96,
    "macroF1": 0.95
  },
  "warnings": []
}
```

### `models/registry/{modelName}/model.json`
- Zasila `GET /api/models/registry`.
- Jest głównym rekordem modelu w rejestrze.
- Dla modelu bootstrap ma `sourceType = "bootstrap"` i `sourceRunName = null`.
- Dla modelu wytrenowanego ma `sourceType = "training"` i `sourceRunName` wskazujący run źródłowy.
- Spina listę modeli z listą treningów przez `sourceRunName`.

### `models/registry/{modelName}/artifacts/*`
- Nie zasila bezpośrednio listy katalogowej, ale jest częścią kompletności wpisu modelu.
- Manifest `model.json` wskazuje główny artefakt przez `artifacts.primaryArtifactRelativePath`.
- Jeśli artefakt wskazany w manifeście nie istnieje, model nie powinien być prezentowany jako gotowy do inferencji lub dalszego treningu bez ostrzeżenia.

### `trainings/reports/{runName}/...`
- Nie jest pełnym źródłem listy `UC-08`, ale jest powiązanym katalogiem raportu dla zakończonego runu.
- Lista używa tylko skrótu raportu zapisanego w `trainings/metadata/{runName}.json`, np. `reportStatus` i `metricsSummary`.
- Szczegółowe pliki raportu należą przede wszystkim do `UC-09`.

## Relacje między rekordami
- `trainings/metadata/{runName}.json.producedModelName` wskazuje docelowy wpis w `models/registry/{modelName}`.
- `models/registry/{modelName}/model.json.sourceRunName` wskazuje run, który utworzył model.
- Dla modelu bootstrap relacja z runem nie istnieje i nie wolno jej sztucznie dopisywać.
- Backend może wykryć niespójność, jeśli run zakończony sukcesem wskazuje `producedModelName`, ale brakuje odpowiadającego `model.json`.

## Kryteria akceptacji
- Użytkownik widzi listę treningów obejmującą runy aktywne, zakończone sukcesem, anulowane i nieudane.
- Użytkownik widzi listę modeli obejmującą modele bootstrap oraz modele powstałe z treningów.
- Model bootstrap jest poprawnie pokazany mimo `sourceRunName = null`.
- Model wytrenowany jest powiązany z runem przez `sourceRunName` / `producedModelName`.
- Frontend pobiera dane wyłącznie z Backendu.
- Backend nie odpytuje `ML` podczas listowania katalogu.
- Publiczne payloady używają `camelCase`, a błędy API zachowują wspólny kontrakt `ErrorApiResponse`.
