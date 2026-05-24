# EXP — Testowa inferencja pojedynczej cyfry z obrazka

## Status
- Typ: eksperyment / narzędzie developerskie.
- Obszar: `src/MachineLearning`.
- Nie jest częścią docelowego publicznego produktu ani pełnego `UC-05`.
- Cel dokumentu: utrzymać ślad zmian, decyzji i problemów wykrytych podczas testowania inferencji modelu po `UC-06`, tak aby później dało się zdecydować, czy zostawić, przepisać, czy usunąć eksperyment.

## Cel eksperymentu
Po wdrożeniu treningu i rejestru modeli chcieliśmy szybko sprawdzić, czy model wskazany jako aktywny potrafi wykonać inferencję na pojedynczym obrazku cyfry.

Eksperyment miał umożliwić ręczny test bez budowania pełnej ścieżki rozwiązywania sudoku:
- pobranie obrazka z domyślnego katalogu przykładów,
- przetworzenie go tym samym pipeline'em przygotowania komórki/cyfry do `28x28`,
- załadowanie aktywnego modelu z registry,
- zwrot rozpoznanej cyfry jako `int`.

## Dodany endpoint
Dodany został testowy endpoint ML:

```http
GET /ml/test/inteference/{name}
```

Uwaga: ścieżka zawiera literówkę `inteference`, bo tak została podana w eksperymencie. Jeśli endpoint zostanie zachowany, warto rozważyć zmianę na `inference` albo utrzymać alias dla kompatybilności lokalnych testów.

Odpowiedź sukcesu:

```json
{
  "digit": 7
}
```

## Zachowanie endpointu
Endpoint:
1. Odczytuje obrazek `{name}` z katalogu `ML_EXAMPLES_UPLOADS_DIR`.
2. Jeśli `{name}` nie ma rozszerzenia, próbuje kolejno `.png`, `.jpg`, `.jpeg`.
3. Przepuszcza obraz przez `CellPreprocessingPipeline`.
4. Odczytuje aktywny model z `ML_MODELS_ACTIVE_DIR/inference.json`.
5. Na podstawie `modelName` ładuje `ML_MODELS_REGISTRY_DIR/{modelName}/model.json`.
6. Buduje model przez `ModelFactory`.
7. Ładuje artefakt `artifacts/model.pt` przez `ModelArtifactLoader`.
8. Dobiera transformację wejścia przez `InputTransformFactory`.
9. Wykonuje inferencję i zwraca `argmax` jako `digit`.

## Dodane i zmienione pliki
### API
- `src/MachineLearning/api/controllers/test_inference_controller.py`
- `src/MachineLearning/api/models/test_digit_inference_api_response.py`
- `src/MachineLearning/api/main.py`
- `src/MachineLearning/api/dependencies.py`

### Application
- `src/MachineLearning/application/features/inference/commands/test_digit_inference/test_digit_inference_command.py`
- `src/MachineLearning/application/features/inference/commands/test_digit_inference/test_digit_inference_command_handler.py`
- `src/MachineLearning/application/features/inference/dto/active_model_reference_dto.py`
- `src/MachineLearning/application/features/inference/dto/test_digit_inference_result_dto.py`
- `src/MachineLearning/application/features/inference/errors/test_digit_inference_errors.py`

### Infrastructure
- `src/MachineLearning/infrastructure/inference/active_model_resolver.py`
- `src/MachineLearning/infrastructure/inference/filesystem_test_image_repository.py`

### Konfiguracja
- `src/MachineLearning/api/config/runtime_settings.py`
- `src/MachineLearning/api/config/environment.py`
- `src/MachineLearning/api/.env`
- `src/MachineLearning/api/.env.local`

Dodane ustawienia:

```env
ML_EXAMPLES_UPLOADS_DIR=/home/wojtek/projects/sudoku/data/examples/uploads
ML_MODELS_ACTIVE_DIR=/home/wojtek/projects/sudoku/data/models/active
ML_MODELS_REGISTRY_DIR=/home/wojtek/projects/sudoku/data/models/registry
```

W `.env.local` zmieniono też runner treningowy:

```env
ML_TRAINING_RUNNER=pytorch
```

Ta zmiana była potrzebna, bo `mock` tworzył artefakty użyteczne do testów workflow, ale nie do realnej jakości inferencji.

### Testy
- `src/MachineLearning/tests/integration/test_test_inference_controller.py`

Test buduje tymczasowy katalog examples, active model i registry, a następnie sprawdza odpowiedź endpointu.

## Wymagany layout plików runtime
Aktywny model:

```text
data/models/active/inference.json
```

Minimalny przykład:

```json
{
  "modelName": "train-20260429-205435-cnn-baseline-uc12-dataset-v2"
}
```

Wpis modelu:

```text
data/models/registry/{modelName}/model.json
data/models/registry/{modelName}/artifacts/model.pt
```

Przykładowy obrazek testowy:

```text
data/examples/uploads/cyfra7.png
```

Wywołanie:

```http
GET /ml/test/inteference/cyfra7
```

## Wymagania wobec `model.json`
Inferencja ML wymaga pełnego manifestu technicznego modelu, nie tylko skróconego manifestu listującego.

Wymagane pola:

```json
{
  "framework": "pytorch",
  "architecture": {
    "type": "custom-cnn-v1",
    "family": "cnn",
    "numClasses": 10,
    "inputChannels": 1,
    "inputHeight": 28,
    "inputWidth": 28,
    "inputProfile": "default-28x28-v1"
  },
  "artifacts": {
    "primaryArtifactRelativePath": "artifacts/model.pt",
    "format": "pytorch-state-dict"
  },
  "capabilities": {
    "canUseForInference": true
  }
}
```

## Odkryte problemy
### 1. BE finalizuje zbyt ubogi manifest modelu wynikowego
Po treningu BE tworzył `models/registry/{producedModelName}/model.json` w formie wystarczającej do listowania modeli, ale niewystarczającej do runtime inferencji ML.

Brakowało m.in.:
- `framework`,
- `architecture.type`,
- `architecture.family`,
- `architecture.numClasses`,
- `architecture.inputChannels`,
- `architecture.inputHeight`,
- `architecture.inputWidth`,
- `artifacts.format`.

Wniosek: BE powinien przy finalizacji modelu wynikowego przepisywać techniczne pola architektury i format artefaktu z manifestu modelu bazowego, jeśli trening działa jako `fineTuning` i architektura się nie zmienia.

### 2. Rozjazd definicji `custom-cnn-v1`
Bootstrap `cnn-baseline` i runtime `ModelFactory` miały różne definicje `custom-cnn-v1`.

Objaw:

```json
{
  "errorType": "base_model_artifact_invalid",
  "message": "Artefakt modelu bazowego nie pasuje do manifestu."
}
```

Przyczyna: `state_dict` zapisany przez bootstrap pasował do większej architektury CNN, a runtime budował mniejszą.

Zmiana wykonana w eksperymencie:
- `src/MachineLearning/infrastructure/training/model/custom_digit_cnn_v1.py` dostosowano do architektury bootstrapowej,
- `src/MachineLearning/init_bootstrap/custom_cnn.py` zaczął używać tej samej klasy `CustomDigitCnnV1`, zamiast definiować własną wewnętrzną klasę.

Wniosek: `architecture.type` powinien wybierać jedną wersjonowaną implementację kodową. Parametry takie jak `numClasses` i `inputChannels` powinny pochodzić z manifestu. Nie powinniśmy trzymać dwóch implementacji tej samej nazwy architektury.

### 3. ResNet nadal wymaga ujednolicenia
Bootstrap obsługuje więcej wariantów ResNet niż runtime `ModelFactory`.

Bootstrap ma specyfikacje m.in.:
- `resnet18`,
- `resnet34`,
- `resnet50`,
- `resnet101`,
- `resnet152`,
- `wide_resnet50_2`,
- `wide_resnet101_2`.

Runtime `ModelFactory` na moment eksperymentu obsługiwał tylko część wariantów.

Wniosek: należy rozważyć przeniesienie wspólnej mapy/specyfikacji architektur ResNet do neutralnego modułu runtime, z którego korzystają i bootstrap, i trening/inferencja.

### 4. Rozjazd ścieżek tymczasowych datasetu
Po zmianach konfiguracji ML zapisywał przygotowane `.npz` do:

```text
/home/wojtek/projects/sudoku/data/tmp/datasets
```

BE szukał tymczasowego artefaktu w:

```text
/home/wojtek/projects/sudoku/tmp/datasets
```

Objaw:
- ML zwracał `200 OK` z `/ml/datasets/prepare`,
- BE kończył `POST /api/datasets/processed` błędem `503`,
- w logach BE pojawiał się `FileStorageItemNotFoundException`.

Wniosek: `ML_TEMP_DATASETS_DIRECTORY_PATH` i `DatasetsPreparation:TemporaryArtifactsDirectoryPath` muszą wskazywać ten sam katalog. W lokalnym środowisku zalecane jest:

```env
ML_TEMP_DATASETS_DIRECTORY_PATH=/home/wojtek/projects/sudoku/tmp/datasets
```

## Decyzje techniczne z eksperymentu
### Parametryzacja modeli
Manifest `model.json` powinien parametryzować model na poziomie:
- `architecture.type`,
- `architecture.family`,
- `numClasses`,
- `inputChannels`,
- `inputHeight`,
- `inputWidth`,
- `inputProfile`,
- `artifacts.format`.

Nie wprowadzamy pełnego opisu warstw sieci w JSON. Układ warstw pozostaje wersjonowanym kodem dla `architecture.type`, np. `custom-cnn-v1`. Jeśli układ warstw się zmienia, powinna powstać nowa wersja typu, np. `custom-cnn-v2`.

### Zakres odpowiedzialności
- `Backend` pozostaje `source of truth` dla aktywnego modelu i finalizacji manifestów.
- `ML` ładuje techniczny manifest i artefakt, ale nie powinien samodzielnie decydować, który model jest aktywny poza odczytem `inference.json`.
- Endpoint eksperymentalny omija BE i jest narzędziem developerskim, więc nie powinien być traktowany jako docelowy kontrakt dla FE.

## Ryzyka
- Endpoint może zostać przypadkowo potraktowany jako docelowe API produktu.
- Ścieżka `inteference` zawiera literówkę.
- Ręczne poprawianie `model.json` dla modeli wynikowych jest podatne na błędy i powinno zostać zastąpione poprawką BE.
- `ML_TRAINING_RUNNER=pytorch` może wydłużyć lokalne flow i wymaga działających zależności PyTorch.
- Wyniki inferencji na pojedynczych obrazkach nie potwierdzają jakości pełnego pipeline'u Sudoku.

## Rekomendowane następne kroki
1. Poprawić BE finalizację `model.json` tak, aby model wynikowy dziedziczył pełny techniczny manifest modelu bazowego.
2. Ujednolicić obsługę ResNet między bootstrapem i runtime `ModelFactory`.
3. Dopisać test kontraktowy dla manifestu modelu wynikowego po `completed`.
4. Dopisać test konfiguracji lokalnej sprawdzający zgodność katalogu tymczasowego datasetów BE i ML.
5. Zdecydować, czy endpoint testowy zostaje jako narzędzie developerskie, czy po stabilizacji `UC-05` zostaje usunięty.

## Kryteria pozostawienia eksperymentu
Eksperyment można zostawić, jeśli:
- endpoint jest wyraźnie oznaczony jako developerski,
- nie jest wystawiany jako publiczne API FE,
- ma prostą dokumentację uruchomienia,
- pomaga szybko diagnozować aktywny model po treningu.

## Kryteria usunięcia eksperymentu
Eksperyment można usunąć, jeśli:
- powstanie pełny `POST /ml/solve-from-image`,
- BE będzie miało własny test/diagnostykę aktywnego modelu,
- test pojedynczej cyfry przestanie dawać wartość diagnostyczną,
- utrzymywanie osobnego endpointu zacznie generować koszt lub mylić kontrakty.

## Stan weryfikacji
- Składnia zmienionych plików Python była sprawdzana przez `py_compile`.
- Diagnostyka edytora nie wskazywała błędów lintera dla zmienionych plików.
- Pełny test integracyjny wymaga środowiska Python z zależnościami `opencv-python-headless`, `torch`, `torchvision`.

