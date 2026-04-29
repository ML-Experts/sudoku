# UC-06 ML — Plan implementacyjny (`POST /ml/trainings`)

## 1. Przeznaczenie endpointa
- Endpoint wewnętrzny `BE -> ML` uruchamia techniczny run treningowy na jednym przygotowanym artefakcie `.npz`.
- Endpoint nie jest dostępny dla `FE`; `FE` komunikuje się wyłącznie z `BE`, a `BE` pozostaje `source of truth` dla runów, statusów, modeli i rekordów widocznych w UI.
- `ML` przyjmuje od `BE` kompletnie rozwiązaną konfigurację runu: `runName`, referencję do modelu bazowego, dataset `.npz`, profile, seed oraz ścieżki wejścia/wyjścia.
- `ML` wykonuje trening, ewaluację, zapisuje techniczne artefakty i raportuje eventy do `BE` przez `POST /internal/ml/trainings/{runName}/events`.
- `ML` nie finalizuje `models/registry/{producedModelName}/model.json`; manifest modelu wynikowego tworzy/finalizuje `BE`.

## 2. Założenia planu
- Plan bazuje na `PRD`, `UC-06 BE`, architekturze generycznego runnera i regułach `architecture_ml`, a nie na bieżących uproszczeniach `FE` lub `BE`.
- `POST /ml/trainings` ma pozostać jednym endpointem dla `CNN`, `ResNet` i przyszłych architektur. Nie tworzymy osobnych endpointów typu `trainCnn` albo `trainResNet`.
- Przygotowanie `.npz` jest zakończone wcześniej w `UC-12`; `UC-06 ML` nie wykonuje preprocessingu datasetu ani splitu.
- Dataset `.npz` pozostaje kanoniczny i wspólny. Różnice między architekturami obsługują transformacje tensora i fabryki modeli, a nie osobne formaty datasetu.
- Obecny dynamiczny mock nie może definiować zachowania produkcyjnego. W szczególności należy usunąć założenie stałych `8` kroków/zdarzeń widocznych dla `BE`.
- Liczba eventów progress ma wynikać z rzeczywistego profilu treningowego i liczby epok. Jeśli profil ma `epochs = 20`, runner wysyła progress per epoka `1..20`; jeśli profil zostanie ograniczony przez bezpiecznik `ML_TRAINING_MAX_EPOCHS_OVERRIDE`, `epochTotal` pokazuje wartość po ograniczeniu.

## 3. Kontrakt API ML <-> BE
- Kontrakt `BE -> ML` ma pozostać taki sam jak w planie `UC-06 BE`; plan ML nie dodaje, nie usuwa i nie zmienia nazw pól requestu ani response.
- Implementacja PyTorch może wewnętrznie używać `state_dict`, ale nazwa i ścieżka artefaktu w komunikacji oraz w eventach musi wynikać z manifestu i wartości przekazanych przez `BE`, bez zmiany kontraktu HTTP.

### 3.1 Request `StartTrainingRunApiEntry`
```json
{
  "runName": "train-20260411-130500-cnn-mnist-baseline-sudokuDigitsV1",
  "baseModel": {
    "name": "cnn-mnist-baseline",
    "directoryPath": "/opt/sudoku/shared/models/registry/cnn-mnist-baseline",
    "manifestPath": "/opt/sudoku/shared/models/registry/cnn-mnist-baseline/model.json",
    "primaryArtifactPath": "/opt/sudoku/shared/models/registry/cnn-mnist-baseline/artifacts/model.keras",
    "inputProfile": "default-28x28-v1",
    "sourceType": "bootstrap"
  },
  "processedDataset": {
    "name": "sudokuDigitsV1",
    "filePath": "/opt/sudoku/shared/data/processed/sudokuDigitsV1.npz",
    "preprocessingProfile": "default-28x28-v1"
  },
  "resolvedConfiguration": {
    "trainingMode": "fineTuning",
    "trainingProfileName": "cnn-default-v1",
    "augmentationProfileName": "digits-light-v1",
    "benchmarkName": "sudoku-benchmark-v1",
    "seed": 1234
  },
  "outputModel": {
    "name": "train-20260411-130500-cnn-mnist-baseline-sudokuDigitsV1",
    "directoryPath": "/opt/sudoku/shared/models/registry/train-20260411-130500-cnn-mnist-baseline-sudokuDigitsV1"
  },
  "outputPaths": {
    "runDirectoryPath": "/opt/sudoku/shared/trainings/runs/train-20260411-130500-cnn-mnist-baseline-sudokuDigitsV1",
    "reportDirectoryPath": "/opt/sudoku/shared/trainings/reports/train-20260411-130500-cnn-mnist-baseline-sudokuDigitsV1",
    "benchmarkDirectoryPath": "/opt/sudoku/shared/data/benchmark",
    "temporaryWorkingDirectoryPath": "/opt/sudoku/shared/tmp/trainings/train-20260411-130500-cnn-mnist-baseline-sudokuDigitsV1"
  }
}
```

### 3.2 Response `202 Accepted`
```json
{
  "runName": "train-20260411-130500-cnn-mnist-baseline-sudokuDigitsV1",
  "status": "queued",
  "acceptedAtUtc": "2026-04-11T13:05:01Z",
  "warnings": []
}
```

### 3.3 Eventy `ML -> BE`
- Eventy aktywne: `statusChanged`, `progress`.
- Eventy terminalne: `completed`, `failed`, `cancelled`.
- `sequence` jest monotoniczne w obrębie jednego runu.
- Event terminalny musi być ponawiany z tym samym `sequence` i payloadem aż do odpowiedzi `2xx` albo do wyczerpania jawnie skonfigurowanej polityki retry/pending terminal event.
- `progress.epochCurrent` i `progress.epochTotal` wynikają z realnego profilu treningu, nigdy z magicznej liczby mocka.

Przykład eventu progress dla epoki:
```json
{
  "eventType": "progress",
  "sequence": 5,
  "runName": "train-20260411-130500-cnn-mnist-baseline-sudokuDigitsV1",
  "status": "running",
  "stage": "training",
  "occurredAtUtc": "2026-04-11T13:07:15Z",
  "message": "Epoch 7/20.",
  "progress": {
    "percent": 35.0,
    "epochCurrent": 7,
    "epochTotal": 20,
    "etaSeconds": 92
  },
  "warnings": [],
  "result": null,
  "failure": null
}
```

## 4. Zachowanie warstwowe

### 4.1 API
- `api` zawiera wyłącznie FastAPI controller, modele `ApiEntry/ApiResponse`, mapowanie requestu do komendy i mapowanie wyjątków na `ErrorApiResponse`.
- Kontroler `POST /ml/trainings` nie tworzy modelu, nie czyta `.npz`, nie zapisuje artefaktów i nie publikuje eventów treningowych bezpośrednio.
- `POST /ml/trainings/{runName}/cancel` nie zabija procesu siłowo; przekazuje intencję anulowania do aplikacyjnego handlera i rejestru anulowań.

### 4.2 Application
- `Application` orkiestruje use-case startu i anulowania runu po stronie `ML`.
- Odpowiada za walidację kompletności requestu, zgodność `baseModel.inputProfile == processedDataset.preprocessingProfile`, sprawdzenie jednego aktywnego runu i zbudowanie `TrainingRunContextDto`.
- `Application` zna porty (`TrainingRunner`, `TrainingEventPublisher`, `ModelManifestReader`, `FilesystemPathValidator`, `ActiveTrainingRunGuard`), ale nie zna PyTorch, NumPy, HTTP klienta ani filesystemowych detali implementacji.
- `Application` rezerwuje aktywny run przed startem workera i zwalnia go po terminalnym statusie albo błędzie startu.

### 4.3 Domain / Models
- `models` zawiera neutralne modele i enumy: statusy runu, typy eventów, stage, manifest modelu, status raportu.
- Modele domenowe nie zależą od FastAPI, Pydantic requestów, PyTorch, NumPy ani ścieżek konfiguracyjnych.
- Manifest modelu opisuje architekturę, rodzinę modelu, `inputProfile`, liczbę klas i artefakt główny. Runtime treningowy używa go do zbudowania modelu i transformacji wejścia.

### 4.4 Infrastructure
- `Infrastructure` zawiera implementacje zależne od PyTorch, NumPy, filesystemu, HTTP i czasu systemowego.
- Implementuje czytanie manifestu, walidację ścieżek, fabrykę modelu, loader/writer artefaktów, dataset `.npz`, dataloadery, transformacje, profile treningowe, optimizer, policy fine-tuningu, pętlę treningową, metryki, raporty, publisher eventów i rejestr anulowania.
- Nowe usługi w `Infrastructure` należy najpierw sprawdzić pod kątem istniejących odpowiedników. Jeśli adapter już istnieje, rozszerzamy go lub używamy ponownie; jeśli nie istnieje, tworzymy go generycznie, bez zaszywania jednego endpointa.

## 5. Pliki per warstwa i odpowiedzialności

### 5.1 API (`src/MachineLearning/api`)
- `api/controllers/trainings_controller.py` (update/reuse) — router `/ml/trainings`; cienki start i cancel, mapowanie `TrainingRunCommandError` na `ErrorApiResponse`; bez logiki treningu.
- `api/models/training_api_models.py` (update/reuse) — modele `StartTrainingRunApiEntry`, `StartedTrainingRunApiResponse`, `CancelTrainingRunApiResponse`, `TrainingRunEventApiEntry`, `TrainingRunProgressApiEntry`, `TrainingRunResultApiEntry`, `TrainingRunFailureApiEntry`; JSON w `camelCase`.
- `api/models/error_api_response.py` (reuse) — wspólny payload błędu `{ errorType, message }`.
- `api/dependencies.py` (update) — composition root dla handlerów treningu, `TrainingRunnerFactory`, `CancellationRegistry`, `FilesystemPathValidator`, `ModelManifestReader`.
- `api/config/runtime_settings.py` (update/reuse) — typed settings dla treningu: runner, backend URL, retry eventów, device, allowed output roots, max epoch override.
- `api/config/environment.py` (update/reuse) — jedyny loader `.env`/`.env.{ML_ENVIRONMENT}`; dodanie brakujących zmiennych dla realnego treningu bez drugiego systemu konfiguracji.
- `api/main.py` (reuse) — rejestracja kontrolera treningów, bez logiki use-case.
- `api/.env` (update) — baza i `ML_ENVIRONMENT=local`.
- `api/.env.local` (update) — lokalne, jawne wartości na sztywno, np. `ML_TRAINING_RUNNER=pytorch|mock`, lokalny `ML_TRAINING_BACKEND_BASE_URL`, lokalne `ML_TRAINING_ALLOWED_OUTPUT_ROOTS`.
- `api/.env.production` (update/workflow) — produkcyjny overlay dostarczany przez workflow, z `ML_TRAINING_RUNNER=pytorch`, URL-em `BE` po localhost i absolutnymi katalogami runtime.

### 5.2 Application (`src/MachineLearning/application/features/trainings`)
- `commands/start_training_run/start_training_run_command.py` (reuse) — komenda use-case z polami przekazanymi przez `BE`.
- `commands/start_training_run/start_training_run_command_handler.py` (update/reuse) — walidacja profili, manifestu, ścieżek, pojedynczego aktywnego runu, budowa `TrainingRunContextDto`, start runnera w tle.
- `commands/start_training_run/start_training_run_command_result_dto.py` (reuse) — wynik startu z `runName`, `status`, `acceptedAtUtc`, `warnings`.
- `commands/cancel_training_run/cancel_training_run_command.py` (reuse) — komenda anulowania po `runName`.
- `commands/cancel_training_run/cancel_training_run_command_handler.py` (reuse) — przekazanie anulowania do rejestru anulowań.
- `commands/cancel_training_run/cancel_training_run_command_result_dto.py` (reuse) — wynik anulowania z `requestDisposition`.
- `dto/training_run_context_dto.py` (update/reuse) — wewnętrzny kontekst runnera: request, manifest, ścieżki, konfiguracja.
- `dto/training_run_event_dto.py` (reuse) — DTO eventów publikowanych do `BE`.
- `errors/training_run_errors.py` (update/reuse) — jawne wyjątki aplikacyjne mapowane na HTTP: `400`, `404`, `409`, `422`, `500`.
- `ports/training_ports.py` (update/reuse) — protokoły portów: `TrainingRunner`, `TrainingEventPublisher`, `ModelManifestReader`, `FilesystemPathValidator`, `ActiveTrainingRunGuard`, `CancellationRegistry`, `UtcClock`.
- `services/training_event_sequence.py` (reuse) — monotoniczny licznik sekwencji w obrębie runu.

### 5.3 Domain / Models (`src/MachineLearning/models`)
- `models/model_manifest.py` (update/reuse) — domenowy model manifestu rejestru: framework, architecture, input profile, artefakt główny.
- `models/training_run_status.py` (reuse) — statusy `queued`, `running`, `cancelling`, `succeeded`, `failed`, `cancelled`.
- `models/training_run_stage.py` (reuse) — stage `queued`, `training`, `evaluation`, `finished`.
- `models/training_run_event_type.py` (reuse) — typy eventów `statusChanged`, `progress`, `completed`, `failed`, `cancelled`.
- `models/report_status.py` (reuse) — status raportu `ready`, `missing`, `corrupted`.
- `models/model_framework.py` albo rozszerzenie `model_manifest.py` (new/update, jeśli brakuje) — jawna walidacja `framework = pytorch`.
- `models/model_architecture_family.py` albo rozszerzenie `model_manifest.py` (new/update, jeśli brakuje) — dozwolone rodziny `cnn`, `resnet`.

### 5.4 Infrastructure (`src/MachineLearning/infrastructure`)
- `time/system_utc_clock.py` (reuse) — źródło czasu UTC dla eventów i raportów.
- `storage/filesystem_path_validator.py` (update/reuse) — walidacja istnienia plików oraz tego, czy katalogi output mieszczą się w dozwolonych rootach.
- `training/cancellation/cancellation_registry.py` (update/reuse) — pamięciowy rejestr jednego aktywnego runu, status `running/cancelling`, idempotentne requesty cancel.
- `training/cancellation/cancellation_token.py` (reuse) — kooperacyjny token anulowania i wyjątek `CancelledTrainingRun`.
- `training/events/backend_training_event_publisher.py` (update/reuse) — HTTP publisher eventów do `BE`, best-effort dla aktywnych eventów i reliable retry dla terminalnych.
- `training/runners/training_runner_factory.py` (update/reuse) — wybór `mock` albo `pytorch` z konfiguracji; produkcyjnie `pytorch`, mock tylko do testów/smoke.
- `training/runners/mock_training_runner.py` (update) — testowy runner zgodny z interfejsem; usunąć semantykę produkcyjnych `8` kroków. Jeśli zostaje, jego liczba epok ma pochodzić z profilu/testowej konfiguracji albo być wyraźnie testowa i nieużywana produkcyjnie.
- `training/runners/pytorch_training_runner.py` (update/reuse) — realny runner PyTorch: seed, device, model, wagi, dataset, profile, training loop, checkpointy, ewaluacja, raporty, artifact writer, eventy i anulowanie.
- `training/model/model_manifest_reader.py` (update/reuse) — odczyt `model.json` i walidacja wymaganych pól runtime.
- `training/model/model_factory.py` (update/reuse) — budowa `CustomDigitCnnV1` albo `torchvision` ResNet na podstawie manifestu.
- `training/model/custom_digit_cnn_v1.py` (reuse) — implementacja bazowej architektury CNN dla cyfr.
- `training/model/model_artifact_loader.py` (update/reuse) — ładowanie wag `state_dict`/formatu wynikającego z manifestu, bez zgadywania po samej nazwie pliku.
- `training/model/model_artifact_writer.py` (update/reuse) — zapis finalnego artefaktu do `outputModel.directoryPath/artifacts`.
- `training/data/npz_digit_dataset.py` (update/reuse) — walidacja i odczyt `x_train`, `y_train`, `x_val`, `y_val`, `x_test`, `y_test`.
- `training/data/digit_dataloader_factory.py` (update/reuse) — budowa `DataLoader` dla splitów.
- `training/data/input_transform_factory.py` (update/reuse) — wybór transformacji po rodzinie architektury i profilu augmentacji.
- `training/data/input_transforms.py` (update/reuse) — transformacje `CNN -> 1x28x28`, `ResNet -> 3x224x224` albo zgodne z manifestem.
- `training/profiles/training_profile.py` (reuse) — model profilu treningowego: epochs, batch size, learning rate, optimizer, fine tuning policy.
- `training/profiles/training_profile_catalog.py` (update/reuse) — katalog profili `cnn-default-v1`, `resnet18-finetune-v1`; obsługa `ML_TRAINING_MAX_EPOCHS_OVERRIDE`.
- `training/profiles/fine_tuning_policy_factory.py` (update/reuse) — `all` dla CNN, `head-only` dla ResNet MVP.
- `training/profiles/optimizer_factory.py` (reuse) — budowa optymalizatora na podstawie profilu.
- `training/profiles/scheduler_factory.py` (new, jeśli potrzebny) — przyszłe schedulery bez rozbudowy runnera.
- `training/reporting/metrics_calculator.py` (update/reuse) — accuracy, precision, recall, F1, confusion matrix.
- `training/reporting/training_report_writer.py` (update/reuse) — zapis `summary.json`, `metrics.json`, `confusion_matrix.json` do `reportDirectoryPath`.
- `training/reporting/confusion_matrix_writer.py` (new, jeśli obecny writer robi zbyt dużo) — opcjonalne wydzielenie zapisu macierzy pomyłek.

### 5.5 Testy (`src/MachineLearning/tests`)
- `tests/integration/test_trainings_controller.py` (update/reuse) — kontrakt `202`, błędy `404/409/422`, cancel.
- `tests/unit/training/test_model_factory.py` (new) — obsługa CNN, ResNet i architektury nieobsługiwanej.
- `tests/unit/training/test_input_transform_factory.py` (new) — kształty tensorów dla CNN i ResNet.
- `tests/unit/training/test_training_profile_catalog.py` (new) — profil zgodny/niezgodny z rodziną architektury i override epok.
- `tests/unit/training/test_npz_digit_dataset.py` (new) — wymagane klucze `.npz`, puste train, niespójne rozmiary.
- `tests/integration/test_pytorch_training_runner.py` (new) — mini `.npz`, 1 epoka, zapis artefaktu, raport i terminalny event.
- `tests/integration/test_training_cancellation.py` (new) — cancel między epokami, event `cancelled`, brak finalnego sukcesu.

## 6. Sprawdzenie istniejących usług Infrastructure i reuse
- Istnieje już szkielet `TrainingRunnerFactory`, `MockTrainingRunner`, `PytorchTrainingRunner`, `ModelFactory`, `NpzDigitDatasetLoader`, `TrainingProfileCatalog`, `BackendTrainingEventPublisher` i rejestr anulowania. Plan zakłada ich weryfikację i rozszerzenie, a nie tworzenie równoległego workflow.
- Istnieją adaptery datasetowe i preprocessingowe z `UC-12`; `UC-06` nie powinien ich duplikować ani ponownie przygotowywać danych.
- Jeśli pojawi się potrzeba nowego writer'a, loadera albo transformacji, tworzymy mały generyczny adapter w `infrastructure/training/*`, aby mógł być użyty później przez `UC-07`, `UC-09`, inferencję albo kolejne profile treningu.
- Runtime treningu nie importuje narzędzi z `src/MachineLearning/init_bootstrap`. Wspólnym kontraktem z bootstrapem jest tylko `models/registry/{modelName}/model.json` i katalog `artifacts/`.

## 7. Migracja z mocka i usunięcie stałych 8 kroków
- Produkcyjny przebieg nie może wysyłać do `BE` stałej liczby kroków z mocka.
- Należy usunąć lub odizolować wszystkie magiczne wartości typu `total_epochs = 7`, "8 steps", "mock step 1/8" z kodu używanego przez produkcyjny runner.
- `PytorchTrainingRunner` wysyła:
  1. `statusChanged` po wejściu w `running`.
  2. `progress` po każdej realnie wykonanej epoce.
  3. opcjonalny `statusChanged` dla `evaluation`, jeśli chcemy pokazać zmianę stage.
  4. dokładnie jeden terminalny `completed`, `failed` albo `cancelled`.
- `epochTotal` zawsze pochodzi z `TrainingProfile.epochs` po zastosowaniu ewentualnego override.
- `percent` dla epok może być liczony jako `epoch / epochTotal * 100`; jeśli dochodzi osobna faza ewaluacji, nie należy sztucznie dopisywać jej jako ósmego kroku. Można wysłać osobny `statusChanged(stage=evaluation)` bez udawania epoki.
- `MockTrainingRunner`, jeśli zostaje dla testów integracyjnych, ma być konfigurowalny i opisany jako narzędzie testowe. Nie wolno opierać publicznego kontraktu `BE/FE` na liczbie eventów mocka.

## 8. Wyjątki, błędy i fallbacki

### 8.1 Błędy synchroniczne przed akceptacją runu
- `400 Bad Request` — niepoprawny payload HTTP/Pydantic.
- `404 Not Found` — brak `baseModel.manifestPath`, `baseModel.primaryArtifactPath` albo `processedDataset.filePath`.
- `409 Conflict` — aktywny run już trwa po stronie `ML`.
- `422 Unprocessable Content` — niezgodność profili, nieobsługiwany manifest, `framework != pytorch`, nieobsługiwana architektura, nieobsługiwany profil treningowy, uszkodzony `.npz`.
- `500 Internal Server Error` — nieoczekiwany błąd rezerwacji, walidacji infrastrukturalnej albo startu workera przed `202`.

### 8.2 Błędy po akceptacji runu
- Po zwróceniu `202 Accepted` błędy nie wracają przez odpowiedź startową. Runner raportuje je terminalnym eventem `failed`.
- `failed` oznacza, że model wynikowy nie nadaje się do inferencji albo workflow nie dał się domknąć.
- Jeśli problem dotyczy wyłącznie raportu, ale artefakt modelu jest kompletny i używalny, runner wysyła `completed` z `reportStatus = missing` albo `corrupted` oraz ostrzeżeniem.
- Przy anulowaniu runner wysyła `cancelled`, zwalnia aktywny run i nie zapisuje finalnego modelu jako sukcesu. Cleanup runtime artefaktów koordynuje `BE`.

### 8.3 Fallbacki kontrolowane
- `ML_TRAINING_DEVICE=auto`: jeśli CUDA nie jest dostępna, runner przechodzi na CPU.
- `ML_TRAINING_DEVICE=cpu`: zawsze CPU.
- `ML_TRAINING_DEVICE=cuda`: jeśli CUDA nie jest dostępna, runner powinien zakończyć run błędem czytelnym jako `failed` albo odrzucić start `422`, zgodnie z decyzją implementacyjną; nie ukrywamy wymuszonego CUDA przez cichy fallback.
- Brak splitu `val` lub `test` w `.npz` jako klucza jest błędem, ale pusty split może być dopuszczalny, jeśli schemat `.npz` z `UC-12` tak przewiduje. Runner musi wtedy nie używać pustego splitu do metryk końcowych albo zwrócić jawne `422`, jeśli profil wymaga testu.
- Brak możliwości wysłania eventu aktywnego (`progress`) można logować i kontynuować. Brak potwierdzenia eventu terminalnego wymaga retry.

## 9. Specyficzna logika i pseudokod
```python
def handle_start_training(command, task_scheduler):
    validate_input_profile(command)
    active_run_guard.ensure_no_active_run()

    ensure_file_exists(command.base_model.manifest_path)
    ensure_file_exists(command.base_model.primary_artifact_path)
    ensure_file_exists(command.processed_dataset.file_path)
    ensure_output_directories_are_allowed(command.output_paths)

    manifest = model_manifest_reader.read(command.base_model.manifest_path)
    validate_manifest(manifest, command.base_model.input_profile)
    validate_framework(manifest.framework == "pytorch")

    context = TrainingRunContextDto(command=command, model_manifest=manifest)
    cancellation_token = active_run_guard.reserve(context.run_name)

    try:
        training_runner.start_background(context, cancellation_token, task_scheduler)
    except Exception:
        active_run_guard.release(context.run_name)
        raise

    return StartedTrainingRunDto(status="queued")
```

```python
async def run_pytorch_training(context, cancellation_token):
    sequence = TrainingEventSequence()
    seed_everything(context.resolved_configuration.seed)
    device = resolve_device()

    cancellation_registry.mark_running(context.run_name)
    await publish_status_changed(sequence, status="running", stage="training")

    model = model_factory.build(context.model_manifest).to(device)
    artifact_loader.load(model, context.base_model.primary_artifact_path, device)

    profile = profile_catalog.get(
        context.resolved_configuration.training_profile_name,
        context.model_manifest.architecture,
    )
    transform = input_transform_factory.build(
        context.model_manifest,
        context.resolved_configuration.augmentation_profile_name,
    )
    arrays = npz_dataset_loader.load(context.processed_dataset.file_path)
    dataloaders = dataloader_factory.build(arrays, transform, profile.batch_size)

    parameters = fine_tuning_policy_factory.apply(model, profile)
    optimizer = optimizer_factory.build(profile, parameters)

    for epoch in range(1, profile.epochs + 1):
        cancellation_token.throw_if_cancelled()
        train_one_epoch(model, dataloaders["train"], optimizer, device)
        write_checkpoint(context.output_paths.run_directory_path, model, epoch)
        await publish_progress(
            sequence=sequence,
            epoch_current=epoch,
            epoch_total=profile.epochs,
            percent=epoch / profile.epochs * 100,
        )

    cancellation_token.throw_if_cancelled()
    await publish_status_changed(sequence, status="running", stage="evaluation")
    metrics = evaluate(model, dataloaders)

    report_status, report_paths, report_warnings = write_reports(metrics)
    artifact_relative_path = artifact_writer.write(
        model,
        context.output_model.directory_path,
    )

    await publish_completed(
        sequence=sequence,
        artifact_relative_path=artifact_relative_path,
        report_status=report_status,
        report_paths=report_paths,
        warnings=report_warnings,
    )
```

## 10. Główne funkcje / komponenty
- `start_training()` — endpoint FastAPI dla `POST /ml/trainings`.
- `cancel_training()` — endpoint FastAPI dla anulowania.
- `StartTrainingRunCommandHandler.handle()` — walidacja i start runu w tle.
- `TrainingRunnerFactory.create()` — wybór implementacji runnera z konfiguracji.
- `PytorchTrainingRunner.run()` — pełny workflow treningu i eventów.
- `ModelManifestReader.read()` — odczyt i walidacja manifestu modelu.
- `ModelFactory.build()` — budowa `torch.nn.Module`.
- `ModelArtifactLoader.load()` — ładowanie wag modelu bazowego.
- `NpzDigitDatasetLoader.load()` — walidacja i odczyt `.npz`.
- `InputTransformFactory.build()` — dopasowanie wejścia do architektury.
- `TrainingProfileCatalog.get()` — pobranie profilu i liczby epok.
- `FineTuningPolicyFactory.apply()` — zamrożenie/odmrożenie parametrów.
- `OptimizerFactory.build()` — konfiguracja optymalizatora.
- `MetricsCalculator.calculate()` — metryki końcowe.
- `TrainingReportWriter.write()` — raporty JSON.
- `ModelArtifactWriter.write()` — finalny artefakt modelu.
- `BackendTrainingEventPublisher.publish()` — publikacja eventów do `BE`.
- `CancellationRegistry.request_cancel()` — idempotentne anulowanie.

## 11. Przepływ wewnątrz ML
1. `API` odbiera `POST /ml/trainings` i mapuje `StartTrainingRunApiEntry` na `StartTrainingRunCommand`.
2. `Application` waliduje profile, manifest, pliki wejściowe, katalogi wyjściowe i brak aktywnego runu.
3. `Application` buduje `TrainingRunContextDto`, rezerwuje aktywny run i zleca runnerowi start w tle.
4. `API` zwraca `202 Accepted` ze statusem `queued`.
5. `PytorchTrainingRunner` oznacza run jako `running`, publikuje `statusChanged`.
6. Runner buduje model z manifestu, ładuje wagi modelu bazowego i dataset `.npz`.
7. Runner dobiera transformacje, dataloadery, profil treningu, fine-tuning policy i optimizer.
8. Runner wykonuje pętlę epok. Po każdej epoce zapisuje checkpoint i publikuje `progress` z realnym `epochCurrent/epochTotal`.
9. Runner wykonuje ewaluację, zapisuje raporty i finalny artefakt modelu.
10. Runner wysyła terminalny event `completed`, `failed` albo `cancelled` do `BE`.
11. Runner zwalnia aktywny run po stronie `ML`.

## 12. Workflow GitHub + konfiguracja środowisk
- `Local`:
  - wartości ustawiamy jawnie w `src/MachineLearning/api/.env.local`;
  - lokalnie można wybrać `ML_TRAINING_RUNNER=mock` do szybkich smoke testów albo `ML_TRAINING_RUNNER=pytorch` do realnego treningu;
  - lokalne ścieżki output roots wpisujemy na sztywno, np. katalogi w workspace/dev runtime;
  - lokalny run nie zależy od GitHub Actions.
- `Production`:
  - `.github/workflows/ml-cd.yml` pakuje całe `src/MachineLearning`, `requirements.txt`, `api/.env` i `api/.env.production`;
  - workflow ustawia `ML_ENVIRONMENT=production` w release;
  - produkcyjny overlay powinien zawierać `ML_TRAINING_RUNNER=pytorch`, `ML_TRAINING_BACKEND_BASE_URL=http://127.0.0.1:5000`, retry eventów terminalnych, `ML_TRAINING_DEVICE=auto` oraz `ML_TRAINING_ALLOWED_OUTPUT_ROOTS` obejmujące wyłącznie dozwolone katalogi `/opt/sudoku/shared/trainings`, `/opt/sudoku/shared/models/registry`, `/opt/sudoku/shared/tmp`;
  - workflow nie powinien nadpisywać `models/registry`, `models/active`, `trainings`, `data` ani `examples`;
  - jeśli bootstrap modelu seed jest częścią operacji, musi być osobnym krokiem z dostarczeniem `model.json` i `artifacts/`, nie efektem zwykłego deployu kodu ML.

## 13. Kolejność implementacji historyjki
1. Zweryfikować aktualny kontrakt `StartTrainingRunApiEntry` względem `UC-06 BE` i zostawić jeden endpoint `POST /ml/trainings`.
2. Uporządkować mock: przenieść całą semantykę produkcyjną do `TrainingRunner` i usunąć stałe 8 kroków z zachowania oczekiwanego przez system.
3. Dokończyć walidacje `Application`: manifest, `framework=pytorch`, zgodność profili, dozwolone output roots, pojedynczy aktywny run.
4. Dokończyć `ModelManifestReader`, `ModelFactory`, `ModelArtifactLoader` i `ModelArtifactWriter`.
5. Dokończyć dataset `.npz`, dataloadery i transformacje wejścia dla `CNN` oraz `ResNet`.
6. Dokończyć `TrainingProfileCatalog`, `FineTuningPolicyFactory`, `OptimizerFactory` i ewentualny `SchedulerFactory`.
7. Dokończyć `PytorchTrainingRunner`: pętla epok, checkpointy, anulowanie, eventy per epoka, ewaluacja.
8. Dokończyć raporty: `summary.json`, `metrics.json`, `confusion_matrix.json`, `reportStatus`.
9. Dokończyć `BackendTrainingEventPublisher`: retry terminalnych eventów i idempotencja payloadu.
10. Uzupełnić `.env.local`, `.env.production`, `runtime_settings.py` i workflow ML-CD.
11. Dodać testy jednostkowe oraz integracyjne na mini `.npz`.
12. Przełączyć środowisko docelowe na `ML_TRAINING_RUNNER=pytorch`; mock zostawić tylko do testów i smoke.

## 14. Zależności między historyjkami
- **Twarde wejściowe**:
  - `UC-12` — istnieje przygotowany `.npz` ze stałym schematem `x_train`, `y_train`, `x_val`, `y_val`, `x_test`, `y_test`.
  - `BE UC-06` — `BE` generuje `runName`, `producedModelName`, resolved ścieżki, profile i seed oraz odbiera eventy.
  - `INF-08` — istnieje standard `models/registry/{modelName}/model.json` i model bootstrap.
  - `UC-13` — autoryzacja publicznego startu jest po stronie `BE`; `ML` pozostaje usługą wewnętrzną.
- **Wyjściowe**:
  - `UC-07` — konsumuje eventy postępu przez `BE -> SignalR`.
  - `UC-08` — lista runów/modeli bazuje na rekordach finalizowanych przez `BE` po eventach `ML`.
  - `UC-09` — szczegóły i metryki używają raportów zapisanych przez `ML`.
  - `UC-10` — model wytrenowany może zostać później ustawiony jako aktywny, jeśli `BE` finalizuje manifest jako używalny.

## 15. Guardraile implementacyjne
- Nie dodawać drugiego systemu konfiguracji poza `api/config/environment.py` i `.env*`.
- Nie hardcodować ścieżek `/opt/sudoku/...` w kodzie; ścieżki przychodzą z `BE` i są walidowane względem `ML_TRAINING_ALLOWED_OUTPUT_ROOTS`.
- Nie importować modeli API do `Application` ani `Infrastructure`.
- Nie umieszczać PyTorch/NumPy/HTTP klienta w `Application`.
- Nie tworzyć osobnych workflow per architektura modelu.
- Nie tworzyć osobnego `.npz` dla ResNet.
- Nie pozwalać `ML` samodzielnie wybierać modelu z rejestru; wybór modelu należy do `BE`.
- Nie zapisywać `model.json` po stronie `ML`.
- Nie uznawać braku raportu za `failed`, jeśli artefakt modelu jest kompletny i używalny.
- Nie publikować publicznej semantyki progressu opartej na mockowych 8 krokach.
- `cancel` jest kooperacyjny; nie zabijamy procesu siłowo w endpointcie HTTP.
- Event terminalny ma być odporny na chwilowy błąd transportu `ML -> BE`.

## 16. Inne istotne reguły
- Logi techniczne powinny zawierać `runName`, `baseModel.name`, `processedDataset.name`, `trainingProfileName`, ale nie powinny wypisywać pełnych payloadów z potencjalnie wrażliwymi ścieżkami poza diagnostyką debug.
- `sourceRevision` pozostaje po stronie `BE`; `ML` może przepisywać je do raportu tylko jeśli zostanie przekazane w kontrakcie w przyszłości.
- `TrainingProfile` jest wersjonowany nazwą. Zmiana liczby epok albo hiperparametrów powinna skutkować nową nazwą profilu, chyba że jest to lokalny override testowy.
- `ML_TRAINING_MAX_EPOCHS_OVERRIDE` jest bezpiecznikiem runtime, nie częścią biznesowego kontraktu `FE`.
- `etaSeconds` może być `null` w MVP, ale `epochCurrent`, `epochTotal` i `percent` muszą być spójne.
- Dla porównywalności eksperymentów seed musi ustawiać `random`, `numpy`, `torch` i CUDA, jeśli jest używana.

## 17. Plan testów minimum
- Unit `StartTrainingRunCommandHandler`: profile mismatch, brak plików, brak dozwolonego output root, aktywny run.
- Unit `ModelManifestReader`: brak wymaganych pól, `framework != pytorch`, brak architektury.
- Unit `ModelFactory`: `custom-cnn-v1`, `resnet18`, nieobsługiwany typ.
- Unit `InputTransformFactory`: CNN daje `1x28x28`, ResNet daje `3x224x224` albo rozmiar z manifestu.
- Unit `TrainingProfileCatalog`: profil zgodny z rodziną, niezgodny z rodziną, override epok.
- Unit `NpzDigitDatasetLoader`: brak kluczy, puste `train`, niespójne długości `x/y`.
- Integracyjny `POST /ml/trainings`: `202 Accepted`, worker uruchomiony, event `statusChanged`.
- Integracyjny `PytorchTrainingRunner`: mini `.npz`, 1 epoka, progress z `epochTotal=1`, zapis artefaktu i raportów, terminalny `completed`.
- Integracyjny cancel: żądanie cancel między epokami, terminalny `cancelled`, brak finalnego artefaktu sukcesu.
- Integracyjny event retry: terminalny event ponawiany z tym samym `sequence` po błędzie transportu.
