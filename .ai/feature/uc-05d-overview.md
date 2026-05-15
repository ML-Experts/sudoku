# UC-05D — Graficzne naniesienie cyfr na obraz

## Cel
Wygenerować obraz wynikowy z naniesionymi cyframi rozwiązania.

## Warianty
- wariant podstawowy: naniesienie cyfr na obraz planszy po korekcji perspektywy z `UC-04`,
- wariant ambitny: naniesienie cyfr na oryginalne zdjęcie wejściowe sprzed korekcji perspektywy.

## Kontrakt `FE -> BE`
### `POST /api/sudoku/overlay`
- Request body: `RenderSudokuOverlayApiEntry`.
- `200 OK` -> `ImageApiResponse`.

Minimalny zakres wejścia:
- `boardImage` jako `ImageApiEntry`,
- `recognizedGrid`,
- `solvedGrid`,
- `overlayMode`, np. `warpedBoard` albo `originalImage`.

Przykład:

```json
{
  "boardImage": {
    "mimeType": "image/png",
    "base64": "..."
  },
  "recognizedGrid": [
    [5, 3, null, null, 7, null, null, null, null],
    [6, null, null, 1, 9, 5, null, null, null],
    [null, 9, 8, null, null, null, null, 6, null],
    [8, null, null, null, 6, null, null, null, 3],
    [4, null, null, 8, null, 3, null, null, 1],
    [7, null, null, null, 2, null, null, null, 6],
    [null, 6, null, null, null, null, 2, 8, null],
    [null, null, null, 4, 1, 9, null, null, 5],
    [null, null, null, null, 8, null, null, 7, 9]
  ],
  "solvedGrid": [
    [5, 3, 4, 6, 7, 8, 9, 1, 2],
    [6, 7, 2, 1, 9, 5, 3, 4, 8],
    [1, 9, 8, 3, 4, 2, 5, 6, 7],
    [8, 5, 9, 7, 6, 1, 4, 2, 3],
    [4, 2, 6, 8, 5, 3, 7, 9, 1],
    [7, 1, 3, 9, 2, 4, 8, 5, 6],
    [9, 6, 1, 5, 3, 7, 2, 8, 4],
    [2, 8, 7, 4, 1, 9, 6, 3, 5],
    [3, 4, 5, 2, 8, 6, 1, 7, 9]
  ],
  "overlayMode": "warpedBoard"
}
```

Reguły odpowiedzi błędnych:
- `400 Bad Request` -> niepoprawny payload,
- `422 Unprocessable Entity` -> brak zgodności między `recognizedGrid`, `solvedGrid` i obrazem,
- `503 Service Unavailable` -> renderer `ML` jest niedostępny.

## Kontrakt `BE -> ML`
### `POST /ml/sudoku/overlay`
- Request body: ten sam biznesowy zestaw danych potrzebnych do renderu.
- Response body: `ImageApiResponse`.

## Uwagi
- Overlay jest osobną funkcjonalnością od samego solvera.
- Wariant na oryginalnym zdjęciu wymaga zachowania transformacji perspektywy z etapu preprocessingu.
- Generowanie overlay nie powinno blokować podstawowej prezentacji rozwiązania w gridzie.

## Kryteria akceptacji
- System potrafi wygenerować obraz wynikowy dla planszy po korekcji perspektywy.
- Brak overlay nie blokuje podstawowego wyniku w postaci siatki 9×9.
- Publiczny kontrakt renderowania przechodzi przez `Backend`.
