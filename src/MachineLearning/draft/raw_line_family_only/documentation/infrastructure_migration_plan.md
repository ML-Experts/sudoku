# Plan migracji do `Infrastructure`

## Cel

Ten dokument opisuje, jak przenieść aktywny eksperyment vision do warstwy
`Infrastructure` tak, aby:

- `Application` nie musiało zmieniać swoich portów,
- publiczne kontrakty `UC-04` pozostały zgodne z obecnym `BE`,
- `UC-06` i przygotowanie datasetów dostały pełny zestaw artefaktów potrzebnych
  do treningu i diagnostyki,
- nie zgubić semantyki aktualnego lifecycle'u `LogicalLine`.

Jeśli dokumentacja i kod są niespójne, źródłem prawdy pozostaje kod.

## Stan wejściowy

Na dziś istnieją trzy istotne warstwy:

1. aktywny eksperyment planszy i linii:
   - `detection.py`
   - `logical_line_core.py`
   - `logical_lines.py`
   - `logical_line_frame_warp.py`
   - `logical_line_frame_cells.py`
   - `preprocessing_api.py`
2. obecne porty i handlery `Application`, które mają pozostać stabilne:
   - preprocessing planszy,
   - ekstrakcja komórek,
   - inferencja pojedynczej komórki,
   - przygotowanie datasetów.
3. warstwa `Infrastructure`, która ma dostarczyć implementacje pod istniejące
   porty zamiast zmuszać `Application` do zmiany kontraktów.

## Najważniejsze decyzje migracyjne

### 1. `preprocess/board` idzie pełnym pipeline'em

Ścieżka `PUT /ml/preprocess/board` ma startować od surowego zdjęcia i przechodzić:

1. preprocessing obrazu,
2. detekcję rodzin,
3. budowę `LogicalLine`,
4. grouping `RAW`,
5. `full containment prune`,
6. `vertex containment merge`,
7. `pixel connection`,
8. intersections,
9. trim,
10. kandydatów ramek,
11. wybór zwycięzcy,
12. `warp`.

To jest ścieżka ekstrakcji planszy, a nie tylko helper do cięcia komórek.

### 2. `preprocess/cells` pracuje na planszy już po `warp`

Ścieżka `PUT /ml/preprocess/cells` ma przyjmować obraz planszy już po korekcji
perspektywy.

Nie powinna:

- wykrywać families,
- liczyć `LogicalLine`,
- szukać ramki,
- wykonywać `warp`.

Jej rola to:

- podział planszy na 9x9,
- zbudowanie wewnętrznych artefaktów komórek,
- zwrot publicznego `CellsGridApiResponse`.

### 3. Publiczne API `UC-04` nie zwraca komórek `ml_ready`

Publiczny `CellsGridApiResponse` dla `UC-04` powinien zwracać komórki widokowe
9x9, czyli materiał do dalszej pracy użytkownika i `BE`.

Nie powinien zwracać:

- odwróconych kolorów,
- wycentrowanego binarnego `28x28`,
- technicznego widoku przygotowanego stricte pod model.

Artefakty `ml_ready` pozostają potrzebne wewnętrznie dla:

- inferencji komórki,
- przygotowania datasetów,
- preview jakości danych,
- pełnego wejścia do `UC-06`.

### 4. Pełne wejście do `UC-06` obejmuje więcej niż samo `CellsGridApiResponse`

Dla `UC-06` i dataset preparation potrzebujemy pełnego kontraktu wewnętrznego:

- `warped_board_image`,
- `raw_cells` 9x9,
- `raw_preview_image`,
- `ml_ready_cells_uint8`,
- `ml_ready_cells_float32`,
- `ml_ready_preview_image`.

To jest pełne wejście, a nie minimalny wariant.

## Ważne doprecyzowanie o rozdzielczości

Aktualny eksperymentalny `preprocess_board_image(...)`:

- skaluje `source_bgr` przez `resize_for_display(...)`,
- wykrywa families i wybiera ramkę na `display_bgr`,
- wykonuje `warp` również na `display_bgr`.

To nie oznacza, że wcześniejsza ścieżka zawsze tak działała.

Wcześniejsza ścieżka `Infrastructure` wykonywała transformację perspektywy na
obrazie źródłowym przekazanym do handlera.

Dlatego migracja powinna jawnie zdecydować jedną z dwóch opcji:

1. akceptujemy eksperymentalny wariant i świadomie warpujemy z `display_bgr`,
2. przywracamy warp z pełnej rozdzielczości:
   - albo przez detekcję na obrazie źródłowym,
   - albo przez przeskalowanie punktów / rogów zwycięskiej ramki z przestrzeni
     `display_bgr` z powrotem do `source_bgr`.

Docelowo bezpieczniejsza jest opcja 2, bo lepiej zachowuje szczegóły planszy
przed cięciem na komórki.

## Docelowy podział odpowiedzialności

### A. Warstwa eksperymentalna

Pozostaje źródłem algorytmu i artefaktów:

- detekcja families,
- lifecycle `LogicalLine`,
- frame candidates,
- warp,
- dzielenie na komórki,
- budowa wariantów `raw` i `ml_ready`.

### B. `Infrastructure`

Ma dostarczyć adaptery zgodne z portami używanymi dziś przez `Application`.

Najważniejsza zasada:

- zmieniamy implementacje, nie kontrakty `Application`.

### C. `Application`

Powinno zostać możliwie stabilne:

- te same handlery,
- te same DTO,
- te same oczekiwane typy zwracane,
- brak wiedzy o szczegółach eksperymentu i snapshotach linii.

## Pliki do przywrócenia lub zbudowania w `Infrastructure`

### Krytyczne dla działania

- `infrastructure/vision/opencv_board_cells_extractor.py`
- `infrastructure/vision/opencv_image_codec.py`
- `infrastructure/vision/opencv_perspective_transformer.py`
- `infrastructure/vision/opencv_text_overlay_renderer.py`
- `infrastructure/vision/opencv_adaptive_threshold_binarizer.py`
- `infrastructure/vision/opencv_grayscale_blur_preprocessor.py`
- `infrastructure/vision/opencv_largest_contour_detector.py`

### Już przywrócone

- `infrastructure/vision/cell_cleaning.py`
- `infrastructure/vision/cell_preprocessing_pipeline.py`

Te dwa pliki nie były duchami. Są nadal potrzebne przez:

- inferencję pojedynczej komórki,
- przygotowanie datasetów,
- preview danych,
- testy jednostkowe.

## Adaptery, które należy zbudować

### 1. Adapter preprocessingu planszy

Cel:

- zachować publiczny kontrakt `ImageApiResponse`,
- wewnątrz użyć aktywnego pipeline'u families -> frame -> warp.

Docelowa odpowiedzialność:

- dekodowanie wejścia,
- uruchomienie pełnego pipeline'u,
- mapowanie błędów na:
  - `invalid_image_payload`
  - `board_not_found`
  - `perspective_correction_failed`

### 2. Adapter ekstrakcji komórek z gotowej planszy

Cel:

- zachować `CellsGridApiResponse`,
- wewnętrznie mieć dostęp do:
  - `raw_cells`,
  - `preview_image`,
  - `ml_ready_cells_uint8`,
  - `ml_ready_preview_image`.

Docelowa zasada:

- publiczne `cells` mają być widokowe,
- `ml_ready` ma zostać jako dodatkowy artefakt wewnętrzny.

### 3. Adapter pełnego kontraktu vision dla datasetów

To nie musi być endpoint HTTP.

Potrzebny jest wewnętrzny kontrakt / wynik `Infrastructure`, który zwróci:

- obraz planszy po `warp`,
- surowe komórki 9x9,
- `raw_preview_image`,
- `ml_ready_cells_uint8`,
- `ml_ready_cells_float32`,
- `ml_ready_preview_image`.

Ten kontrakt zasili:

- przygotowanie datasetów,
- preview datasetów,
- później ewentualny trening i walidację.

### 4. Adapter zgodności `CellPreprocessingPipeline`

`Application` nadal oczekuje:

- `build_foreground_mask(...)`,
- `run_uint8(...)`,
- `run(...)`.

Dlatego `CellPreprocessingPipeline` ma pozostać stabilnym portem do:

- inferencji pojedynczej komórki,
- przygotowania datasetów,
- porównania zgodności `uint8` i `float32`.

## Kolejność migracji

### Krok 1. Ustabilizować `cell_cleaning.py` i `cell_preprocessing_pipeline.py`

To jest fundament współdzielony przez:

- inferencję,
- datasets,
- preview,
- zgodność `uint8` / `float32`.

Ten krok jest już częściowo wykonany przez przywrócenie tych plików.

### Krok 2. Odbudować brakujące moduły `Infrastructure`

Najpierw trzeba przywrócić importowalne moduły, z których korzysta
`api/dependencies.py`.

Bez tego `Application` nadal trzyma uchwyt do nieistniejących implementacji.

### Krok 3. Rozdzielić dwa poziomy wejścia

Trzeba jawnie rozdzielić:

- surowe zdjęcie planszy -> pełny pipeline -> `warp`,
- już skorygowana plansza -> cięcie 9x9.

Ten podział musi być widoczny zarówno w implementacji, jak i w dokumentacji.

### Krok 4. Naprawić semantykę `CellsGridApiResponse`

Aktualne eksperymentalne `logical_line_frame_cells.py` buduje `api_response`
z `ml_ready_cells`.

Przed migracją do `Infrastructure` należy to zmienić tak, aby:

- `api_response` zwracało komórki widokowe,
- `ml_ready_cells` zostały w osobnych polach wyniku wewnętrznego.

### Krok 5. Zdecydować o warpie z pełnej rozdzielczości

To jest punkt, którego nie wolno zostawić jako domyślnego niedopowiedzenia.

Migracja musi jawnie wybrać:

- `warp` z `display_bgr`,
- albo `warp` z `source_bgr` po przemapowaniu geometrii.

Do docelowej `Infrastructure` rekomendowany jest `warp` z pełnej
rozdzielczości.

### Krok 6. Zbudować wewnętrzny kontrakt dla datasetów i `UC-06`

Po ustabilizowaniu board + cells trzeba wystawić jeden wynik `Infrastructure`
z pełnym zestawem artefaktów potrzebnych downstream.

### Krok 7. Dopiero potem przepiąć `api/dependencies.py`

To powinien być ostatni krok integracyjny, nie pierwszy.

Najpierw adaptery, potem kompozycja.

## Ryzyka, których nie wolno zgubić

### 1. Pomieszanie dwóch wejść

Największy błąd byłby taki:

- używać `extract_cells_from_board_image(...)` jako wejścia od surowego zdjęcia,
- albo robić detekcję ramki ponownie w `preprocess/cells`.

### 2. Zmiana publicznej semantyki komórek

Jeśli `CellsGridApiResponse` dalej będzie zwracało `ml_ready`, użytkownik i
`BE` dostaną techniczny obraz modelowy zamiast normalnego widoku komórek.

### 3. Drift między preview a treningiem

`UC-06` potrzebuje, aby:

- `preview_uint8`,
- `training_float32`

były budowane z tej samej ścieżki przetwarzania.

### 4. Utrata jakości przez warp z obrazu przeskalowanego

Jeśli zostawimy `display_bgr` bez decyzji architektonicznej, możemy obniżyć
jakość komórek wejściowych do treningu i inferencji.

### 5. Mylenie stanu `post_connection` z finalną geometrią

Dla analizy linii ważny jest snapshot `post_connection`, ale ścieżka planszy do
`warp` idzie dalej przez intersections i wybór ramki.

## Stan docelowy po migracji

Po zakończeniu migracji system powinien mieć:

1. stabilne porty `Application`,
2. pełny runtime `UC-04`:
   - raw image -> board warp,
   - warped board -> 9x9 cells,
3. pełny kontrakt wejściowy do `UC-06`:
   - warped board,
   - raw cells,
   - preview images,
   - `ml_ready` uint8,
   - `ml_ready` float32,
4. wspólny `CellPreprocessingPipeline` dla inferencji i datasetów,
5. dokumentację, która rozróżnia:
   - lifecycle linii,
   - ekstrakcję planszy,
   - cięcie komórek,
   - artefakty treningowe.
