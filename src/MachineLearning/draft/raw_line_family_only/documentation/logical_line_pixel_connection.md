# Raw Line Family Only - pixel connection

## Cel

Ten dokument opisuje etap pixel-validated connection wykonywany po
`post_merge`, ale jeszcze przed intersection analysis.

## Główne pliki

- `logical_line_connections.py`
- `logical_line_connection_candidates.py`
- `logical_line_connection_execution.py`
- `logical_line_connection_types.py`
- `logical_line_search.py`
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
- po sukcesie może scalić całe logical lines.

`CROSS_AXIS`

- próbuje połączyć koniec linii z wierzchołkiem linii prostopadłej,
- dodaje segmenty połączenia, ale nie scala obu linii w jedną.

`CROSS_AXIS_SPAN`

- próbuje połączyć koniec linii z punktem na ciele linii prostopadłej,
- używa punktów celu wybranych z fragmentu linii mieszczącego się w
  prostokącie tolerancji.

## Wyszukiwanie ścieżki

Silnik wyszukiwania jest w `logical_line_search.py`.

Najważniejsze założenia:

- ścieżka jest szukana po białych pikselach,
- wyszukiwanie odbywa się w ograniczonym `SearchArea`,
- dla części kandydatów kod próbuje najpierw prostego łącznika,
- jeśli to się nie uda, używany jest BFS.

Ten sam moduł zawiera też helpery wykorzystywane poza samym connection, między
innymi przez containment i merge po wierzchołku.

## Wynik connection

Po znalezieniu ścieżki kod dodaje segmenty:

- `SAME_AXIS_CONNECTION`
- `CROSS_AXIS_CONNECTION`

Są to pełnoprawne `LineSegment`, które później:

- pozostają w `line_segments`,
- biorą udział w sortowaniu,
- mogą wpływać na `start_segment` i `end_segment`,
- są widoczne w overlayach i raporcie.

## Znaczenie stanu `post_connection`

Po connection kod klonuje stan linii i zapisuje:

- `horizontal_post_connection_logical_lines`
- `vertical_post_connection_logical_lines`

To jest snapshot:

- po connection,
- przed intersection pruning,
- przed finalnym wyborem ramki.

## Ważna konwencja pikselowa

Piksel jest atomowy również na tym etapie.

Jeśli segment kończy się na `axis_end == 566`, to następny segment zaczynający
się od `axis_start == 567` oznacza naturalną kontynuację na następnym pikselu,
a nie overlap na tym samym pikselu osi.
