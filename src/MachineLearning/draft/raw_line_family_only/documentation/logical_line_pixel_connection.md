# Raw Line Family Only - pixel connection

## Cel

Ten dokument opisuje etap pixel-validated connection wykonywany po
`post_merge`, który domyka geometrię aktywnego lifecycle linii przed etapem
zbierania intersections i ich późniejszego trimu.

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
- preferuje najbardziej restrykcyjny wariant, w którym obie linie mają
  potwierdzoną ścieżkę po białych pikselach i można wskazać wspólny punkt
  spotkania w obu prostokątach tolerancji,
- jeśli wspólny punkt nie przechodzi, może zaakceptować obustronnie
  potwierdzony kontakt bez jednego punktu spotkania,
- dopiero na końcu akceptuje jednostronny kontakt znaleziony w jednym
  prostokącie tolerancji,
- po sukcesie dodaje connector-y odpowiadające najbardziej restrykcyjnemu
  wariantowi, który przeszedł walidację,
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
- `CROSS_AXIS` sprawdza strategie od najbardziej do najmniej restrykcyjnej:
  wspólny `meeting_point`, obustronny kontakt, jednostronny kontakt,
- `CROSS_AXIS_SPAN` używa BFS do potwierdzenia, że kontakt jest lokalnie możliwy,
- po walidacji `cross_axis` finalna geometria connection zależy od strategii,
  która jako pierwsza przeszła walidację.

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
- przed budową aktywnych intersections i przed trimem do przecięć,
- pokazujący geometrię jeszcze nieobciętą do granic wynikających z
  przecięć.

W aktualnej wersji eksperymentu:

- `horizontal_post_connection_logical_lines` i
  `vertical_post_connection_logical_lines` to jawny snapshot diagnostyczny,
- `horizontal_logical_lines` i `vertical_logical_lines` nie są już po prostu
  kopią stanu `post_connection`,
- po connection działa aktywne zbieranie `logical_line_intersections`,
- potem działa aktywny trim linii do przecięć,
- po trimie intersections są liczone ponownie na finalnej geometrii,
- nie ma dalszego aktywnego etapu `intersection/frame`, który wybierałby ramkę
  planszy.

## Co dzieje się po connection

Po zapisaniu snapshotu `post_connection` kod:

- wyznacza `logical_line_intersections` dla linii poziomych i pionowych,
- trimuje każdą linię do zakresu wyznaczonego przez skrajne przecięcia,
- ponownie wyznacza `logical_line_intersections` już dla obciętej geometrii,
- traktuje tak zaktualizowane `horizontal_logical_lines` i
  `vertical_logical_lines` jako finalny wynik etapu detekcji.

To rozdzielenie jest ważne:

- connection nadal odpowiada za geometrię linii,
- pierwszy przebieg intersections służy jako wejście do trimu,
- trim aktywnie modyfikuje geometrię linii po connection,
- drugi przebieg intersections odświeża finalny opis przecięć po trimie,
- przyszły etap dalszej analizy ramki nadal nie jest częścią aktywnego kodu.

## Co nie jest wynikiem końcowym tego etapu

`ToleranceRectangle` pozostaje ważnym narzędziem samego connection, ale
aktualny kod nie przechowuje już finalnych kolekcji typu
`horizontal_tolerance_rectangles` ani `vertical_tolerance_rectangles` w
`RawLineFamilyResult`.

## Ważna konwencja pikselowa

Piksel jest atomowy również na tym etapie.

Jeśli segment kończy się na `axis_end == 566`, to następny segment zaczynający
się od `axis_start == 567` oznacza naturalną kontynuację na następnym pikselu,
a nie overlap na tym samym pikselu osi.
