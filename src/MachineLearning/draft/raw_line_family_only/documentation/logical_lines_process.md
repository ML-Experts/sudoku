# Raw Line Family Only - indeks procesu

## Cel

Ten plik jest krótkim punktem wejścia do aktualnej dokumentacji eksperymentu
`raw_line_family_only`.

Po ostatnim uproszczeniu usunięty został etap wyboru ramki, ale do aktywnego
kodu wróciło zbieranie `logical_line_intersections`. Końcowym stanem
eksperymentu są dziś linie po `pixel connection`, po trimie do przecięć oraz
aktywne intersections policzone już na tej finalnej geometrii.

Jeśli opis dokumentów i implementacja rozjeżdżają się ze sobą, źródłem prawdy
jest aktualny kod w tym katalogu, przede wszystkim:

- `pipeline/pipeline.py`
- `detection.py`
- `logical_line_core.py`
- moduły `logical_line_*`
- moduły `visualization/*`

## Zakres aktualnej dokumentacji

Dokumentacja obejmuje dziś:

- preprocessing obrazu,
- detekcję rodzin linii,
- budowę i grupowanie `LogicalLine`,
- full containment prune,
- vertex containment merge,
- pixel-validated connection,
- zbieranie intersections po connection,
- trim linii do przecięć i ponowne przeliczenie intersections,
- wizualizacje i raportowanie artefaktów notebooka.

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

### 3. Wizualizacje i raportowanie

Pliki:

- `visualization_and_artifacts.md`
- `intersections_and_visualization.md`
- `intersection_analysis_and_frame_selection.md`

Zakres:

- aktualne overlaye i boardy debugowe,
- raport tekstowy notebooka,
- status dawnych dokumentów `intersection`.

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
   - budowane są `logical_line_intersections`,
   - wykonywany jest trim linii do przecięć,
   - intersections są przeliczane ponownie na finalnej geometrii.
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

Interpretacja:

- `pre_connection` oznacza stan po grouping segmentów `RAW`,
- `horizontal_containment_prune_result` i `vertical_containment_prune_result`
  opisują etap full containment prune,
- `horizontal_vertex_containment_merge_result` i
  `vertical_vertex_containment_merge_result` opisują etap merge'u linii
  częściowo zawartych przez wierzchołek,
- `post_merge` oznacza stan po `vertex containment merge`, ale jeszcze przed
  pixel connection,
- `post_connection` oznacza snapshot po pixel connection, ale jeszcze przed
  trimem do przecięć,
- `logical_line_intersections` oznacza aktywne przecięcia policzone na finalnej
  geometrii linii po trimie,
- kolekcje bez prefiksu `pre/post` oznaczają finalny stan detekcji, który jest
  dziś późniejszy niż sam stan po connection.

## Najważniejsze aktualizacje względem starszego opisu

W aktualnym kodzie:

- nie ma już nazw plików z prefiksem `raw_line_family_only_`,
- bootstrap eksportuje `load_api()` i zwraca obiekt `Api`,
- nie ma już `SegmentOrigin.TOLERANCE`,
- istnieją tylko `RAW`, `SAME_AXIS_CONNECTION`, `CROSS_AXIS_CONNECTION`,
- grouping `RAW` jest osobnym etapem między `build_logical_lines(...)`
  a containment prune,
- po full containment prune jest osobny etap `vertex containment merge`,
- pixel connection ma trzy klasy kandydatów:
  `same_axis`, `cross_axis`, `cross_axis_span`,
- `same_axis` może dalej materializować ścieżkę BFS jako geometrię connection,
  ale `cross_axis` używa BFS tylko do walidacji kontaktu i buduje finalne
  dociągnięcia tak, żeby minimalizować skręt,
- aktywne intersections są dziś liczone po `pixel connection`,
- po pierwszym przypisaniu intersections działa aktywny trim linii do przecięć,
- model przecięcia przechowuje niezależne `kind` oraz `order`,
- finalne intersections są przeliczane ponownie po trimie,
- nie wrócił dawny etap `intersection analysis` ani wybór ramki,
- `intersection_analysis_and_frame_selection.md` pozostał jako notatka
  historyczna o usuniętym etapie.

## Mapa odpowiedzialności modułów

- `bootstrap.py`
  - ładowanie API do notebooka, ustawienie `sys.path` dla lokalnych podkatalogów
    i kontrolowany reload modułów
- `pipeline/pipeline.py`
  - główna orkiestracja preprocessingu i budowy artefaktów
- `pipeline/pipeline_artifacts.py`
  - model `RawLineFamilyArtifacts`
- `pipeline/pipeline_report.py`
  - tekstowy opis artefaktów i stanów pośrednich
- `pipeline/pipeline_plots.py`
  - kolejność i nazwy obrazów pokazywanych w notebooku
- `pipeline/pipeline_selection.py`
  - wybór aktywnego obrazu datasetowego lub ręcznie podanej ścieżki
- `detection.py`
  - pełna orkiestracja detekcji rodzin i `LogicalLine`
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
- `intersection_model.py`
  - model `LogicalLineIntersection`, `LogicalLineIntersectionKind` i
    `IntersectionOrder`
- `logical_line_intersections.py`
  - aktywne zbieranie intersections po connection i wybór referencyjnej pary
    segmentów
- `logical_line_intersection_trimming.py`
  - trim linii do przecięć i ponowne przypisanie intersections
- `logical_line_search.py`
  - cienka publiczna fasada dla helperów search-related
- `logical_line_search_area.py`
  - `SearchArea` i maska prostokąta tolerancji
- `logical_line_search_window_points.py`
  - zbieranie punktów okna segmentów i `LogicalLine`
- `logical_line_search_goals.py`
  - budowa punktów celu dla connection
- `logical_line_search_pathfinding.py`
  - straight path i BFS używane przez connection jako budowa ścieżki albo sama
    walidacja zależnie od typu kandydata
- `logical_line_search_point_to_line.py`
  - helper point-to-line używany przez continuity
- `visualization/visualization.py`
  - agregacja funkcji renderujących
- `visualization/visualization_containment.py`
  - overlaye i boardy dla full containment prune
- `visualization/visualization_vertex_containment_merge.py`
  - overlaye i boardy dla `vertex containment merge`
- `visualization/visualization_logical_lines.py`
  - overlaye `post_merge`, `post_connection` i finalnych `LogicalLine`
- `visualization/visualization_intersections.py`
  - overlaye aktywnych intersections
- `visualization/visualization_trimmed_logical_lines.py`
  - porównanie stanu `post_connection` z finalnymi liniami po trimie
- `visualization/visualization_raw_segment_groups.py`
  - boardy i overlaye grup segmentów `RAW`

## Notatka o importach notebooka

Notebook nie importuje modułów przez pełną ścieżkę repozytorium typu
`src.MachineLearning...`.

Aktualny wzorzec to:

- `import bootstrap`
- `import pipeline`

To działa dlatego, że `bootstrap.py` dodaje do `sys.path`:

- katalog wariantu `raw_line_family_only`,
- podkatalog `pipeline/`,
- podkatalog `visualization/`.

## Kolejność czytania

Jeśli chcesz szybko zrozumieć system, czytaj w tej kolejności:

1. `pipeline_overview.md`
2. `logical_line_lifecycle.md`
3. `logical_line_build_and_grouping.md`
4. `logical_line_containment_and_vertex_merge.md`
5. `logical_line_pixel_connection.md`
6. `visualization_and_artifacts.md`
7. `intersections_and_visualization.md`
