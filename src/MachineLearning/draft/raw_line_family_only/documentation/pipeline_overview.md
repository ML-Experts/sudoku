# Raw Line Family Only - pipeline i artefakty

## Cel

Ten dokument opisuje aktualną orkiestrację eksperymentu
`raw_line_family_only` z perspektywy notebooka i pipeline'u.

Jeśli dokumentacja i implementacja rozjeżdżają się ze sobą, źródłem prawdy jest
kod, przede wszystkim:

- `pipeline/pipeline.py`
- `detection.py`
- `logical_line_core.py`
- `logical_lines.py`
- moduły `visualization/*`

Dokumenty szczegółowe:

- `logical_line_lifecycle.md`
- `logical_line_build_and_grouping.md`
- `logical_line_containment_and_vertex_merge.md`
- `logical_line_pixel_connection.md`
- `intersections_and_visualization.md`
- `visualization_and_artifacts.md`

## Notebook i bootstrap

Aktualny notebook eksperymentalny to `experiment.ipynb`.

Notebook korzysta z API budowanego przez `load_api()` z `bootstrap.py`.
Bootstrap:

- dodaje katalog wariantu oraz `pipeline/` i `visualization/` do `sys.path`,
- czyści wcześniej załadowane moduły z bieżącego wariantu,
- importuje moduły w ustalonej kolejności,
- składa obiekt `Api` używany przez notebook.

Notebook powinien używać lokalnych importów:

- `import bootstrap`
- `import pipeline`

Nie należy wracać do importów od repo root typu `from src.MachineLearning...`.

## Publiczny entrypoint

Publicznym entrypointem warstwy pipeline jest
`run_raw_line_family_pipeline(...)` z `pipeline/pipeline.py`.

Wejście:

- `active_image_path`
- `config`
- `notebook_api`

Wyjście:

- `RawLineFamilyArtifacts`

## Preprocessing

Aktualna kolejność preprocessingu:

1. `load_image_bgr(...)`
2. `resize_for_display(...)`
3. konwersja do skali szarości:
   - `gray_image`
4. median denoise:
   - `denoised_image`
   - `denoise_name = median_{kernel}`
5. adaptacyjna binaryzacja Gaussa:
   - `binary_image`
   - `threshold_name = gaussian_block{...}_c{...}`
6. soft cleanup komponentów:
   - `clean_binary`
   - `cleanup_name = adaptive_plus_components_soft`
   - `min_component_area_px`
7. directional close repair:
   - `repaired_binary`
   - `repair_name = directional_close`

Znaczenie obrazów:

- `clean_binary` służy do detekcji rodzin i wejściowych segmentów Hougha,
- `repaired_binary` służy do pixel connection i większości finalnych overlayów,
- prostokąty tolerancji są geometrią pomocniczą connection i nie są osobnym
  retained artifactem notebooka.

## Dwa przebiegi `detect_line_families(...)`

Pipeline wywołuje `detect_line_families(...)` dwa razy.

### 1. Przebieg tylko dla rodzin

Wywołanie:

- `detect_line_families(clean_binary, config, include_logical_lines=False)`

Cel:

- dostać `horizontal_segments` i `vertical_segments`,
- zbudować overlay rodzin na `clean_binary` i na obrazie źródłowym,
- nie uruchamiać cięższych etapów `LogicalLine`.

### 2. Pełna detekcja

Wywołanie:

- `detect_line_families(
  clean_binary,
  config,
  pixel_connection_binary_image=repaired_binary,
  )`

Pełny przebieg wykonuje:

1. klasyfikację segmentów Hougha do rodzin,
2. budowę wstępnych `LogicalLine`,
3. grouping `RAW`,
4. full containment prune,
5. vertex containment merge,
6. pixel connection,
7. przypisanie intersections,
8. trim linii do przecięć,
9. ponowne przeliczenie intersections,
10. budowę grup boundary i kandydatów ramek.

Ważne:

- rodziny i wejściowe segmenty pochodzą z `clean_binary`,
- walidacja przejść po pikselach odbywa się na `repaired_binary`.

## `RawLineFamilyResult`

Główny wynik domenowy zwracany z `detection.py` to `RawLineFamilyResult`.

Najważniejsze pola:

- `raw_segment_count`
- `orientation_offset_degrees`
- `horizontal_angle_degrees`
- `vertical_angle_degrees`
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
- `horizontal_boundary_groups`
- `vertical_boundary_groups`
- `logical_line_frame_candidates`

Interpretacja stanów:

- `pre_connection` - stan po grouping `RAW`,
- `post_merge` - stan po `vertex containment merge`,
- `post_connection` - stan po `pixel connection`, ale przed trimem,
- kolekcje bez prefiksu `pre/post` - finalny stan po trimie,
- `logical_line_intersections` - intersections policzone na finalnej geometrii.
- `horizontal_boundary_groups` i `vertical_boundary_groups` - grupy linii zbudowane
  po finalnym `START/END`,
- `logical_line_frame_candidates` - wszystkie znalezione kandydaty ramek bez
  rankingu i bez wyboru najlepszego.

## `RawLineFamilyArtifacts`

`run_raw_line_family_pipeline(...)` buduje `RawLineFamilyArtifacts` z:

1. obrazów preprocessingu:
   - `source_bgr`
   - `display_bgr`
   - `gray_image`
   - `denoised_image`
   - `binary_image`
   - `clean_binary`
   - `repaired_binary`
2. wyniku domenowego:
   - `line_family_result`
3. overlayów i boardów:
   - `binary_family_overlay`
   - `source_family_overlay`
   - `raw_segment_group_board`
   - `containment_prune_board`
   - `vertex_containment_merge_board`
   - `binary_post_connection_logical_line_overlay`
   - `source_post_connection_logical_line_overlay`
   - `binary_logical_line_overlay`
   - `source_logical_line_overlay`
   - `source_trimmed_logical_line_overlay`
   - `source_logical_line_intersection_overlay`
   - `source_logical_line_frame_overlay`
4. nazw etapów:
   - `denoise_name`
   - `threshold_name`
   - `cleanup_name`
   - `repair_name`

Notebook może budować artefakty ręcznie, ale powinien zachować tę samą
semantykę pól i kolejność stanów co `pipeline/pipeline.py`.

## Raport tekstowy

`describe_raw_line_family_artifacts(...)` z `pipeline/pipeline_report.py`
opisuje nie tylko finalny wynik, ale też stany pośrednie.

Raport obejmuje między innymi:

- kształty obrazów i nazwy preprocessingu,
- liczbę surowych segmentów Hougha,
- liczbę segmentów rodzin poziomych i pionowych,
- finalną liczbę `LogicalLine`,
- liczbę segmentów `same_axis_connection` i `cross_axis_connection`,
- liczbę przecięć `cross` i `touch`,
- liczbę grup boundary i kandydatów ramek,
- statystyki grouping `RAW`, containment prune i vertex merge,
- stan `post_merge`, `post_connection` i finalny stan linii,
- listę plotów generowanych dla notebooka.

## Plot items notebooka

Kolejność obrazów buduje `build_raw_line_family_plot_items(...)` z
`pipeline/pipeline_plots.py`.

Stała część listy:

1. `source`
2. `gray`
3. `denoise: ...`
4. `binary: ...`
5. `cleanup: ...`
6. `repair: ...`
7. `raw line families on cleanup binary`
8. `raw line families on source`

Opcjonalnie, jeśli artefakty istnieją:

- `raw segment groups board`
- `containment prune board`
- `logical lines post vertex merge board`
- `logical lines post connection on repair binary`
- `logical lines post connection on source`
- `logical line intersections on source`
- `logical lines trimmed vs post connection on source`
- `logical line frames on source`

Zawsze obecne po pełnym przebiegu:

- `logical lines final on repair binary`
- `logical lines final on source`

## Najważniejsze założenia

1. `clean_binary` i `repaired_binary` pełnią różne role i nie są zamiennikami.
2. Pipeline przechowuje osobno stan po grouping, po merge'u, po connection i
   finalny stan po trimie.
3. Raport i overlaye są częścią eksperymentu, a nie pobocznym dodatkiem.
4. Po finalnych intersections pipeline buduje grupy boundary i kandydaty ramek.
5. Ranking ramek i wybór najlepszej ramki nie są częścią aktywnego pipeline'u.
