# Raw Line Family Only - indeks procesu

## Cel

Ten plik jest krótkim punktem wejścia do dokumentacji eksperymentu
`raw_line_family_only`.

Jeśli opis dokumentów i implementacja rozjeżdżają się ze sobą, źródłem prawdy
jest kod, przede wszystkim:

- `pipeline/pipeline.py`
- `detection.py`
- `logical_line_core.py`
- moduły `logical_line_*`
- moduły `visualization/*`

## Aktualny stan eksperymentu

Końcowym stanem aktywnego pipeline'u są dziś:

- finalne `horizontal_logical_lines` i `vertical_logical_lines`,
- `logical_line_intersections` policzone po trimie,
- retained overlaye i boardy zdefiniowane w `pipeline/pipeline_plots.py`.

Ważne:

- etap wyboru ramki nie jest już częścią aktywnego flow,
- po `pixel connection` kod nadal wykonuje intersections i trim,
- prostokąty tolerancji są geometrią pomocniczą connection, a nie osobnym
  renderem notebooka.

## Mapa dokumentów

### 1. End-to-end pipeline

Plik: `pipeline_overview.md`

Zakres:

- bootstrap notebooka i reload modułów,
- preprocessing,
- dwa przebiegi `detect_line_families(...)`,
- `RawLineFamilyResult` i `RawLineFamilyArtifacts`,
- raport oraz plot items notebooka.

### 2. Lifecycle `LogicalLine`

Plik: `logical_line_lifecycle.md`

Zakres:

- mapa etapów `LogicalLine`,
- znaczenie snapshotów `pre_connection`, `post_merge`, `post_connection`,
- linki do dokumentów szczegółowych.

### 3. Dokumenty szczegółowe

- `logical_line_build_and_grouping.md`
- `logical_line_containment_and_vertex_merge.md`
- `logical_line_pixel_connection.md`
- `intersections_and_visualization.md`
- `visualization_and_artifacts.md`

### 4. Notatka historyczna

- `intersection_analysis_and_frame_selection.md`

To już nie jest opis aktywnego końca pipeline'u. Plik został zachowany tylko
jako kontekst po usuniętym etapie analizy ramki.

## Skrócony przepływ

1. `experiment.ipynb` ładuje API przez `bootstrap.load_api()`.
2. Pipeline wykonuje preprocessing: grayscale, median denoise, adaptive
   threshold, soft component cleanup, directional close repair.
3. `detect_line_families(...)` uruchamia się dwa razy:
   - raz tylko do overlayu rodzin linii na `clean_binary`,
   - raz do pełnej detekcji z pixel connection na `repaired_binary`.
4. Pełna detekcja wykonuje:
   - klasyfikację segmentów Hougha do rodzin,
   - budowę `LogicalLine`,
   - grouping `RAW`,
   - full containment prune,
   - vertex containment merge,
   - pixel connection,
   - przypisanie intersections,
   - trim do przecięć,
   - ponowne przeliczenie intersections.
5. Pipeline albo notebook buduje `RawLineFamilyArtifacts`.

## Jak czytać dokumentację

Jeśli chcesz szybko zrozumieć system, czytaj w tej kolejności:

1. `pipeline_overview.md`
2. `logical_line_lifecycle.md`
3. `logical_line_build_and_grouping.md`
4. `logical_line_containment_and_vertex_merge.md`
5. `logical_line_pixel_connection.md`
6. `visualization_and_artifacts.md`
7. `intersections_and_visualization.md`
