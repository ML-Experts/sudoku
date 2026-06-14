# Raw Line Family Only - intersection analysis i frame selection

## Cel

Ten dokument opisuje końcowy etap domenowy wykonywany po pixel connection:

- analizę przecięć,
- pruning linii po liczbie przecięć,
- ordering przecięć,
- budowę kandydatów ramki,
- wybór najlepszej ramki,
- przypisanie `frame_side`.

## Główne pliki

- `intersections.py`
- `intersection_analysis.py`
- `intersection_candidates.py`
- `intersection_models.py`
- `intersection_ordering.py`
- `intersection_pruning.py`
- `intersection_frame.py`
- `intersection_segment_geometry.py`

## Wejście do etapu intersections

Do `analyze_logical_line_intersections(...)` trafiają:

- `horizontal_post_connection_logical_lines`
- `vertical_post_connection_logical_lines`

Są to linie już po:

- merge geometrycznym,
- grouping `RAW`,
- full containment prune,
- vertex containment merge,
- pixel connection.

## Modele intersections

### `LogicalLineIntersectionKind`

Możliwe typy przecięcia:

- `CROSS`
- `TOUCH`

Interpretacja:

- `CROSS` oznacza przecięcie wewnątrz obu segmentów,
- `TOUCH` oznacza kontakt na końcu któregoś segmentu lub wspólnym punkcie
  granicznym.

### `IntersectionOrder`

Po przypisaniu kolejności przecięć wzdłuż osi linii możliwe są wartości:

- `NONE`
- `START`
- `MIDDLE`
- `END`
- `BOTH`

### `LogicalLineIntersection`

Najważniejsze pola:

- `ref_horizontal_line`
- `ref_vertical_line`
- `ref_horizontal_segment`
- `ref_vertical_segment`
- `point`
- `kind`
- `horizontal_order`
- `vertical_order`

Najważniejsze właściwości pochodne:

- `is_horizontal_boundary`
- `is_vertical_boundary`
- `is_mutual_boundary`

### `LogicalLineBorderPair`

Reprezentuje jedną linię i zbiór linii, z którymi tworzy przecięcia będące
wspólnymi granicami.

### `LogicalLineFrame`

Reprezentuje kandydata ramki przez cztery linie:

- `top_line`
- `bottom_line`
- `left_line`
- `right_line`

### `LogicalLineIntersectionAnalysis`

Finalny wynik etapu intersections:

- `frame`
- `horizontal_lines`
- `vertical_lines`
- `intersections`

## Etap 1. Zbieranie kandydatów przecięć

`analyze_logical_line_intersections(...)` zaczyna od:

- `_clear_logical_line_metadata(...)`
- `_collect_candidate_intersections(...)`

Na tym etapie kod:

- czyści stare metadata linii,
- przegląda pary pozioma linia x pionowa linia,
- znajduje kandydatów przecięć na poziomie segmentów.

## Etap 2. Wstępny pruning po minimum przecięć

Pierwszy pruning jest wykonywany z progiem:

- `minimum_intersection_count = 2`

Znaczenie:

- linia z mniej niż dwoma przecięciami nie może sensownie uczestniczyć w dalszej
  analizie siatki,
- pruning jest iteracyjny, więc usunięcie jednej linii może obniżyć liczby
  przecięć kolejnych linii.

## Etap 3. Ordering i boundary classification

Po wstępnym pruning kod:

- buduje lookup kandydatów,
- przypisuje kolejność przecięć osobno dla rodzin `HORIZONTAL` i `VERTICAL`.

To właśnie tutaj intersection może zostać oznaczony jako:

- `START`
- `MIDDLE`
- `END`
- `BOTH`

Na tej podstawie później wyznaczane są przecięcia brzegowe i mutual boundary
intersections.

## Etap 4. Budowa kandydatów ramki

Funkcja `_find_logical_line_frames(...)` działa na grafie zbudowanym z
przecięć `is_mutual_boundary`.

Najważniejszy pomysł:

- linie są węzłami,
- sąsiedztwo istnieje wtedy, gdy dwie linie mają mutual boundary intersection,
- kod szuka cyklu złożonego z czterech różnych linii:
  - horizontal
  - vertical
  - horizontal
  - vertical

Po znalezieniu czterech linii:

- poziome są sortowane na `top_line` i `bottom_line`,
- pionowe są sortowane na `left_line` i `right_line`.

## Etap 5. Wybór najlepszej ramki

Wśród kandydatów `_select_best_frame(...)` wybiera jedną ramkę.

Kryteria są dwa:

1. minimalizacja sumy odchyleń liczby przecięć od wartości `10` dla każdej
   linii ramki
2. przy remisie preferowana jest większa powierzchnia ramki

## Etap 6. Drugi pruning po wyborze ramki

Po wyborze ramki wykonywany jest drugi pruning:

- `minimum_intersection_count = 10`

Linie należące do wybranej ramki są chronione przez `protected_line_keys`, więc
nie wypadają z wyniku nawet wtedy, gdy po redukcji pozostałych linii ich liczba
przecięć chwilowo spadnie.

## Etap 7. Publiczne intersections i `frame_side`

Po końcowym pruning:

- budowana jest finalna lista `LogicalLineIntersection`,
- na liniach ramki ustawiane jest:
  - `FrameSide.TOP`
  - `FrameSide.BOTTOM`
  - `FrameSide.LEFT`
  - `FrameSide.RIGHT`

Wszystkie pozostałe linie zachowują:

- `FrameSide.NONE`

## Border pairs

`find_logical_line_border_pairs(...)` buduje uporządkowaną listę
`LogicalLineBorderPair` na podstawie mutual boundary intersections.

To jest osobny artefakt diagnostyczny pokazujący, które linie były kandydatami
sąsiedztwa brzegowego jeszcze przed wyborem jednej ramki.

## Co trafia do wyniku detekcji

Po zakończeniu etapu `detect_line_families(...)` zapisuje:

- `logical_line_intersection_analysis`
- `logical_line_intersections`
- `logical_line_border_pairs`
- `logical_line_frames`

oraz podmienia finalne kolekcje:

- `horizontal_logical_lines`
- `vertical_logical_lines`

na linie po intersection analysis i pruning.
