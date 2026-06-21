# Raw Line Family Only - containment i merge po wierzchołku

## Cel

Ten dokument opisuje dwa etapy wykonywane po grouping segmentów `RAW` i przed
pixel connection:

- full containment prune,
- vertex containment merge.

Oba etapy pracują na liniach jednej rodziny i korzystają z tej samej logiki
ciągłości osi poprzecznej.

## Główne pliki

- `logical_line_full_containment.py`
- `logical_line_vertex_containment_merge.py`
- `logical_line_cross_axis_continuity.py`
- `logical_line_search.py`
- `logical_line_search_point_to_line.py`
- `logical_line_debug.py`

## Wspólna idea

Po grouping `RAW` pipeline ma już czytelniejsze `LogicalLine`, ale nadal może
mieć:

- linie w pełni zduplikowane przez dłuższą linię tej samej rodziny,
- linie częściowo wpadające swoim wierzchołkiem w zakres osi dłuższej linii,
- linie rozbite na kilka bliskich reprezentacji po tej samej stronie planszy.

Z tego powodu przed pixel connection wykonywane są dwa osobne etapy:

1. najpierw usuwanie linii w pełni zawartych,
2. potem merge linii częściowo zawartych przez wierzchołek.

## Grupowanie po osi poprzecznej

Wspólna logika grupowania jest w `logical_line_cross_axis_continuity.py`.

Najważniejszy model:

- `LogicalLineCrossAxisGroup`

Najważniejsze pola:

- `cross_axis_start`
- `cross_axis_end`
- `anchor_line`
- `grouped_logical_lines`
- `grouped_logical_line_ids`

Linie są uznawane za spójne na osi poprzecznej, jeśli zachodzi co najmniej jeden
z warunków:

- mały dystans na osi poprzecznej,
- overlap zakresu osi poprzecznej,
- znalezienie ścieżki po białych pikselach od wierzchołka kandydata do
  `anchor_line`.

Do walidacji po pikselach używany jest helper point-to-line z
`logical_line_search_point_to_line.py`.

`logical_line_search.py` pozostał jako cienka fasada kompatybilności dla
publicznych importów search-related helperów.

## Etap 1. Full containment prune

Publiczny entrypoint:

- `prune_logical_lines_by_full_axis_containment(...)`

### Cel etapu

Etap próbuje usunąć takie `LogicalLine`, które:

- są w pełni zawarte na osi głównej wewnątrz dłuższej linii tej samej rodziny,
- są spójne z tą dłuższą linią na osi poprzecznej,
- nie wnoszą nowej wartości do dalszych etapów.

### Predykat osiowy

Predykat containment jest zdefiniowany przez:

- `logical_line_is_contained_on_axis(...)`

Warunek:

- `container_line.axis_start <= candidate_line.axis_start`
- `candidate_line.axis_end <= container_line.axis_end`

### Wynik etapu

Etap zwraca:

- `PruneContainedLogicalLinesResult`

Najważniejsze pola:

- `input_logical_lines`
- `pruned_logical_lines`
- `removed_logical_lines`
- `cross_axis_groups`

### Jak działa heurystyka

1. linie są sortowane malejąco po `axis_length`
2. najdłuższa linia staje się `anchor_line`
3. zbierane są linie w pełni zawarte w jej `axis_start..axis_end`
4. kandydaci są grupowani po ciągłości osi poprzecznej
5. linie uznane za zawarte trafiają do `removed_logical_lines`
6. kandydaci odrzuceni przez continuity wracają do puli
7. proces powtarza się dla kolejnych `anchor_line`

## Stan diagnostyczny po full containment prune

`detect_line_families(...)` zapisuje wynik tego etapu osobno jako:

- `horizontal_containment_prune_result`
- `vertical_containment_prune_result`

To nie jest tylko kolejny snapshot listy linii, ale pełny wynik diagnostyczny
z grupami continuity.

## Etap 2. Vertex containment merge

Publiczny entrypoint:

- `merge_logical_lines_by_vertex_axis_containment(...)`

### Cel etapu

Etap próbuje scalić takie `LogicalLine`, które:

- należą do tej samej rodziny,
- przeszły już przez full containment prune,
- mają jeden z końców wpadający w zakres osi dłuższej linii,
- są wystarczająco spójne na osi poprzecznej, żeby traktować je jako jedną
  linię.

### Predykat osiowy

Predykat jest zdefiniowany przez:

- `logical_line_is_vertex_contained_on_axis(...)`

W aktualnym kodzie kandydat trafia do etapu merge'u, jeśli:

- `candidate_line.axis_start` mieści się w zakresie `container_line`, albo
- `candidate_line.axis_end` mieści się w zakresie `container_line`.

### Wynik etapu

Etap zwraca:

- `MergeVertexContainedLogicalLinesResult`

Najważniejsze pola:

- `input_logical_lines`
- `merged_logical_lines`
- `consumed_logical_lines`
- `merge_groups`

Każdy `merge_group` jest reprezentowany przez `LogicalLineCrossAxisGroup`.

### Jak działa heurystyka

1. linie są sortowane malejąco po `axis_length`
2. najdłuższa linia staje się `anchor_line`
3. kandydaci z trafieniem w zakres osi `anchor_line` trafiają do weryfikacji
4. continuity na osi poprzecznej odrzuca kandydatów pozornie bliskich
5. `anchor_line.merge_logical_line(...)` scala segmenty skonsumowanych linii
6. po merge'u uruchamiane jest ponownie `group_raw_segments(...)`, żeby
   odświeżyć reprezentację segmentów `RAW`

## Znaczenie stanu `post_merge`

Po vertex containment merge kod zapisuje snapshot:

- `horizontal_post_merge_logical_lines`
- `vertical_post_merge_logical_lines`

To jest stan:

- po full containment prune,
- po merge'u po wierzchołku,
- przed dodawaniem segmentów connection.

## Ważna konwencja pikselowa

Tak jak w reszcie pipeline'u piksel jest atomowy.

Jeśli jedna linia kończy się na `axis_end == 566`, a druga zaczyna na
`axis_start == 567`, to taka relacja oznacza bezpośrednią kontynuację po
następnym pikselu, a nie klasyczny overlap na tej samej pozycji osiowej.
