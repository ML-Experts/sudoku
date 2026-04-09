# UC-04 ML — Plan implementacyjny (PUT /ml/preprocess/board)

## 1. Cel planu
- Dostarczyć endpoint `PUT /ml/preprocess/board` zgodnie z `@.ai/feature/ml/uc-04.md`.
- Przenieść logikę z `@src/MachineLearning/draft/Sudoku_preprocessing.ipynb` do clean architecture bez zmiany funkcjonalnej etapu 1 (board detection + perspective correction).
- Zachować stateless flow: wejście/wyjście tylko przez JSON (`ImageApiEntry` -> `ImageApiResponse`), bez trwałego zapisu wyniku preprocessingu.

## 2. Zakres i granice
- W zakresie:
  - dekodowanie wejściowego obrazu z `base64`,
  - preprocessing OpenCV: grayscale -> blur -> adaptive threshold -> largest contour -> perspective warp,
  - zwrot obrazu planszy po korekcji perspektywy jako `image/png` (lub MIME konfigurowalny),
  - obsługa błędów `422` z `ErrorApiResponse`.
- Poza zakresem:
  - podział na siatkę `9x9` (`PUT /ml/preprocess/cells`),
  - zapis artefaktów preprocessingu na dysk,
  - jakikolwiek odczyt obrazów z folderu datasetu,
  - adapter do pobierania/wczytywania obrazów z pliku w runtime UC-04.

## 3. Mapping notebook -> clean architecture
- `folder = "/v2_train"`: usuwamy z runtime; źródłem obrazu jest `ImageApiEntry` od BE.
- `file.endswith(".jpg") or ".jpeg"`: brak iteracji po plikach w runtime; walidujemy `mimeType` z listy dozwolonych MIME (konfigurowalnej).
- `print(f"Wczytano ...")`: zastępujemy logowaniem technicznym (`logger.debug/info`) z `requestId`.
- `plt.imshow(...)`: zastępujemy opcjonalnym debug pipeline (bez renderowania wykresów); brak twardego UI/debug w logice runtime.
- Kroki OpenCV zostają podobne algorytmicznie, ale są wydzielone do adaptera infrastruktury z parametrami.
- Plik `@src/MachineLearning/draft/Sudoku_preprocessing.ipynb` pozostaje bez zmian jako materiał referencyjny.

## 4. Kontrakt API (docelowy)
- Endpoint: `PUT /ml/preprocess/board`
- Request: `ImageApiEntry`
  - `mimeType: string`
  - `base64: string`
- Response success: `200 OK` + `ImageApiResponse`
  - `mimeType: string`
  - `base64: string`
- Response error: `422 Unprocessable Content` + `ErrorApiResponse`
  - `errorType`
  - `message`

## 5. Plan zmian w kodzie

### 5.1 API (`src/MachineLearning/api`)
- Dodać kontroler `api/controllers/preprocessing_controller.py`:
  - router `APIRouter(prefix="/ml", tags=["preprocessing"])`,
  - akcja `@put("/preprocess/board")`.
- Dodać modele HTTP:
  - `api/models/image_api_entry.py`,
  - `api/models/image_api_response.py`,
  - `api/models/error_api_response.py`.
- W `api/main.py` podpiąć nowy router obok istniejącego `runtime_status_controller`.
- Zmapować wyjątki use case do odpowiedzi `422 Unprocessable Content` z top-level `ErrorApiResponse` (`errorType`, `message`), np. przez `JSONResponse` albo dedykowany exception handler.
- Nie opierać kontraktu błędu na domyślnym `detail` z `HTTPException`.

### 5.2 Application (`src/MachineLearning/application`)
- Dodać feature-first use case:
  - `application/features/preprocessing/commands/preprocess_board/preprocess_board_command.py`,
  - `application/features/preprocessing/commands/preprocess_board/preprocess_board_command_handler.py`,
  - `application/features/preprocessing/commands/preprocess_board/preprocess_board_command_result_dto.py`.
- `PreprocessBoardCommand` przyjmuje wyłącznie dane runtime (`mime_type`, `base64_image`), bez ścieżek.
- `PreprocessBoardCommandHandler`:
  - waliduje wejście (MIME/base64),
  - korzysta z portów infrastruktury:
    - `ImageCodec` (techniczny encode/decode),
    - `GrayscaleBlurPreprocessor`,
    - `AdaptiveThresholdBinarizer`,
    - `LargestContourDetector`,
    - `PerspectiveTransformer`,
  - zwraca `PreprocessBoardCommandResultDto`.
- Dodać jawne porty (Protocol) w module handlera:
  - `ImageCodec`,
  - `GrayscaleBlurPreprocessor`,
  - `AdaptiveThresholdBinarizer`,
  - `LargestContourDetector`,
  - `PerspectiveTransformer`.

### 5.3 Models (`src/MachineLearning/models`)
- Dodać modele domenowe neutralne dla preprocessingu:
  - `models/preprocessing_image.py` (np. surowe bytes + `mime_type`),
  - `models/board_quad.py` (4 punkty planszy po sortowaniu).
- Modele domenowe nie znają FastAPI/Pydantic.

### 5.4 Infrastructure (`src/MachineLearning/infrastructure`)
- Nie dodajemy adaptera `file reader` / `dataset loader` dla UC-04 runtime.
- Jedynym źródłem obrazu wejściowego jest `ImageApiEntry` przekazane przez BE.
- Dodać **4 generyczne adaptery CV** (zgodnie z ustaleniem):
  - `infrastructure/vision/opencv_grayscale_blur_preprocessor.py`,
  - `infrastructure/vision/opencv_adaptive_threshold_binarizer.py`,
  - `infrastructure/vision/opencv_largest_contour_detector.py`,
  - `infrastructure/vision/opencv_perspective_transformer.py`.
- Dodatkowo adapter techniczny do serializacji obrazu:
  - `infrastructure/vision/opencv_image_codec.py`.
- Adaptery muszą przyjmować parametry (wstrzykiwane), zamiast hardcodu:
  - `grayscale_color_conversion_code`,
  - `gaussian_kernel_size`,
  - `gaussian_sigma_x`,
  - `adaptive_threshold_block_size`,
  - `adaptive_threshold_c`,
  - `contour_retrieval_mode`,
  - `contour_approximation_mode`,
  - `polygon_epsilon_factor`,
  - `output_board_size`.
- Adaptery nie znają endpointów ani DTO; realizują tylko operacje techniczne.

### 5.5 Dependencies / DI (`api/dependencies.py`)
- Dodać fabryki:
  - `get_preprocess_board_command_handler()`,
  - `get_preprocessing_settings()`.
- Wstrzykiwać implementacje infrastrukturalne wraz z parametrami ustawień.

## 6. Konfiguracja runtime (`.env*` + `RuntimeSettings`)
- Rozszerzyć `api/config/runtime_settings.py` o sekcję preprocessingu, np.:
  - `ml_preprocess_allowed_input_mime_types`,
  - `ml_preprocess_board_output_mime_type`,
  - `ml_preprocess_board_output_size`,
  - parametry OpenCV (blur/threshold/contour/epsilon).
- Rozszerzyć loader `api/config/environment.py`, aby wczytywał te pola z `.env` / `.env.{ML_ENVIRONMENT}`.
- Nie dodawać runtimeowych ścieżek danych dla tego use case (UC-04 działa na obrazie przekazanym przez BE).

## 7. Obsługa błędów i mapowanie `errorType`
- `invalid_image_payload` — niepoprawny `base64`/MIME.
- `board_not_found` — brak wiarygodnego konturu planszy.
- `perspective_correction_failed` — nie udało się wykonać transformacji.
- Każdy z powyższych mapowany na `422` + top-level `ErrorApiResponse` (`errorType`, `message`), bez opakowania w `detail`.

## 8. Testy
- Unit (`application`):
  - poprawny flow komendy dla mocków portów,
  - walidacja niedozwolonego MIME,
  - walidacja uszkodzonego base64.
- Unit (`infrastructure`):
  - wykrycie planszy na obrazach referencyjnych,
  - stabilność parametrów OpenCV przy minimalnych i nominalnych wartościach.
- Integracyjne (`api`):
  - `PUT /ml/preprocess/board` zwraca `200` i `ImageApiResponse`,
  - błędny payload zwraca `422` + top-level `ErrorApiResponse`.

## 9. Kryteria ukończenia (DoD)
- Endpoint działa zgodnie z kontraktem UC-04.
- Kod runtime nie używa notebookowego dostępu do folderu/datasetu.
- Kod runtime nie wczytuje obrazu z pliku i nie posiada adaptera file-loader dla UC-04.
- Infrastruktura jest parametryzowalna i możliwa do reuse w kolejnych historyjkach.
- Nazwy plików/klas/funkcji są angielskie i zgodne z konwencją projektu.
- `Sudoku_preprocessing.ipynb` pozostaje niezmieniony jako draft.
- Testy jednostkowe i integracyjne przechodzą lokalnie.

## 10. Kolejność wdrożenia
1. Modele API + DTO + command skeleton.
2. Adaptery infrastruktury (4 adaptery CV + `ImageCodec`) z parametrami.
3. Handler + DI + kontroler.
4. Mapowanie błędów i testy.
5. Kalibracja domyślnych parametrów w `.env.local`.
