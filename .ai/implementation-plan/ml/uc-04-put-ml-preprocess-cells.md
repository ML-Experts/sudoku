# UC-04 ML — Plan implementacyjny (PUT /ml/preprocess/cells)

## 1. Cel planu
- Dostarczyć endpoint `PUT /ml/preprocess/cells` zgodnie z `@.ai/feature/ml/uc-04.md`.
- Zrealizować etap 2 preprocessingu: podział obrazu planszy (po warp) na `9x9` i zwrot `CellsGridApiResponse`.
- Zachować clean architecture: use case w `application`, operacje CV w generycznym `infrastructure`, brak trwałego zapisu wyników.

## 2. Zakres i granice
- W zakresie:
  - przyjęcie obrazu planszy (`ImageApiEntry`) od BE,
  - podział obrazu na regularną siatkę `9x9`,
  - opcjonalny crop marginesów komórek (parametryzowany),
  - zwrot `cells: ImageApiResponse[9][9]`.
- Poza zakresem:
  - ponowne wykrywanie planszy (to etap `preprocess/board`),
  - klasyfikacja cyfr i inferencja modelu,
  - zapis komórek na dysku,
  - adapter do wczytywania obrazu planszy z pliku/datasetu w runtime UC-04.

## 3. Zasady wejścia i spójność z UC-04
- Endpoint zakłada, że wejściem jest obraz planszy po korekcji perspektywy.
- Brak zależności od ścieżek plików, datasetów i rozszerzeń typu `.jpeg` po stronie runtime.
- Jedynym źródłem wejścia jest payload `ImageApiEntry` od BE (brak file-loadera).
- Walidacja wejścia oparta o `mimeType` i `base64`, zgodnie z kontraktem API.
- JSON zwracany w `camelCase`.

## 4. Kontrakt API (docelowy)
- Endpoint: `PUT /ml/preprocess/cells`
- Request: `ImageApiEntry`
- Response success: `200 OK` + `CellsGridApiResponse`
  - `cells: ImageApiResponse[9][9]`
- Response error: `422 Unprocessable Content` + `ErrorApiResponse`
  - `errorType`
  - `message`

## 5. Plan zmian w kodzie

### 5.1 API (`src/MachineLearning/api`)
- Rozszerzyć `api/controllers/preprocessing_controller.py` o akcję:
  - `@put("/preprocess/cells")`.
- Dodać model odpowiedzi:
  - `api/models/cells_grid_api_response.py`.
- Reuse istniejących modeli:
  - `ImageApiEntry`,
  - `ImageApiResponse`,
  - `ErrorApiResponse`.
- Dodać mapowanie wyników DTO -> `CellsGridApiResponse`.
- Zmapować wyjątki use case do odpowiedzi `422 Unprocessable Content` z top-level `ErrorApiResponse` (`errorType`, `message`), np. przez `JSONResponse` albo dedykowany exception handler.
- Nie opierać kontraktu błędu na domyślnym `detail` z `HTTPException`.

### 5.2 Application (`src/MachineLearning/application`)
- Dodać use case:
  - `application/features/preprocessing/commands/extract_cells/extract_cells_command.py`,
  - `application/features/preprocessing/commands/extract_cells/extract_cells_command_handler.py`,
  - `application/features/preprocessing/commands/extract_cells/extract_cells_command_result_dto.py`.
- `ExtractCellsCommand` przyjmuje runtime payload obrazu planszy.
- `ExtractCellsCommandHandler`:
  - dekoduje obraz przez port `ImageCodec`,
  - wywołuje port `BoardCellsExtractor`,
  - encoduje każdą komórkę do `ImageApiResponse`,
  - waliduje wymiar wyjściowy `9x9`.

### 5.3 Models (`src/MachineLearning/models`)
- Dodać modele domenowe:
  - `models/cells_grid.py` (silnie typowana macierz komórek),
  - ewentualnie `models/image_matrix.py` dla wielokrotnego use-case reuse.
- Model domenowy przechowuje dane neutralnie (np. `np.ndarray`/bytes) bez API-owych DTO.

### 5.4 Infrastructure (`src/MachineLearning/infrastructure`)
- Dodać generyczny adapter (to jest **5. adapter CV** po 4 adapterach z `preprocess/board`):
  - `infrastructure/vision/opencv_board_cells_extractor.py`.
- Nie dodajemy adaptera `file reader` w tym use case.
- Adapter przyjmuje parametry:
  - `grid_rows` (domyślnie `9`),
  - `grid_cols` (domyślnie `9`),
  - `cell_inner_margin_ratio`,
  - `minimum_cell_size_px`,
  - `output_cell_size_px` (opcjonalny resize).
- Algorytm bazowy:
  1. wyznaczenie wymiarów planszy,
  2. podział geometryczny na komórki,
  3. opcjonalne przycięcie marginesu komórki,
  4. standaryzacja rozmiaru komórek (jeśli skonfigurowane),
  5. zwrot macierzy `rows x cols`.
- Adapter ma pozostać generyczny (brak twardego założenia "Sudoku" w nazwach klas/metod poza domyślnymi parametrami).

### 5.5 Dependencies / DI (`api/dependencies.py`)
- Dodać fabrykę:
  - `get_extract_cells_command_handler()`.
- Reuse `get_preprocessing_settings()` z planu `preprocess/board`.
- Wstrzykiwać te same komponenty `ImageCodec`, aby uniknąć duplikacji logiki kodowania/dekodowania.

## 6. Konfiguracja runtime (`.env*` + `RuntimeSettings`)
- Dodać ustawienia dla etapu cells:
  - `ML_PREPROCESS_CELLS_GRID_ROWS=9`,
  - `ML_PREPROCESS_CELLS_GRID_COLS=9`,
  - `ML_PREPROCESS_CELLS_INNER_MARGIN_RATIO`,
  - `ML_PREPROCESS_CELLS_OUTPUT_CELL_SIZE`.
- Trzymać wartości jako konfigurowalne, aby reuse był możliwy dla innych historyjek i wariantów preprocessingu.
- Nie dodawać żadnych hardcodowanych folderów wejściowych.

## 7. Obsługa błędów i mapowanie `errorType`
- `invalid_image_payload` — niepoprawne dane wejściowe.
- `invalid_board_image_shape` — obraz zbyt mały/nieprawidłowy do podziału.
- `cells_extraction_failed` — brak możliwości zbudowania poprawnej siatki `9x9`.
- Wszystkie mapowane na `422` + top-level `ErrorApiResponse` (`errorType`, `message`), bez opakowania w `detail`.

## 8. Testy
- Unit (`application`):
  - poprawny mapping wyniku `BoardCellsExtractor` do DTO `cells`,
  - walidacja rozmiaru siatki innego niż `9x9` -> błąd domenowy.
- Unit (`infrastructure`):
  - deterministyczny podział planszy na `9x9`,
  - test dla różnych `inner_margin_ratio`.
- Integracyjne (`api`):
  - `PUT /ml/preprocess/cells` zwraca `200` i macierz `9x9`,
  - błędny payload zwraca `422` + top-level `ErrorApiResponse` z poprawnym `errorType`.

## 9. Kryteria ukończenia (DoD)
- Endpoint działa zgodnie z kontraktem UC-04.
- Odpowiedź zawiera pełną macierz `cells[9][9]` w `ImageApiResponse`.
- Infrastructure jest parametryzowalne i generyczne (bez twardych stałych poza domyślną konfiguracją).
- Application zawiera funkcjonalność specyficzną dla UC-04 (walidacja i orkiestracja use case).
- Brak zapisu wyników preprocessingu na dysk.
- Brak wczytywania wejściowego obrazu z pliku/datasetu w runtime UC-04.
- Testy jednostkowe/integracyjne przechodzą.

## 10. Kolejność wdrożenia
1. Dodać modele API i DTO dla `cells`.
2. Dodać `BoardCellsExtractor` i parametry runtime.
3. Zaimplementować handler + DI + endpoint.
4. Ujednolicić mapowanie błędów `422`.
5. Pokryć testami i zweryfikować kompatybilność z BE.
