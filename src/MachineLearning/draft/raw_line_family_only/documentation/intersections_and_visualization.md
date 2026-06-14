# Raw Line Family Only - archiwum etapu intersections

## Status

Ten dokument jest historyczną notatką po usunięciu z aktywnego kodu etapu
`intersection/frame`.

W aktualnej wersji eksperymentu:

- pipeline kończy się na `pixel connection`,
- finalne `horizontal_logical_lines` i `vertical_logical_lines` oznaczają już
  wynik po connection,
- nie istnieją aktywne moduły `intersection_*`,
- nie istnieją też overlaye intersections ani ramki.

## Co pozostało aktualne

Z dawnego opisu końcowego etapu nadal warto pamiętać tylko o tym, że:

- wejściem do dawnych eksperymentów intersections był stan `post_connection`,
- wizualizacje i raport były traktowane jako część eksperymentu, a nie poboczny
  dodatek,
- `post_connection` nadal jest ważnym snapshotem diagnostycznym.

## Gdzie patrzeć teraz

Aktualny opis aktywnego pipeline'u znajduje się w:

- `logical_lines_process.md`
- `pipeline_overview.md`
- `logical_line_lifecycle.md`
- `logical_line_pixel_connection.md`
- `visualization_and_artifacts.md`

## Dlaczego plik został

Zostawiamy ten dokument w repo jako ślad po wcześniejszym kierunku rozwoju,
żeby łatwiej odczytać starsze notatki, commity i rozmowy odnoszące się do
`intersections`.
