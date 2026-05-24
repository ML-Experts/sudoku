# UC-09 — Szczegóły treningu i metryki

## Cel
- Pokazać użytkownikowi szczegóły pojedynczego runu treningowego: konfigurację, status, model bazowy, model wynikowy, użyty dataset, benchmark oraz metryki.
- Udostępnić dane raportowe w UI bez bezpośredniego dostępu `FE` do plików i bez bezpośredniej komunikacji `FE -> ML`.
- Utrzymać `Backend` jako `source of truth` dla publicznego stanu runu, przy jednoczesnym traktowaniu raportów `ML` jako plikowego kontraktu technicznego między `BE` i `ML`.

## Diagram przepływu
```mermaid
flowchart TD
    A[FE: użytkownik otwiera szczegóły treningu] -->|FE -> BE<br/>GET /api/trainings/{runName}| B[BE: czyta rekord runu<br/>read trainings/metadata/{runName}.json]

    B --> C{Run istnieje?}
    C -->|nie<br/>404 ErrorApiResponse| D[FE: pokazuje brak runu]

    C -->|tak| E[BE: czyta powiązany model bazowy<br/>read models/registry/{baseModelName}/model.json]
    E --> F[BE: czyta model wynikowy, jeśli istnieje<br/>read models/registry/{producedModelName}/model.json]
    F --> G{reportStatus}

    G -->|ready| H[BE: czyta raport<br/>read summaryRelativePath<br/>read metricsRelativePath<br/>read confusionMatrixRelativePath]
    G -->|missing / corrupted / pending| I[BE: buduje odpowiedź bez kompletnych metryk<br/>z warnings]

    H --> J[BE: mapuje dane na TrainingRunDetailsApiResponse]
    I --> J
    J -->|BE -> FE<br/>200 TrainingRunDetailsApiResponse| K[FE: renderuje konfigurację, metryki i macierz pomyłek]

    L[ML: kończy trening w UC-06] --> M[ML: zapisuje raporty<br/>write trainings/reports/{runName}/...]
    M -->|ML -> BE<br/>POST /internal/ml/trainings/{runName}/events<br/>completed + report refs| N[BE: aktualizuje metadata runu]
    N --> B

    %% FE -> BE
    linkStyle 0 stroke:#2563eb,stroke-width:2px

    %% BE -> FE
    linkStyle 10 stroke:#16a34a,stroke-width:2px

    %% ML -> BE
    linkStyle 12 stroke:#ca8a04,stroke-width:2px

    %% Internal
    linkStyle 1,2,3,4,5,6,7,8,9,11,13 stroke:#7c3aed,stroke-width:1.5px
```

## Historyjka
Jako użytkownik administracyjny chcę otworzyć szczegóły zakończonego albo trwającego treningu, aby porównać konfigurację i jakość modelu z innymi modelami oraz zdecydować, czy model wynikowy nadaje się do dalszego użycia.

## Role warstw
### `FE`
- Otwiera widok szczegółów po `runName`, najczęściej z listy `UC-08`.
- Pobiera dane wyłącznie przez `GET /api/trainings/{runName}`.
- Renderuje konfigurację runu, status, progres końcowy, ostrzeżenia, metryki, confusion matrix oraz relacje do modelu bazowego i wynikowego.
- Nie czyta ścieżek systemowych i nie pobiera raportów bezpośrednio z dysku ani z `ML`.

### `BE`
- Jest właścicielem publicznego endpointu szczegółów runu.
- Czyta `trainings/metadata/{runName}.json` jako główny rekord stanu runu.
- Dołącza dane z `models/registry/{baseModelName}/model.json` i, jeśli istnieje, z `models/registry/{producedModelName}/model.json`.
- Czyta pliki raportu z `trainings/reports/{runName}` tylko wtedy, gdy rekord runu wskazuje raport jako dostępny.
- Mapuje plikowe kontrakty `BE/ML` na publiczny kontrakt `FE/BE`, bez ujawniania absolutnych ścieżek runtime.

### `ML`
- Nie udostępnia endpointu szczegółów treningu dla `FE`.
- Generuje raporty i metryki podczas końcowej ewaluacji runu w `UC-06`.
- Zapisuje raporty w katalogu przekazanym przez `BE` jako `reportDirectoryPath`.
- Raportuje do `BE` referencje względne do plików raportu przez końcowy event `completed`.

## Kontrakty `FE -> BE`
### `GET /api/trainings/{runName}`
- Endpoint chroniony tokenem administracyjnym z `UC-13`.
- `200 OK` -> `TrainingRunDetailsApiResponse`.
- `404 Not Found` -> `ErrorApiResponse`, jeśli `trainings/metadata/{runName}.json` nie istnieje.
- `409 Conflict` -> `ErrorApiResponse`, jeśli rekord runu istnieje, ale wskazuje niespójne albo niebezpieczne referencje plikowe.
- `422 Unprocessable Entity` -> `ErrorApiResponse`, jeśli raport istnieje, ale nie da się go zmapować na publiczny kontrakt.

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
    "trainingProfileName": "default-finetune-v1",
    "augmentationProfileName": "default-augment-v1",
    "benchmarkName": "sudoku-benchmark-v1",
    "seed": 1234,
    "sourceRevision": null
  },
  "progress": {
    "percent": 100,
    "epoch": 10,
    "totalEpochs": 20,
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

## Kontrakty `ML -> BE` istotne dla `UC-09`
`UC-09` nie wymaga nowego endpointu `BE -> ML`. Szczegóły treningu bazują na danych zapisanych wcześniej w `UC-06`.

### Końcowy event `completed`
- Kanał: `POST /internal/ml/trainings/{runName}/events`.
- `ML` przekazuje `BE` stan raportu i względne referencje do plików raportu.
- Referencje są względne względem `trainings/reports/{runName}` albo `models/registry/{producedModelName}` zgodnie z kontraktem `UC-06`.
- `BE` zapisuje te referencje w `trainings/metadata/{runName}.json` i używa ich później w `UC-09`.

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
    "confusionMatrixRelativePath": "confusion_matrix.json"
  },
  "failure": null
}
```

## Plikowe kontrakty `BE/ML`
### `trainings/metadata/{runName}.json`
Główne źródło prawdy dla publicznego statusu runu. Plik tworzy i aktualizuje `BE`, a dane wejściowe do części pól pochodzą z eventów `ML`.

Przykładowy zakres wykorzystywany przez `UC-09`:

```json
{
  "runName": "train-20260503-112233",
  "status": "succeeded",
  "stage": "finished",
  "createdAtUtc": "2026-05-03T09:22:33Z",
  "startedAtUtc": "2026-05-03T09:23:02Z",
  "finishedAtUtc": "2026-05-03T09:40:12Z",
  "baseModelName": "cnn-bootstrap",
  "producedModelName": "train-20260503-112233",
  "processedDatasetName": "sudokuDigitsV1",
  "trainingMode": "fineTuning",
  "trainingProfileName": "default-finetune-v1",
  "augmentationProfileName": "default-augment-v1",
  "benchmarkName": "sudoku-benchmark-v1",
  "seed": 1234,
  "sourceRevision": null,
  "reportStatus": "ready",
  "metricsSummary": {
    "accuracy": 0.96,
    "macroF1": 0.95
  },
  "reportArtifacts": {
    "summaryRelativePath": "summary.json",
    "metricsRelativePath": "metrics.json",
    "confusionMatrixRelativePath": "confusion_matrix.json"
  },
  "warnings": []
}
```

### `trainings/reports/{runName}/summary.json`
Źródło skrótu raportu. Plik zapisuje `ML`, a `BE` czyta z niego `metricsSummary`, `trainingDurationSeconds` i `averageInferenceTimeMs`, a następnie mapuje te pola na `TrainingRunDetailsApiResponse.report.summary`.

```json
{
  "runName": "train-20260503-112233",
  "baseModelName": "cnn-bootstrap",
  "processedDatasetName": "sudokuDigitsV1",
  "producedModelName": "train-20260503-112233",
  "architectureType": "custom-cnn-v1",
  "trainingProfileName": "default-finetune-v1",
  "augmentationProfileName": "default-augment-v1",
  "benchmarkName": "sudoku-benchmark-v1",
  "seed": 1234,
  "epochs": 20,
  "device": "cpu",
  "metricsSummary": {
    "accuracy": 0.96,
    "precisionMacro": 0.95,
    "recallMacro": 0.95,
    "f1Macro": 0.95
  },
  "trainingDurationSeconds": 1050,
  "averageInferenceTimeMs": 12.4
}
```

### `trainings/reports/{runName}/metrics.json`
Źródło metryk szczegółowych. Plik zapisuje `ML`, a `BE` czyta z niego `classes` oraz `history` i mapuje je odpowiednio na `perClassMetrics` oraz `history` w publicznej odpowiedzi.

```json
{
  "runName": "train-20260503-112233",
  "accuracy": 0.96,
  "precisionMacro": 0.95,
  "recallMacro": 0.95,
  "f1Macro": 0.95,
  "classes": [
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
  ]
}
```

### `trainings/reports/{runName}/{confusionMatrixRelativePath}`
Źródło macierzy pomyłek. Plik zapisuje `ML`, a `BE` mapuje go bez zmiany semantyki etykiet.

```json
{
  "classNames": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
  "matrix": [
    [100, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 118, 1, 0, 0, 0, 0, 1, 0, 0]
  ]
}
```

### `models/registry/{modelName}/model.json`
Źródło informacji o modelu bazowym i wynikowym. `UC-09` tylko odczytuje ten plik przez `BE`; nie zmienia zasad finalizacji z `UC-06`.

## Mapowanie plików na odpowiedź `BE -> FE`
- `trainings/metadata/{runName}.json` zasila pola główne odpowiedzi: `runName`, `status`, `stage`, daty, `configuration`, `progress`, `warnings`, nazwy modeli i nazwę datasetu.
- `models/registry/{baseModelName}/model.json` zasila `baseModel`.
- `models/registry/{producedModelName}/model.json` zasila `producedModel`, ale tylko jeśli run zakończył się sukcesem i model wynikowy istnieje.
- Metadane datasetu przetworzonego z `data/processed` zasilają `dataset.preprocessingProfile` i `dataset.sampleCounts`; jeśli ich brakuje, `BE` może zwrócić `null` w tych polach i dodać ostrzeżenie.
- `summary.json.metricsSummary.accuracy` mapuje się na `report.summary.accuracy`.
- `summary.json.metricsSummary.precisionMacro` mapuje się na `report.summary.precisionMacro`.
- `summary.json.metricsSummary.recallMacro` mapuje się na `report.summary.recallMacro`.
- `summary.json.metricsSummary.f1Macro` mapuje się na `report.summary.f1Macro`.
- `summary.json.trainingDurationSeconds` mapuje się na `report.summary.trainingDurationSeconds`.
- `summary.json.averageInferenceTimeMs` mapuje się na `report.summary.averageInferenceTimeMs`.
- `metrics.json.classes[]` mapuje się na `report.perClassMetrics[]`.
- `metrics.json.history[]` mapuje się na `report.history[]`.
- `{confusionMatrixRelativePath}.classNames` i `{confusionMatrixRelativePath}.matrix` mapują się na `report.confusionMatrix`.
- Pola raportu, które są techniczne albo diagnostyczne, np. `summary.json.device`, `summary.json.epochs` albo top-level `metrics.json.accuracy`, mogą pozostać w plikach, ale nie muszą być wystawiane w publicznym kontrakcie `TrainingRunDetailsApiResponse`.

## Relacje między kontraktami
- `runName` identyfikuje run i spina `GET /api/trainings/{runName}`, `trainings/metadata/{runName}.json` oraz `trainings/reports/{runName}`.
- `baseModelName` wskazuje model bazowy w `models/registry/{baseModelName}/model.json`.
- `producedModelName` wskazuje model wynikowy w `models/registry/{producedModelName}/model.json`, jeśli run zakończył się sukcesem.
- `reportStatus = ready` oznacza, że `BE` może próbować czytać raporty z `trainings/reports/{runName}`.
- `reportStatus = missing` albo `corrupted` nie unieważnia automatycznie modelu, jeśli manifest modelu i artefakty inferencyjne są kompletne.
- `reportStatus = pending` może występować dla runu aktywnego; UI pokazuje wtedy konfigurację i bieżący status, ale nie pokazuje kompletnych metryk końcowych.

## Pliki danych istotne dla `UC-09`
- `trainings/metadata/{runName}.json` — główny rekord runu i źródło konfiguracji publicznej.
- `trainings/reports/{runName}/{summaryRelativePath}` — skrót i konfiguracja raportu wskazane przez event `ML -> BE`.
- `trainings/reports/{runName}/{metricsRelativePath}` — metryki per klasa i historia treningu wskazane przez event `ML -> BE`.
- `trainings/reports/{runName}/{confusionMatrixRelativePath}` — macierz pomyłek wskazana przez event `ML -> BE`.
- `models/registry/{baseModelName}/model.json` — manifest modelu bazowego.
- `models/registry/{producedModelName}/model.json` — manifest modelu wynikowego, jeśli istnieje.

## Przesunięcia i granice plików
- Raporty końcowe runu powinny znajdować się w `trainings/reports/{runName}`, a nie w `trainings/runs/{runName}` ani w `models/registry/{modelName}`.
- `trainings/runs/{runName}` pozostaje miejscem checkpointów, logów i artefaktów roboczych, które nie są publicznym kontraktem widoku szczegółów.
- `models/registry/{producedModelName}/artifacts` zawiera artefakty modelu, ale nie powinien przejmować raportów treningowych.
- `models/registry/{producedModelName}/model.json` może zawierać skrót lub referencję do `sourceRunName`, ale pełne metryki porównawcze pozostają w `trainings/reports/{runName}`.
- Jeśli istniejące implementacje zapisują pliki wskazywane przez `summaryRelativePath`, `metricsRelativePath` albo `confusionMatrixRelativePath` w katalogu runu roboczego, docelowo trzeba przenieść je do `trainings/reports/{runName}` i zapisać względne referencje w `trainings/metadata/{runName}.json`.
- `FE` nie otrzymuje absolutnych ścieżek, nazw katalogów runtime ani linków do pobierania artefaktów; widzi dane domenowe potrzebne do wyrenderowania widoku w UI.

## Kryteria akceptacji
- Użytkownik może otworzyć szczegóły runu po `runName` z listy treningów.
- Widok pokazuje konfigurację runu, dataset, model bazowy, model wynikowy, status raportu, benchmark i metryki.
- Dla kompletnego raportu UI pokazuje co najmniej accuracy, precision, recall, F1 oraz confusion matrix.
- Dla raportu brakującego albo uszkodzonego UI pokazuje ostrzeżenie, ale nie ukrywa pozostałych danych runu.
- Backend czyta raporty i manifesty z plików systemowych, ale nie ujawnia `FE` ścieżek absolutnych.
- `ML` nie dostaje nowego publicznego endpointu dla szczegółów treningu; dostarcza dane przez pliki raportu i końcowy event z `UC-06`.
- Publiczne payloady używają `camelCase`, a błędy API używają `ErrorApiResponse`.
