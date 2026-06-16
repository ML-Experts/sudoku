# Raw Line Family Only - intersections i wizualizacja

## Status

Ten dokument opisuje aktualny, aktywny etap zbierania intersections po
`pixel connection`.

W aktualnej wersji eksperymentu:

- finalna geometria linii kończy się na `pixel connection`,
- po connection kod buduje aktywne `logical_line_intersections`,
- nie ma aktywnego etapu wyboru ramki ani przypisania `frame_side`,
- intersections mają już własny overlay w notebooku i pipeline.

## Główne pliki

- `intersection_models.py`
- `logical_line_intersections.py`
- `visualization/visualization_intersections.py`
- `detection.py`
- `pipeline/pipeline.py`
- `pipeline/pipeline_report.py`

## Wejście do etapu

Intersections są dziś budowane na:

- `horizontal_logical_lines`
- `vertical_logical_lines`

czyli na finalnych rodzinach linii po `pixel connection`.

To znaczy:

- connection odpowiada za finalną geometrię linii,
- intersections już nie zmieniają jeszcze linii,
- przecięcia są aktywnym opisem relacji między rodzinami po domknięciu
  geometrii.

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
- pola:
  - `horizontal_order`
  - `vertical_order`

Ważne rozróżnienie:

- `kind` jest dziś liczone niezależnie od `IntersectionOrder`,
- `horizontal_order` i `vertical_order` pozostają przygotowane pod kolejny etap
  klasyfikacji i naprawy geometrii,
- pola orderów startują jako `NONE`.

## Aktualna heurystyka budowy intersections

Publiczny entrypoint:

- `build_logical_line_intersections(...)`

Aktualny przebieg:

1. kod iteruje po parach finalnych linii `horizontal` / `vertical`,
2. dla każdej pary sprawdza pary segmentów należących do tych linii,
3. liczy punkt przecięcia linii wspierających segmenty,
4. odrzuca kandydatów, których punkt nie leży na obu skończonych segmentach,
5. klasyfikuje lokalny `kind` na podstawie pozycji punktu na segmentach
   referencyjnych,
6. wybiera najlepszy kandydat dla danej pary linii.

Dzisiejsza reguła `kind` jest lokalna i segmentowa:

- `cross` tylko wtedy, gdy punkt leży w `MIDDLE` obu segmentów referencyjnych,
- w przeciwnym razie `touch`.

## Wizualizacja

Publiczna funkcja renderująca:

- `build_logical_line_intersection_overlays(...)`

Overlay pokazuje:

- punkt przecięcia,
- inny marker dla `cross` i `touch`,
- etykietę pary linii, np. `H3xV7`,
- dodatkowe obramowanie boundary, jeśli w przyszłości order dla którejś linii
  zostanie ustawiony na granicę.

## Gdzie patrzeć teraz

Aktualny opis powiązanego pipeline'u znajduje się w:

- `logical_lines_process.md`
- `pipeline_overview.md`
- `logical_line_lifecycle.md`
- `logical_line_pixel_connection.md`
- `visualization_and_artifacts.md`
