# Raw Line Family Only - intersections i wizualizacja

## Status

Ten dokument opisuje aktualny, aktywny etap intersections wykonywany po
`pixel connection`, razem z trimem linii do przecięć.

W aktualnej wersji eksperymentu:

- `pixel connection` nie jest już ostatnią modyfikacją geometrii linii,
- po connection kod buduje aktywne `logical_line_intersections`,
- potem trimuje linie do przecięć i ponownie przelicza intersections,
- po finalnych intersections buduje grupy boundary i kandydatów ramek,
- nie ma aktywnego etapu rankingu ramek ani przypisania `frame_side`,
- intersections mają już własny overlay w notebooku i pipeline.

## Główne pliki

- `intersection_model.py`
- `logical_line_intersections.py`
- `logical_line_intersection_trimming.py`
- `visualization/visualization_intersections.py`
- `visualization/visualization_trimmed_logical_lines.py`
- `detection.py`
- `pipeline/pipeline.py`
- `pipeline/pipeline_report.py`
- `logical_line_frames.py`
- `visualization/visualization_frames.py`

## Wejście do etapu

Intersections są dziś budowane w dwóch krokach:

- najpierw na stanie `post_connection`,
- potem ponownie na finalnych `horizontal_logical_lines` i
  `vertical_logical_lines` po trimie.

To znaczy:

- connection najpierw domyka geometrię lokalnie,
- pierwszy przebieg intersections dostarcza granic do trimu,
- trim obcina finalne linie do skrajnych przecięć,
- drugi przebieg intersections opisuje relacje na finalnej geometrii.

## Model domenowy

Podstawowym modelem jest `LogicalLineIntersection`.

Przechowuje on:

- referencję do linii poziomej i pionowej,
- referencję do segmentu poziomego i pionowego wybranego jako segmenty
  referencyjne dla przecięcia,
- punkt przecięcia,
- jawne `kind`:
  - `cross`
  - `touch`
- pole:
  - `order`

Ważne rozróżnienie:

- `kind` jest dziś liczone niezależnie od `IntersectionOrder`,
- `order` opisuje pozycję przecięcia na danej linii osiowej,
- `order` jest wyliczane z kolejności przecięć po osi danej linii.

## Aktualna heurystyka intersections i trimu

Publiczne entrypointy:

- `assign_logical_line_intersections(...)`
- `trim_logical_lines_to_intersections(...)`

Aktualny przebieg:

1. kod iteruje po parach linii `horizontal` / `vertical`,
2. dla każdej pary sprawdza pary segmentów należących do tych linii,
3. liczy punkt przecięcia linii wspierających segmenty,
4. odrzuca kandydatów, których punkt nie leży na obu skończonych segmentach,
5. klasyfikuje lokalny `kind` na podstawie pozycji punktu na segmentach
   referencyjnych,
6. wybiera najlepszy kandydat dla danej pary linii,
7. wylicza `order` na podstawie pozycji przecięcia na osi linii,
8. wykorzystuje skrajne przecięcia jako granice trimu,
9. po trimie liczy intersections ponownie.

Dzisiejsza reguła `kind` jest lokalna i segmentowa:

- `cross` tylko wtedy, gdy punkt leży w `MIDDLE` obu segmentów referencyjnych,
- w przeciwnym razie `touch`.

## Aktywny trim do przecięć

Po pierwszym przypisaniu intersections kod uruchamia
`trim_logical_lines_to_intersections(...)`.

Semantyka:

- każda linia jest przycinana do zakresu osi pomiędzy skrajnym przecięciem
  `START/BOTH` i skrajnym przecięciem `END/BOTH`,
- jeśli linia ma tylko jedno przecięcie (`BOTH`), trim nie daje dwóch granic,
  więc geometria pozostaje bez zmian,
- gdy to samo przecięcie pełniłoby obie granice, jego `kind` jest degradowane
  do `touch`,
- po potencjalnym trimie intersections są przeliczane jeszcze raz, żeby finalny
  stan był zgodny z nową geometrią.

## Wizualizacja

Publiczna funkcja renderująca:

- `build_logical_line_intersection_overlays(...)`

Overlay pokazuje:

- punkt przecięcia,
- inny marker dla `cross` i `touch`,
- etykietę pary linii, np. `H3xV7`,
- dodatkowe wyróżnienie dla przecięć boundary wynikające z `order`.

Powiązany overlay:

- `build_trimmed_logical_line_overlays(...)`

Ten widok pokazuje różnicę między:

- przygaszonym stanem `post_connection`,
- finalnymi liniami po trimie do przecięć.

## Kandydaci ramek po intersections

Po finalnym trimie i po finalnym przeliczeniu intersections aktywny kod buduje:

- `horizontal_boundary_groups`,
- `vertical_boundary_groups`,
- `logical_line_frame_candidates`.

Jest to etap heurystycznego znalezienia wszystkich ramek spełniających kryteria
boundary i wzajemnych przecięć grup.

Ważne:

- ten etap nie wybiera jeszcze najlepszej ramki,
- `frame_side` nie jest ustawiane,
- overlay ramek jest osobnym retained artifactem notebooka i pipeline'u.

## Gdzie patrzeć teraz

Aktualny opis powiązanego pipeline'u znajduje się w:

- `logical_lines_process.md`
- `pipeline_overview.md`
- `logical_line_lifecycle.md`
- `logical_line_pixel_connection.md`
- `visualization_and_artifacts.md`
