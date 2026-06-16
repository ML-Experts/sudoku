# Raw Line Family Only - lifecycle `LogicalLine`

## Cel

Ten plik jest krótką mapą etapu `LogicalLine`.

Pełna orkiestracja pipeline'u jest opisana w `pipeline_overview.md`, a ten plik
ma tylko ustawić pojęcia, snapshoty i dokumenty szczegółowe.

## Zakres lifecycle

Lifecycle `LogicalLine` obejmuje dziś:

- budowę linii z segmentów rodzin,
- merge geometryczny,
- grouping segmentów `RAW`,
- full containment prune,
- vertex containment merge,
- pixel-validated connection,
- intersections po connection,
- trim linii do przecięć i ponowne przeliczenie intersections,
- budowę grup boundary i kandydatów ramek po finalnej geometrii.

## Snapshoty i stany

Najważniejsze stany pośrednie:

- `pre_connection` - stan po grouping `RAW`,
- `post_merge` - stan po `vertex containment merge`,
- `post_connection` - stan po `pixel connection`, ale przed trimem,
- finalne `horizontal_logical_lines` i `vertical_logical_lines` - stan po trimie
  i po ponownym przeliczeniu intersections.
- `horizontal_boundary_groups`, `vertical_boundary_groups` i
  `logical_line_frame_candidates` - stan zbudowany na bazie finalnych linii i
  finalnych intersections.

Ważne:

- `LogicalLine` jest głównym nośnikiem stanu domenowego dla etapu linii,
- segmenty connection są częścią finalnej geometrii linii,
- `SegmentOrigin` ma dziś tylko `RAW`, `SAME_AXIS_CONNECTION`,
  `CROSS_AXIS_CONNECTION`.

## Dokumenty szczegółowe

### 1. Budowa i grouping

Plik: `logical_line_build_and_grouping.md`

Zakres:

- modele bazowe i `LogicalLine`,
- budowa wstępnych linii,
- merge geometryczny,
- grouping `RAW`,
- znaczenie `pre_connection`.

### 2. Containment i merge po wierzchołku

Plik: `logical_line_containment_and_vertex_merge.md`

Zakres:

- full containment prune,
- grupowanie po osi poprzecznej,
- vertex containment merge,
- znaczenie `post_merge`.

### 3. Pixel connection

Plik: `logical_line_pixel_connection.md`

Zakres:

- `ToleranceRectangle`,
- `ConnectionKind`,
- search po białych pikselach,
- semantyka `SAME_AXIS_CONNECTION` i `CROSS_AXIS_CONNECTION`,
- znaczenie `post_connection`.

### 4. Intersections i overlaye

Plik: `intersections_and_visualization.md`

Zakres:

- model `LogicalLineIntersection`,
- niezależne pola `kind` i `order`,
- trim do przecięć,
- overlay intersections i widok trimmed vs post-connection.

## Najważniejsze założenia

1. Grouping `RAW`, containment, vertex merge i pixel connection to osobne etapy.
2. `post_connection` nie jest dziś stanem finalnym.
3. Po connection działa aktywne przypisanie intersections, trim i ponowne
   przeliczenie intersections.
4. Po trimie działa aktywna budowa grup boundary i kandydatów ramek.
5. Dawny etap analizy ramki z rankingiem i `frame_side` nie wrócił do aktywnego
   pipeline'u.
