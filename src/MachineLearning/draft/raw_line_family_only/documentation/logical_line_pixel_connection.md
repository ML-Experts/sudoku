# Raw Line Family Only - pixel connection

## Cel

Ten dokument opisuje etap pixel-validated connection wykonywany po
`post_merge`, który domyka geometrię aktywnego lifecycle linii przed etapem
zbierania intersections.

## Główne pliki

- `logical_line_connections.py`
- `logical_line_connection_candidates.py`
- `logical_line_connection_execution.py`
- `logical_line_connection_types.py`
- `logical_line_search.py`
- `logical_line_search_area.py`
- `logical_line_search_window_points.py`
- `logical_line_search_goals.py`
- `logical_line_search_pathfinding.py`
- `logical_line_core.py`

## Wejście do etapu

Na wejściu connection trafiają:

- `horizontal_post_merge_logical_lines`
- `vertical_post_merge_logical_lines`
- `pixel_connection_binary`

W pipeline `pixel_connection_binary` jest zwykle równe `repaired_binary`.

To ważne rozdzielenie:

- detekcja rodzin startuje z `clean_binary`,
- walidacja po pikselach odbywa się na `repaired_binary`.

## Cel etapu

Merge geometryczny opiera się na lokalnych tolerancjach osi.

Pixel connection próbuje dodatkowo udowodnić, że dwa końce linii da się połączyć
ścieżką po białych pikselach.

W aktualnym kodzie etap ten ma dwie różne semantyki:

- dla `SAME_AXIS` znaleziona ścieżka po białych pikselach jest dalej używana jako
  geometria finalnego connection,
- dla `CROSS_AXIS` i `CROSS_AXIS_SPAN` ścieżka po białych pikselach służy już
  tylko do walidacji kontaktu, a finalny connector jest budowany jako jedno
  możliwie prostoliniowe dociągnięcie z minimalnym skrętem względem końcowego
  segmentu `LogicalLine`.

## `ToleranceRectangle`

Dla końców linii budowane są `ToleranceRectangle` przez
`LogicalLine.build_tolerance_rectangle(...)`.

Prostokąt zawiera:

- `reference_point`
- `recognition_vector`
- `vector_length`
- `padding`

To jest obszar:

- rozpoznawania kandydatów do połączenia,
- wyznaczania punktów celu dla wyszukiwania ścieżki.

## `ConnectionKind`

Aktualne typy kandydatów:

- `SAME_AXIS`
- `CROSS_AXIS`
- `CROSS_AXIS_SPAN`

Priorytet sortowania kandydatów:

1. `SAME_AXIS`
2. `CROSS_AXIS`
3. `CROSS_AXIS_SPAN`

W ramach tego samego typu pierwszeństwo ma mniejszy `distance_px`.

## Znaczenie typów połączeń

`SAME_AXIS`

- próbuje połączyć dwa końce linii tej samej rodziny,
- po sukcesie może scalić całe logical lines,
- używa wyszukanej ścieżki jako geometrii finalnego connection.

`CROSS_AXIS`

- próbuje połączyć koniec linii z wierzchołkiem linii prostopadłej,
- wymaga walidacji po obu stronach połączenia,
- po sukcesie dodaje po jednym connectorze do wspólnego punktu spotkania,
- nie scala obu linii w jedną.

`CROSS_AXIS_SPAN`

- próbuje połączyć koniec linii z punktem na ciele linii prostopadłej,
- używa punktów celu wybranych z fragmentu linii mieszczącego się w
  prostokącie tolerancji,
- wybiera punkt kontaktu minimalizujący zmianę kąta względem końcowego
  segmentu źródłowej linii.

## Wyszukiwanie ścieżki

Po refaktorze `logical_line_search.py` jest cienką fasadą kompatybilności.

Właściwa logika została rozdzielona według odpowiedzialności:

- `logical_line_search_area.py`
  - budowa `SearchArea` i test przynależności punktu do maski
- `logical_line_search_window_points.py`
  - zbieranie białych punktów z segmentów i całych `LogicalLine`
  - budowa `start_points`
- `logical_line_search_goals.py`
  - budowa punktów celu dla `same_axis`, `cross_axis` i `cross_axis_span`
- `logical_line_search_pathfinding.py`
  - straight path i BFS używane do walidacji lub budowy connection zależnie od
    typu kandydata

Publiczne entrypointy używane przez stage connection nadal mogą być importowane
przez `logical_line_search.py`, ale implementacja nie jest już monolitem.

Najważniejsze założenia:

- ścieżka jest szukana po białych pikselach,
- wyszukiwanie odbywa się w ograniczonym `SearchArea`,
- dla części kandydatów kod próbuje najpierw prostego łącznika,
- `SAME_AXIS` może materializować ścieżkę BFS jako segmenty connection,
- `CROSS_AXIS` i `CROSS_AXIS_SPAN` używają BFS tylko do potwierdzenia, że
  kontakt jest lokalnie możliwy,
- po walidacji `cross_axis` finalna geometria connection jest wybierana tak,
  żeby robić możliwie mało skrętów i maksymalnie zachować kierunek końcowego
  segmentu.

Helper point-to-line używany poza samym connection, między innymi przez
continuity dla containment i merge po wierzchołku, jest teraz wydzielony do
`logical_line_search_point_to_line.py`.

## Wynik connection

Po wykonaniu connection kod może dodać segmenty:

- `SAME_AXIS_CONNECTION`
- `CROSS_AXIS_CONNECTION`

Są to pełnoprawne `LineSegment`, które później:

- pozostają w `line_segments`,
- biorą udział w sortowaniu,
- mogą wpływać na `start_segment` i `end_segment`,
- są widoczne w overlayach i raporcie.

Ważne rozróżnienie:

- dla `SAME_AXIS_CONNECTION` segmenty mogą odtwarzać realną trasę znalezioną po
  białych pikselach,
- dla `CROSS_AXIS_CONNECTION` segmenty są dziś kontrolowanymi dociągnięciami
  geometrycznymi i nie odwzorowują łamanej ścieżki BFS jeden do jednego.

## Znaczenie stanu `post_connection`

Po connection kod klonuje stan linii i zapisuje:

- `horizontal_post_connection_logical_lines`
- `vertical_post_connection_logical_lines`

To jest snapshot:

- po connection,
- przed budową aktywnych intersections i finalnych prostokątów tolerancji,
- zgodny z finalną geometrią linii w `horizontal_logical_lines` i
  `vertical_logical_lines`.

W aktualnej wersji eksperymentu:

- `horizontal_post_connection_logical_lines` i
  `vertical_post_connection_logical_lines` to jawny snapshot diagnostyczny,
- `horizontal_logical_lines` i `vertical_logical_lines` oznaczają już finalny
  wynik etapu detekcji,
- po connection działa aktywne zbieranie `logical_line_intersections`,
- nie ma dalszego aktywnego etapu `intersection/frame`, który zmieniałby te
  linie po connection albo wybierał ramkę planszy.

## Co dzieje się po connection

Po zapisaniu snapshotu `post_connection` kod:

- traktuje `horizontal_logical_lines` i `vertical_logical_lines` jako finalną
  geometrię linii,
- buduje `logical_line_intersections` na parach finalnych linii poziomych i
  pionowych,
- dopiero potem buduje `horizontal_tolerance_rectangles` i
  `vertical_tolerance_rectangles`.

To rozdzielenie jest ważne:

- connection nadal odpowiada za geometrię linii,
- intersections nie modyfikują jeszcze linii, tylko opisują wykryte punkty,
- przyszły etap naprawy granic może używać `kind`, `horizontal_order` i
  `vertical_order`, ale nie jest jeszcze częścią aktywnego kodu.

## Ważna konwencja pikselowa

Piksel jest atomowy również na tym etapie.

Jeśli segment kończy się na `axis_end == 566`, to następny segment zaczynający
się od `axis_start == 567` oznacza naturalną kontynuację na następnym pikselu,
a nie overlap na tym samym pikselu osi.
