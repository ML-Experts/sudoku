# Raw Line Family Only - indeks procesu

## Cel

Ten plik jest krótkim punktem wejścia do aktualnej dokumentacji eksperymentu
`raw_line_family_only`.

Dokumentacja została rozbita na kilka plików, bo obecny pipeline obejmuje już
więcej niż samo budowanie `LogicalLine`:

- preprocessing obrazu,
- detekcję rodzin linii,
- budowę i grupowanie `LogicalLine`,
- containment prune linii zawartych,
- pixel-validated connection,
- analizę przecięć,
- wybór ramki planszy,
- wizualizacje i raportowanie artefaktów notebooka.

Jeśli opis dokumentów i implementacja rozjeżdżają się ze sobą, źródłem prawdy
jest aktualny kod w tym katalogu, przede wszystkim:

- `raw_line_family_only_pipeline.py`
- `raw_line_family_only_detection.py`
- `raw_line_family_only_logical_line_core.py`
- moduły `raw_line_family_only_logical_line_*`
- moduły `raw_line_family_only_intersection_*`

## Mapa dokumentów

### 1. Pipeline i artefakty notebooka

Plik: `raw_line_family_only_pipeline_overview.md`

Zakres:

- bootstrap notebooka i reload modułów,
- preprocessing obrazu,
- dwa przebiegi `detect_line_families(...)`,
- `RawLineFamilyArtifacts`,
- raport tekstowy i lista plotów.

### 2. Lifecycle `LogicalLine`

Plik: `raw_line_family_only_logical_line_lifecycle.md`

Zakres:

- modele domenowe i konfiguracja,
- budowa linii z segmentów Hougha,
- merge geometryczny,
- grouping segmentów `RAW`,
- containment prune,
- pixel connection,
- znaczenie `SegmentOrigin`, `ConnectionKind` i `RawSegmentGroupStatus`.

### 3. Przecięcia, ramka i wizualizacje

Plik: `raw_line_family_only_intersections_and_visualization.md`

Zakres:

- analiza przecięć między rodzinami,
- pruning i ordering,
- kandydaci ramki i wybór najlepszej ramki,
- `frame_side`,
- aktualne overlaye i plansze debugowe.

## Skrócony przepływ end-to-end

Aktualny przebieg eksperymentu wygląda następująco:

1. Notebook ładuje API przez `raw_line_family_only_bootstrap.py`.
2. `run_raw_line_family_pipeline(...)` wykonuje preprocessing:
   - grayscale,
   - median denoise,
   - adaptive threshold,
   - soft component cleanup,
   - directional close repair.
3. Pipeline uruchamia `detect_line_families(...)` dwa razy:
   - pierwszy raz tylko do overlayu rodzin linii na `clean_binary`,
   - drugi raz do pełnej detekcji z pixel connection na `repaired_binary`.
4. W pełnej detekcji:
   - Hough zwraca surowe segmenty,
   - segmenty są klasyfikowane do rodzin poziomych i pionowych,
   - powstają wstępne `LogicalLine`,
   - wykonywany jest grouping segmentów `RAW`,
   - wykonywany jest containment prune linii zawartych w innych liniach tej samej rodziny,
   - wykonywany jest pixel connection,
   - uruchamiana jest analiza przecięć i wybór ramki,
   - budowane są finalne prostokąty tolerancji.
5. Pipeline zwraca `RawLineFamilyArtifacts` z obrazami pośrednimi, overlayami,
   boardami i wynikiem domenowym.

## Aktualne stany pośrednie

Najważniejsze kolekcje trzymane w `RawLineFamilyResult`:

- `horizontal_segments`
- `vertical_segments`
- `horizontal_pre_connection_logical_lines`
- `vertical_pre_connection_logical_lines`
- `horizontal_containment_prune_result`
- `vertical_containment_prune_result`
- `horizontal_post_connection_logical_lines`
- `vertical_post_connection_logical_lines`
- `horizontal_logical_lines`
- `vertical_logical_lines`
- `logical_line_intersections`
- `logical_line_border_pairs`
- `logical_line_frames`

Interpretacja:

- `pre_connection` oznacza stan po grouping segmentów `RAW`,
- `horizontal_containment_prune_result` i `vertical_containment_prune_result`
  opisują etap containment prune pomiędzy grouping `RAW` a pixel connection,
- `post_connection` oznacza stan po pixel connection i przed intersection pruning,
- kolekcje bez prefiksu `pre/post` oznaczają stan finalny po analizie przecięć
  i wyborze ramki.

## Najważniejsze aktualizacje względem starszego opisu

Poprzedni dokument opisywał starszy stan eksperymentu. W aktualnym kodzie:

- nie ma już `SegmentOrigin.TOLERANCE`,
- istnieją tylko `RAW`, `SAME_AXIS_CONNECTION`, `CROSS_AXIS_CONNECTION`,
- grouping `RAW` jest osobnym etapem między `build_logical_lines(...)`
  a pixel connection,
- containment prune jest osobnym etapem między grouping `RAW`
  a pixel connection,
- pixel connection ma trzy klasy kandydatów:
  `same_axis`, `cross_axis`, `cross_axis_span`,
- analiza przecięć i wybór ramki są osobnym etapem po connection,
- wizualizacje obejmują więcej niż tylko rodziny, logical lines
  i tolerance rectangles.

## Mapa odpowiedzialności modułów

- `raw_line_family_only_bootstrap.py`
  - ładowanie API do notebooka i kontrolowany reload modułów
- `raw_line_family_only_pipeline.py`
  - główna orkiestracja preprocessingu i budowy artefaktów
- `raw_line_family_only_detection.py`
  - pełna orkiestracja detekcji rodzin, `LogicalLine` i intersections
- `raw_line_family_only_logical_lines.py`
  - publiczna fasada dla budowy i pixel connection linii logicznych
- `raw_line_family_only_logical_line_core.py`
  - główny obiekt domenowy `LogicalLine`
- `raw_line_family_only_raw_segment_grouping.py`
  - grouping segmentów `RAW` i naprawa granic grup
- `raw_line_family_only_logical_line_containment.py`
  - containment prune i grupowanie linii po ciągłości osi poprzecznej
- `raw_line_family_only_logical_line_connections.py`
  - pixel-validated connection
- `raw_line_family_only_visualization_containment.py`
  - overlaye i boardy dla containment prune
- `raw_line_family_only_intersections.py`
  - publiczna fasada dla intersections, pruning i frame selection
- `raw_line_family_only_visualization.py`
  - agregacja funkcji renderujących
- `raw_line_family_only_pipeline_report.py`
  - tekstowy opis artefaktów i stanów pośrednich
- `raw_line_family_only_pipeline_plots.py`
  - kolejność i nazwy obrazów pokazywanych w notebooku

## Kolejność czytania

Jeśli chcesz szybko zrozumieć system, czytaj w tej kolejności:

1. `raw_line_family_only_pipeline_overview.md`
2. `raw_line_family_only_logical_line_lifecycle.md`
3. `raw_line_family_only_intersections_and_visualization.md`
