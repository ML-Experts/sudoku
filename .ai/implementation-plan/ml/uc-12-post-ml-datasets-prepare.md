# UC-12 ML — Plan implementacyjny (`POST /ml/datasets/prepare`)

## 1. Przeznaczenie endpointa
- Endpoint wewnętrzny `BE -> ML` odpowiedzialny za techniczne przygotowanie jednego artefaktu datasetowego `.npz` na podstawie logicznych źródeł (`board` i `digit`) wybranych wcześniej w `UC-11`.
- Endpoint nie jest publiczny dla `FE`; `FE` komunikuje się wyłącznie z `BE`.
- Celem biznesowym jest unifikacja różnych źródeł danych do wspólnego formatu treningowego dla kolejnych use-case'ów (`UC-06`, `UC-07`, `UC-09`).

## 2. Założenia planu (ważne)
- Plan bazuje na `PRD` i specyfikacji `UC-12`, nie na aktualnym stanie implementacji FE/BE.
- `BE` pozostaje `source of truth` dla workflow i rekordów; `ML` dostarcza wykonanie techniczne i raport.
- Rozdział odpowiedzialności:
  - `Application`: logika use-case, walidacje biznesowe, orkiestracja kroków.
  - `Infrastructure`: implementacje techniczne (OpenCV, NumPy, I/O, parsery formatów).
  - `Domain/Models`: modele i reguły domenowe bez zależności od FastAPI/HTTP.
  - `API`: transport HTTP, mapowanie modeli i błędów.

## 3. Kontrakt API wejście/wyjście (ML <-> BE)

### 3.1 Request (`PrepareDatasetArtifactApiEntry`)
```json
{
  "datasetName": "digits-boards-v1",
  "preprocessingProfile": "default-28x28-v1",
  "sources": [
    {
      "name": "v1_training",
      "type": "board",
      "splitPolicy": {
        "mode": "selected",
        "groupBy": "board",
        "ratios": { "train": 0.5, "val": 0.5, "test": 0.0 }
      }
    },
    {
      "name": "t10k",
      "type": "digit",
      "splitPolicy": {
        "mode": "mix",
        "groupBy": "sample",
        "ratios": { "train": 0.8, "val": 0.1, "test": 0.1 }
      }
    }
  ]
}
```

### 3.2 Response 200 (`PreparedDatasetArtifactApiResponse`)
```json
{
  "sampleCounts": { "train": 9657, "val": 2657, "test": 1000 },
  "sources": [
    {
      "name": "v1_training",
      "requestedType": "board",
      "detectedType": "board",
      "processedSampleCount": 8100,
      "includedSampleCount": 3314,
      "emptyCellCount": 4772,
      "rejectedSampleCount": 14,
      "warnings": []
    }
  ],
  "warnings": []
}
```

### 3.3 Response błędów (`ErrorApiResponse`)
- `422 Unprocessable Content` dla błędów walidacji danych źródłowych/kontraktu wejściowego.
- `500 Internal Server Error` dla błędów nieobsłużonych.
- Format:
```json
{
  "errorType": "dataset_source_invalid",
  "message": "Nie udało się przygotować danych dla źródła v1_training."
}
```

## 4. Zachowanie warstwowe (API / Application / Domain / Infrastructure)

### 4.1 API
- Przyjmuje request `PrepareDatasetArtifactApiEntry`.
- Waliduje format transportowy (obecność pól, typy JSON) i przekazuje komendę do `Application`.
- Mapuje wynik DTO na `PreparedDatasetArtifactApiResponse`.
- Mapuje wyjątki use-case na `ErrorApiResponse`.

### 4.2 Application
- Wykonuje walidację reguł use-case (spójność splitów, profile, źródła, zgodność typu żądanego i wykrytego).
- Orkiestruje pipeline:
  1. Rozwiązanie logical source -> technical input.
  2. Ekstrakcja próbek (board/digit).
  3. Wspólny preprocessing komórki.
  4. Split i budowa tablic `x_*`, `y_*`.
  5. Zapis tymczasowego artefaktu `tmp/{datasetName}.npz`.
  6. Złożenie raportu dla `BE`.
- Nie implementuje detali OpenCV/NumPy/file I/O (to rola `Infrastructure`).

### 4.3 Domain (models)
- Definiuje neutralne modele:
  - polityka splitu,
  - rekord próbki kanonicznej,
  - raport per źródło,
  - agregaty/liczniki.
- Definiuje reguły semantyczne:
  - `board`: `0 -> null` (pusta komórka),
  - `digit`: `0` pozostaje legalną etykietą klasy.

### 4.4 Infrastructure
- Implementuje:
  - skanowanie katalogów,
  - parser `.dat`,
  - loader IDX-UBYTE,
  - preprocessing OpenCV,
  - serializację `np.savez_compressed`,
  - deterministyczne sortowanie i przypisywanie splitów.
- Każda implementacja ma być generyczna i reusable dla kolejnych use-case'ów (bez logiki specyficznej dla jednego endpointa w adapterze).

## 5. Pliki per warstwa + odpowiedzialności

## API (`src/MachineLearning/api`)
- `api/controllers/datasets_controller.py` (new) — endpoint `POST /ml/datasets/prepare`.
- `api/models/prepare_dataset_artifact_api_entry.py` (new) — model requestu.
- `api/models/prepare_dataset_source_api_entry.py` (new) — model źródła.
- `api/models/dataset_split_policy_api_entry.py` (new) — model polityki splitu.
- `api/models/split_ratios_api_entry.py` (new) — model udziałów splitu.
- `api/models/prepared_dataset_artifact_api_response.py` (new) — model odpowiedzi sukcesu.
- `api/models/prepared_dataset_source_report_api_response.py` (new) — raport per źródło.
- `api/models/split_sample_counts_api_response.py` (new) — agregaty splitów.
- `api/models/error_api_response.py` (reuse/new) — wspólny model błędu.
- `api/dependencies.py` (update/new) — DI handlera use-case i adapterów infrastrukturalnych.
- `api/main.py` (update) — rejestracja routera datasets.

## Application (`src/MachineLearning/application`)
- `application/features/datasets/commands/prepare_dataset_artifact/prepare_dataset_artifact_command.py` (new) — komenda use-case.
- `application/features/datasets/commands/prepare_dataset_artifact/prepare_dataset_artifact_command_handler.py` (new) — orkiestracja całego przepływu.
- `application/features/datasets/commands/prepare_dataset_artifact/prepare_dataset_artifact_command_result_dto.py` (new) — wynik use-case.
- `application/features/datasets/dto/prepare_dataset_source_dto.py` (new) — DTO źródła.
- `application/features/datasets/dto/dataset_split_policy_dto.py` (new) — DTO polityki splitu.
- `application/features/datasets/dto/canonical_prepared_sample_dto.py` (new) — DTO próbki kanonicznej.
- `application/features/datasets/dto/prepared_dataset_source_report_dto.py` (new) — DTO raportu źródła.
- `application/features/datasets/dto/split_sample_counts_dto.py` (new) — DTO agregatów splitu.
- `application/features/datasets/errors/*.py` (new) — jawne wyjątki domenowo-aplikacyjne.

## Domain / Models (`src/MachineLearning/models`)
- `models/dataset_source_type.py` (new) — enum `board|digit|boardDerived`.
- `models/dataset_split.py` (new) — enum `train|val|test`.
- `models/canonical_prepared_sample.py` (new) — model próbki po unifikacji.
- `models/board_grid_label.py` (new) — model etykiet planszy 9x9.
- `models/preprocessing_profile.py` (new) — model ustawień recepty preprocessingu.
- `models/preparation_report.py` (new) — model raportu końcowego.

## Infrastructure (`src/MachineLearning/infrastructure`)
- `infrastructure/datasets/source_resolver.py` (new) — mapowanie logical source -> fizyczne wejście.
- `infrastructure/datasets/board_dataset_scanner.py` (new) — rekurencyjne wykrywanie par `.jpg + .dat`.
- `infrastructure/datasets/board_dat_parser.py` (new) — parser etykiet z `.dat`.
- `infrastructure/datasets/idx_dataset_loader.py` (new) — wczytanie par IDX-UBYTE.
- `infrastructure/datasets/sample_split_assigner.py` (new) — deterministyczny split (mix/selected).
- `infrastructure/vision/board_cells_extractor.py` (new/reuse) — wycinanie komórek z planszy.
- `infrastructure/vision/cell_preprocessing_pipeline.py` (new) — wspólny preprocessing `board` i `digit`.
- `infrastructure/storage/npz_dataset_artifact_writer.py` (new) — zapis `np.savez_compressed`.
- `infrastructure/storage/temp_dataset_path_provider.py` (new) — generowanie ścieżki tymczasowej wg konfiguracji.
- `infrastructure/reporting/preparation_report_builder.py` (new) — składanie raportu i warningów.

## 6. Sprawdzenie istniejących usług Infrastructure i reuse
- Istnieje po stronie `BE`:
  - `Infrastructure/Ml/MlDatasetsPreparationHttpClient.cs` — reusable klient `BE -> ML` (nie tworzyć duplikatu).
  - `Infrastructure/Storage/ProcessedDatasetsGateway.cs` — zapis/odczyt rekordów `.npz` i metadanych po stronie `BE`.
- W `ML` brak gotowych adapterów datasets (wg aktualnego drzewa kodu), więc należy je utworzyć.
- Każdy nowy adapter `Infrastructure` w `ML` projektujemy jako wielokrotnego użytku (np. `cell_preprocessing_pipeline.py` używalny również przez ścieżkę inferencji i przyszłe UC augmentacji).

## 7. Wyjątki, błędy i fallbacki

### 7.1 Kluczowe wyjątki
- `raw_dataset_not_found` — brak źródła `name` w oczekiwanej lokalizacji.
- `raw_dataset_type_mismatch` — struktura źródła niezgodna z deklarowanym `type`.
- `dataset_source_invalid` — niespójne/pary niekompletne (`.jpg/.dat` lub IDX).
- `no_samples_prepared` — po filtracji/brudnych danych brak próbek nadzorowanych.
- `unsupported_preprocessing_profile` — profil preprocessingu nieznany.
- `dataset_artifact_write_failed` — błąd zapisu `.npz`.

### 7.2 Fallbacki (kontrolowane)
- Per źródło: uszkodzone rekordy (np. jedna plansza) są odrzucane i raportowane, jeśli globalnie pozostają poprawne próbki.
- Globalnie: gdy wszystkie źródła kończą się bez próbek, zwracamy `422` (`no_samples_prepared`) i nie zapisujemy artefaktu.
- Brak jednego splitu (`val`/`test`) nie jest błędem krytycznym — zapisujemy pustą tablicę dla stałego schematu `.npz`.

## 8. Specyficzna logika (pseudokod)
```python
def prepare_dataset_artifact(command):
    validate_command(command)
    all_samples = []
    source_reports = []

    for source in command.sources:
        resolved = source_resolver.resolve(source.name, source.type)
        detected_type = resolved.detected_type
        ensure_type_compatible(source.type, detected_type)

        if detected_type == "board":
            boards = board_scanner.scan_pairs(resolved.path)
            prepared = []
            for board_pair in boards:
                image, label_grid = load_board_pair(board_pair)
                cells = board_cells_extractor.extract(image)  # 81 cells
                split = split_assigner.assign_group(source.split_policy, board_pair.group_key)
                for idx, cell in enumerate(cells):
                    raw_label = label_grid[idx]
                    label = None if raw_label == 0 else raw_label
                    processed = cell_preprocessor.run(cell, command.preprocessing_profile)
                    prepared.append(sample(split, label, processed, "boardDerived"))
        else:
            digits = idx_loader.load(resolved.images_path, resolved.labels_path)
            prepared = []
            for record in digits:
                split = split_assigner.assign_sample(source.split_policy, record.sample_key)
                processed = cell_preprocessor.run(record.image, command.preprocessing_profile)
                prepared.append(sample(split, record.label, processed, "digit"))

        all_samples.extend(prepared)
        source_reports.append(report_builder.from_source(source, detected_type, prepared))

    supervised = [s for s in all_samples if s.label is not None]
    ensure_non_empty(supervised)

    arrays = build_npz_arrays(supervised)  # x_train, y_train, ...
    npz_writer.write(temp_path_provider.for_name(command.dataset_name), arrays)

    return build_result(source_reports, arrays.counts)
```

## 9. Główne funkcje / komponenty
- `prepare_dataset_artifact()` — use-case orchestrator.
- `resolve_source()` — rozpoznanie i walidacja technicznego wejścia.
- `scan_board_pairs()` — wykrywanie kompletnych par planszy.
- `parse_board_labels()` — odczyt i walidacja gridu 9x9.
- `load_idx_pair()` — odczyt danych `digit`.
- `preprocess_cell_image()` — wspólny preprocessing komórki.
- `assign_split()` — deterministyczny podział danych.
- `build_npz_arrays()` — budowa tablic końcowych.
- `write_npz_artifact()` — zapis skompresowanego `.npz`.
- `build_preparation_report()` — raport jakości i liczników.

## 10. Przepływ wewnątrz ML (end-to-end)
1. API odbiera request i mapuje do komendy.
2. Application waliduje request i uruchamia orkiestrację.
3. Infrastructure czyta źródła i normalizuje próbki do formatu kanonicznego.
4. Application filtruje/kwalifikuje próbki do tablic nadzorowanych.
5. Infrastructure zapisuje tymczasowy artefakt `.npz`.
6. Application zwraca raport, API mapuje do odpowiedzi HTTP.
7. `BE` pobiera wynik i finalizuje zapis artefaktu do `data/processed`.

## 11. Workflow GitHub + konfiguracja środowisk
- `Production`:
  - Workflow ML-CD ustawia `ML_ENVIRONMENT=production`.
  - Workflow dostarcza/aktualizuje `.env.production` z absolutnymi ścieżkami (`boards`, `digits`, `tmp/datasets`, `tmp/ml-work`).
  - Nie trzymamy runtimeowych ścieżek datasetów w GitHub Variables jako źródła prawdy aplikacji.
- `Local`:
  - `.env.local` zawiera jawne, "na sztywno" ustawione ścieżki lokalne.
  - Lokalny run nie polega na mechanice workflow CI/CD.

## 12. Kolejność implementacji historyjki (zalecana)
1. Kontrakty API + modele `ApiEntry/ApiResponse`.
2. DTO + komenda + wyjątki w `Application`.
3. Domain models i reguły semantyczne etykiet.
4. Infrastructure: source resolver + parsery + loadery.
5. Infrastructure: wspólny pipeline preprocessingu komórek.
6. Infrastructure: split assigner + writer `.npz` + report builder.
7. Handler use-case + DI + kontroler.
8. Mapowanie błędów HTTP i testy integracyjne endpointu.
9. Testy wydajnościowe batch i walidacja deterministyczności splitu.

## 13. Zależności między historyjkami
- **Twarde zależności wejściowe**:
  - `UC-11` (lista raw candidates) — źródło nazw `name/type`.
  - `UC-13` (autoryzacja) — ochrona endpointu publicznego po stronie `BE`.
- **Zależności wyjściowe**:
  - `UC-06` (start treningu) — konsumuje gotowe `.npz`.
  - `UC-07`/`UC-09` — pośrednio zależne przez pipeline treningowy.
- **Niezależne funkcjonalnie**:
  - `UC-01`, `UC-02`, `UC-04` nie blokują implementacji endpointu przygotowania datasetu.

## 14. Guardraile implementacyjne
- Nie hardcodować ścieżek ani URL-i integracyjnych w kodzie.
- Nie mieszać modeli API z modelami domenowymi.
- Nie umieszczać logiki OpenCV/NumPy w `Application`.
- Zachować `camelCase` w JSON i nazewnictwo `ApiEntry/ApiResponse/Dto`.
- Zapewnić deterministyczność kolejności próbek i splitu.
- Nie zapisywać finalnego `data/processed/{name}.npz` po stronie ML (to odpowiedzialność BE).
- W `board`: nigdy nie mapować pustej komórki na klasę `0` w tablicach nadzorowanych.

## 15. Inne istotne reguły jakościowe
- Wymagane logowanie techniczne z kontekstem źródła (`datasetName`, `sourceName`) bez logowania danych wrażliwych.
- Każdy warning jakościowy musi być zwrócony do raportu, nie tylko do logów.
- Stabilny i wersjonowany `preprocessingProfile` jako element reprodukowalności.
- Stały schemat `.npz` (`x_train`, `y_train`, `x_val`, `y_val`, `x_test`, `y_test`, `class_names`) niezależnie od brakujących splitów.

## 16. Plan testów (minimum)
- Unit (`Application`): walidacje splitów, zgodność typu, obsługa `no_samples_prepared`.
- Unit (`Infrastructure`): parser `.dat`, loader IDX, split assigner, writer `.npz`.
- Integracyjne (`API`): `200`, `422`, `500`, poprawny format `ErrorApiResponse`.
- E2E (`BE -> ML`): pełny przepływ przygotowania i odbioru raportu.
