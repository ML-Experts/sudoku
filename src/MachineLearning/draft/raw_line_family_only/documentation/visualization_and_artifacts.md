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
- `visualization/visualization_intersections.py`
- `visualization/visualization_trimmed_logical_lines.py`
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

Funkcja:

- `build_raw_segment_group_board(...)`

Pokazują:

- grupy zbudowane przed prune i connection,
- relacje między seedem, trial segmentem i output segmentem,
- stan `pre_connection`.

### 3. Full containment prune

Funkcja:

- `build_containment_prune_board(...)`

Pokazują:

- `anchor_line` pozostawione po pruningu,
- `grouped_logical_lines` usunięte jako linie w pełni zawarte,
- grupowanie po ciągłości osi poprzecznej,
- stan pomiędzy grouping `RAW` a merge'em vertex.

### 4. Vertex containment merge

Funkcja:

- `build_vertex_containment_merge_board(...)`

Pokazują:

- `anchor_line` po merge'u,
- `grouped_logical_lines` skonsumowane przez merge,
- stan po merge'u, ale jeszcze przed pixel connection.

### 5. Logical lines po merge'u vertex

W aktualnym pipeline nie ma osobnego retained overlayu dla stanu `post_merge`.

Stan ten jest pokazywany pośrednio przez:

- `build_vertex_containment_merge_board(...)`

oraz raportowany tekstowo w `pipeline/pipeline_report.py`.

### 6. Logical lines po connection

Funkcja:

- `build_post_connection_logical_line_overlays(...)`

Pokazuje:

- stan `post_connection`,
- segmenty dodane przez connection,
- geometrię jeszcze nieobciętą do przecięć.

### 7. Finalne logical lines

Funkcje:

- `build_logical_line_overlays(...)`
- `build_logical_line_overlays_for_lines(...)`

Pokazują:

- finalne linie po trimie do przecięć,
- wszystkie segmenty linii,
- wierzchołki start i end,
- segmenty o różnych originach.

### 8. Trimmed logical lines

Funkcja:

- `build_trimmed_logical_line_overlays(...)`

To widok diagnostyczny pokazujący:

- przygaszony stan `post_connection`,
- finalne linie po trimie do przecięć nałożone na ten sam obraz.

### 9. Intersections

Funkcja:

- `build_logical_line_intersection_overlays(...)`

Pokazuje:

- aktywne `logical_line_intersections` po trimie i po ponownym ich
  przeliczeniu,
- rozróżnienie `cross` i `touch`,
- punkt przecięcia wraz z etykietą pary linii,
- dodatkowy marker boundary wynikający z `order`.

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
   post-connection, finalnych linii, intersections oraz widoku trimmed
4. nazwy etapów, takie jak `denoise_name`, `threshold_name`, `cleanup_name`,
   `repair_name`

## Związek z raportem notebooka

`describe_raw_line_family_artifacts(...)` raportuje między innymi:

- wynik full containment prune,
- wynik vertex containment merge,
- rozkład segmentów w stanie `post_merge`,
- rozkład segmentów w stanie `post_connection`,
- rozkład segmentów w finalnym stanie linii po trimie,
- liczność przecięć `cross` i `touch`,
- obecność retained artifactów overlayowych.

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
- `logical lines post connection on source`
- `logical line intersections on source`
- `logical lines trimmed vs post connection on source`

Zawsze obecne po pełnym przebiegu:

- `logical lines final on repair binary`
- `logical lines final on source`
