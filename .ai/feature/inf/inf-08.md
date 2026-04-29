# INF-08 — Bootstrap rejestru modeli i standard manifestów

## Cel
- Opisać standard wpisu modelu w `models/registry/{modelName}` bez użycia bazy danych.
- Umożliwić jednorazowe lub powtarzalne utworzenie modeli bootstrap, które mogą być użyte jako model bazowy do treningu albo jako aktywny model inferencyjny.
- Ujednolicić sposób traktowania modeli bootstrap i modeli wytrenowanych w `UC-06`: dla `BE`, `ML`, inferencji i treningu oba typy są wpisami katalogowymi w `models/registry`.
- Zapewnić procedurę operacyjną, która może zostać uruchomiona ręcznie przez developera albo automatycznie przez workflow GitHub / post-deploy.

## Zakres
- Dotyczy katalogów:
  - `models/registry`,
  - `models/active`,
  - `src/MachineLearning/init_bootstrap`.
- Dotyczy modeli bootstrap:
  - własny mały `CNN` jako baseline,
  - `ResNet18` jako wariant transfer learning oparty o `torchvision`.
- Dotyczy standardu `model.json`, minimalnego layoutu `artifacts/` oraz reguł idempotentnego tworzenia brakujących wpisów.

## Poza zakresem
- Trening modeli na datasetach użytkownika — to realizuje `UC-06`.
- Przełączanie aktywnego modelu przez API — to realizuje `UC-10`.
- Dynamiczne instalowanie bibliotek przez init bootstrap.
- Pobieranie modeli z losowych repozytoriów GitHub.
- Scalanie wielu modeli albo utrzymywanie delty wag względem bootstrapu.

## Decyzje architektoniczne
- Każdy model używany przez system musi być reprezentowany jako wpis katalogowy `models/registry/{modelName}`.
- Model pochodzący z biblioteki, np. `torchvision.models.resnet18`, przed użyciem w `UC-06` musi zostać zmaterializowany jako lokalny wpis bootstrap w `models/registry`.
- `init_bootstrap` nie instaluje bibliotek. Biblioteki są instalowane przez:
  - ręczne `pip install -r src/MachineLearning/requirements.txt`,
  - albo workflow GitHub / skrypt deployu.
- Główne `requirements.txt` warstwy ML zawiera biblioteki potrzebne do obsługi modeli bootstrap, np. `torch` i `torchvision`.
- Główne `.env` / `.env.{environment}` warstwy ML zawiera konfigurację runtime i listę bootstrap modeli do utworzenia.
- `.env` nie powtarza listy bibliotek z `requirements.txt`; deklaruje, które modele mają istnieć w rejestrze.
- Init bootstrap jest idempotentny: ponowne uruchomienie nie nadpisuje kompletnego wpisu modelu, chyba że jawnie włączono tryb overwrite.
- `UC-06` i inferencja nie rozróżniają technicznie modelu bootstrap i modelu wytrenowanego. Oba typy ładuje ten sam mechanizm na podstawie `model.json` i artefaktów.

## Proponowana lokalizacja
```text
src/MachineLearning/
├── api/
├── application/
├── infrastructure/
├── models/
├── init_bootstrap/
│   ├── __init__.py
│   ├── __main__.py
│   ├── bootstrap_models.py
│   ├── model_builders.py
│   ├── model_manifest_builder.py
│   └── model_registry_writer.py
└── requirements.txt
```

`init_bootstrap` jest osobnym narzędziem administracyjnym w repozytorium, ale korzysta z tego samego środowiska `.venv`, tego samego `requirements.txt` i tej samej konfiguracji `.env` co warstwa ML.

## Konfiguracja `.env`
Przykładowe wartości:

```dotenv
ML_MODELS_REGISTRY_DIRECTORY_PATH=/home/wojtek/projects/sudoku/data/models/registry
ML_ACTIVE_MODEL_DIRECTORY_PATH=/home/wojtek/projects/sudoku/data/models/active
ML_BOOTSTRAP_MODELS_JSON=[{"family":"cnn","type":"custom-cnn-v1","displayName":"CNN baseline"},{"family":"resnet","type":"resnet18","displayName":"ResNet18 ImageNet bootstrap"}]
ML_BOOTSTRAP_OVERWRITE_EXISTING=false
ML_BOOTSTRAP_SET_ACTIVE_IF_MISSING=true
ML_BOOTSTRAP_DEFAULT_ACTIVE_MODEL=cnn-baseline
```

Znaczenie:
- `ML_MODELS_REGISTRY_DIRECTORY_PATH` — absolutna ścieżka do `models/registry`.
- `ML_ACTIVE_MODEL_DIRECTORY_PATH` — absolutna ścieżka do `models/active`.
- `ML_BOOTSTRAP_MODELS_JSON` — minimalna deklaracja bootstrap modeli; init rozwija ją do pełnego `model.json` na podstawie szablonów dla `family` + `type`.
- `ML_BOOTSTRAP_OVERWRITE_EXISTING` — jeśli `false`, kompletny istniejący wpis jest pomijany.
- `ML_BOOTSTRAP_SET_ACTIVE_IF_MISSING` — jeśli `true`, init może utworzyć wskaźnik aktywnego modelu, gdy go nie ma.
- `ML_BOOTSTRAP_DEFAULT_ACTIVE_MODEL` — model ustawiany jako aktywny tylko wtedy, gdy brak istniejącego wskaźnika.

Minimalna deklaracja modelu bootstrap w `.env` zawiera:
- `family` — rodzina modelu, np. `cnn` albo `resnet`.
- `type` — konkretny typ architektury, np. `custom-cnn-v1` albo `resnet18`.
- `displayName` — opcjonalna nazwa czytelna dla UI i raportów.
- `name` — opcjonalny identyfikator wpisu rejestru; jeśli nie zostanie podany, init generuje go deterministycznie.

Reguła generowania `name`:
- jeśli deklaracja zawiera `name`, init używa tej wartości po walidacji formatu,
- jeśli `name` nie istnieje, ale istnieje `displayName`, init generuje slug z `displayName`,
- jeśli nie istnieje ani `name`, ani `displayName`, init generuje slug z połączenia `family` i `type`, np. `resnet-resnet18`,
- slug jest tworzony przez zamianę tekstu na lowercase, usunięcie znaków spoza `[a-z0-9-]`, zamianę ciągów spacji / separatorów na pojedynczy `-` oraz obcięcie separatorów z początku i końca,
- jeśli wygenerowany `name` koliduje z inną deklaracją w tym samym `ML_BOOTSTRAP_MODELS_JSON`, init kończy się błędem konfiguracji,
- jeśli wygenerowany `name` koliduje z istniejącym wpisem w `models/registry` i wpis jest kompletny, init stosuje standardową idempotencję; jeśli wpis jest niekompletny, init kończy się błędem albo wymaga trybu overwrite.

Przykład deklaracji pojedynczego modelu:

```json
{
  "family": "resnet",
  "type": "resnet18",
  "displayName": "ResNet18 ImageNet bootstrap"
}
```

Powyższa deklaracja bez jawnego `name` wygeneruje `name = "resnet18-imagenet-bootstrap"`.

Takie podejście oznacza, że operator nie wypełnia ręcznie wszystkich pól manifestu. Utrzymuje tylko listę modeli do zapewnienia, a `init_bootstrap` odpowiada za uzupełnienie pól technicznych.

## Zależności
Zależności modeli bootstrap trzymamy w głównym:

```text
src/MachineLearning/requirements.txt
```

Przykładowo:

```text
torch
torchvision
numpy
```

`init_bootstrap` zakłada, że zależności są już zainstalowane. Jeśli `.env` wymaga modelu `resnet18-imagenet-bootstrap`, a `torchvision` nie jest dostępne, init kończy się czytelnym błędem i nie próbuje wykonywać `pip install`.

## Layout rejestru modeli
Każdy wpis:

```text
models/registry/{modelName}/
├── model.json
└── artifacts/
    └── model.pt
```

Minimalny wymóg:
- katalog modelu istnieje,
- `model.json` istnieje i jest poprawnym JSON,
- `artifacts/` istnieje,
- główny artefakt wskazany w `model.json` istnieje.

Modele bootstrap nie mają własnego katalogu `trainings/*` i nie mają `sourceRunName`.

## Semantyka pól `model.json`
Manifest jest kontraktem dla `BE`, `ML`, loadera modelu, fabryki architektur oraz UI. Program nie powinien zgadywać typu modelu na podstawie nazwy katalogu ani nazwy pliku artefaktu; decyzje techniczne muszą wynikać z jawnych pól manifestu.

Pola główne:
- `name` — logiczny identyfikator wpisu rejestru; powinien odpowiadać nazwie katalogu `models/registry/{modelName}`.
- `displayName` — nazwa czytelna dla UI i raportów.
- `sourceType` — pochodzenie wpisu; w `MVP` dopuszczamy `bootstrap` albo `trainingRun`.
- `sourceRunName` — nazwa runu treningowego, który wyprodukował model; dla `bootstrap` zawsze `null`.
- `framework` — framework runtime modelu, np. `pytorch`; loader używa go do wyboru mechanizmu ładowania artefaktu.

Pola `architecture`:
- `architecture.type` — główny klucz techniczny dla `ModelFactory`; określa konkretną architekturę do zbudowania, np. `custom-cnn-v1` albo `resnet18`.
- `architecture.family` — rodzina modelu używana do filtrowania, raportowania i polityk treningowych, np. `cnn` albo `resnet`.
- `architecture.variant` — wariant w obrębie rodziny, np. `digit-cnn-small` albo `resnet18`; jest stabilnym opisem wariantu, ale nie zastępuje `architecture.type` w fabryce.
- `architecture.library` — opcjonalne źródło implementacji architektury, np. `torchvision`; dla własnego `CNN` może być pominięte.
- `architecture.pretrainedSource` — opcjonalna informacja o pierwotnych wagach bootstrap, np. `ResNet18_Weights.DEFAULT`; po imporcie do registry model jest jednak ładowany z lokalnego artefaktu, nie z internetu.
- `architecture.numClasses` — liczba klas wyjściowych modelu; dla sudoku typowo `10`, jeśli klasy obejmują `empty` albo `0`, oraz cyfry `1-9`.
- `architecture.inputChannels` — liczba kanałów wejściowych oczekiwana przez model, np. `1` dla grayscale CNN albo `3` dla RGB ResNet.
- `architecture.inputHeight` i `architecture.inputWidth` — rozmiar wejścia oczekiwany przez model po preprocessingu.
- `architecture.inputProfile` — nazwa profilu transformacji wejścia; `TransformFactory` używa jej do wyboru resize, grayscale/RGB, normalizacji i konwersji tensora.

Pola `artifacts`:
- `artifacts.primaryArtifactRelativePath` — ścieżka do głównego artefaktu względem katalogu wpisu `models/registry/{modelName}`.
- `artifacts.format` — format artefaktu, np. `pytorch-state-dict`; loader używa go do wyboru sposobu odczytu.

Pola `capabilities`:
- `capabilities.canStartTraining` — czy model może być wybrany jako model bazowy w `UC-06`.
- `capabilities.canUseForInference` — czy model może zostać ustawiony jako aktywny model inferencyjny.

Pola `training`:
- `training.defaultTrainingProfileName` — sugerowany profil treningowy dla tego typu modelu.
- `training.defaultAugmentationProfileName` — sugerowany profil augmentacji danych.

Pola `metadata`:
- `metadata.createdBy` — komponent albo proces, który utworzył wpis, np. `init_bootstrap`.
- `metadata.description` — opis pomocniczy dla człowieka; nie powinien sterować logiką programu.

Minimalny kontrakt dla loadera to: `framework`, `architecture.type`, `architecture.inputProfile`, `artifacts.primaryArtifactRelativePath` i `artifacts.format`. Minimalny kontrakt dla listowania modeli przez `BE` to: `name`, `sourceType`, `sourceRunName`, `capabilities.canStartTraining` i `capabilities.canUseForInference`.

## Szablony manifestów
`init_bootstrap` utrzymuje wewnętrzne szablony manifestów dla wspieranych par `family` + `type`. Deklaracja z `.env` wybiera szablon, a init uzupełnia brakujące pola pełnego `model.json`.

Przykładowe mapowanie:

```text
family=cnn, type=custom-cnn-v1 -> template: custom_digit_cnn_v1
family=resnet, type=resnet18 -> template: torchvision_resnet18_imagenet
```

Szablon definiuje wartości domyślne:
- `name`,
- `framework`,
- `architecture.variant`,
- `architecture.library`,
- `architecture.pretrainedSource`,
- `architecture.numClasses`,
- `architecture.inputChannels`,
- `architecture.inputHeight`,
- `architecture.inputWidth`,
- `architecture.inputProfile`,
- `artifacts.primaryArtifactRelativePath`,
- `artifacts.format`,
- `capabilities`,
- `training`,
- `metadata.description`.

Deklaracja z `.env` może nadpisać tylko wybrane pola opisowe i operacyjne, np. `name`, `displayName`, `canStartTraining`, `canUseForInference`. Nie powinna nadpisywać pól technicznych takich jak `inputChannels`, `inputHeight`, `inputWidth`, `artifacts.format` ani `architecture.library`, chyba że zostanie to jawnie dodane jako obsługiwany przypadek w kodzie initu.

Jeśli `init_bootstrap` otrzyma parę `family` + `type`, dla której nie istnieje szablon, kończy się błędem konfiguracji. Nie tworzy wtedy częściowego wpisu w `models/registry`.

Efektem działania initu jest zawsze pełny `model.json`. Minimalna deklaracja z `.env` nie jest zapisywana jako manifest modelu; jest tylko wejściem do procesu generowania wpisu rejestru.

## Przykładowy `model.json` dla `CNN`
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
    "description": "Własny mały CNN utworzony jako lokalny bootstrap. Może wymagać treningu przed użyciem do inferencji."
  }
}
```

`canUseForInference` dla losowo zainicjalizowanego CNN powinno być `false`. Jeśli bootstrap CNN jest wcześniej wytrenowany np. na `MNIST` i ma sensowne metryki, może mieć `canUseForInference = true`.

## Przykładowy `model.json` dla `ResNet18`
```json
{
  "name": "resnet18-imagenet-bootstrap",
  "displayName": "ResNet18 ImageNet bootstrap",
  "sourceType": "bootstrap",
  "sourceRunName": null,
  "framework": "pytorch",
  "architecture": {
    "type": "resnet18",
    "family": "resnet",
    "variant": "resnet18",
    "library": "torchvision",
    "pretrainedSource": "ResNet18_Weights.DEFAULT",
    "numClasses": 10,
    "inputChannels": 3,
    "inputHeight": 224,
    "inputWidth": 224,
    "inputProfile": "digits-224x224-rgb-v1"
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
    "defaultTrainingProfileName": "resnet18-finetune-v1",
    "defaultAugmentationProfileName": "digits-light-v1"
  },
  "metadata": {
    "createdBy": "init_bootstrap",
    "description": "ResNet18 zainicjalizowany z oficjalnych wag torchvision i zapisany jako lokalny wpis registry."
  }
}
```

Dla `ResNet18` init powinien zapisać lokalny artefakt po dostosowaniu ostatniej warstwy klasyfikacyjnej do liczby klas projektu. Taki bootstrap może służyć jako punkt startowy fine-tuningu, ale bez treningu na danych sudoku nie powinien być traktowany jako produkcyjny model inferencyjny.

## Aktywny model inferencyjny
Aktywny model wskazuje lekki plik:

```text
models/active/inference.json
```

Przykład:

```json
{
  "modelName": "cnn-baseline",
  "registryRelativePath": "../registry/cnn-baseline",
  "setBy": "init_bootstrap"
}
```

Init może utworzyć ten plik tylko wtedy, gdy:
- `ML_BOOTSTRAP_SET_ACTIVE_IF_MISSING=true`,
- plik `inference.json` jeszcze nie istnieje,
- wskazany model istnieje i ma `canUseForInference = true`.

Jeśli żaden bootstrap nie nadaje się do inferencji, brak aktywnego modelu jest dopuszczalny jako stan techniczny bootstrapu i powinien być raportowany czytelnym błędem administracyjnym.

## Procedura init bootstrap
1. Załaduj konfigurację `.env` zgodnie z loaderem ML.
2. Odczytaj i sparsuj `ML_BOOTSTRAP_MODELS_JSON`.
3. Dla każdej deklaracji modelu:
   - odczytaj `family` i `type`,
   - znajdź szablon manifestu dla pary `family` + `type`,
   - zastosuj dozwolone nadpisania z deklaracji, np. `name` albo `displayName`,
   - sprawdź wymagane biblioteki,
   - sprawdź, czy `models/registry/{modelName}` istnieje,
   - jeśli wpis jest kompletny i overwrite jest wyłączony, pomiń,
   - jeśli wpis jest niekompletny, przerwij z czytelnym błędem albo odtwórz go tylko w trybie overwrite,
   - zbuduj architekturę,
   - zapisz `artifacts/model.pt`,
   - zapisz `model.json`.
4. Opcjonalnie ustaw aktywny model, jeśli nie ma `models/active/inference.json`.
5. Zwróć raport tekstowy: utworzone, pominięte, błędne wpisy.

## Uruchomienie ręczne
```bash
cd src/MachineLearning
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m init_bootstrap
```

Ręczne uruchomienie jest wymagane dla lokalnego developmentu i testowania procedury bez workflow GitHub.

## Uruchomienie w workflow / deployu
Rekomendowany etap workflow:

```text
1. Checkout repo.
2. Setup Python.
3. Utworzenie / aktywacja venv.
4. pip install -r src/MachineLearning/requirements.txt.
5. Przygotowanie `.env` / `.env.production` z absolutnymi ścieżkami runtime.
6. python -m init_bootstrap.
7. Weryfikacja, że wymagane wpisy istnieją w `models/registry`.
8. Deploy / restart usług.
```

W środowisku produkcyjnym init powinien działać na docelowym katalogu runtime `models/registry`, a nie na katalogu tymczasowym paczki buildowej, chyba że proces deployu jawnie synchronizuje te artefakty.

## Integracja z `UC-06`
- `BE` listuje modele przez skan `models/registry/*/model.json`.
- Model bootstrap może być wybrany do treningu, jeśli `capabilities.canStartTraining = true`.
- `sourceRunName = null` dla bootstrapu jest poprawne.
- `ML` dostaje od `BE`:
  - `baseModel.directoryPath`,
  - `baseModel.manifestPath`,
  - `baseModel.primaryArtifactPath`,
  - `baseModel.sourceType = bootstrap`.
- `ML` ładuje bootstrap tak samo jak model wytrenowany: przez manifest i artefakt.
- Po zakończonym treningu `ML` zapisuje finalne artefakty do `models/registry/{producedModelName}/artifacts`, a `BE` finalizuje `model.json`.

## Loader i fabryka modeli
Różnice między `CNN` i `ResNet18` powinny być ukryte w jednym miejscu:
- `ModelFactory` tworzy architekturę na podstawie `architecture.type`.
- `ModelLoader` ładuje `state_dict` z artefaktu.
- `TransformFactory` dobiera preprocessing na podstawie `inputProfile`.

Wspólny kod treningu i inferencji powinien operować na `torch.nn.Module`, a nie na osobnych klasach treningowych dla `CNN` i `ResNet18`.

Przykładowa logika:

```text
model.json -> ModelFactory -> torch.nn.Module
model.json + artifacts/model.pt -> ModelLoader -> LoadedModel
inputProfile -> TransformFactory -> preprocessing
LoadedModel + batch -> Trainer / InferenceService
```

## Idempotencja i błędy
- Istniejący kompletny wpis jest pomijany.
- Brakujący wpis jest tworzony.
- Niekompletny wpis bez overwrite powoduje błąd, żeby nie ukryć uszkodzonego rejestru.
- Brak biblioteki wymaganej przez model powoduje błąd z instrukcją instalacji `pip install -r src/MachineLearning/requirements.txt`.
- Brak internetu przy pierwszym pobraniu wag `torchvision` powoduje błąd initu; kolejne uruchomienia mogą korzystać z cache albo z już zapisanego lokalnego artefaktu.
- Init nie usuwa modeli wytrenowanych w `UC-06`.
- Init nie nadpisuje aktywnego modelu, jeśli `models/active/inference.json` już istnieje.

## Kryteria akceptacji
- Istnieje dokumentowany layout `models/registry/{modelName}` z `model.json` i `artifacts/`.
- Istnieje dokumentowana procedura utworzenia bootstrap modeli bez `sourceRunName`.
- Bootstrap modeli działa na podstawie głównego `requirements.txt` i `.env` warstwy ML.
- Init można uruchomić ręcznie i z workflow.
- Init jest idempotentny i nie instaluje bibliotek.
- Model z `torchvision` po imporcie jest lokalnym wpisem rejestru i nie wymaga specjalnego traktowania przez `UC-06`.
- `BE`, `ML` i proces operacyjny mają rozdzielone odpowiedzialności:
  - proces operacyjny / deploy tworzy bootstrap wpisy,
  - `ML` zapisuje techniczne artefakty modeli wynikowych,
  - `BE` finalizuje biznesowy `model.json` dla modeli wytrenowanych przez system i pozostaje źródłem prawdy workflow.
