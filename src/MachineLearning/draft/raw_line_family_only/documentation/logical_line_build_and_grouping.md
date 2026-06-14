# Raw Line Family Only - budowa linii i grouping `RAW`

## Cel

Ten dokument opisuje początek lifecycle `LogicalLine`:

- modele bazowe,
- budowę wstępnych linii,
- merge geometryczny,
- grouping segmentów `RAW`,
- znaczenie stanu `pre_connection`.

## Główne pliki

- `models.py`
- `geometry.py`
- `logical_lines.py`
- `logical_line_core.py`
- `logical_line_merging.py`
- `logical_line_types.py`
- `raw_segment_grouping.py`
- `logical_line_segment_geometry.py`
- `logical_line_debug.py`

## Modele bazowe

### `ExperimentConfig`

Najważniejsze parametry dla tego etapu:

- `line_family_angle_tolerance_degrees`
- `logical_line_cross_axis_thickness_px`
- `logical_line_axis_gap_tolerance_px`
- `raw_segment_group_black_gap_tolerance_px`

### `LineFamilyName`

Rodzina segmentu:

- `UNCLASSIFIED`
- `HORIZONTAL`
- `VERTICAL`

### `SegmentOrigin`

Pochodzenie segmentu:

- `RAW`
- `SAME_AXIS_CONNECTION`
- `CROSS_AXIS_CONNECTION`

W aktualnym kodzie nie ma `SegmentOrigin.TOLERANCE`.

### `LineSegment`

Najważniejsze pola i właściwości dla tego etapu:

- `family_name`
- `start`
- `end`
- `origin`
- `axis_start`
- `axis_end`
- `cross_axis_start`
- `cross_axis_end`

Interpretacja osi zależy od rodziny:

- dla `HORIZONTAL`, oś główna to `x`,
- dla `VERTICAL`, oś główna to `y`.

## Główny obiekt domenowy

`LogicalLine` jest zdefiniowana w `logical_line_core.py`.

Najważniejsze pola:

- `family_name`
- `debug_name`
- `line_segments`
- `raw_segment_group_results`
- `start_segment`
- `end_segment`

Najważniejsze właściwości:

- `start_vertex`
- `end_vertex`
- `axis_start`
- `axis_end`
- `axis_length`
- `cross_axis_start`
- `cross_axis_end`
- `longest_segment`

Najważniejsze metody używane na tym etapie:

- `add_segment(...)`
- `replace_segments(...)`
- `clone()`
- `merge_logical_line(...)`
- `does_segment_touch(...)`
- `does_logical_line_touch(...)`
- `group_raw_segments(...)`

## Wejście do budowy `LogicalLine`

Ten etap zakłada, że `detect_line_families(...)` ma już:

- surowe segmenty z Hougha,
- oszacowaną orientację planszy,
- segmenty sklasyfikowane do rodzin poziomej i pionowej.

Na wejściu pracujemy już na:

- `horizontal_segments`
- `vertical_segments`

Każdy segment z rodziny jest wcześniej normalizowany przez
`classify_line_segment(...)`, tak aby kierunek był spójny w ramach rodziny.

## Budowa wstępnych `LogicalLine`

Publiczna fasada etapu:

- `build_logical_lines(...)` z `logical_lines.py`

Szczegóły implementacyjne:

- `logical_line_merging.py`
- `geometry.py`
- `logical_line_types.py`

Algorytm:

1. segmenty są sortowane przez `segment_sort_key(...)`
2. pierwszy segment staje się seedem nowej `LogicalLine`
3. kolejne segmenty są porównywane przez `does_segment_touch(...)`
4. jeśli segment pasuje, zostaje dodany do tej samej linii
5. jeśli nie pasuje, pozostaje do późniejszego rozpatrzenia
6. po przejściu całej listy powstaje jedna linia, a proces rusza dalej dla
   kolejnych segmentów

## Merge geometryczny segmentów i linii

`LogicalLine.does_segment_touch(...)` porównuje kandydat z każdym segmentem już
należącym do linii.

Wewnętrznie używana jest funkcja:

- `line_segments_intersect(...)` z `geometry.py`

W aktualnym eksperymencie nie chodzi tu o klasyczne przecięcie 2D, tylko o
odpowiedź na pytanie, czy dwa segmenty tej samej rodziny mogą należeć do jednej
logical line.

Sprawdzane są między innymi:

- zgodność rodziny,
- odległość na osi poprzecznej,
- przerwa na osi głównej.

Jeżeli segmenty są blisko siebie, ale mają małą przerwę na osi głównej, kod może
utworzyć `bridge_segment` z `origin=SegmentOrigin.SAME_AXIS_CONNECTION`.

Po zbudowaniu wstępnych linii wykonywany jest jeszcze merge całych linii:

- `merge_logical_lines(...)`
- `LogicalLine.does_logical_line_touch(...)`

## Ważna konwencja pikselowa

Piksel jest traktowany atomowo.

To znaczy, że jeśli jedna linia kończy się na `axis_end == 566`, to segment
zaczynający się od `axis_start == 567` jest bezpośrednią kontynuacją, a nie
overlapem ani przecięciem.

Ta konwencja obowiązuje dalej także przy interpretacji grouping, containment i
connection.

## Grouping segmentów `RAW`

To jest osobny etap wykonywany po merge geometrycznym i przed containment.

Wejście:

- lista `LogicalLine` jednej rodziny,
- `pixel_connection_binary`,
- referencyjny kąt rodziny,
- `black_gap_tolerance_px`

Publiczne wejście z poziomu obiektu:

- `LogicalLine.group_raw_segments(...)`

### Co robi grouping

Etap bierze tylko segmenty o `origin=RAW` i próbuje zamienić kilka sąsiednich
krótkich segmentów na bardziej reprezentatywny segment wyjściowy.

Przebieg:

1. z linii wybierane są tylko segmenty `RAW`
2. `collect_raw_candidate_window(...)` buduje okno kandydatów pokrywających
   ciągły zakres osi
3. `build_raw_segment_group_result(...)` buduje próbny odcinek od seed segmentu
   do najbardziej odległego poprawnego boundary segmentu
4. `find_first_invalid_black_gap_point(...)` sprawdza, czy po rastrze odcinka
   nie ma zbyt długiej czarnej przerwy
5. jeśli jest przerwa, grupa zostaje przycięta do bezpiecznej granicy
6. `repair_adjacent_raw_group_boundaries(...)` poprawia granice sąsiednich grup
7. `replace_segments(...)` zamienia oryginalne segmenty `RAW` na `output_segment`
   każdej grupy

### Wynik grouping

Szczegóły grup są trzymane w `raw_segment_group_results`.

Każdy `RawSegmentGroupResult` zawiera między innymi:

- `seed_segment`
- `consumed_segments`
- `trial_segment`
- `output_segment`
- `accepted_boundary_segment`
- `first_invalid_gap_point`
- `status`

Możliwe statusy:

- `SINGLE_SEGMENT`
- `MERGED`
- `TRIMMED_BY_BLACK_GAP`

## Znaczenie stanu `pre_connection`

`detect_line_families(...)` klonuje linie po grouping i zapisuje je jako:

- `horizontal_pre_connection_logical_lines`
- `vertical_pre_connection_logical_lines`

To jest snapshot po grouping `RAW`, ale jeszcze przed:

- full containment prune,
- vertex containment merge,
- pixel connection,
- budową finalnych prostokątów tolerancji.
