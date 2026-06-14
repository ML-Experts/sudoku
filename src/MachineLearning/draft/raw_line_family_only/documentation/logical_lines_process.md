# Raw Line Family Only - indeks procesu

## Cel

Ten plik jest krótkim punktem wejścia do aktualnej dokumentacji eksperymentu
`raw_line_family_only`.

Po refaktorze kod w tym katalogu używa już krótkich nazw plików bez prefiksu
`raw_line_family_only_`, ale sam wariant eksperymentu nadal nazywa się
`raw_line_family_only`.

Dokumentacja obejmuje dziś cały przepływ:

- preprocessing obrazu,
- detekcję rodzin linii,
- budowę i grupowanie `LogicalLine`,
- full containment prune,
- vertex containment merge,
- pixel-validated connection,
- analizę przecięć,
- wybór ramki planszy,
- wizualizacje i raportowanie artefaktów notebooka.

Jeśli opis dokumentów i implementacja rozjeżdżają się ze sobą, źródłem prawdy
jest aktualny kod w tym katalogu, przede wszystkim:

- `pipeline.py`
- `detection.py`
- `logical_line_core.py`
- moduły `logical_line_*`
- moduły `intersection_*`
- moduły `visualization_*`

## Mapa dokumentów

### 1. Pipeline i artefakty notebooka

Plik: `pipeline_overview.md`

Zakres:

- bootstrap notebooka i reload modułów,
- preprocessing obrazu,
- dwa przebiegi `detect_line_families(...)`,
- `RawLineFamilyArtifacts`,
- raport tekstowy i lista plotów.

### 2. Lifecycle `LogicalLine`

Plik indeksowy: `logical_line_lifecycle.md`

Pliki szczegółowe:

- `logical_line_build_and_grouping.md`
- `logical_line_containment_and_vertex_merge.md`
- `logical_line_pixel_connection.md`

Zakres:

- modele domenowe i konfiguracja,
- budowa linii z segmentów Hougha,
- merge geometryczny,
- grouping segmentów `RAW`,
- full containment prune,
- vertex containment merge,
- pixel connection,
- znaczenie `SegmentOrigin`, `ConnectionKind` i `RawSegmentGroupStatus`.

### 3. Przecięcia, ramka i wizualizacje

Plik indeksowy: `intersections_and_visualization.md`

Pliki szczegółowe:

- `intersection_analysis_and_frame_selection.md`
- `visualization_and_artifacts.md`

Zakres:

- analiza przecięć między rodzinami,
- pruning i ordering,
- kandydaci ramki i wybór najlepszej ramki,
- `frame_side`,
- aktualne overlaye i plansze debugowe.

## Skrócony przepływ end-to-end

Aktualny przebieg eksperymentu wygląda następująco:

1. Notebook `experiment.ipynb` ładuje API przez `bootstrap.load_api()`.
2. Pipeline wykonuje preprocessing:
   - grayscale,
   - median denoise,
   - adaptive threshold,
   - soft component cleanup,
   - directional close repair.
3. `detect_line_families(...)` jest uruchamiane dwa razy:
   - pierwszy raz tylko do overlayu rodzin linii na `clean_binary`,
   - drugi raz do pełnej detekcji z pixel connection na `repaired_binary`.
4. W pełnej detekcji:
   - Hough zwraca surowe segmenty,
   - segmenty są klasyfikowane do rodzin poziomych i pionowych,
   - powstają wstępne `LogicalLine`,
   - wykonywany jest grouping segmentów `RAW`,
   - wykonywany jest full containment prune,
   - wykonywany jest vertex containment merge,
   - wykonywany jest pixel connection,
   - uruchamiana jest analiza przecięć i wybór ramki,
   - budowane są finalne prostokąty tolerancji.
5. Pipeline albo notebook buduje `RawLineFamilyArtifacts` z obrazami pośrednimi,
   overlayami, boardami i wynikiem domenowym.

## Aktualne stany pośrednie

Najważniejsze kolekcje i wyniki trzymane w `RawLineFamilyResult`:

- `horizontal_segments`
- `vertical_segments`
- `horizontal_pre_connection_logical_lines`
- `vertical_pre_connection_logical_lines`
- `horizontal_containment_prune_result`
- `vertical_containment_prune_result`
- `horizontal_vertex_containment_merge_result`
- `vertical_vertex_containment_merge_result`
- `horizontal_post_merge_logical_lines`
- `vertical_post_merge_logical_lines`
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
  opisują etap full containment prune,
- `horizontal_vertex_containment_merge_result` i
  `vertical_vertex_containment_merge_result` opisują etap merge'u linii
  częściowo zawartych przez wierzchołek,
- `post_merge` oznacza stan po `vertex containment merge`, ale jeszcze przed
  pixel connection,
- `post_connection` oznacza stan po pixel connection i przed intersection
  pruning,
- kolekcje bez prefiksu `pre/post` oznaczają stan finalny po analizie przecięć
  i wyborze ramki.

## Najważniejsze aktualizacje względem starszego opisu

Poprzedni opis był częściowo zgodny ze stanem sprzed refaktoru. W aktualnym
kodzie:

- nie ma już nazw plików z prefiksem `raw_line_family_only_`,
- bootstrap eksportuje `load_api()` i zwraca obiekt `Api`,
- nie ma już `SegmentOrigin.TOLERANCE`,
- istnieją tylko `RAW`, `SAME_AXIS_CONNECTION`, `CROSS_AXIS_CONNECTION`,
- grouping `RAW` jest osobnym etapem między `build_logical_lines(...)`
  a containment prune,
- po full containment prune jest osobny etap `vertex containment merge`,
- pixel connection ma trzy klasy kandydatów:
  `same_axis`, `cross_axis`, `cross_axis_span`,
- analiza przecięć i wybór ramki są osobnym etapem po connection,
- wizualizacje obejmują więcej niż tylko rodziny, logical lines
  i tolerance rectangles.

## Mapa odpowiedzialności modułów

- `bootstrap.py`
  - ładowanie API do notebooka i kontrolowany reload modułów
- `pipeline.py`
  - główna orkiestracja preprocessingu i budowy artefaktów
- `pipeline_artifacts.py`
  - model `RawLineFamilyArtifacts`
- `pipeline_report.py`
  - tekstowy opis artefaktów i stanów pośrednich
- `pipeline_plots.py`
  - kolejność i nazwy obrazów pokazywanych w notebooku
- `pipeline_selection.py`
  - wybór aktywnego obrazu datasetowego lub ręcznie podanej ścieżki
- `detection.py`
  - pełna orkiestracja detekcji rodzin, `LogicalLine` i intersections
- `logical_lines.py`
  - publiczna fasada dla budowy i pixel connection linii logicznych
- `logical_line_core.py`
  - główny obiekt domenowy `LogicalLine`
- `raw_segment_grouping.py`
  - grouping segmentów `RAW` i naprawa granic grup
- `logical_line_full_containment.py`
  - full containment prune
- `logical_line_vertex_containment_merge.py`
  - merge linii częściowo zawartych przez wierzchołek
- `logical_line_cross_axis_continuity.py`
  - grupowanie linii po ciągłości osi poprzecznej
- `logical_line_connections.py`
  - pixel-validated connection
- `intersections.py`
  - publiczna fasada dla intersections, pruning i frame selection
- `visualization.py`
  - agregacja funkcji renderujących
- `visualization_containment.py`
  - overlaye i boardy dla full containment prune
- `visualization_vertex_containment_merge.py`
  - overlaye i boardy dla `vertex containment merge`

## Kolejność czytania

Jeśli chcesz szybko zrozumieć system, czytaj w tej kolejności:

1. `pipeline_overview.md`
2. `logical_line_lifecycle.md`
3. `logical_line_build_and_grouping.md`
4. `logical_line_containment_and_vertex_merge.md`
5. `logical_line_pixel_connection.md`
6. `intersections_and_visualization.md`
7. `intersection_analysis_and_frame_selection.md`
8. `visualization_and_artifacts.md`
