# Raw Line Family Only - wizualizacje i artefakty

## Cel

Ten dokument opisuje aktualne overlaye, boardy i artefakty raportowe używane
przez notebook `experiment.ipynb` i przez `pipeline/pipeline.py`.

## Główne pliki

- `visualization/visualization.py`
- `visualization/visualization_line_families.py`
- `visualization/visualization_logical_lines.py`
- `visualization/visualization_raw_segment_groups.py`
- `visualization/visualization_containment.py`
- `visualization/visualization_vertex_containment_merge.py`
- `visualization/visualization_tolerance_rectangles.py`
- `visualization/visualization_long_segments.py`
- `pipeline/pipeline_artifacts.py`
- `pipeline/pipeline_plots.py`
- `pipeline/pipeline_report.py`

## Rola `visualization/visualization.py`

`visualization/visualization.py` jest agregatorem funkcji renderujących.

Notebook i pipeline nie powinny składać większości overlayów ręcznie z modułów
szczegółowych, tylko korzystać z tej warstwy agregującej.

## Kategorie renderów

### 1. Rodziny linii

Funkcja:

- `build_line_family_overlays(...)`

Pokazuje:

- surowe segmenty poziome,
- surowe segmenty pionowe.

### 2. Grouping segmentów `RAW`

Funkcje:

- `build_raw_segment_group_overlays(...)`
- `build_raw_segment_group_board(...)`

Pokazują:

- grupy zbudowane przed prune i connection,
- relacje między seedem, trial segmentem i output segmentem,
- stan `pre_connection`.

### 3. Full containment prune

Funkcje:

- `build_containment_prune_overlays(...)`
- `build_containment_prune_board(...)`

Pokazują:

- `anchor_line` pozostawione po pruningu,
- `grouped_logical_lines` usunięte jako linie w pełni zawarte,
- grupowanie po ciągłości osi poprzecznej,
- stan pomiędzy grouping `RAW` a merge'em vertex.

### 4. Vertex containment merge

Funkcje:

- `build_vertex_containment_merge_overlays(...)`
- `build_vertex_containment_merge_board(...)`

Pokazują:

- `anchor_line` po merge'u,
- `grouped_logical_lines` skonsumowane przez merge,
- stan po merge'u, ale jeszcze przed pixel connection.

### 5. Logical lines po merge'u vertex

Funkcja:

- `build_post_merge_logical_line_overlays(...)`

Pokazuje:

- stan `post_merge`,
- wynikowe linie logiczne po etapie merge'u,
- brak segmentów dodanych jeszcze przez pixel connection.

### 6. Logical lines po connection

Funkcja:

- `build_post_connection_logical_line_overlays(...)`

Pokazuje:

- stan `post_connection`,
- segmenty dodane przez connection.

### 7. Finalne logical lines

Funkcje:

- `build_logical_line_overlays(...)`
- `build_logical_line_overlays_for_lines(...)`

Pokazują:

- finalne linie po connection,
- wszystkie segmenty linii,
- wierzchołki start i end,
- segmenty o różnych originach.

### 8. Long segment candidates

Funkcje:

- `build_long_segment_candidate_overlays(...)`
- `build_long_segment_candidate_board(...)`

To osobny widok diagnostyczny dla segmentów o długości co najmniej `80%`
najdłuższego segmentu w danej linii.

### 9. Tolerance rectangles

Funkcja:

- `build_tolerance_rectangle_overlays(...)`

Pokazuje:

- prostokąty tolerancji dla finalnych logical lines,
- punkt referencyjny,
- wektor rozpoznawania.

## `RawLineFamilyArtifacts`

`run_raw_line_family_pipeline(...)` buduje `RawLineFamilyArtifacts`, który
spina:

- obrazy preprocessingu,
- wynik domenowy `RawLineFamilyResult`,
- boardy i overlaye,
- nazwy etapów preprocessingu.

Najważniejsze grupy pól:

1. obrazy preprocessingu, takie jak `gray_image`, `clean_binary`,
   `repaired_binary`
2. wynik domenowy `line_family_result`
3. overlaye i boardy dla rodzin, grouping, containment, vertex merge,
   post-merge, post-connection, finalnych linii i tolerance rectangles
4. nazwy etapów, takie jak `denoise_name`, `threshold_name`, `cleanup_name`,
   `repair_name`

## Związek z raportem notebooka

`describe_raw_line_family_artifacts(...)` raportuje między innymi:

- wynik full containment prune,
- wynik vertex containment merge,
- rozkład segmentów w stanie `post_merge`,
- rozkład segmentów w stanie `post_connection`,
- rozkład segmentów w finalnym stanie linii,
- opis long segment candidates.

To oznacza, że wizualizacje i raport opisują ten sam pipeline z dwóch
perspektyw:

- obrazy,
- tekstowe statystyki i rozpiska stanów.

## Plot items notebooka

Kolejność obrazów pokazywanych w notebooku jest budowana przez
`build_raw_line_family_plot_items(...)` z `pipeline/pipeline_plots.py`.

Stała część listy:

1. `source`
2. `gray`
3. `denoise: ...`
4. `binary: ...`
5. `cleanup: ...`
6. `repair: ...`
7. `raw line families on cleanup binary`
8. `raw line families on source`

Opcjonalnie, jeśli odpowiednie artefakty istnieją:

- `raw segment groups board`
- `containment prune board`
- `logical lines post vertex merge board`
- `logical lines post connection on repair binary`
- `long segment candidates on repair binary`
- `tolerance rectangles on repair binary`

Zawsze obecne po pełnym przebiegu:

- `logical lines final after connection on repair binary`
- `logical lines final after connection on source`
