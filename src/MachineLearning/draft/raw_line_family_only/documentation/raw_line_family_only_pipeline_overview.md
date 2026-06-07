# Raw Line Family Only - pipeline i artefakty

## Cel

Ten dokument opisuje aktualną orkiestrację eksperymentu
`raw_line_family_only` z perspektywy notebooka i pipeline'u.

Zakres obejmuje:

- bootstrap API do notebooka,
- preprocessing obrazu,
- sposób wywołania `detect_line_families(...)`,
- budowę `RawLineFamilyArtifacts`,
- raport tekstowy i listę plotów.

Szczegóły domenowe `LogicalLine`, grouping `RAW`, pixel connection i
intersection analysis są opisane w:

- `raw_line_family_only_logical_line_lifecycle.md`
- `raw_line_family_only_intersections_and_visualization.md`

## Główne pliki

- `raw_line_family_only_bootstrap.py`
- `raw_line_family_only_pipeline.py`
- `raw_line_family_only_pipeline_artifacts.py`
- `raw_line_family_only_pipeline_report.py`
- `raw_line_family_only_pipeline_plots.py`
- `raw_line_family_only_pipeline_selection.py`
- `raw_line_family_only_detection.py`

## Rola notebooka i bootstrapu

Notebook `raw_line_family_only_experiment.ipynb` korzysta z API budowanego przez
`load_raw_line_family_only_api()` z `raw_line_family_only_bootstrap.py`.

Bootstrap odpowiada za:

- dodanie katalogu wariantu do `sys.path`,
- wyczyszczenie wcześniej załadowanych modułów `raw_line_family_only_*`,
- ponowny import modułów we właściwej kolejności,
- złożenie jednego obiektu `RawLineFamilyOnlyApi`.

Najważniejsze elementy `RawLineFamilyOnlyApi`:

- `ExperimentConfig`
- funkcje preprocessingu:
  - `apply_median_denoise`
  - `apply_gaussian_threshold`
  - `apply_soft_component_cleanup`
  - `apply_directional_close_repair`
- `detect_line_families`
- funkcje renderujące z `raw_line_family_only_visualization.py`

To API jest celowo stabilnym punktem wejścia dla notebooka po refaktorze.

## Wejście pipeline

Publiczny entrypoint w warstwie pipeline'u:

- `run_raw_line_family_pipeline(...)` z `raw_line_family_only_pipeline.py`

Wejście:

- `active_image_path`
- `config`
- `notebook_api`

Wyjście:

- `RawLineFamilyArtifacts`

## Etapy preprocessingu

Aktualna kolejność w `run_raw_line_family_pipeline(...)`:

1. wczytanie obrazu przez `load_image_bgr(...)`
2. przygotowanie obrazu do pracy i wyświetlania przez `resize_for_display(...)`
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

- `clean_binary` jest używane do detekcji rodzin i wejściowych segmentów Hougha,
- `repaired_binary` jest używane jako obraz do pixel connection i do większości
  finalnych overlayów debugowych.

## Dwa przebiegi `detect_line_families(...)`

Pipeline wywołuje `detect_line_families(...)` dwa razy.

### Przebieg 1: tylko rodziny

Wywołanie:

- `detect_line_families(clean_binary, config, include_logical_lines=False)`

Cel:

- dostać `horizontal_segments` i `vertical_segments`,
- zbudować overlay rodzin linii na `clean_binary` i na obrazie źródłowym,
- nie uruchamiać cięższych etapów `LogicalLine`.

To jest czysto diagnostyczny przebieg do wizualizacji segmentów rodzin.

### Przebieg 2: pełna detekcja

Wywołanie:

- `detect_line_families(
  clean_binary,
  config,
  pixel_connection_binary_image=repaired_binary,
  )`

Cel:

- zbudować komplet stanów pośrednich i finalnych,
- uruchomić grouping `RAW`,
- wykonać pixel connection,
- przeprowadzić analizę przecięć i wybór ramki,
- zwrócić wynik do raportu i renderów notebooka.

Ważne rozdzielenie odpowiedzialności:

- rodziny i wejściowe segmenty pochodzą z `clean_binary`,
- walidacja przejść po pikselach odbywa się na `repaired_binary`.

## Co zwraca `detect_line_families(...)`

Główny wynik domenowy to `RawLineFamilyResult` z
`raw_line_family_only_detection.py`.

Najważniejsze pola:

- `raw_segment_count`
- `orientation_offset_degrees`
- `horizontal_angle_degrees`
- `vertical_angle_degrees`
- `horizontal_segments`
- `vertical_segments`
- `horizontal_pre_connection_logical_lines`
- `vertical_pre_connection_logical_lines`
- `horizontal_post_connection_logical_lines`
- `vertical_post_connection_logical_lines`
- `horizontal_logical_lines`
- `vertical_logical_lines`
- `horizontal_tolerance_rectangles`
- `vertical_tolerance_rectangles`
- `logical_line_intersection_analysis`
- `logical_line_intersections`
- `logical_line_border_pairs`
- `logical_line_frames`

Interpretacja stanów:

- `pre_connection` oznacza stan po grouping segmentów `RAW`,
- `post_connection` oznacza stan po pixel connection i przed pruningiem
  intersection-driven,
- kolekcje finalne oznaczają stan po intersections, pruning i frame selection.

## Budowa `RawLineFamilyArtifacts`

`run_raw_line_family_pipeline(...)` buduje następnie `RawLineFamilyArtifacts`
z `raw_line_family_only_pipeline_artifacts.py`.

Artefakty można podzielić na cztery grupy.

### 1. Obrazy preprocessingu

- `source_bgr`
- `display_bgr`
- `gray_image`
- `denoised_image`
- `binary_image`
- `clean_binary`
- `repaired_binary`

### 2. Wynik domenowy

- `line_family_result`

### 3. Overlaye i boardy

- `binary_family_overlay`
- `source_family_overlay`
- `raw_segment_group_board`
- `binary_raw_segment_group_overlay`
- `source_raw_segment_group_overlay`
- `binary_post_connection_logical_line_overlay`
- `source_post_connection_logical_line_overlay`
- `binary_logical_line_overlay`
- `source_logical_line_overlay`
- `binary_long_segment_candidate_overlay`
- `source_long_segment_candidate_overlay`
- `long_segment_candidate_board`
- `binary_logical_line_intersection_overlay`
- `source_logical_line_intersection_overlay`
- `binary_frame_overlay`
- `source_frame_overlay`
- `binary_tolerance_rectangle_overlay`
- `source_tolerance_rectangle_overlay`

### 4. Nazwy etapów

- `denoise_name`
- `threshold_name`
- `cleanup_name`
- `repair_name`

## Raport tekstowy

Funkcja `describe_raw_line_family_artifacts(...)` z
`raw_line_family_only_pipeline_report.py` opisuje nie tylko finalny wynik,
ale też kilka ważnych stanów pośrednich.

Raport obejmuje między innymi:

- kształty obrazów i nazwy etapów preprocessingu,
- liczbę surowych segmentów Hougha,
- liczbę segmentów rodzin poziomych i pionowych,
- finalną liczbę `LogicalLine`,
- liczbę segmentów `same_axis_connection`,
- liczbę segmentów `cross_axis_connection`,
- liczbę prostokątów tolerancji,
- liczbę intersections, border pairs i frames,
- statystyki RAW segment grouping,
- stan kolekcji `post_connection`,
- kandydatów długich segmentów,
- listę plotów generowanych dla notebooka.

To ważne, bo raport jest dzisiaj źródłem debug contextu, a nie tylko krótkim
podsumowaniem liczników.

## Plot items notebooka

Kolejność obrazów pokazywanych w notebooku jest budowana przez
`build_raw_line_family_plot_items(...)` z
`raw_line_family_only_pipeline_plots.py`.

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
- `raw segment groups before pixel merge on repair binary`
- `raw segment groups before pixel merge on source`
- `logical lines post connection on repair binary`
- `logical lines post connection on source`
- `long segment candidates on repair binary`
- `long segment candidates on source`
- `logical lines board: blue=all, red=longest`
- `frames on repair binary`
- `frames on source`
- `tolerance rectangles on repair binary`
- `tolerance rectangles on source`

Zawsze obecne po pełnym przebiegu:

- `logical lines final after intersections on repair binary`
- `logical lines final after intersections on source`
- `logical line intersections on repair binary`
- `logical line intersections on source`

## Aktualny przepływ pipeline

```mermaid
flowchart TD
    loadApi[Load notebook API] --> loadImage[Load source image]
    loadImage --> preprocess[Preprocess image]
    preprocess --> familyPass[detect_line_families on clean_binary only families]
    preprocess --> fullPass[detect_line_families on clean_binary with repaired_binary for pixel connection]
    familyPass --> familyOverlay[Build family overlays]
    fullPass --> buildArtifacts[Build RawLineFamilyArtifacts]
    buildArtifacts --> buildPlots[Build notebook plot items]
    buildArtifacts --> buildReport[Describe artifacts]
```

## Najważniejsze założenia aktualnej wersji

1. Notebook może wykonywać część kroków ręcznie, ale oficjalnym entrypointem
   orchestration jest `run_raw_line_family_pipeline(...)`.
2. `clean_binary` i `repaired_binary` pełnią różne role i nie należy ich
   traktować jako zamienników.
3. Pipeline przechowuje osobno stan przed connection, po connection i po
   intersection analysis.
4. Raport i overlaye są częścią eksperymentu, a nie dodatkiem pobocznym.
5. Źródłem prawdy dla kolejności etapów jest kod w
   `raw_line_family_only_pipeline.py` i `raw_line_family_only_detection.py`.
