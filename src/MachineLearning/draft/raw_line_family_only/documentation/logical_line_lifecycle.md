# Raw Line Family Only - lifecycle `LogicalLine`

## Cel

Ten plik jest teraz krótkim indeksem dokumentacji dla etapu `LogicalLine`.

Po refaktorze i rozbudowie heurystyk lifecycle linii logicznych jest już zbyt
duży, żeby utrzymywać cały opis w jednym pliku bez niepotrzebnego kontekstu.

## Zakres tego etapu

Lifecycle `LogicalLine` obejmuje dziś:

- budowę linii z segmentów rodzin poziomych i pionowych,
- merge geometryczny segmentów i całych linii,
- grouping segmentów `RAW`,
- full containment prune,
- vertex containment merge,
- pixel-validated connection,
- snapshoty stanów `pre_connection`, `post_merge` i `post_connection`.

Preprocessing, notebook, artefakty i pełna orkiestracja są opisane w
`pipeline_overview.md`.

Analiza przecięć, ramka i finalne wizualizacje są opisane w:

- `intersection_analysis_and_frame_selection.md`
- `visualization_and_artifacts.md`

## Mapa dokumentów

### 1. Budowa linii i grouping `RAW`

Plik: `logical_line_build_and_grouping.md`

Zakres:

- modele bazowe i `LogicalLine`,
- budowa wstępnych linii,
- merge geometryczny,
- grouping segmentów `RAW`,
- znaczenie stanu `pre_connection`.

### 2. Containment i merge po wierzchołku

Plik: `logical_line_containment_and_vertex_merge.md`

Zakres:

- full containment prune,
- grupowanie po ciągłości osi poprzecznej,
- vertex containment merge,
- znaczenie stanu `post_merge`.

### 3. Pixel connection

Plik: `logical_line_pixel_connection.md`

Zakres:

- `ToleranceRectangle`,
- `ConnectionKind`,
- wyszukiwanie ścieżki po białych pikselach,
- segmenty `SAME_AXIS_CONNECTION` i `CROSS_AXIS_CONNECTION`,
- znaczenie stanu `post_connection`.

## Aktualny flow

```mermaid
flowchart TD
    familySegments[Classified family segments] --> buildLines[build_logical_lines]
    buildLines --> mergeLines[merge_logical_lines]
    mergeLines --> groupRaw[group_raw_segments in each line]
    groupRaw --> savePre[Clone pre_connection state]
    savePre --> fullContainment[full containment prune]
    fullContainment --> vertexMerge[vertex containment merge]
    vertexMerge --> savePostMerge[Clone post_merge state]
    savePostMerge --> pixelConnect[connect_logical_lines_by_pixels]
    pixelConnect --> savePost[Clone post_connection state]
    savePost --> handoff[Pass lines to intersection analysis]
```

## Najważniejsze założenia aktualnej wersji

1. `LogicalLine` jest głównym nośnikiem stanu domenowego dla etapu linii.
2. `logical_lines.py` jest publiczną fasadą, a logika jest rozbita na mniejsze
   wyspecjalizowane moduły `logical_line_*`.
3. Grouping `RAW`, containment, vertex merge i pixel connection to cztery różne
   etapy i nie należy ich mieszać w dokumentacji.
4. Segmenty connection są częścią finalnej linii, a nie tylko wizualnym
   dodatkiem.
