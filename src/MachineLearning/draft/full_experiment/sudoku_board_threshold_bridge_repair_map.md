# Sudoku board threshold - bridge repair między liniami logicznymi

## Cel tej części algorytmu

`Bridge repair` odpowiada za sytuację, w której jedna logiczna linia planszy sudoku została rozbita na kilka osobnych grup segmentów, mimo że geometrycznie powinna być traktowana jako jedna linia.

Typowe powody rozcięcia:

- lokalny szum,
- słabszy kontrast,
- przerwa po binaryzacji,
- zagięcie kartki,
- cień,
- nierówna farba / druk,
- agresywny cleanup lub repair wcześniejszego etapu.

Bridge repair działa **po scaleniu segmentów w logiczne linie**, ale **przed filtrowaniem po stycznościach z drugą rodziną**.

To bardzo ważne, bo:

1. najpierw chcemy odzyskać brakujące części linii,
2. dopiero potem liczyć przecięcia `horizontal x vertical`,
3. dopiero potem usuwać słabe linie.


## Gdzie zaczyna się bridge repair w pipeline

Główny punkt wejścia:

- `sudoku_board_threshold_line_detection.py`

Najważniejsze wywołanie:

- `bridge_line_family_gaps()`

Bridge repair uruchamia się osobno dla obu rodzin:

1. dla linii poziomych,
2. dla linii pionowych.

Schemat wywołań wygląda tak:

```text
detect_line_families()
-> merge_line_family_segments(horizontal)
-> merge_line_family_segments(vertical)
-> bridge_line_family_gaps(horizontal)
-> bridge_line_family_gaps(vertical)
-> annotate_cross_family_touches(...)
-> iteratively_filter_lines_by_touch_points(...)
```

Czyli bridge repair jest ostatnim etapem "naprawy wewnątrz jednej rodziny", zanim zacznie się logika przecięć między rodzinami.


## Najważniejsze pliki

### Pliki główne

- `sudoku_board_threshold_line_bridge_family.py`  
  Orkiestracja bridge repair dla całej rodziny linii.

- `sudoku_board_threshold_line_bridge_inspection.py`  
  Analiza jednej pary linii i wybór najlepszego kandydata bridge.

- `sudoku_board_threshold_line_bridge_candidate.py`  
  Twarda walidacja pojedynczej próby bridge.

- `sudoku_board_threshold_line_bridge_geometry.py`  
  Geometria idealnego połączenia: punkty start/end, boxy końców, corridor polygon.

- `sudoku_board_threshold_line_bridge_positions.py`  
  Generowanie kandydatów pozycji łączenia na podstawie support intervals.

- `sudoku_board_threshold_line_bridge_diagnostics.py`  
  Budowanie diagnostyki i ranking powodów odrzucenia.


### Pliki pomocnicze, od których bridge zależy

- `sudoku_board_threshold_line_merge.py`  
  Po bridge znowu składamy komponenty w nowy `MergedLine`.

- `sudoku_board_threshold_line_geometry.py`  
  Dostarcza operacje geometrii 2D: pozycje na linii, corridor polygon, boxy, clamp itp.

- `sudoku_board_threshold_models.py`  
  Modele `LineBridge`, `LineBridgeDiagnostic`, `MergedLine`.


### Pliki, w których wynik jest potem pokazywany

- `sudoku_board_threshold_visualization.py`
- `sudoku_board_threshold_notebook_report_line_descriptions.py`
- `sudoku_board_threshold_notebook_report_lines.py`


## Jakie dane wchodzą do bridge repair

Bridge repair nie pracuje na surowych segmentach Hough. Dostaje już linie logiczne po wcześniejszym scaleniu.

Wejście do `bridge_line_family_gaps()`:

- `binary_image`  
  Binarka po preprocessingu i repair obrazu.

- `merged_lines: list[MergedLine]`  
  Lista logicznych linii jednej rodziny, np. tylko `horizontal`.

- `family_angle_degrees`  
  Uśredniony kąt rodziny.

- `family_name`  
  `"horizontal"` albo `"vertical"`.

- `config`
- `minimum_dimension`


## Co dokładnie zawiera `MergedLine`

Bridge repair opiera się głównie na tych polach `MergedLine`:

- `projection`  
  Pozycja linii w osi prostopadłej do kierunku rodziny.

- `span_start`, `span_end`, `span_length`  
  Zakres całej logicznej linii wzdłuż jej kierunku.

- `support_intervals`  
  Najważniejsze pole dla bridge repair. To rzeczywiste fragmenty pokryte przez segmenty.

- `segments`  
  Surowe segmenty tworzące daną linię logiczną.

Most między dwiema liniami jest szukany właśnie między ich `support_intervals`, a nie wyłącznie między skrajnymi punktami całego `span`.


## Etap 1. Wyliczenie progów bridge

Plik:

- `sudoku_board_threshold_line_bridge_family.py`

Funkcja:

- `resolve_bridge_thresholds(config, minimum_dimension)`

Ta funkcja przelicza heurystyki konfiguracyjne na piksele:

- `bridge_projection_tolerance_px`
- `bridge_max_gap_px`
- `bridge_endpoint_tolerance_px`

Znaczenie:

- `projection_tolerance`  
  Jak daleko od siebie mogą leżeć dwie linie w osi prostopadłej i nadal być uznane za kandydatów do połączenia.

- `max_gap`  
  Jak duża może być luka między końcami dwóch fragmentów.

- `endpoint_tolerance`  
  Jak duży obszar wokół idealnych końców mostu przeszukujemy.

To jest pierwszy filtr jakości. Jeśli dwie linie są za daleko "obok siebie", bridge repair nawet nie próbuje ich łączyć.


## Etap 2. Przejście po parach linii w rodzinie

Plik:

- `sudoku_board_threshold_line_bridge_family.py`

Funkcja:

- `bridge_line_family_gaps(...)`

To główny orchestrator dla całej rodziny.

Co robi:

1. bierze aktualną listę `current_lines`,
2. przechodzi po wszystkich parach `(first_index, second_index)`,
3. dla każdej pary woła `line_bridge_candidate(...)`,
4. zbiera zaakceptowane bridge w `iteration_bridges`,
5. scala linie po zaakceptowanych mostach,
6. powtarza iteracyjnie aż w danej iteracji nic już nie da się połączyć.

To ważne: bridge repair nie jest jednorazowy.

Działa iteracyjnie, bo po połączeniu:

- A z B,

może się okazać, że nowa, większa linia `(A+B)` da się jeszcze połączyć z:

- C.

Czyli mamy logikę typu:

```text
iteracja 1: A + B
iteracja 2: (A+B) + C
iteracja 3: brak nowych połączeń -> stop
```


## Etap 3. Analiza jednej pary linii

Plik:

- `sudoku_board_threshold_line_bridge_inspection.py`

Funkcja:

- `inspect_line_bridge_candidate(...)`

To jest centralna funkcja decyzyjna dla jednej pary linii.

Jej odpowiedzialność:

1. sprawdzić, czy linie są dostatecznie blisko w osi projekcji,
2. wygenerować sensowne pozycje kandydackie do mostu,
3. ocenić kandydatów po kolei,
4. zwrócić pierwszy zaakceptowany `LineBridge`,
5. jeśli nic nie przejdzie, zwrócić najlepszą diagnostykę odrzucenia.


### Krok 3.1. Filtr po `projection_distance`

Pierwsza rzecz:

```text
projection_distance_px = abs(first_line.projection - second_line.projection)
```

Jeśli:

```text
projection_distance_px > projection_tolerance_px
```

to para odpada od razu z powodem:

- `projection_too_far`

Sens:

- dwie linie z tej samej rodziny muszą leżeć mniej więcej na tej samej wysokości albo szerokości,
- jeśli jedna jest wyraźnie przesunięta względem drugiej, to prawie na pewno nie są fragmentami tej samej linii planszy.


### Krok 3.2. Generowanie kandydatów pozycji mostu

Plik:

- `sudoku_board_threshold_line_bridge_positions.py`

Funkcja:

- `candidate_interval_bridge_positions(first_line, second_line)`

Ta funkcja pracuje na `support_intervals`.

Dla każdej pary przedziałów:

- interval z pierwszej linii,
- interval z drugiej linii,

tworzy kandydatów na bazie końców przedziałów:

1. początek pierwszego przedziału vs drugi przedział,
2. koniec pierwszego przedziału vs drugi przedział,
3. początek drugiego przedziału vs pierwszy przedział,
4. koniec drugiego przedziału vs pierwszy przedział.

Potem:

- rzutuje punkt końcowy na przeciwny przedział przez `np.clip`,
- wylicza `gap`,
- deduplikuje kandydatów,
- sortuje rosnąco po `gap`.

Zwracany kandydat ma postać:

- `(first_position, second_position, gap_px)`

Znaczenie:

- `first_position`  
  pozycja wzdłuż pierwszej linii,

- `second_position`  
  pozycja wzdłuż drugiej linii,

- `gap_px`  
  odległość, którą trzeba "domknąć".

To jest bardzo ważny detal implementacyjny:

- bridge repair nie łączy ślepo skrajnych końców całych linii,
- tylko szuka **najbliższych logicznych miejsc styku między realnymi obszarami pokrycia**.


## Etap 4. Ocena pojedynczego kandydata bridge

Plik:

- `sudoku_board_threshold_line_bridge_candidate.py`

Funkcja:

- `evaluate_bridge_attempt(...)`

To jest najważniejszy etap walidacji. Tutaj powstaje odpowiedź na pytanie:

- "czy dla tej konkretnej pozycji most naprawdę istnieje w obrazie?"


### Krok 4.1. Budowa geometrii idealnego bridge

Plik:

- `sudoku_board_threshold_line_bridge_geometry.py`

Funkcja:

- `build_bridge_geometry(...)`

Na wejściu mamy:

- `first_line.projection`,
- `second_line.projection`,
- `first_position`,
- `second_position`,
- `family_angle_degrees`.

Z tego budowane są:

- `ideal_start_point`
- `ideal_end_point`
- `start_box`
- `end_box`
- `corridor_polygon`


### Co oznaczają te obiekty

#### `ideal_start_point` / `ideal_end_point`

To geometrycznie idealne końce mostu, obliczane przez:

- `point_from_line_position(...)`

czyli z reprezentacji:

- pozycja linii w osi normalnej (`projection`)
- pozycja wzdłuż linii (`position`)

na punkt `(x, y)` w obrazie.


#### `start_box` / `end_box`

To małe prostokąty wokół idealnych końców mostu:

- budowane przez `build_axis_aligned_box(...)`

Ich rola:

- nie wymagać idealnie trafionego piksela końcowego,
- dopuścić małe przesunięcie końców przez szum i deformacje.


#### `corridor_polygon`

To wąski czworokąt między `ideal_start_point` i `ideal_end_point`:

- budowany przez `build_corridor_polygon(...)`

Można o nim myśleć jak o:

- "tunelu", w którym powinien znajdować się rzeczywisty materiał obrazowy łączący obie linie.

Bridge repair nie przeszukuje całego ROI losowo, tylko właśnie ten korytarz.


## Etap 5. Szybkie odrzucenia

W `evaluate_bridge_attempt(...)` jest kilka szybkich powodów odrzucenia.

### 5.1. `gap_too_large`

Jeśli:

```text
gap_px > max_gap_px
```

to kandydat odpada od razu.

Sens:

- nie chcemy sztucznie łączyć dwóch odległych linii, bo ryzyko fałszywego bridge byłoby zbyt duże.


### 5.2. Specjalny przypadek `gap_px <= 1e-6`

Jeżeli przerwa praktycznie nie istnieje, kod traktuje to jako przypadek nakładania albo styku.

Wtedy:

1. `build_overlap_bridge_segment(...)` generuje minimalny, niezerowy segment,
2. tworzony jest `LineBridge`,
3. wynik zostaje zaakceptowany bez pełnej analizy komponentów w korytarzu.

To jest techniczny zabieg, żeby:

- nie tworzyć degeneratu długości 0,
- mieć jawny obiekt bridge nawet dla styku granicznego.


## Etap 6. Budowa ROI i maski korytarza

Jeśli kandydat nie odpadł wcześniej, kod przechodzi do analizy binarki.

W `evaluate_bridge_attempt(...)` wyznaczane są:

- minimalne i maksymalne `x`,
- minimalne i maksymalne `y`,

na podstawie:

- `start_box`,
- `end_box`,
- punktów `corridor_polygon`.

Z tego budowany jest:

- `roi = binary_image[min_y:max_y+1, min_x:max_x+1]`

Potem powstaje:

- `corridor_mask`

czyli maska wypełnionego wielokąta korytarza wewnątrz ROI.

Następnie:

- `candidate_mask = (roi > 0) & (corridor_mask > 0)`

czyli zostają tylko białe piksele obrazu znajdujące się wewnątrz dozwolonego korytarza.


## Etap 7. Odrzucenia związane z materiałem obrazowym

### 7.1. `empty_roi`

ROI wyszło puste. To raczej przypadek brzegowy geometrii albo clampingu.


### 7.2. `no_candidate_pixels`

W korytarzu nie ma żadnych foreground pixels.

Sens:

- obraz nie daje żadnego dowodu, że między liniami istnieje ciągłość.


### 7.3. `no_components`

Po `connectedComponents(candidate_mask)` nie ma żadnych sensownych komponentów.

To praktycznie znaczy:

- korytarz istnieje,
- ale nie ma w nim materiału, który da się potraktować jako struktura łącząca.


## Etap 8. Sprawdzenie, czy istnieje wspólny komponent łączący oba końce

Po znalezieniu komponentów kod buduje:

- `start_mask`
- `end_mask`

czyli osobne maski prostokątów końcowych.

Następnie zbiera:

- etykiety komponentów dotykających `start_box`,
- etykiety komponentów dotykających `end_box`.

Jeśli przecięcie tych zbiorów jest puste:

- `common_labels = start_labels & end_labels`

to kandydat odpada z powodem:

- `no_common_component`

Sens:

- sam materiał w korytarzu nie wystarczy,
- potrzebny jest **jeden wspólny komponent**, który łączy oba końce.

To bardzo silny warunek i właśnie on chroni przed przypadkami:

- z jednej strony jest trochę szumu,
- z drugiej strony też jest trochę szumu,
- ale nie ma rzeczywistej ciągłości pomiędzy nimi.


## Etap 9. Sprawdzenie ciągłości projekcji komponentu

Plik:

- `sudoku_board_threshold_line_bridge_geometry.py`

Funkcja:

- `component_has_continuous_bridge_projection(...)`

To bardzo ciekawy i ważny krok.

Kod bierze punkty najlepszego wspólnego komponentu i:

1. rzutuje je na wektor mostu,
2. zaokrągla pozycje do pikseli,
3. sprawdza, czy zajęte pozycje pokrywają cały odcinek od początku do końca,
4. dopuszcza tylko bardzo małe dziury projekcyjne.

Zwracane są:

- `has_continuous_projection`
- `projection_coverage_start_px`
- `projection_coverage_end_px`
- `projection_max_hole_px`

Kandydat odpada z powodem:

- `discontinuous_projection`

jeżeli komponent:

- wprawdzie dotyka obu końców,
- ale po rzucie na oś mostu nie tworzy sensownej ciągłej struktury.

To jest bardzo dobra heurystyka przeciwko "hakom", "plamom" i nieregularnym blobom, które przypadkiem zahaczają o oba końce, ale nie są liniowym łącznikiem.


## Etap 10. Zbudowanie końcowego segmentu bridge

Jeśli komponent przeszedł wszystkie warunki, kod:

1. szuka pikseli komponentu najbliższych idealnemu startowi,
2. szuka pikseli komponentu najbliższych idealnemu końcowi,
3. z tych dwóch punktów buduje rzeczywisty segment bridge przez:
   - `build_detected_line_segment(...)`

Ten krok jest ważny, bo finalny segment bridge nie musi być dokładnie równy idealnemu połączeniu geometrycznemu.

Zamiast tego:

- punkt startowy i końcowy są "zakotwiczone" w realnym komponencie binarnym.

Jeśli długość takiego segmentu jest zbyt mała:

- `degenerate_segment`

W przeciwnym razie powstaje:

- `LineBridge`


## Co zawiera `LineBridge`

Model:

- `sudoku_board_threshold_models.py`

Pola:

- `family_name`
- `first_line_index`
- `second_line_index`
- `segment`
- `ideal_start_point`
- `ideal_end_point`
- `corridor_polygon`
- `start_box`
- `end_box`
- `gap_px`

To jest bardzo dobry obiekt debugowy, bo przechowuje jednocześnie:

- finalny segment używany do późniejszego scalania,
- geometrię idealną,
- obszar przeszukiwania,
- informację diagnostyczną o luce.


## Etap 11. Scalanie linii po zaakceptowanych bridge

Plik:

- `sudoku_board_threshold_line_bridge_family.py`

Funkcja:

- `merge_lines_with_bridges(...)`

Po zaakceptowaniu listy `bridges` dla iteracji:

1. budowana jest lista sąsiedztwa między indeksami linii,
2. liczona jest spójność przez `connected_components(...)`,
3. dla każdej spójnej grupy zbierane są:
   - wszystkie segmenty oryginalnych linii,
   - wszystkie segmenty zaakceptowanych bridge,
4. z całości powstaje nowy `MergedLine` przez:
   - `build_merged_line(...)`

To jest bardzo elegancki moment implementacji:

- bridge nie "modyfikuje" starej linii,
- tylko dokleja segment mostu i buduje nową linię logiczną od zera.

Dzięki temu automatycznie aktualizują się:

- `support_intervals`,
- `span`,
- `covered_length`,
- `centroid`,
- `segment_count`,
- `total_segment_length`.


## Etap 12. Iteracyjność całego bridge repair

Funkcja:

- `bridge_line_family_gaps(...)`

Mosty są znajdowane iteracyjnie, bo po scaleniu linii zmienia się geometria:

- nowa linia ma inny `span`,
- nowe `support_intervals`,
- większy zasięg,
- nowe możliwości połączenia z kolejnym fragmentem.

Pętla kończy się, gdy:

- `iteration_bridges` jest puste,

czyli żadna para aktualnych linii nie przeszła bridge repair.


## Diagnostyka bridge repair

### Gdzie powstaje

- `sudoku_board_threshold_line_bridge_diagnostics.py`
- `sudoku_board_threshold_line_bridge_inspection.py`
- `sudoku_board_threshold_line_bridge_candidate.py`

Każda para linii może zwrócić `LineBridgeDiagnostic`, nawet jeśli nie powstał most.


### Jakie są powody odrzucenia

Aktualne `reject_reason`:

- `projection_too_far`
- `no_bridge_positions`
- `gap_too_large`
- `empty_roi`
- `no_candidate_pixels`
- `no_components`
- `no_common_component`
- `discontinuous_projection`
- `degenerate_segment`
- `accepted`


### Ranking diagnostyk

Funkcja:

- `bridge_diagnostic_priority(...)`

Jeśli dla jednej pary było kilku kandydatów i żaden nie przeszedł, kod nie zwraca losowej porażki, tylko "najciekawszą" diagnostykę.

Priorytet jest ustawiony mniej więcej tak:

1. `accepted`
2. `degenerate_segment`
3. `discontinuous_projection`
4. `no_common_component`
5. `no_components`
6. `no_candidate_pixels`
7. `empty_roi`
8. `gap_too_large`
9. `no_bridge_positions`
10. `projection_too_far`

Sens:

- użytkownik ma zobaczyć możliwie najbardziej informacyjny powód, a nie tylko pierwszy lepszy.


## Gdzie bridge repair trafia do wyniku końcowego

Plik:

- `sudoku_board_threshold_line_detection.py`

Po bridge repair wynik trafia do `LineFamilyResult` jako:

- `horizontal_bridges`
- `vertical_bridges`
- `horizontal_pre_filter_merged_lines`
- `vertical_pre_filter_merged_lines`
- `horizontal_bridge_diagnostics`
- `vertical_bridge_diagnostics`

Kolejność ma znaczenie:

1. najpierw bridge repair,
2. potem `annotate_cross_family_touches(...)`,
3. potem filtracja po liczbie styczności,
4. potem endpoint connections.


## Gdzie można to zobaczyć w notebooku

### Overlaye

Plik:

- `sudoku_board_threshold_visualization.py`

Najważniejsze funkcje:

- `draw_line_bridges(...)`
- `build_bridged_line_family_overlays(...)`

Na overlayach widać:

- `corridor_polygon`
- `start_box`
- `end_box`
- finalny segment bridge
- idealne punkty końcowe

To jest bardzo przydatne, bo można wizualnie sprawdzić:

- czy korytarz jest dobrze ustawiony,
- czy boxy końców nie są za małe,
- czy most nie jest akceptowany zbyt agresywnie,
- czy nie łączy złych par.


### Opisy tekstowe w notebooku

Pliki:

- `sudoku_board_threshold_notebook_report_line_descriptions.py`
- `sudoku_board_threshold_notebook_report_lines.py`

Najważniejsze funkcje:

- `_describe_bridge_diagnostics(...)`
- `describe_line_debug_artifacts(...)`
- `run_line_debug_analysis(...)`

Notebook wypisuje m.in.:

- liczbę zaakceptowanych bridge,
- liczbę odrzuceń,
- rozkład powodów odrzuceń,
- najbliższe odrzucone pary,
- przy `discontinuous_projection` także:
  - `projection_coverage_start_px`
  - `projection_coverage_end_px`
  - `projection_max_hole_px`


## Bridge repair krok po kroku - skrót wykonawczy

```text
wejście: merged lines jednej rodziny + binarka
-> policz progi bridge
-> dla każdej pary linii:
   -> sprawdź projection distance
   -> wygeneruj kandydatów z support intervals
   -> dla kandydatów od najmniejszego gap:
      -> wyznacz idealny start/end
      -> zbuduj start_box, end_box i corridor_polygon
      -> jeśli gap za duży: odrzuć
      -> jeśli overlap: zaakceptuj specjalnym trybem
      -> wytnij ROI
      -> zbuduj maskę korytarza
      -> znajdź foreground pixels w korytarzu
      -> policz connected components
      -> sprawdź wspólny komponent między start_box i end_box
      -> sprawdź ciągłość projekcji komponentu
      -> zakotwicz realny segment bridge w obrazie
      -> zaakceptuj LineBridge
-> z zaakceptowanych bridge zbuduj komponenty spójne
-> scal linie + bridge segments w nowe MergedLine
-> powtarzaj aż brak nowych bridge
```


## Co w tej implementacji jest najmocniejsze

### 1. Bridge nie jest czysto geometryczny

Kod nie łączy linii wyłącznie dlatego, że są blisko siebie.

Wymaga jeszcze potwierdzenia w obrazie binarnym:

- w korytarzu,
- między boxami końcowymi,
- przez wspólny komponent,
- z ciągłą projekcją.


### 2. Kandydaci są generowani z realnego pokrycia, a nie ze spanów

To bardzo dobra decyzja.

`support_intervals` reprezentują rzeczywiste odcinki pokryte segmentami, więc bridge repair lepiej reaguje na porwane linie i nie robi zbyt długich sztucznych połączeń.


### 3. Wynik jest iteracyjny

Po każdym udanym łączeniu budowana jest nowa, większa linia logiczna, co pozwala domknąć bardziej złożone przypadki typu:

- mały fragment + mały fragment + główna część linii.


### 4. Diagnostyka jest mocna

To nie jest "black box". Da się zobaczyć:

- co było sprawdzane,
- gdzie,
- z jakim `gap`,
- z jakim `projection distance`,
- dlaczego kandydat odpadł.


## Co jest tu najbardziej złożone

Największa złożoność siedzi w:

- `evaluate_bridge_attempt(...)`

bo tam jednocześnie miesza się:

- geometria idealnego mostu,
- analiza ROI,
- connected components,
- ciągłość projekcji,
- kotwiczenie finalnego segmentu,
- diagnostyka.

Jeśli kiedyś będziecie chcieli tę część upraszczać, to właśnie ten punkt jest pierwszym kandydatem do rozbicia.


## Sensowny refaktor tej części

Najbardziej naturalny podział `evaluate_bridge_attempt(...)` to:

1. `build_bridge_search_region(...)`
2. `extract_bridge_candidate_mask(...)`
3. `find_common_bridge_component(...)`
4. `validate_bridge_component_projection(...)`
5. `build_bridge_segment_from_component(...)`

To nic nie zmienia algorytmicznie, ale znacznie poprawiłoby czytelność.


## Podsumowanie

Bridge repair w tym eksperymencie to nie jest proste "dorysowanie kreski między dwoma końcami". To wieloetapowy test:

1. czy dwie linie są blisko siebie geometrycznie,
2. czy istnieje sensowny kandydat połączenia między ich realnymi przedziałami pokrycia,
3. czy w binarce naprawdę jest materiał łączący oba końce,
4. czy ten materiał tworzy ciągłą strukturę wzdłuż kierunku mostu,
5. czy z tego da się zbudować sensowny segment, który potem można scalić z liniami logicznymi.

To właśnie sprawia, że bridge repair jest jednym z najważniejszych i najbardziej zaawansowanych fragmentów obecnego pipeline'u.
