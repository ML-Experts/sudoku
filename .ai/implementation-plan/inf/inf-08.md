# INF-08 — Plan implementacyjny init bootstrap rejestru modeli

## 1. Opis przeznaczenia
- Celem `INF-08` jest dostarczenie osobnej, idempotentnej aplikacji inicjalizacyjnej dla warstwy `MachineLearning`, która tworzy brakujące wpisy bootstrap w `models/registry` oraz opcjonalnie ustawia pierwszy aktywny model w `models/active/inference.json`.
- Aplikacja nie jest endpointem HTTP, nie jest wywoływana przez użytkownika z `FE` i nie należy do standardowego runtime serwisu ML. Jest uruchamiana jako init:
  - lokalnie przez developera,
  - produkcyjnie przez workflow GitHub / deploy / post-deploy,
  - opcjonalnie ręcznie przez operatora serwera.
- Wszystko, co dotyczy tej aplikacji, ma znajdować się w jednym folderze:

```text
src/MachineLearning/init_bootstrap
```

- Jedyny dozwolony dostęp poza tym folderem:
  - odczyt konfiguracji z głównego `.env` / `.env.{environment}` w `src/MachineLearning`,
  - korzystanie z zależności z głównego `src/MachineLearning/requirements.txt`,
  - zapis do katalogów runtime wskazanych w `.env` (`models/registry`, `models/active`),
  - cache bibliotek ML używany przez `torchvision`, jeśli wymagany przez oficjalny mechanizm PyTorch.
- Plan świadomie nie sugeruje się aktualnym stanem implementacji `FE` i `BE`. `init_bootstrap` jest osobnym narzędziem operacyjnym, a nie częścią clean architecture aplikacji webowej.

## 2. Zakres funkcjonalny
- Utworzenie lokalnych wpisów bootstrap w `models/registry/{modelName}` na podstawie deklaracji w `.env`.
- Obsługa minimum dwóch rodzin modeli:
  - własny mały `CNN` jako baseline,
  - `ResNet18` z `torchvision` jako punkt startowy do transfer learning / fine-tuningu.
- Wygenerowanie kompletnego `model.json` na podstawie szablonu dla pary `family + type`.
- Zapis głównego artefaktu modelu pod ścieżką wskazaną w manifeście, domyślnie `artifacts/model.pt`.
- Opcjonalne utworzenie `models/active/inference.json`, ale tylko gdy wskaźnik nie istnieje i wskazany model ma `canUseForInference = true`.
- Zwrócenie raportu tekstowego / exit code możliwego do użycia w workflow.

## 3. Poza zakresem
- Brak endpointów FastAPI.
- Brak zależności od `FE`, `BE`, kontrolerów, handlerów `Application` i istniejących modułów runtime ML.
- Brak treningu modeli na datasetach użytkownika (`UC-06`).
- Brak przygotowania datasetów (`UC-12`).
- Brak przełączania aktywnego modelu przez API (`UC-10`).
- Brak dynamicznego `pip install` w kodzie initu.
- Brak pobierania gotowych modeli z losowych repozytoriów GitHub.
- Brak naprawiania / migracji modeli wytrenowanych przez `UC-06`.

## 4. Założenia projektowe
- `init_bootstrap` jest idempotentny:
  - kompletny istniejący wpis jest pomijany,
  - brakujący wpis jest tworzony,
  - niekompletny wpis bez trybu overwrite kończy proces błędem,
  - istniejący aktywny wskaźnik nie jest nadpisywany.
- Manifest jest kontraktem technicznym. Loader modeli, trening i inferencja nie zgadują architektury z nazwy katalogu albo nazwy pliku.
- Model bootstrap i model wytrenowany przez `UC-06` są dla konsumentów takim samym typem wpisu registry: katalog + `model.json` + `artifacts/`.
- `sourceType = bootstrap` i `sourceRunName = null` są poprawnym stanem.
- Losowo zainicjalizowany model `CNN` oraz `ResNet18` z wymienioną głowicą klasyfikacyjną domyślnie nie powinny mieć `canUseForInference = true`, dopóki nie mają sensownych wag dla domeny sudoku.
- `init_bootstrap` może zakończyć się sukcesem bez aktywnego modelu, jeżeli żaden wpis bootstrap nie nadaje się do inferencji.

## 5. Konfiguracja `.env`

Konfiguracja znajduje się w głównym folderze `src/MachineLearning`, nie w `init_bootstrap`.

Ważna zasada: `.env` jest źródłem wartości konfiguracyjnych, a `settings.py` nie jest drugim miejscem konfiguracji. `settings.py` ma być wyłącznie kodem, który:
- odczytuje wartości z `.env`,
- sprawdza, czy wymagane zmienne istnieją,
- konwertuje tekst z `.env` na typy używane przez program, np. `bool`, `Path`, listę deklaracji JSON,
- zatrzymuje init z czytelnym błędem, jeśli konfiguracja jest niepoprawna.

Nie wpisujemy w `settings.py` ścieżek runtime, list modeli ani wartości specyficznych dla `local` / `production`.

Przykład lokalny:

```dotenv
ML_ENVIRONMENT=local
ML_MODELS_REGISTRY_DIRECTORY_PATH=/home/wojtek/projects/sudoku/data/models/registry
ML_ACTIVE_MODEL_DIRECTORY_PATH=/home/wojtek/projects/sudoku/data/models/active
ML_BOOTSTRAP_MODELS_JSON=[{"family":"cnn","type":"custom-cnn-v1","name":"cnn-baseline","displayName":"CNN baseline"},{"family":"resnet","type":"resnet18","displayName":"ResNet18 ImageNet bootstrap"}]
ML_BOOTSTRAP_OVERWRITE_EXISTING=false
ML_BOOTSTRAP_SET_ACTIVE_IF_MISSING=true
ML_BOOTSTRAP_DEFAULT_ACTIVE_MODEL=cnn-baseline
```

Znaczenie:
- `ML_ENVIRONMENT` — `local` albo `production`; wybiera plik `.env.{environment}`, jeśli stosujemy overlay.
- `ML_MODELS_REGISTRY_DIRECTORY_PATH` — absolutna ścieżka do `models/registry`.
- `ML_ACTIVE_MODEL_DIRECTORY_PATH` — absolutna ścieżka do `models/active`.
- `ML_BOOTSTRAP_MODELS_JSON` — lista modeli, które init ma zapewnić.
- `ML_BOOTSTRAP_OVERWRITE_EXISTING` — jawna zgoda na odtworzenie niekompletnego albo istniejącego wpisu.
- `ML_BOOTSTRAP_SET_ACTIVE_IF_MISSING` — pozwala utworzyć `active/inference.json`, gdy go nie ma.
- `ML_BOOTSTRAP_DEFAULT_ACTIVE_MODEL` — nazwa modelu ustawianego jako aktywny tylko przy braku wskaźnika.

Minimalna deklaracja modelu:

```json
{
  "family": "resnet",
  "type": "resnet18",
  "displayName": "ResNet18 ImageNet bootstrap"
}
```

Dozwolone pola nadpisywane z `.env`:
- `name`,
- `displayName`,
- `canStartTraining`,
- `canUseForInference`.

Pola techniczne, których nie nadpisujemy z `.env` w MVP:
- `architecture.inputChannels`,
- `architecture.inputHeight`,
- `architecture.inputWidth`,
- `architecture.inputProfile`,
- `architecture.library`,
- `artifacts.format`,
- `artifacts.primaryArtifactRelativePath`.

## 6. Zależności Python

Główne `src/MachineLearning/requirements.txt` musi zawierać zależności potrzebne dla initu:

```text
numpy
python-dotenv
python-slugify
torch
torchvision
```

Reguły:
- `init_bootstrap` nie wykonuje `pip install`.
- Brak `torch` albo `torchvision` kończy się czytelnym błędem z instrukcją instalacji zależności z głównego `requirements.txt`.
- Jeśli `torchvision` musi pobrać oficjalne wagi przy pierwszym uruchomieniu, brak internetu jest błędem initu. Po zapisaniu lokalnego artefaktu kolejne uruchomienia nie powinny potrzebować internetu dla kompletnego wpisu.

## 7. Layout docelowy rejestru

Każdy wpis modelu:

```text
models/registry/{modelName}/
├── model.json
└── artifacts/
    └── model.pt
```

Minimalny kompletny wpis:
- istnieje katalog `models/registry/{modelName}`,
- istnieje poprawny JSON `model.json`,
- istnieje katalog `artifacts`,
- istnieje główny artefakt wskazany przez `artifacts.primaryArtifactRelativePath`,
- `model.json.name` jest równy nazwie katalogu,
- `sourceType = bootstrap`,
- `sourceRunName = null`.

Aktywny model:

```text
models/active/inference.json
```

Przykład:

```json
{
  "modelName": "mnist-cnn-baseline",
  "registryRelativePath": "../registry/mnist-cnn-baseline",
  "setBy": "init_bootstrap"
}
```

## 8. Warstwy aplikacji init bootstrap

To nie jest clean architecture. Warstwy są technicznym podziałem wewnątrz jednego folderu `init_bootstrap`, żeby init był czytelny i testowalny bez zależności od reszty aplikacji.

### 8.1 Warstwa CLI / entrypoint
- Odpowiada za start procesu, argumenty, exit code i wypisanie raportu.
- Nie zna detali PyTorch ani struktury manifestów poza uruchomieniem orkiestratora.

### 8.2 Warstwa konfiguracji
- Ładuje `.env` z głównego `src/MachineLearning`.
- Waliduje wymagane zmienne i parsuje `ML_BOOTSTRAP_MODELS_JSON`.
- Normalizuje booleany, ścieżki absolutne i deklaracje modeli.

### 8.3 Warstwa szablonów i manifestów
- Utrzymuje zamknięty katalog wspieranych par `family + type`.
- Buduje pełny `model.json` z szablonu i dozwolonych nadpisań.
- Pilnuje kontraktu manifestu i spójności `name`.

### 8.4 Warstwa budowania modeli
- Tworzy obiekty `torch.nn.Module` dla wspieranych architektur.
- Dla `CNN` tworzy własny lokalny model.
- Dla `ResNet18` używa `torchvision`, wymienia ostatnią warstwę na liczbę klas projektu i zapisuje lokalny `state_dict`.

### 8.5 Warstwa registry I/O
- Sprawdza kompletność wpisów.
- Tworzy katalogi i zapisuje artefakty atomowo.
- Nie usuwa modeli wytrenowanych przez `UC-06`.
- Nie nadpisuje aktywnego modelu, jeśli wskaźnik istnieje.

### 8.6 Warstwa raportowania i błędów
- Agreguje wynik dla każdego modelu: `created`, `skipped`, `failed`.
- Mapuje błędy na stabilne `errorType` oraz exit code.
- Wypisuje diagnostykę bez sekretów i bez dumpowania całego `.env`.

### 8.7 Warstwa testów lokalnych modułu
- Testy żyją wewnątrz `src/MachineLearning/init_bootstrap/tests`.
- Nie importują aplikacyjnych warstw ML.
- Używają tymczasowych katalogów registry/active i minimalnych mocków builderów tam, gdzie test nie powinien pobierać wag.

## 9. Pliki per warstwa i odpowiedzialności

Wszystkie pliki aplikacji znajdują się w `src/MachineLearning/init_bootstrap`.

### CLI / entrypoint
- `[NOWY]` `__init__.py`
  - oznacza folder jako moduł Pythona,
  - eksportuje wersję modułu, jeśli będzie potrzebna w raportach.
- `[NOWY]` `__main__.py`
  - umożliwia uruchomienie `python -m init_bootstrap`,
  - wywołuje `cli.main()`.
- `[NOWY]` `cli.py`
  - parsuje argumenty techniczne, np. `--dry-run`, `--verbose`, `--env-file`,
  - uruchamia `BootstrapModelsApplication`,
  - mapuje wynik na exit code,
  - wypisuje raport końcowy.

### Konfiguracja
- `[NOWY]` `env_loader.py`
  - odnajduje główny folder `src/MachineLearning`,
  - ładuje `.env`,
  - opcjonalnie ładuje `.env.{ML_ENVIRONMENT}` jako overlay,
  - nie korzysta z istniejącego `api/config`.
- `[NOWY]` `settings.py`
  - definiuje `BootstrapSettings` jako typowany wynik odczytu `.env`,
  - waliduje wymagane ścieżki i flagi,
  - konwertuje wartości `.env` do typów Pythona,
  - nie zawiera własnych wartości konfiguracyjnych i nie zastępuje `.env`.
- `[NOWY]` `bootstrap_declaration.py`
  - model pojedynczej deklaracji z `ML_BOOTSTRAP_MODELS_JSON`,
  - walidacja pól `family`, `type`, `name`, `displayName`, capability overrides.
- `[NOWY]` `constants.py`
  - nazwy zmiennych środowiskowych,
  - dozwolone statusy raportu,
  - standardowe nazwy plików: `model.json`, `artifacts/model.pt`, `inference.json`.

### Nazewnictwo i walidacja
- `[NOWY]` `naming.py`
  - deterministyczne generowanie `modelName`,
  - slugowanie tekstu,
  - walidacja formatu `[a-z0-9-]+`,
  - wykrywanie kolizji nazw w jednym `ML_BOOTSTRAP_MODELS_JSON`.
- `[NOWY]` `validation.py`
  - walidacja manifestu przed zapisem,
  - walidacja kompletności istniejącego wpisu,
  - reguły capability, np. aktywny model wymaga `canUseForInference = true`.

### Szablony i manifesty
- `[NOWY]` `manifest_templates.py`
  - zamknięta mapa wspieranych szablonów:
    - `family=cnn`, `type=custom-cnn-v1`,
    - `family=resnet`, `type=resnet18`,
  - domyślne wartości architektury, treningu i capability.
- `[NOWY]` `manifest_builder.py`
  - buduje pełny manifest z szablonu i deklaracji `.env`,
  - ustawia `sourceType = bootstrap`,
  - ustawia `sourceRunName = null`,
  - pilnuje zgodności `name` z katalogiem.
- `[NOWY]` `manifest_io.py`
  - zapis i odczyt `model.json`,
  - formatowanie JSON stabilnym sortowaniem kluczy / wcięciami,
  - brak logiki budowania architektury.

### Budowanie modeli i artefaktów
- `[NOWY]` `model_builders.py`
  - publiczny dispatcher `build_model_for_manifest(manifest)`,
  - wybiera builder po `architecture.type`.
- `[NOWY]` `custom_cnn.py`
  - definicja małego `torch.nn.Module` dla `custom-cnn-v1`,
  - brak zależności od treningu i datasetów.
- `[NOWY]` `torchvision_resnet.py`
  - budowa `resnet18`,
  - użycie oficjalnych wag `ResNet18_Weights.DEFAULT`, jeśli szablon tak deklaruje,
  - wymiana klasyfikatora na `architecture.numClasses`.
- `[NOWY]` `artifact_serializer.py`
  - zapis `state_dict` do `artifacts/model.pt`,
  - walidacja, że plik powstał i nie jest pusty,
  - izolacja detali `torch.save`.

### Registry I/O
- `[NOWY]` `filesystem.py`
  - małe helpery I/O: tworzenie katalogów, zapis pliku tymczasowego, atomic replace,
  - brak wiedzy o modelach.
- `[NOWY]` `registry_inspector.py`
  - sprawdza, czy wpis istnieje,
  - rozróżnia `missing`, `complete`, `incomplete`,
  - zwraca powody niekompletności.
- `[NOWY]` `registry_writer.py`
  - tworzy katalog modelu,
  - zapisuje artefakt i manifest w bezpiecznej kolejności,
  - obsługuje `overwriteExisting`,
  - sprząta częściowo utworzony wpis po błędzie zapisu.
- `[NOWY]` `active_model_writer.py`
  - tworzy `models/active/inference.json`,
  - działa wyłącznie w trybie `setActiveIfMissing`,
  - nie nadpisuje istniejącego wskaźnika.

### Orkiestracja
- `[NOWY]` `bootstrap_models.py`
  - główny przypadek użycia initu,
  - iteruje po deklaracjach,
  - wywołuje builder manifestu, registry inspector, builder modelu i writer,
  - agreguje raport.
- `[NOWY]` `result.py`
  - modele wyniku: `BootstrapRunResult`, `BootstrapModelResult`,
  - statusy per model: `created`, `skipped`, `failed`,
  - licznik ostrzeżeń.
- `[NOWY]` `exceptions.py`
  - jawne wyjątki z `errorType`,
  - np. `bootstrap_configuration_invalid`, `bootstrap_dependency_missing`, `bootstrap_registry_entry_incomplete`.
- `[NOWY]` `logging_config.py`
  - konfiguracja logowania konsolowego,
  - brak logowania sekretów i pełnych wartości `.env`.

### Testy modułu
- `[NOWY]` `tests/__init__.py`
  - marker pakietu testowego.
- `[NOWY]` `tests/test_naming.py`
  - slugowanie, walidacja nazw, kolizje.
- `[NOWY]` `tests/test_settings.py`
  - parsowanie `.env`, booleany, JSON deklaracji.
- `[NOWY]` `tests/test_manifest_builder.py`
  - pełny manifest dla `CNN` i `ResNet18`,
  - brak możliwości nadpisania pól technicznych.
- `[NOWY]` `tests/test_registry_inspector.py`
  - `missing`, `complete`, `incomplete`.
- `[NOWY]` `tests/test_registry_writer_idempotency.py`
  - brak nadpisywania kompletnego wpisu,
  - błąd dla niekompletnego wpisu bez overwrite,
  - overwrite tylko po jawnej fladze.
- `[NOWY]` `tests/test_active_model_writer.py`
  - tworzenie wskaźnika tylko, gdy go nie ma,
  - brak ustawienia modelu bez `canUseForInference`.
- `[NOWY]` `tests/test_bootstrap_models.py`
  - przepływ end-to-end na tymczasowym registry z mockiem buildera.

## 10. Standard manifestu `model.json`

Minimalny manifest bootstrap:

```json
{
  "name": "cnn-baseline",
  "displayName": "CNN baseline",
  "sourceType": "bootstrap",
  "sourceRunName": null,
  "framework": "pytorch",
  "architecture": {
    "type": "custom-cnn-v1",
    "family": "cnn",
    "variant": "digit-cnn-small",
    "numClasses": 10,
    "inputChannels": 1,
    "inputHeight": 28,
    "inputWidth": 28,
    "inputProfile": "digits-28x28-grayscale-v1"
  },
  "artifacts": {
    "primaryArtifactRelativePath": "artifacts/model.pt",
    "format": "pytorch-state-dict"
  },
  "capabilities": {
    "canStartTraining": true,
    "canUseForInference": false
  },
  "training": {
    "defaultTrainingProfileName": "cnn-default-v1",
    "defaultAugmentationProfileName": "digits-light-v1"
  },
  "metadata": {
    "createdBy": "init_bootstrap",
    "description": "Własny mały CNN utworzony jako lokalny bootstrap."
  }
}
```

Kontrakt minimalny dla przyszłego loadera:
- `framework`,
- `architecture.type`,
- `architecture.inputProfile`,
- `artifacts.primaryArtifactRelativePath`,
- `artifacts.format`.

To oznacza, że sam plik `artifacts/model.pt` i ścieżka do niego nie wystarczają. W PyTorch, jeśli zapisujemy `state_dict`, plik zawiera wagi, ale zwykle nie zawiera kompletnej definicji architektury. Program ładujący model musi najpierw:
1. Odczytać `model.json`.
2. Sprawdzić `framework`, np. `pytorch`.
3. Po `architecture.type` wybrać właściwy kod budujący architekturę, np. `custom-cnn-v1` albo `resnet18`.
4. Użyć pól `architecture.numClasses`, `inputChannels`, `inputHeight`, `inputWidth` i ewentualnie `architecture.variant/library`, żeby zbudować moduł o tym samym kształcie.
5. Odczytać `artifacts.primaryArtifactRelativePath`.
6. Wczytać wagi z `model.pt` do zbudowanego modelu.
7. Po `architecture.inputProfile` dobrać preprocessing wejścia, np. `28x28 grayscale` dla CNN albo `224x224 RGB` dla ResNet.

Dlatego manifest musi zawierać zarówno referencję do fizycznego pliku wag, jak i techniczne pola mówiące, jak ten plik interpretować. Brak któregoś z tych pól powinien oznaczać model niekompletny albo nieładowalny.

W MVP powyższe pola są wystarczające dla modeli bootstrap, pod warunkiem że w kodzie przyszłego loadera / factory istnieje jawne mapowanie:

```text
architecture.type=custom-cnn-v1 -> build_custom_cnn_v1(...)
architecture.type=resnet18 -> build_resnet18(...)
inputProfile=digits-28x28-grayscale-v1 -> transform 28x28 grayscale
inputProfile=digits-224x224-rgb-v1 -> transform 224x224 RGB
```

Kontrakt minimalny dla listowania przez `BE`:
- `name`,
- `displayName`,
- `sourceType`,
- `sourceRunName`,
- `capabilities.canStartTraining`,
- `capabilities.canUseForInference`.

## 11. Przepływ w obrębie ML init

1. Operator / workflow uruchamia:

```bash
cd src/MachineLearning
python -m init_bootstrap
```

`python -m init_bootstrap` oznacza: uruchom pakiet Pythona `init_bootstrap` jako program. Python szuka wtedy katalogu `init_bootstrap` w bieżącym katalogu (`src/MachineLearning`) i wykonuje plik `init_bootstrap/__main__.py`. Dzięki temu init można odpalić bez osobnego skryptu `.sh` i bez podawania ścieżki do konkretnego pliku `.py`.

2. `__main__.py` przekazuje sterowanie do `cli.py`.
3. `cli.py` ładuje ustawienia przez `env_loader.py` i `settings.py`.
4. `settings.py` parsuje `ML_BOOTSTRAP_MODELS_JSON`.
5. `naming.py` uzupełnia lub waliduje `name` każdej deklaracji.
6. `bootstrap_models.py` dla każdej deklaracji:
   - znajduje szablon w `manifest_templates.py`,
   - buduje manifest przez `manifest_builder.py`,
   - sprawdza stan wpisu przez `registry_inspector.py`,
   - pomija kompletny wpis bez overwrite,
   - buduje model przez `model_builders.py`,
   - zapisuje artefakt przez `artifact_serializer.py`,
   - zapisuje manifest przez `registry_writer.py`.
7. Po modelach `active_model_writer.py` próbuje utworzyć `active/inference.json`, jeśli konfiguracja na to pozwala.
8. `result.py` składa raport.
9. `cli.py` wypisuje raport i zwraca exit code.

## 12. Specyficzna logika — pseudokod

### 12.1 Główny init

```python
def run_bootstrap():
    settings = load_settings_from_machine_learning_env()
    declarations = parse_bootstrap_models(settings.bootstrap_models_json)
    declarations = assign_and_validate_unique_names(declarations)

    results = []

    for declaration in declarations:
        try:
            template = manifest_templates.get(declaration.family, declaration.type)
            manifest = manifest_builder.build(template, declaration)

            state = registry_inspector.inspect(settings.registry_path, manifest)

            if state.is_complete and not settings.overwrite_existing:
                results.append(skipped(manifest.name, "entry_complete"))
                continue

            if state.is_incomplete and not settings.overwrite_existing:
                raise RegistryEntryIncomplete(state.reasons)

            model = model_builders.build_model_for_manifest(manifest)
            registry_writer.write_entry(
                registry_path=settings.registry_path,
                manifest=manifest,
                model=model,
                overwrite=settings.overwrite_existing,
            )

            results.append(created(manifest.name))

        except BootstrapError as error:
            results.append(failed(declaration.display_name_or_type, error))
            if error.is_fatal:
                break

    active_result = active_model_writer.ensure_active_if_missing(settings, results)
    return BootstrapRunResult(results, active_result)
```

### 12.2 Idempotencja wpisu registry

```python
def inspect_entry(registry_path, manifest):
    model_dir = registry_path / manifest["name"]
    manifest_path = model_dir / "model.json"
    artifact_path = model_dir / manifest["artifacts"]["primaryArtifactRelativePath"]

    if not model_dir.exists():
        return MissingEntry()

    missing = []
    if not manifest_path.is_file():
        missing.append("model.json")
    if not artifact_path.is_file():
        missing.append(str(artifact_path))
    if manifest_path.is_file() and read_json(manifest_path).get("name") != manifest["name"]:
        missing.append("model_name_mismatch")

    if missing:
        return IncompleteEntry(missing)

    return CompleteEntry()
```

### 12.3 Atomiczny zapis wpisu

```python
def write_entry(registry_path, manifest, model, overwrite):
    target_dir = registry_path / manifest["name"]
    temp_dir = registry_path / f".{manifest['name']}.tmp"

    if temp_dir.exists():
        remove_directory(temp_dir)

    create_directory(temp_dir / "artifacts")

    artifact_serializer.save_state_dict(
        model=model,
        path=temp_dir / manifest["artifacts"]["primaryArtifactRelativePath"],
    )
    manifest_io.write_json(temp_dir / "model.json", manifest)

    validate_complete_entry(temp_dir, manifest)

    if target_dir.exists() and overwrite:
        replace_directory(temp_dir, target_dir)
    elif not target_dir.exists():
        move_directory(temp_dir, target_dir)
    else:
        raise RegistryEntryAlreadyExists()
```

### 12.4 Ustawienie aktywnego modelu

```python
def ensure_active_if_missing(settings, created_or_existing_entries):
    active_file = settings.active_model_path / "inference.json"

    if not settings.set_active_if_missing:
        return skipped("disabled")

    if active_file.exists():
        return skipped("active_model_already_set")

    model_name = settings.default_active_model
    manifest = read_manifest(settings.registry_path / model_name / "model.json")

    if not manifest["capabilities"]["canUseForInference"]:
        return skipped("model_not_inference_capable")

    write_json_atomic(active_file, {
        "modelName": model_name,
        "registryRelativePath": f"../registry/{model_name}",
        "setBy": "init_bootstrap",
    })
```

## 13. Główne funkcje
- `cli.main()` — wejście procesu i exit code.
- `env_loader.load_environment()` — ładowanie głównej konfiguracji ML.
- `settings.load_bootstrap_settings()` — walidacja i mapowanie `.env` na obiekt ustawień.
- `parse_bootstrap_declarations()` — parsowanie `ML_BOOTSTRAP_MODELS_JSON`.
- `generate_model_name()` — deterministyczny slug z `name` / `displayName` / `family + type`.
- `build_manifest()` — budowa kompletnego `model.json`.
- `build_model_for_manifest()` — utworzenie `torch.nn.Module`.
- `build_custom_cnn_v1()` — lokalny baseline CNN.
- `build_resnet18()` — `torchvision` ResNet18 z głowicą dla klas projektu.
- `save_state_dict()` — zapis `artifacts/model.pt`.
- `inspect_registry_entry()` — detekcja `missing` / `complete` / `incomplete`.
- `write_registry_entry()` — atomowy zapis wpisu.
- `ensure_active_model_if_missing()` — opcjonalny zapis `models/active/inference.json`.
- `build_run_report()` — raport dla workflow i operatora.

## 14. Wyjątki, fallbacki i zachowania brzegowe

### 14.1 Wyjątki konfiguracji
- `bootstrap_configuration_missing` — brak wymaganej zmiennej `.env`.
- `bootstrap_configuration_invalid` — błędny JSON w `ML_BOOTSTRAP_MODELS_JSON`.
- `bootstrap_model_name_collision` — dwie deklaracje prowadzą do tej samej nazwy.
- `bootstrap_model_name_invalid` — nazwa nie spełnia formatu.
- `bootstrap_template_not_found` — brak szablonu dla `family + type`.

Zachowanie:
- proces kończy się błędem,
- nie tworzy częściowych wpisów,
- exit code różny od zera.

### 14.2 Wyjątki zależności
- `bootstrap_dependency_missing` — brak `torch` albo `torchvision`.
- `bootstrap_pretrained_weights_unavailable` — `torchvision` nie może pobrać oficjalnych wag.

Zachowanie:
- init nie wykonuje `pip install`,
- raport zawiera instrukcję uruchomienia `pip install -r src/MachineLearning/requirements.txt`,
- brak fallbacku do losowych wag dla modelu deklarowanego jako pretrained.

### 14.3 Wyjątki registry
- `bootstrap_registry_entry_incomplete` — istnieje katalog modelu, ale brakuje manifestu albo artefaktu.
- `bootstrap_registry_entry_name_mismatch` — `model.json.name` nie odpowiada nazwie katalogu.
- `bootstrap_artifact_write_failed` — nie udało się zapisać `model.pt`.
- `bootstrap_manifest_write_failed` — nie udało się zapisać `model.json`.

Zachowanie:
- kompletny wpis jest pomijany,
- niekompletny wpis bez overwrite przerywa tworzenie tego modelu i zwraca błąd,
- przy błędzie zapisu usuwany jest katalog tymczasowy,
- modele wytrenowane przez `UC-06` nie są usuwane ani modyfikowane.

### 14.4 Fallbacki kontrolowane
- Brak aktywnego modelu po inicjalizacji jest dopuszczalny, jeśli żaden bootstrap nie ma `canUseForInference = true`.
- Istniejący `active/inference.json` jest zawsze zachowany, nawet jeśli wskazuje model inny niż domyślny.
- Kompletny istniejący wpis jest traktowany jako sukces idempotentny (`skipped`), nie jako błąd.
- `--dry-run` może raportować planowane działania bez zapisu.

### 14.5 Brak fallbacków
- Brak fallbacku do importu z kodu `api/`, `application/`, `infrastructure` lub `models`.
- Brak fallbacku do wartości hardcodowanych w kodzie dla produkcyjnych ścieżek.
- Brak fallbacku z `ResNet18_Weights.DEFAULT` do losowych wag, jeśli manifest deklaruje pretrained source.
- Brak automatycznego overwrite uszkodzonego wpisu bez jawnej flagi.

## 15. Workflow GitHub i konfiguracja środowisk

### 15.1 Local
- Lokalnie wartości są wpisane jawnie w `src/MachineLearning/.env.local` albo głównym `src/MachineLearning/.env`.
- Ścieżki lokalne mogą być "na sztywno", np. `/home/wojtek/projects/sudoku/data/models/registry`.
- Lokalny developer uruchamia:

```bash
cd src/MachineLearning
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m init_bootstrap
```

### 15.2 Production
- Workflow produkcyjny zmienia / generuje produkcyjny `.env.production` dla `src/MachineLearning`.
- Zmienne produkcyjne muszą wskazywać realne katalogi runtime, nie katalog paczki buildowej.
- Workflow powinien wykonać init po instalacji zależności i przed restartem usług ML/BE, żeby runtime widział gotowy rejestr.

Przykładowy etap workflow:

```text
1. Checkout repo.
2. Setup Python.
3. Utworzenie / aktywacja venv.
4. pip install -r src/MachineLearning/requirements.txt.
5. Wygenerowanie src/MachineLearning/.env.production z sekretów/variables workflow.
6. Ustawienie ML_ENVIRONMENT=production.
7. cd src/MachineLearning && python -m init_bootstrap.
8. Weryfikacja obecności wymaganych wpisów w models/registry.
9. Restart usług.
```

Zmienne / sekrety workflow:
- `ML_MODELS_REGISTRY_DIRECTORY_PATH`,
- `ML_ACTIVE_MODEL_DIRECTORY_PATH`,
- `ML_BOOTSTRAP_MODELS_JSON`,
- `ML_BOOTSTRAP_OVERWRITE_EXISTING=false`,
- `ML_BOOTSTRAP_SET_ACTIVE_IF_MISSING`,
- `ML_BOOTSTRAP_DEFAULT_ACTIVE_MODEL`.

Reguły workflow:
- Produkcyjny workflow może modyfikować wyłącznie env produkcyjny i katalogi runtime.
- Lokalny `.env.local` nie jest generowany przez workflow.
- Sekrety nie trafiają do repo.
- Workflow nie powinien nadpisywać kompletnego registry przy każdym deployu.
- Jeżeli init kończy się błędem, deploy powinien zostać zatrzymany przed restartem usług.

## 16. Zależności między historyjkami

### Wejściowe
- `INF-01` / `INF-02` — projekt musi mieć odtwarzalne uruchomienie i środowisko Python z `requirements.txt`.
- `INF-03` — produkcyjne katalogi runtime muszą istnieć albo workflow musi mieć prawo je utworzyć.
- `INF-07` — jeśli init ma działać automatycznie w produkcji, workflow CD musi mieć etap `python -m init_bootstrap`.

### Nieblokujące
- `UC-01`, `UC-02`, `UC-04` — przykłady i preprocessing obrazów nie są wymagane do utworzenia registry bootstrap.
- `UC-11`, `UC-12`, `UC-13` — datasety i autoryzacja administracyjna nie są wymagane do działania initu.

### Wyjściowe
- `UC-06` — start treningu potrzebuje wpisów registry, z których można wybrać model bazowy z `canStartTraining = true`.
- `UC-08` — lista modeli powinna pokazać także wpisy bootstrap bez `sourceRunName`.
- `UC-09` — szczegóły treningów muszą akceptować relację do modelu bazowego bootstrap.
- `UC-10` — aktywny model wskazuje wpis registry; wskaźnik utworzony przez init jest stanem startowym, a API później może go zmienić.

## 17. Kolejność implementacji kodu
1. Dodać zależności `torch` i `torchvision` do `src/MachineLearning/requirements.txt`.
2. Utworzyć folder `src/MachineLearning/init_bootstrap` z entrypointami `__init__.py`, `__main__.py`, `cli.py`.
3. Zaimplementować loader `.env` i model `BootstrapSettings`.
4. Zaimplementować parser deklaracji `ML_BOOTSTRAP_MODELS_JSON`.
5. Zaimplementować `naming.py` i walidację nazw.
6. Zaimplementować `manifest_templates.py` dla `custom-cnn-v1` i `resnet18`.
7. Zaimplementować `manifest_builder.py` i testy kontraktu manifestu.
8. Zaimplementować `custom_cnn.py` i `torchvision_resnet.py`.
9. Zaimplementować `artifact_serializer.py`.
10. Zaimplementować `registry_inspector.py`, `registry_writer.py` i atomiczny zapis.
11. Zaimplementować `active_model_writer.py`.
12. Zaimplementować główną orkiestrację `bootstrap_models.py` i raport `result.py`.
13. Dodać testy jednostkowe modułu w `init_bootstrap/tests`.
14. Dodać lokalne wartości `.env.local` / `.env` dla bootstrapu.
15. Rozszerzyć workflow GitHub o etap produkcyjnego initu.
16. Uruchomić lokalny smoke test `python -m init_bootstrap` na pustym tymczasowym registry.
17. Uruchomić drugi smoke test na tym samym registry i potwierdzić idempotentne `skipped`.

## 18. Guardraile implementacyjne
- Nie importować niczego z obecnych warstw `api`, `application`, `infrastructure`, `models` serwisu ML.
- Nie tworzyć endpointów HTTP dla initu.
- Nie dodawać logiki initu do `main.py` serwisu ML.
- Nie instalować bibliotek z poziomu kodu initu.
- Nie hardcodować ścieżek produkcyjnych w kodzie.
- Nie nadpisywać kompletnego wpisu registry bez jawnego `ML_BOOTSTRAP_OVERWRITE_EXISTING=true`.
- Nie nadpisywać istniejącego `models/active/inference.json`.
- Nie usuwać modeli wytrenowanych przez `UC-06`.
- Nie zapisywać minimalnej deklaracji z `.env` jako `model.json`; manifest musi być pełny.
- Nie pozwalać `.env` nadpisywać technicznych pól architektury bez jawnego rozszerzenia kodu.
- Nie traktować braku `sourceRunName` jako błędu dla bootstrapu.
- Nie traktować braku aktywnego modelu jako błędu initu, jeśli żaden model nie ma capability inferencyjnej.
- Nie logować sekretów, pełnej zawartości `.env` ani ścieżek w sposób utrudniający publikację logów.

## 19. Inne istotne reguły
- `modelName` jest stabilnym identyfikatorem i musi być deterministyczny.
- Kolejność deklaracji w `ML_BOOTSTRAP_MODELS_JSON` nie może wpływać na zawartość pojedynczego manifestu, jedynie na kolejność raportu.
- Manifesty JSON powinny być formatowane stabilnie, żeby diff był czytelny.
- Wpis bootstrap musi pozostać lokalnym wpisem registry nawet wtedy, gdy pierwotnie powstał z `torchvision`.
- `canStartTraining = true` oznacza, że model może być bazą treningu, nie że jest gotowy do inferencji.
- `canUseForInference = true` wolno ustawić tylko dla modelu z wagami sensownymi dla klasyfikacji cyfr sudoku / baseline demo.
- Exit code:
  - `0` — wszystkie modele utworzone albo pominięte idempotentnie,
  - `1` — błąd konfiguracji, zależności albo registry,
  - opcjonalnie `2` — częściowy sukces, jeśli zespół zdecyduje dopuścić tryb kontynuacji po błędzie pojedynczego modelu.

## 20. Plan testów
- Unit:
  - parsowanie `.env`,
  - walidacja `ML_BOOTSTRAP_MODELS_JSON`,
  - slugowanie i kolizje nazw,
  - budowanie manifestów,
  - detekcja kompletnego / niekompletnego wpisu,
  - idempotencja writerów,
  - reguły aktywnego modelu.
- Integracyjne lokalne:
  - pusty registry -> tworzy wpisy,
  - drugie uruchomienie -> `skipped`,
  - niekompletny wpis bez overwrite -> błąd,
  - niekompletny wpis z overwrite -> odtworzenie,
  - istniejący `active/inference.json` -> bez zmian.
- Smoke workflow:
  - `pip install -r src/MachineLearning/requirements.txt`,
  - `cd src/MachineLearning && python -m init_bootstrap`,
  - walidacja obecności `model.json` i `artifacts/model.pt`.

## 21. Kryteria akceptacji
- Istnieje folder `src/MachineLearning/init_bootstrap` zawierający całość kodu initu.
- Init korzysta wyłącznie z głównego `.env` / `.env.{environment}` i `requirements.txt` warstwy ML.
- `python -m init_bootstrap` tworzy brakujące wpisy bootstrap w `models/registry`.
- Ponowne uruchomienie na kompletnym registry nie nadpisuje wpisów i kończy się sukcesem.
- Niekompletny wpis jest raportowany jako błąd, chyba że jawnie włączono overwrite.
- `models/active/inference.json` jest tworzony tylko wtedy, gdy go nie ma i wskazany model może być użyty do inferencji.
- Workflow produkcyjny potrafi uruchomić init na produkcyjnym `.env.production`.
- Lokalny `.env.local` zawiera jawne ścieżki lokalne i nie zależy od workflow.
- `UC-06` może później traktować bootstrap i model wytrenowany tak samo: przez `model.json` i `artifacts/model.pt`.
