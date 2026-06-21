# Raw Line Family Only - archiwum intersection analysis

## Status

Ten dokument opisuje usunięty etap eksperymentu.

W aktywnym kodzie:

- istnieją aktywne moduły `intersection_model.py` i
  `logical_line_intersections.py`,
- `detect_line_families(...)` buduje dziś aktywne `logical_line_intersections`,
- po pierwszym przypisaniu intersections kod trimuje jeszcze linie do przecięć
  i przelicza intersections ponownie,
- nadal nie ma etapu `intersection analysis`,
- `RawLineFamilyResult` nie przechowuje już pól:
  - `logical_line_intersection_analysis`
  - `logical_line_border_pairs`
  - `logical_line_frames`
- `FrameSide` pozostaje w modelu jako historyczny enum, ale nie jest już
  ustawiany przez końcowy etap pipeline'u.

## Co było wcześniej

W starszej wersji eksperymentu po `pixel connection` istniał dodatkowy etap:

- zbierania przecięć między rodzinami,
- orderingu przecięć,
- budowy kandydatów ramki,
- wyboru najlepszej ramki,
- przypisania `frame_side`.

To wyjaśnia, dlaczego starsze notatki i commity mogą odwoływać się do:

- `LogicalLineIntersection`,
- `LogicalLineBorderPair`,
- `LogicalLineFrame`,
- `LogicalLineIntersectionAnalysis`.

## Aktualny odpowiednik końca pipeline'u

Dziś po `pixel connection` kod:

- klonuje stan do `horizontal_post_connection_logical_lines` i
  `vertical_post_connection_logical_lines`,
- przypisuje aktywne `logical_line_intersections`,
- trimuje `horizontal_logical_lines` i `vertical_logical_lines` do przecięć,
- przelicza `logical_line_intersections` ponownie na finalnej geometrii,
- traktuje ten stan jako finalny wynik etapu detekcji.

## Gdzie patrzeć zamiast tutaj

Aktualny opis aktywnego końca pipeline'u znajduje się w:

- `logical_line_pixel_connection.md`
- `pipeline_overview.md`
- `visualization_and_artifacts.md`
