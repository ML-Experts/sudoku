# Sudoku board threshold experiment - mapa procesu i kodu

## Cel

Celem eksperymentu jest stabilne znalezienie wszystkich linii planszy sudoku na trudnych obrazach:

- wycinki z gazety,
- wydruki na kartce,
- obrazy z szumem,
- zdjęcia pod kątem,
- lekkie zagięcia kartki.

Aktualny notebook `sudoku_board_threshold_experiment.ipynb` jest poligonem do szybkiego porównywania wariantów preprocessingu, binaryzacji, naprawy linii, grupowania linii, budowy ramek i warpu.

Najważniejszy obecny cel algorytmu:

1. przygotować dobrą binarkę,
2. znaleźć surowe segmenty linii,
3. pogrupować je w logiczne linie poziome i pionowe,
4. odfiltrować linie słabe na podstawie styczności z drugą rodziną,
5. zbudować ramkę planszy z 4 wspólnych wierzchołków.


## Najkrótszy przepływ danych

```text
obraz wejściowy
-> grayscale
-> odszumianie / kontrast
-> adaptive threshold (z odwróceniem)
-> cleanup binarki
-> repair binarki
-> HoughLinesP
-> podział na rodziny horizontal / vertical
-> scalanie małych segmentów w logiczne linie
-> bridge repair dla przerw w liniach
-> liczenie styczności horizontal x vertical
-> iteracyjne filtrowanie linii po liczbie styczności
-> wspólne endpointy / aligned vertices
-> kandydaci ramek z 4 relacji narożnych
-> wybór najlepszej ramki
-> warp do kwadratu
```


## Rola notebooka

Notebook `sudoku_board_threshold_experiment.ipynb` nie powinien zawierać ciężkiej logiki algorytmicznej. Jego rola jest obecnie poprawna i sprowadza się głównie do:

- wyboru obrazka,
- ustawienia `ExperimentConfig`,
- uruchomienia kolejnych etapów pipeline'u,
- wypisania krótkiego opisu wyników,
- pokazania overlayów debugowych.

Główne moduły orkiestracyjne notebooka:

- `sudoku_board_threshold_notebook_bootstrap.py`  
  Ładuje i reloaduje moduły oraz buduje `ThresholdNotebookApi`.
- `sudoku_board_threshold_notebook_pipeline.py`  
  Prowadzi etap wejściowy: wybór obrazka, preprocessing, threshold, cleanup, repair.
- `sudoku_board_threshold_notebook_report.py`  
  Agreguje moduły raportowe dla linii, ramek, warpu i komórek.


## Główne modele danych

Plik: `sudoku_board_threshold_models.py`

Najważniejsze obiekty:

- `ExperimentConfig`  
  Wszystkie parametry eksperymentu i heurystyki.
- `DetectedLineSegment`  
  Surowy segment po Hough.
- `MergedLine`  
  Logiczna linia zbudowana z wielu segmentów.
- `LineBridge` i `LineBridgeDiagnostic`  
  Dane o próbach naprawy przerw między logicznymi liniami.
- `EndpointConnection`  
  Powiązanie końca linii poziomej z końcem linii pionowej.
- `LineFamilyResult`  
  Kompletny wynik etapu wykrywania i oczyszczania rodzin linii.
- `LineFrame`  
  Kandydat ramki planszy.
- `FrameDetectionResult`  
  Lista wszystkich i wybranych ramek.

To jest dobry punkt centralny dla danych. Jeśli coś ma być upraszczane, najpierw warto pilnować, żeby nowe etapy nadal produkowały czytelne obiekty tego typu.


## Pipeline krok po kroku

### 0. Bootstrap i konfiguracja

Pliki:

- `sudoku_board_threshold_notebook_bootstrap.py`
- `sudoku_board_threshold_helpers.py`
- `sudoku_board_threshold_models.py`
- `sudoku_board_threshold_paths.py`

Odpowiedzialność:

- dodać katalog `draft` do `sys.path`,
- przeładować moduły podczas pracy w notebooku,
- wystawić wspólne API dla notebooka,
- utrzymać konfigurację eksperymentu i ścieżki do datasetu.

Najważniejsze funkcje:

- `load_threshold_notebook_api()`
- `configure_manual_image_path()`
- `resolve_active_image_selection()`

Wejście:

- ścieżka ręczna albo indeks w datasetcie,
- `ExperimentConfig`.

Wyjście:

- aktywny obrazek,
- gotowe funkcje pomocnicze używane przez notebook.


### 1. Wczytanie obrazu i przygotowanie podglądu

Pliki:

- `sudoku_board_threshold_notebook_pipeline.py`
- `sudoku_board_threshold_display.py`

Odpowiedzialność:

- wczytać obraz BGR,
- zmniejszyć go do wygodnego rozmiaru roboczego,
- skonwertować do grayscale.

Najważniejsze funkcje:

- `run_threshold_preprocess_pipeline()`
- `load_image_bgr()`
- `resize_for_display()`

Wejście:

- `active_image_path`

Wyjście:

- `source_bgr`
- `display_bgr`
- `gray_image`

Uwagi:

- To jest etap czysto przygotowawczy.
- Warto utrzymać zasadę, że wszystko dalsze działa już na `display_bgr` i pochodnych, żeby łatwo porównywać wyniki.


### 2. Odszumianie i wzmacnianie kontrastu

Plik:

- `sudoku_board_threshold_binary.py`

Odpowiedzialność:

- zbudować kilka wariantów obrazu wejściowego do thresholdingu,
- porównać filtry zachowujące linie,
- podbić kontrast lokalny,
- opcjonalnie wyostrzyć obraz.

Najważniejsze funkcje:

- `build_denoise_variants()`
- `_apply_clahe()`
- `_apply_unsharp_mask()`

Warianty obecne w kodzie:

- `gaussian`
- `median`
- `bilateral`
- `nl_means`
- `clahe`
- kombinacje typu `clahe_bilateral`, `clahe_nl_means`
- warianty z dopiskiem `_unsharp`

Wejście:

- `gray_image`

Wyjście:

- `denoise_variants`
- `selected_denoise_image`

Sens etapu:

- zmniejszyć szum,
- nie zniszczyć cienkich linii planszy,
- poprawić warunki pod `adaptiveThreshold`.


### 3. Binaryzacja

Plik:

- `sudoku_board_threshold_binary.py`

Odpowiedzialność:

- zbudować kilka wariantów `adaptiveThreshold`,
- dobrać parę `blockSize` i `C`,
- odwrócić polaryzację tak, aby linie były foregroundem.

Najważniejsze funkcje:

- `adaptive_method_code()`
- `build_threshold_variants()`

Wejście:

- `selected_denoise_image`
- `ExperimentConfig.adaptive_block_sizes`
- `ExperimentConfig.adaptive_c_values`

Wyjście:

- `threshold_variants`
- `selected_binary`

Uwagi:

- Tutaj dzieje się kluczowe odwrócenie kolorów przez `threshold_invert=True`.
- To jest moment, w którym decydujecie, jak bardzo tło i artefakty papieru będą przebijać się do dalszych etapów.


### 4. Cleanup binarki

Plik:

- `sudoku_board_threshold_binary.py`

Odpowiedzialność:

- usunąć drobne komponenty,
- opcjonalnie lekko otworzyć obraz morfologicznie,
- przygotować binarkę pod etap naprawy linii.

Najważniejsze funkcje:

- `resolve_min_component_area_px()`
- `remove_small_connected_components()`
- `build_cleanup_variants()`
- `open_binary_image()`

Wejście:

- `selected_binary`

Wyjście:

- `cleanup_variants`
- `selected_clean_binary`
- `min_component_area_px`

Sens etapu:

- wyrzucić drobny śmieć,
- zostawić geometrię linii możliwie nienaruszoną.


### 5. Repair binarki

Plik:

- `sudoku_board_threshold_binary.py`

Odpowiedzialność:

- domknąć drobne przerwy w liniach,
- porównać warianty morfologiczne,
- przygotować obraz pod Hough.

Najważniejsze funkcje:

- `build_repair_variants()`
- `close_binary_image()`

Obecne strategie:

- `close_square_*`
- `directional_close`

Wejście:

- `selected_clean_binary`

Wyjście:

- `repair_variants`
- `selected_repaired_binary`

Ważna obserwacja:

- Ten etap jest jeszcze częścią preprocessingu obrazu, a nie logiki linii.
- W praktyce ma ogromny wpływ na późniejsze rodziny linii, więc dobrze trzymać go jako osobny, jawny krok.


### 6. Surowe wykrycie segmentów i podział na rodziny linii

Pliki:

- `sudoku_board_threshold_line_detection.py`
- `sudoku_board_threshold_line_families.py`
- `sudoku_board_threshold_line_geometry.py`

Odpowiedzialność:

- wykryć surowe segmenty przez `cv2.HoughLinesP`,
- znaleźć dominujący kąt,
- podzielić segmenty na rodzinę poziomą i pionową,
- doprecyzować kąty rodzin.

Najważniejsze funkcje:

- `detect_line_families()`
- `get_dominant_angle_degrees()`
- `collect_line_family()`
- `refine_family_angle_degrees()`
- `build_line_segment()`

Wejście:

- `selected_repaired_binary`

Wyjście:

- `horizontal_segments`
- `vertical_segments`
- kąty obu rodzin

Sens etapu:

- przejść od pojedynczych odcinków Hough do dwóch stabilnych rodzin geometrycznych.


### 7. Scalanie segmentów w logiczne linie

Pliki:

- `sudoku_board_threshold_line_merge.py`
- `sudoku_board_threshold_line_geometry.py`

Odpowiedzialność:

- połączyć małe segmenty należące do tej samej logicznej linii,
- policzyć ich zakres (`span`), rzeczywiste pokrycie (`covered`) i grubość,
- zbudować jeden obiekt `MergedLine` z wielu segmentów.

Najważniejsze funkcje:

- `should_merge_line_segments()`
- `connected_components()`
- `build_merged_line()`
- `merge_line_family_segments()`

Heurystyki używane przy scalaniu:

- zgodność kąta,
- mała odległość projekcyjna,
- mała przerwa między końcami wzdłuż kierunku linii.

Wejście:

- segmenty jednej rodziny

Wyjście:

- `horizontal_merged_lines`
- `vertical_merged_lines`

To jest bardzo ważny etap pojęciowy:

- surowy Hough daje odcinki,
- ten etap daje pierwsze sensowne "linie logiczne".


### 8. Bridge repair między liniami logicznymi

Pliki:

- `sudoku_board_threshold_line_bridge_family.py`
- `sudoku_board_threshold_line_bridge_inspection.py`
- `sudoku_board_threshold_line_bridge_candidate.py`
- `sudoku_board_threshold_line_bridge_geometry.py`
- `sudoku_board_threshold_line_bridge_positions.py`
- `sudoku_board_threshold_line_bridge_diagnostics.py`

Odpowiedzialność:

- sprawdzić, czy dwie logiczne linie tej samej rodziny powinny zostać potraktowane jako jedna linia z przerwą,
- ocenić kandydatów bridge,
- zachować diagnostykę przyjętych i odrzuconych prób.

Najważniejsze wywołania z perspektywy pipeline'u:

- `bridge_line_family_gaps()`
- `inspect_line_family_bridge_candidates()`

Wejście:

- `horizontal_merged_lines` lub `vertical_merged_lines`
- binarka po repair

Wyjście:

- zaktualizowane logiczne linie,
- `horizontal_bridges` / `vertical_bridges`,
- diagnostyka bridge.

Sens etapu:

- naprawić przypadki, gdzie jedna linia planszy została rozcięta przez szum, cień, zagięcie lub brak kontrastu.


### 9. Styczności między rodzinami i filtrowanie iteracyjne

Plik:

- `sudoku_board_threshold_line_touch.py`

Odpowiedzialność:

- znaleźć punkty styczności między liniami poziomymi i pionowymi,
- przypisać każdej linii liczbę kontaktów z drugą rodziną,
- wielokrotnie usuwać linie zbyt słabe,
- po każdym usunięciu przeliczyć styczności od nowa.

Najważniejsze funkcje:

- `touch_points_for_merged_lines()`
- `annotate_cross_family_touches()`
- `filter_lines_by_min_cross_family_touch_points()`
- `refresh_cross_family_touches()`
- `iteratively_filter_lines_by_touch_points()`

Wejście:

- logiczne linie po scaleniu i bridge repair

Wyjście:

- stabilny zbiór linii, które mają wystarczająco dużo styczności

To jest obecnie serce selekcji jakościowej:

- fałszywa linia zwykle ma mało styczności,
- dobra linia planszy zwykle przecina wiele linii z drugiej rodziny.

Ta sekcja odpowiada bezpośrednio za opisany przez Was mechanizm:

1. policz styczności,
2. zostaw tylko linie z `2+` styczności,
3. przelicz przecięcia jeszcze raz,
4. powtarzaj aż zbiór się ustabilizuje.


### 10. Wspólne endpointy i aligned vertices

Plik:

- `sudoku_board_threshold_line_touch.py`

Odpowiedzialność:

- znaleźć końce linii, które naprawdę odpowiadają sobie geometrycznie,
- wyrównać je do wspólnego punktu narożnego,
- przygotować relacje potrzebne do budowy ramki.

Najważniejsza funkcja:

- `resolve_last_touch_endpoint_connections()`

Wejście:

- końcowe linie poziome i pionowe po filtracji

Wyjście:

- `horizontal_aligned_vertices`
- `vertical_aligned_vertices`
- `endpoint_connections`

To jest etap przejścia z:

- "te dwie linie się gdzieś przecinają"

do:

- "ten konkretny koniec linii poziomej i ten konkretny koniec linii pionowej tworzą wspólny narożnik".


### 11. Budowa kandydatów ramek

Plik:

- `sudoku_board_threshold_frame.py`

Odpowiedzialność:

- zbudować ramkę tylko z pełnego kompletu czterech narożnych relacji,
- policzyć pole, obwód i inne cechy jakości,
- odsiać słabsze i wewnętrzne ramki,
- zwrócić wybrane kandydaty.

Najważniejsze funkcje:

- `find_line_frames()`
- `build_line_frame_candidate()`
- `order_frame_corners()`
- `compute_priority_score()`
- `filter_out_inner_smaller_frames()`

Warunek istnienia ramki:

- `Htop <-> Vleft`
- `Htop <-> Vright`
- `Hbottom <-> Vleft`
- `Hbottom <-> Vright`

Wejście:

- `LineFamilyResult.endpoint_connections`
- końcowe linie `horizontal` i `vertical`

Wyjście:

- `FrameDetectionResult`
- `selected_frames`

To jest bardzo dobry, czytelny etap domenowy. Z perspektywy dokumentacji można go traktować jako osobny use case: "z linii zbuduj ramkę".


### 12. Warp planszy

Pliki:

- `sudoku_board_threshold_warp.py`
- `sudoku_board_threshold_notebook_report_warp.py`

Odpowiedzialność:

- wziąć narożniki najlepszej ramki,
- zbudować transformację perspektywiczną,
- przekształcić planszę do kwadratu.

Najważniejsze funkcje:

- `aligned_frame_corners()`
- `warp_image_from_corners()`
- `build_destination_corners()`
- `build_corner_overlay()`

Wejście:

- `selected_frames[0]`

Wyjście:

- `aligned_warp`

Uwagi:

- To nie jest już etap szukania linii, tylko konsumpcja znalezionej ramki.
- Nadal warto go mieć w tym eksperymencie, bo pozwala szybko ocenić, czy wykryta ramka jest sensowna.


### 13. Podział na komórki 9x9

Pliki:

- `sudoku_board_threshold_cells.py`
- `sudoku_board_threshold_notebook_report_cells.py`

Odpowiedzialność:

- podzielić warp na siatkę 9x9,
- przyciąć marginesy komórek,
- zbudować foreground cyfr,
- usunąć resztki linii siatki.

Najważniejsze funkcje:

- `extract_cells_from_warped_board()`
- `split_image_into_grid()`
- `build_cell_foreground_mask()`
- `clean_cell_binary()`

Ten etap jest już dalszy niż Wasz aktualny główny problem z liniami planszy. W dokumentacji warto go trzymać osobno, żeby nie mieszać celu "znajdź planszę" z celem "przygotuj cyfry do OCR/ML".


## Gdzie co leży

### Warstwa notebook / orkiestracja

- `sudoku_board_threshold_experiment.ipynb`
- `sudoku_board_threshold_notebook_bootstrap.py`
- `sudoku_board_threshold_notebook_pipeline.py`
- `sudoku_board_threshold_notebook_report.py`

To jest warstwa uruchamiania eksperymentu.


### Warstwa modeli i konfiguracji

- `sudoku_board_threshold_models.py`
- `sudoku_board_threshold_paths.py`

To jest warstwa wspólnych struktur danych i parametrów.


### Warstwa preprocessingu obrazu

- `sudoku_board_threshold_display.py`
- `sudoku_board_threshold_binary.py`

Tu powinny żyć tylko operacje na obrazie, bez logiki ramek i geometrii planszy.


### Warstwa geometrii i linii

- `sudoku_board_threshold_line_geometry.py`
- `sudoku_board_threshold_line_families.py`
- `sudoku_board_threshold_line_merge.py`
- `sudoku_board_threshold_line_touch.py`
- `sudoku_board_threshold_line_detection.py`

To jest właściwy rdzeń wykrywania planszy.


### Warstwa bridge repair

- `sudoku_board_threshold_line_bridge_family.py`
- `sudoku_board_threshold_line_bridge_inspection.py`
- `sudoku_board_threshold_line_bridge_candidate.py`
- `sudoku_board_threshold_line_bridge_geometry.py`
- `sudoku_board_threshold_line_bridge_positions.py`
- `sudoku_board_threshold_line_bridge_diagnostics.py`

To jest podsystem specjalistyczny, który warto traktować jako osobny moduł domenowy.


### Warstwa ramek i perspektywy

- `sudoku_board_threshold_frame.py`
- `sudoku_board_threshold_warp.py`

To jest etap przejścia od linii do planszy.


### Warstwa debug / wizualizacja

- `sudoku_board_threshold_visualization.py`
- `sudoku_board_threshold_notebook_report_lines.py`
- `sudoku_board_threshold_notebook_report_frames.py`
- `sudoku_board_threshold_notebook_report_warp.py`
- `sudoku_board_threshold_notebook_report_cells.py`
- `sudoku_board_threshold_notebook_report_line_descriptions.py`
- `sudoku_board_threshold_notebook_report_models.py`

Ta warstwa nie powinna wprowadzać nowej logiki algorytmicznej. Powinna tylko:

- opisać wyniki,
- budować overlaye,
- ułatwiać porównywanie wariantów.


## Naturalny podział na procesy

Jeśli chcecie dalej porządkować kod, sensowny podział odpowiedzialności wygląda tak:

### Proces A. Wejście i preprocessing

Zakres:

- wybór obrazu,
- grayscale,
- odszumianie,
- kontrast,
- binaryzacja,
- cleanup,
- repair.

Pliki:

- `sudoku_board_threshold_notebook_pipeline.py`
- `sudoku_board_threshold_binary.py`
- `sudoku_board_threshold_display.py`


### Proces B. Budowa logicznych linii

Zakres:

- Hough,
- rodziny linii,
- scalanie segmentów,
- bridge repair,
- styczności,
- filtracja iteracyjna,
- aligned vertices.

Pliki:

- `sudoku_board_threshold_line_detection.py`
- `sudoku_board_threshold_line_merge.py`
- `sudoku_board_threshold_line_touch.py`
- pliki `sudoku_board_threshold_line_bridge_*.py`


### Proces C. Budowa planszy

Zakres:

- generowanie ramek,
- ranking ramek,
- wybór najlepszego kandydata,
- warp.

Pliki:

- `sudoku_board_threshold_frame.py`
- `sudoku_board_threshold_warp.py`


### Proces D. Debug i ocena jakości

Zakres:

- overlaye,
- opisy tekstowe,
- porównania wariantów.

Pliki:

- `sudoku_board_threshold_visualization.py`
- `sudoku_board_threshold_notebook_report*.py`


## Co jest już dobrze rozdzielone

- `ExperimentConfig` zbiera heurystyki w jednym miejscu.
- Notebook jest raczej orchestrator niż miejscem ciężkiej logiki.
- Modele `MergedLine`, `EndpointConnection` i `LineFrame` dobrze opisują kolejne poziomy abstrakcji.
- Etap ramek jest dość czytelny domenowo: z relacji narożnych budujemy kandydatów.
- Debug ma osobne moduły raportowe, więc nie miesza się mocno z notebookiem.


## Co wygląda na potencjalnie przekombinowane

### 1. `detect_line_families()` robi bardzo dużo naraz

Obecnie ten jeden etap odpowiada za:

- Hough,
- podział na rodziny,
- scalanie,
- bridge repair,
- styczności,
- filtrację,
- aligned vertices,
- diagnostykę bridge.

To jest logicznie poprawne, ale trudno to dalej upraszczać, bo za dużo decyzji siedzi w jednym przebiegu.

Najlepszy kandydat do rozbicia na mniejsze kroki:

1. `detect_raw_line_segments()`
2. `split_segments_into_families()`
3. `merge_family_segments_into_logical_lines()`
4. `repair_family_line_gaps()`
5. `filter_lines_by_cross_family_support()`
6. `resolve_endpoint_connections()`


### 2. Bridge repair to już osobny podsystem

To dobrze, ale ma kilka plików i łatwo zgubić przepływ.

Warto dopisać w przyszłości jeden plik wejściowy, np.:

- `sudoku_board_threshold_line_bridge_pipeline.py`

który byłby czytelnym facade dla całego bridge subsystemu.


### 3. Preprocessing i selekcja wariantów są jeszcze mocno "notebook-first"

`build_denoise_variants()`, `build_threshold_variants()`, `build_cleanup_variants()` i `build_repair_variants()` są dobre do eksperymentów, ale mniej dobre jako finalny pipeline produkcyjny.

Docelowo można rozdzielić:

- tryb eksperymentalny: buduj wiele wariantów,
- tryb produkcyjny: uruchom tylko jedną wybraną ścieżkę.


### 4. Warstwa raportowa jest czytelna, ale rozproszona

Dzisiaj to działa, ale przy dalszym wzroście liczby komórek notebooka można dojść do sytuacji, w której debug stanie się trudniejszy do nawigacji niż sam algorytm.


## Najbardziej praktyczna propozycja następnego refaktoru

Jeśli celem jest uproszczenie bez zmiany działania, najbezpieczniej zrobić to w tej kolejności:

1. Rozbić `detect_line_families()` na 5-6 małych funkcji etapowych.
2. Wydzielić jawny typ wyniku dla każdego etapu pośredniego, nie tylko końcowy `LineFamilyResult`.
3. Zostawić notebook bez zmian funkcjonalnych, ale oprzeć go na nowych, mniejszych krokach.
4. Dopiero potem zastanawiać się, czy bridge repair albo touch filtering nie są zbyt skomplikowane heurystycznie.


## Minimalna mapa zależności

```text
notebook
-> notebook_bootstrap
-> notebook_pipeline
-> binary / display / paths / models
-> line_detection
   -> line_families
   -> line_merge
   -> line_touch
   -> line_bridge_*
   -> line_geometry
-> frame
-> warp
-> notebook_report_* / visualization
```


## Podsumowanie

Na dziś kod da się czytać jako cztery główne etapy:

1. przygotowanie binarki,
2. budowa logicznych linii,
3. budowa ramki planszy,
4. wizualizacja i ocena wyniku.

Największy ciężar złożoności siedzi teraz nie w notebooku, tylko w jednym miejscu: `sudoku_board_threshold_line_detection.py`, które scala kilka osobnych decyzji algorytmicznych w jedną funkcję.

Jeśli będziecie chcieli uprościć pipeline bez utraty obecnej wiedzy eksperymentalnej, to właśnie ten etap warto rozciąć jako pierwszy.
