# UC-09 ML — Plan implementacyjny (`POST /internal/ml/trainings/{runName}/events`)

## 1. Przeznaczenie endpointa
- `POST /internal/ml/trainings/{runName}/events` jest wewnętrznym endpointem `BE`, wywoływanym przez serwis `ML`.
- Po stronie `ML` ten use-case oznacza publikowanie zdarzeń treningu, metryk, statusu raportu oraz referencji do artefaktów raportowych, a nie dodanie nowego publicznego endpointu FastAPI.
- Endpoint zasila `Backend`, który pozostaje `source of truth` dla publicznego statusu runu, `SignalR`, `GET /api/trainings/{runName}` i finalizacji `models/registry/{producedModelName}/model.json`.
- `FE` nigdy nie komunikuje się bezpośrednio z `ML`; widok szczegółów z `UC-09` czyta dane wyłącznie z `BE`.

## 2. Najważniejsze założenia
- Plan dotyczy wyłącznie części `ML` i nie powinien sugerować się aktualnymi uproszczeniami `FE` ani `BE`.
- Nie zmieniamy kontraktów nazw i pól wypracowanych w `UC-06`: `runName`, `sequence`, `eventType`, `status`, `stage`, `progress`, `result`, `failure`, `reportStatus`, `summaryRelativePath`, `metricsRelativePath`, `confusionMatrixRelativePath`.
- `UC-09 ML` rozszerza i domyka to, co `UC-06 ML` już zaplanowało: realne eventy treningu, raporty `summary.json`, `metrics.json`, `confusion_matrix.json` i terminalny event `completed`.
- Obecny mock nie może definiować semantyki produktu. Jeśli gdziekolwiek została logika „8 kroków”, należy ją usunąć albo ograniczyć wyłącznie do testowego runnera bez wpływu na kontrakt.
- Liczba eventów `progress` ma wynikać z realnej liczby epok po rozstrzygnięciu profilu treningowego, np. `cnn-default-v1 = 20`, `resnet18-finetune-v1 = 10`, albo z wartości po `ML_TRAINING_MAX_EPOCHS_OVERRIDE`.
- Faza ewaluacji nie jest udawaną dodatkową epoką ani „ósmym krokiem”; może być osobnym `statusChanged(stage=evaluation)`.

## 3. Kontrakt `ML -> BE`
### 3.1 Request eventu
Kanał docelowy:

```http
POST /internal/ml/trainings/{runName}/events
```

Przykład eventu `progress`:

```json
{
  "eventType": "progress",
  "sequence": 5,
  "runName": "train-20260503-112233",
  "status": "running",
  "stage": "training",
  "occurredAtUtc": "2026-05-03T09:30:00Z",
  "message": "Epoch 7/20.",
  "progress": {
    "percent": 35.0,
    "epochCurrent": 7,
    "epochTotal": 20,
    "etaSeconds": null
  },
  "warnings": [],
  "result": null,
  "failure": null
}
```

Przykład terminalnego `completed` dla `UC-09`:

```json
{
  "eventType": "completed",
  "sequence": 24,
  "runName": "train-20260503-112233",
  "status": "succeeded",
  "stage": "finished",
  "occurredAtUtc": "2026-05-03T09:40:12Z",
  "message": "Training finished.",
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

### 3.2 Odpowiedź BE
- Sukces: dowolny status `2xx`; preferowany kontrakt BE z `UC-06` to `202 Accepted` bez body.
- `ML` nie używa body odpowiedzi do budowania stanu systemowego.
- Dla eventów aktywnych (`statusChanged`, `progress`) błąd transportu jest logowany i nie zatrzymuje treningu.
- Dla eventów terminalnych (`completed`, `failed`, `cancelled`) `ML` ponawia wysyłkę tego samego payloadu z tym samym `sequence` zgodnie z konfiguracją retry.

## 4. Kontrakty plikowe raportów
Raporty końcowe są technicznym kontraktem `ML/BE`. `ML` zapisuje je w katalogu `reportDirectoryPath` przekazanym przez `BE` w `POST /ml/trainings`.

### `summary.json`
Odpowiedzialność: skrót konfiguracji i metryk potrzebny do szybkiego podglądu w `UC-09`.

```json
{
  "runName": "train-20260503-112233",
  "baseModelName": "cnn-bootstrap",
  "processedDatasetName": "sudokuDigitsV1",
  "producedModelName": "train-20260503-112233",
  "architectureType": "custom-cnn-v1",
  "trainingProfileName": "cnn-default-v1",
  "augmentationProfileName": "digits-light-v1",
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

### `metrics.json`
Odpowiedzialność: metryki szczegółowe per klasa oraz historia treningu per epoka.

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

### `confusion_matrix.json`
Odpowiedzialność: macierz pomyłek na wspólnym benchmarku albo na ustalonym ewaluacyjnym splicie, bez zmiany semantyki etykiet.

```json
{
  "classNames": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
  "matrix": [
    [100, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 118, 1, 0, 0, 0, 0, 1, 0, 0]
  ]
}
```

## 5. Zachowanie warstwowe
### 5.1 API
- Po stronie `ML` nie tworzymy kontrolera dla `/internal/ml/trainings/{runName}/events`, bo ten endpoint należy do `BE`.
- `api` może utrzymywać modele kontraktowe eventu tylko jako modele transportowe `ApiEntry`, ale logika budowania eventu pozostaje poza `api`.
- `api/controllers/trainings_controller.py` pozostaje właścicielem `POST /ml/trainings` i `POST /ml/trainings/{runName}/cancel`; startuje runnera i nie publikuje eventów bezpośrednio.
- `api/dependencies.py` pozostaje composition rootem: składa `BackendTrainingEventPublisher`, runner, writer raportów, profile i ustawienia retry.
- `api/config/environment.py` pozostaje jedynym loaderem `.env`/`.env.{ML_ENVIRONMENT}`; nie dodajemy drugiego systemu konfiguracji.

### 5.2 Application
- `Application` opisuje use-case i porty: trening emituje `TrainingRunEventDto`, a publisher jest portem.
- `Application` nie zna `httpx`, FastAPI, Pydantic, PyTorch ani filesystemowego sposobu zapisu JSON.
- `TrainingEventSequence` zapewnia monotoniczne `sequence` w obrębie jednego runu.
- `TrainingRunEventDto`, `TrainingRunProgressDto`, `TrainingRunResultDto` i `TrainingRunFailureDto` pozostają DTO aplikacyjnymi używanymi przez runner i publisher.
- Handler startu z `UC-06` odpowiada za zbudowanie kontekstu, walidację wejścia, aktywny run i uruchomienie runnera; nie mapuje raportów na publiczny kontrakt FE.

### 5.3 Domain / Models
- `models` zawiera wyłącznie neutralne enumy i modele domenowe: typy eventów, statusy runu, stage, status raportu, manifest modelu.
- `ReportStatus` musi wspierać `ready`, `missing`, `corrupted`; `pending` pozostaje stanem po stronie `BE`, nie wartością terminalnego result z `ML`.
- Status `failed` jest zarezerwowany dla przypadków, w których model wynikowy nie nadaje się do inferencji albo workflow treningu nie dał się domknąć.
- Brak albo uszkodzenie samego raportu, przy kompletnym artefakcie modelu, skutkuje `completed` z `reportStatus = missing | corrupted` i ostrzeżeniem.

### 5.4 Infrastructure
- `Infrastructure` implementuje HTTP publisher, realny runner PyTorch, writer raportów, kalkulator metryk, odczyt `.npz`, dataloadery, transformacje, zapis artefaktów i fallbacki runtime.
- `BackendTrainingEventPublisher` odpowiada za serializację DTO do camelCase JSON i wysyłkę do `BE`.
- `PytorchTrainingRunner` odpowiada za rzeczywisty workflow treningu, publikowanie statusów, progress per epoka, ewaluację, zapis raportów i event terminalny.
- `TrainingReportWriter` zapisuje pliki w `reportDirectoryPath` i zwraca wyłącznie ścieżki względne.
- Nowe usługi infrastrukturalne można dodać dopiero po sprawdzeniu, czy istnieją obecne odpowiedniki. Jeśli trzeba rozbudować raportowanie, należy preferować rozszerzenie `TrainingReportWriter` albo mały generyczny writer, a nie osobny writer zaszyty pod `UC-09`.

## 6. Pliki per warstwa i odpowiedzialności
### 6.1 API (`src/MachineLearning/api`)
- `api/controllers/trainings_controller.py` (reuse) — cienkie wejście dla `POST /ml/trainings` i cancel; pośrednio uruchamia flow, który publikuje eventy do endpointa BE.
- `api/models/training_api_models.py` (reuse/update) — istnieją modele `TrainingRunEventApiEntry`, `TrainingRunProgressApiEntry`, `TrainingRunResultApiEntry`, `TrainingRunFailureApiEntry`; utrzymać nazwy pól zgodne z `UC-06`.
- `api/models/error_api_response.py` (reuse) — wspólny model błędu dla endpointów ML, nie dla odpowiedzi z `/internal/ml/...`.
- `api/dependencies.py` (update/reuse) — składanie `TrainingRunnerFactory`, `BackendTrainingEventPublisher`, `TrainingReportWriter`, `MetricsCalculator`, `TrainingProfileCatalog`; bez logiki workflow.
- `api/config/runtime_settings.py` (update/reuse) — `TrainingSettings`: `backendBaseUrl`, timeout, retry terminalnych i aktywnych eventów, runner, device, allowed output roots, max epoch override.
- `api/config/environment.py` (reuse/update) — scalanie `.env` i `.env.{ML_ENVIRONMENT}`; ewentualne nowe zmienne tylko tutaj.
- `api/.env` (reuse/update) — baza z `ML_ENVIRONMENT=local`.
- `api/.env.local` (update, jeśli brakuje wartości) — lokalne, jawne wartości na sztywno: `ML_TRAINING_BACKEND_BASE_URL`, runner, retry, device.
- `api/.env.production` (workflow/update) — produkcyjny overlay z `ML_ENVIRONMENT=production`, `ML_TRAINING_BACKEND_BASE_URL=http://127.0.0.1:5000`, `ML_TRAINING_RUNNER=pytorch`.

### 6.2 Application (`src/MachineLearning/application/features/trainings`)
- `dto/training_run_event_dto.py` (reuse/update) — aplikacyjny model eventu, progressu, result i failure. Jeśli `UC-09` wymaga `trainingDurationSeconds` albo `averageInferenceTimeMs`, te wartości trafiają do raportów, niekoniecznie do event result.
- `dto/training_run_context_dto.py` (reuse) — kontekst runu z `runName`, modelami, datasetem, konfiguracją i ścieżkami output.
- `services/training_event_sequence.py` (reuse) — monotoniczny licznik `sequence`.
- `ports/training_ports.py` (reuse/update) — port `TrainingEventPublisher.publish(event, terminal=False)` oraz `TrainingRunner`.
- `commands/start_training_run/start_training_run_command_handler.py` (reuse) — startuje runnera, ale nie implementuje HTTP publish ani zapisu raportów.
- `commands/start_training_run/start_training_run_command.py` (reuse) — wejściowy model use-case startu.
- `commands/start_training_run/start_training_run_command_result_dto.py` (reuse) — odpowiedź startu `queued`.
- `commands/cancel_training_run/cancel_training_run_command.py` (reuse) — intencja anulowania.
- `commands/cancel_training_run/cancel_training_run_command_handler.py` (reuse) — przekazuje cancel do rejestru anulowań.
- `commands/cancel_training_run/cancel_training_run_command_result_dto.py` (reuse) — wynik idempotentnego cancel.
- `errors/training_run_errors.py` (reuse) — błędy aplikacyjne mapowane przez API start/cancel.

### 6.3 Domain / Models (`src/MachineLearning/models`)
- `models/training_run_event_type.py` (reuse) — `statusChanged`, `progress`, `completed`, `failed`, `cancelled`.
- `models/training_run_status.py` (reuse) — `queued`, `running`, `cancelling`, `succeeded`, `failed`, `cancelled`.
- `models/training_run_stage.py` (reuse) — `queued`, `training`, `evaluation`, `finished`.
- `models/report_status.py` (reuse/update) — `ready`, `missing`, `corrupted`; nie dodawać tu `pending` jako terminalnego statusu wysyłanego z `ML`.
- `models/model_manifest.py` (reuse) — opis architektury, rodziny, artefaktów i profilu wejściowego używany do raportu i treningu.

### 6.4 Infrastructure (`src/MachineLearning/infrastructure`)
- `training/events/backend_training_event_publisher.py` (reuse/update) — HTTP client do `BE`; serializacja camelCase; retry terminalnych eventów; lekkie logi z `runName`, `eventType`, `sequence`, `reportStatus`.
- `training/runners/pytorch_training_runner.py` (update/reuse) — realny runner; publikuje `statusChanged`, `progress` per epoka, `statusChanged(stage=evaluation)` i terminalny event; zapisuje raporty i model artifact.
- `training/runners/mock_training_runner.py` (update/reuse) — wyłącznie testowy runner; liczba progressów musi wynikać z profilu, nie z „8 kroków”.
- `training/runners/training_runner_factory.py` (reuse/update) — wybór `mock` albo `pytorch` z konfiguracji; produkcyjnie `pytorch`.
- `training/reporting/training_report_writer.py` (update/reuse) — zapis `summary.json`, `metrics.json`, `confusion_matrix.json`; dodać brakujące pola czasu treningu i średniego czasu inferencji, jeśli runner je zmierzy.
- `training/reporting/metrics_calculator.py` (reuse/update) — accuracy, precision, recall, F1, per-class metrics, confusion matrix.
- `training/profiles/training_profile_catalog.py` (reuse) — źródło `epochs`; uwzględnia `ML_TRAINING_MAX_EPOCHS_OVERRIDE`.
- `training/profiles/training_profile.py` (reuse) — profil treningu: epochs, batch size, learning rate, optimizer, fine tuning policy.
- `training/profiles/fine_tuning_policy_factory.py` (reuse) — polityka zamrażania parametrów.
- `training/profiles/optimizer_factory.py` (reuse) — optimizer.
- `training/data/npz_digit_dataset.py` (reuse) — odczyt kanonicznego `.npz`.
- `training/data/digit_dataloader_factory.py` (reuse) — dataloadery splitów.
- `training/data/input_transform_factory.py` (reuse) — transformacja wg manifestu i augmentacji.
- `training/data/input_transforms.py` (reuse) — implementacje transformacji.
- `training/model/model_manifest_reader.py` (reuse) — odczyt manifestu modelu bazowego.
- `training/model/model_factory.py` (reuse) — budowa modelu.
- `training/model/model_artifact_loader.py` (reuse) — ładowanie wag modelu bazowego.
- `training/model/model_artifact_writer.py` (reuse) — zapis finalnego artefaktu i zwrot ścieżki względnej względem `models/registry/{producedModelName}`.
- `training/cancellation/cancellation_registry.py` (reuse) — stan aktywnego runu i cancel.
- `training/cancellation/cancellation_token.py` (reuse) — kooperacyjne przerwanie między bezpiecznymi etapami.
- `time/system_utc_clock.py` (reuse) — czas UTC dla eventów i pomiarów.
- `storage/filesystem_path_validator.py` (reuse) — walidacja dozwolonych output roots przy starcie runu.

### 6.5 Workflow (`.github/workflows`)
- `.github/workflows/ml-cd.yml` (reuse/update) — pakuje `src/MachineLearning`, `requirements.txt`, `api/.env` i `api/.env.production`; nie nadpisuje runtime state.

### 6.6 Testy (`src/MachineLearning/tests`)
- `tests/integration/test_trainings_controller.py` (update/reuse) — start treningu, poprawne wstrzyknięcie publishera i runnera.
- `tests/unit/test_training_profile_catalog.py` (reuse/update) — `epochs` i override.
- `tests/unit/training/test_training_report_writer.py` (new, jeśli brak) — poprawne `summary.json`, `metrics.json`, `confusion_matrix.json`.
- `tests/unit/training/test_backend_training_event_publisher.py` (new, jeśli brak) — payload camelCase, retry terminalnych, brak ciężkich logów.
- `tests/integration/test_pytorch_training_runner.py` (new/update) — mini `.npz`, 1-2 epoki, dokładna liczba progressów równa liczbie epok, raporty i terminalny `completed`.
- `tests/integration/test_mock_training_runner.py` (new/update) — mock nie wysyła stałych 8 kroków, tylko liczbę epok z profilu.

## 7. Usunięcie semantyki „8 kroków”
- Zakaz: `totalSteps = 8`, `step 1/8`, „mock step 8”, stały procent liczony od liczby kroków mocka jako kontrakt produktu.
- Dozwolone: statusy techniczne `statusChanged` bez udawania epok.
- Docelowy schemat eventów:
  1. `statusChanged` po wejściu w `running`, `stage=training`, `epochTotal = profile.epochs`.
  2. `progress` po każdej realnej epoce `1..profile.epochs`.
  3. `statusChanged` dla `stage=evaluation`, jeśli runner wchodzi w ewaluację.
  4. dokładnie jeden terminalny `completed`, `failed` albo `cancelled`.
- `percent` dla progressu treningowego liczymy z epok: `round(epoch / epoch_total * 100, 2)`.
- Jeśli używamy `ML_TRAINING_MAX_EPOCHS_OVERRIDE`, `epochTotal` pokazuje wartość po ograniczeniu.
- Historia w `metrics.json.history[]` ma tyle wpisów, ile realnie wykonanych epok przed sukcesem albo anulowaniem.

## 8. Wyjątki i fallbacki
### 8.1 Eventy aktywne
- Błąd HTTP, timeout albo brak `2xx` przy `progress` lub nieterminalnym `statusChanged` jest logowany jako warning i nie zatrzymuje treningu.
- Liczba prób dla aktywnych eventów pochodzi z `ML_TRAINING_ACTIVE_EVENT_MAX_ATTEMPTS`.
- Nie należy spamować logów pełnym payloadem; wystarczy `runName`, `eventType`, `sequence`, `httpStatus`, `attempt`, `errorType`.

### 8.2 Eventy terminalne
- `completed`, `failed`, `cancelled` muszą być ponawiane z tym samym payloadem i tym samym `sequence`.
- `ML_TRAINING_TERMINAL_EVENT_MAX_ATTEMPTS=0` może oznaczać retry bez limitu, jeśli tak zostanie udokumentowane w settings.
- Po wyczerpaniu limitu retry terminalnego trzeba zalogować error z kontekstem runu; nie wolno tworzyć nowego eventu z nowym `sequence` dla tego samego stanu terminalnego.

### 8.3 Raporty
- Jeśli raporty zapisują się poprawnie: `completed` z `reportStatus=ready` i trzema względnymi ścieżkami.
- Jeśli raportu nie udało się zapisać, ale finalny artefakt modelu istnieje i jest używalny: `completed` z `reportStatus=missing`, ścieżki raportów `null`, warning `training_report_missing`.
- Jeśli raport istnieje, ale walidacja struktury wykryje błąd: `completed` z `reportStatus=corrupted`, warning `training_report_corrupted`.
- Jeśli finalny artefakt modelu nie powstał albo model nie nadaje się do inferencji: `failed`, `result=null`, `failure.canUseProducedModelForInference=false`.

### 8.4 Anulowanie
- Cancel jest kooperacyjny i sprawdzany między epokami oraz przed ewaluacją/zapisem finalnego artefaktu.
- Po `CancelledTrainingRun` runner wysyła `cancelled` i nie wysyła `completed`.
- Cleanup artefaktów runtime koordynuje `BE`; `ML` nie próbuje samodzielnie aktualizować `trainings/metadata`.

### 8.5 Device
- `ML_TRAINING_DEVICE=auto`: użyj CUDA, jeśli dostępna; inaczej CPU.
- `ML_TRAINING_DEVICE=cpu`: zawsze CPU.
- `ML_TRAINING_DEVICE=cuda`: brak CUDA jest błędem, nie cichym fallbackiem.

## 9. Specyficzna logika i pseudokod
```python
async def publish_epoch_progress(sequence, context, epoch, profile, metrics):
    epoch_total = profile.epochs
    event = TrainingRunEventDto(
        event_type="progress",
        sequence=sequence.next(),
        run_name=context.run_name,
        status="running",
        stage="training",
        occurred_at_utc=utc_clock.now(),
        message=f"Epoch {epoch}/{epoch_total}.",
        progress=TrainingRunProgressDto(
            percent=round(epoch / epoch_total * 100, 2),
            epoch_current=epoch,
            epoch_total=epoch_total,
            train_loss=metrics.train_loss,
            validation_loss=metrics.validation_loss,
            train_accuracy=metrics.train_accuracy,
            validation_accuracy=metrics.validation_accuracy,
        ),
        warnings=(),
        result=None,
        failure=None,
    )
    await event_publisher.publish(event, terminal=False)
```

```python
async def finish_successfully(sequence, context, model, metrics, history):
    artifact_relative_path = artifact_writer.write(
        model,
        context.output_model.directory_path,
        context.model_manifest,
    )

    try:
        report_paths = report_writer.write(
            context.output_paths.report_directory_path,
            build_summary(context),
            metrics,
            history,
        )
        report_status = "ready"
        warnings = ()
    except ReportCorrupted:
        report_paths = null_report_paths()
        report_status = "corrupted"
        warnings = ("training_report_corrupted",)
    except Exception:
        report_paths = null_report_paths()
        report_status = "missing"
        warnings = ("training_report_missing",)

    await event_publisher.publish(
        TrainingRunEventDto(
            event_type="completed",
            sequence=sequence.next(),
            run_name=context.run_name,
            status="succeeded",
            stage="finished",
            occurred_at_utc=utc_clock.now(),
            message="Training finished.",
            progress=None,
            warnings=warnings,
            result=TrainingRunResultDto(
                produced_model_name=context.output_model.name,
                report_status=report_status,
                can_use_produced_model_for_inference=True,
                primary_artifact_relative_path=artifact_relative_path,
                metrics_summary=metrics.summary,
                summary_relative_path=report_paths.summary,
                metrics_relative_path=report_paths.metrics,
                confusion_matrix_relative_path=report_paths.confusion_matrix,
            ),
            failure=None,
        ),
        terminal=True,
    )
```

## 10. Główne funkcje / komponenty
- `PytorchTrainingRunner.start()` — pełny lifecycle treningu, eventy, raporty, artefakt modelu.
- `PytorchTrainingRunner._publish_status_changed()` — zmiana stage/status bez udawania epok.
- `PytorchTrainingRunner._publish_progress()` — progress per realna epoka.
- `PytorchTrainingRunner._publish_completed()` — terminalny sukces z referencjami do raportów.
- `PytorchTrainingRunner._publish_failed()` — terminalny błąd bez modelu używalnego do inferencji.
- `PytorchTrainingRunner._publish_cancelled()` — terminalne anulowanie.
- `TrainingReportWriter.write()` — zapis raportów JSON i zwrot względnych nazw plików.
- `MetricsCalculator.calculate()` — metryki do raportów.
- `BackendTrainingEventPublisher.publish()` — publikacja HTTP do `BE` z retry.
- `TrainingProfileCatalog.get()` — rozstrzygnięcie liczby epok i profilu.
- `TrainingEventSequence.next()` — monotoniczny `sequence`.

## 11. Przepływ wewnątrz ML
1. `BE` wywołuje `POST /ml/trainings` z `runName`, modelem bazowym, datasetem, konfiguracją i ścieżkami.
2. `API` mapuje request na komendę i uruchamia handler.
3. `Application` waliduje kontrakt, manifest, pliki, output roots i brak aktywnego runu.
4. `Application` uruchamia runnera w tle i zwraca `202 Accepted` do `BE`.
5. `PytorchTrainingRunner` ustawia seed i device, oznacza run jako `running`.
6. Runner publikuje `statusChanged(stage=training)`.
7. Runner wykonuje pętlę epok i po każdej epoce publikuje `progress`.
8. Runner przechodzi do ewaluacji i opcjonalnie publikuje `statusChanged(stage=evaluation)`.
9. Runner liczy metryki, zapisuje finalny artefakt modelu oraz raporty w `reportDirectoryPath`.
10. Runner publikuje terminalny `completed` z `reportStatus` i ścieżkami raportów albo `failed` / `cancelled`.
11. `BackendTrainingEventPublisher` wysyła event do `BE`; terminalny event retry-uje do `2xx` albo do wyczerpania polityki.
12. `BE` zapisuje event w swoim rekordzie i później wykorzystuje raporty w `GET /api/trainings/{runName}`.

## 12. Logowanie
- Logi informacyjne:
  - start wysyłki terminalnego eventu,
  - dostarczenie terminalnego eventu,
  - zapis raportów,
  - rozpoczęcie treningu i ewaluacji.
- Logi warning:
  - niedostarczony aktywny event,
  - retry terminalnego eventu,
  - brak albo błąd zapisu raportu przy kompletnym artefakcie modelu.
- Logi error:
  - wyczerpanie retry terminalnego eventu,
  - nieobsłużony błąd runnera skutkujący `failed`.
- Minimalny kontekst: `run_name`, `event_type`, `sequence`, `stage`, `report_status`, `attempt`, `http_status_code`, `error_type`.
- Nie logować pełnych payloadów, absolutnych ścieżek i macierzy pomyłek w normalnym poziomie `info`.

## 13. Workflow GitHub + konfiguracja
- `local`:
  - wartości ustawiamy jawnie w `src/MachineLearning/api/.env.local`;
  - lokalnie można używać `ML_TRAINING_RUNNER=mock` do smoke testów;
  - realny trening lokalny używa `ML_TRAINING_RUNNER=pytorch`;
  - `ML_TRAINING_BACKEND_BASE_URL` wskazuje lokalny backend, np. `http://127.0.0.1:5000`.
- `production`:
  - `.github/workflows/ml-cd.yml` pakuje kod `src/MachineLearning`, `requirements.txt`, `api/.env` i overlay `api/.env.production`;
  - workflow ustawia w release `ML_ENVIRONMENT=production`;
  - produkcyjny overlay powinien ustawiać `ML_TRAINING_RUNNER=pytorch`, `ML_TRAINING_BACKEND_BASE_URL=http://127.0.0.1:5000`, timeouty i retry eventów;
  - workflow nie nadpisuje `data`, `models`, `trainings`, `examples` ani `tmp` w `/opt/sudoku/shared`;
  - bootstrap modelu seed pozostaje osobnym krokiem operacyjnym z `model.json` i `artifacts/`.

## 14. Kolejność implementacji
1. Zweryfikować istniejący kontrakt `TrainingRunEventDto` i `BackendTrainingEventPublisher` względem `UC-06` oraz `UC-09`.
2. Przeszukać kod pod kątem „8”, `totalSteps`, `step`, `mock step`, `epochTotal` i usunąć/odizolować stałą semantykę 8 kroków.
3. Upewnić się, że `MockTrainingRunner` publikuje progress na podstawie `TrainingProfile.epochs`, a nie stałej liczby kroków.
4. Dokończyć/zweryfikować `PytorchTrainingRunner`: per-epoka progress, stage `evaluation`, terminalny event, retry terminalny przez publisher.
5. Dokończyć `TrainingReportWriter`: `summary.json`, `metrics.json`, `confusion_matrix.json`, `history`, `metricsSummary`, opcjonalnie czas treningu i średni czas inferencji.
6. Uzupełnić `MetricsCalculator`, jeśli brakuje precision/recall/F1 per klasa lub confusion matrix.
7. Dodać walidację raportów po zapisie, jeśli chcemy rozróżnić `missing` od `corrupted`.
8. Uzupełnić `.env.local`, `.env.production`, `runtime_settings.py` i `ml-cd.yml`, jeśli brakuje ustawień event retry albo `backendBaseUrl`.
9. Dodać testy publishera, writerów raportu, mocka bez 8 kroków i runnera PyTorch na mini `.npz`.
10. Uruchomić testy ML i smoke startu runu z lokalnym backendem.

## 15. Guardraile implementacyjne
- Nie dodawać publicznego endpointu `FE -> ML`.
- Nie dodawać kontrolera ML dla `/internal/ml/trainings/{runName}/events`; ten endpoint należy do `BE`.
- Nie zmieniać nazw pól kontraktu z `UC-06`.
- Nie używać modeli API w `Application`.
- Nie umieszczać HTTP klienta w `Application`.
- Nie hardcodować `/opt/sudoku/...` w kodzie; ścieżki przychodzą z `BE` i są walidowane względem konfiguracji.
- Nie zapisywać ani nie finalizować `model.json` po stronie `ML`.
- Nie traktować braku raportu jako `failed`, jeśli artefakt modelu jest kompletny.
- Nie publikować progressu według stałej liczby 8 kroków.
- Nie tworzyć osobnego systemu raportów dla `UC-09`; raporty mają być tym samym artefaktem, który powstaje przy treningu.
- Nie logować pełnych metryk i macierzy pomyłek na poziomie `info`.

## 16. Zależności między historyjkami
- `UC-06` — start runu, kontekst treningu, kontrakt eventów, aktywny run i cancel.
- `UC-07` — konsumuje eventy przez `BE -> SignalR`; wymaga spójnego `sequence`, `status`, `progress`.
- `UC-08` — lista runów i modeli bazuje na rekordach aktualizowanych po eventach `ML`.
- `UC-09` — szczegóły treningu czytają raporty zapisane przez `ML` i referencje zapisane przez `BE` po terminalnym `completed`.
- `UC-10` — wytrenowany model może zostać aktywowany dopiero po finalizacji przez `BE`.
- `UC-12` — dostarcza `.npz` z kanonicznym schematem danych.
- `UC-13` — chroni publiczne operacje w `BE`; `ML` pozostaje wewnętrzne.
- `INF-08` — definiuje standard rejestru modeli i bootstrap.

## 17. Inne istotne reguły
- `sequence` rośnie w obrębie runu i nie jest globalnym licznikiem systemowym.
- `occurredAtUtc` zawsze jest w UTC i serializowane z sufiksem `Z`.
- `summaryRelativePath`, `metricsRelativePath`, `confusionMatrixRelativePath` są względne względem `trainings/reports/{runName}`.
- `primaryArtifactRelativePath` jest względne względem `models/registry/{producedModelName}`.
- `metricsSummary` w DTO może być pomocnicze, ale publiczny widok `UC-09` opiera się na plikach raportowych czytanych przez `BE`.
- Benchmark w MVP może być reprezentowany przez ewaluacyjny split `.npz`, ale pole `benchmarkName` musi zostać zachowane w raportach.
- Jeśli w przyszłości dojdzie osobny benchmark directory, należy dodać generyczny adapter ewaluacji w `infrastructure/training/reporting` albo `infrastructure/training/evaluation`, bez przenoszenia tej logiki do `Application`.

## 18. Plan testów minimum
- Unit: `BackendTrainingEventPublisher` serializuje camelCase i wysyła pod `/internal/ml/trainings/{runName}/events`.
- Unit: aktywny event po błędzie transportu nie zatrzymuje flow.
- Unit: terminalny event retry-uje ten sam payload i ten sam `sequence`.
- Unit: `TrainingReportWriter` tworzy trzy pliki z oczekiwanymi polami.
- Unit: `TrainingProfileCatalog` zwraca `epochs` po override.
- Integracyjny: `MockTrainingRunner` z profilem 3 epok wysyła 3 eventy `progress`, a nie 8.
- Integracyjny: `PytorchTrainingRunner` na mini `.npz` wysyła `statusChanged`, `progress` per epoka, `statusChanged(stage=evaluation)` i `completed`.
- Integracyjny: błąd zapisu raportu po zapisie modelu kończy się `completed` z `reportStatus=missing`.
- Integracyjny: błąd zapisu artefaktu modelu kończy się `failed`.
- Integracyjny: cancel między epokami kończy się `cancelled` bez `completed`.
