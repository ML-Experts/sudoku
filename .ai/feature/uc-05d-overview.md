# UC-05D — Graficzne naniesienie cyfr na obraz

## Cel
Wygenerować końcowy obraz rozwiązania przez dorysowanie cyfr na pojedynczych komórkach z etapu 2 `UC-04`, a następnie sklejenie ich w `FE` w jedną planszę 9x9 bez marginesów i przerw.

## Wybrany wariant implementacyjny
- Wariant podstawowy nie renderuje całej planszy po stronie `ML`.
- Po zakończonym backtrackingu `FE` wysyła kolejne komórki z etapu 2 `UC-04` do wyrenderowania.
- Każde żądanie zawiera pojedynczy obraz komórki jako `base64` oraz cyfrę, która ma zostać narysowana na tej komórce.
- `Backend` jest wyłącznie warstwą pośrednią: waliduje kontrakt, przekazuje żądanie do `ML` i zwraca odpowiedź bez własnej logiki renderowania.
- `ML` używa `OpenCV` do naniesienia cyfry na pojedynczą komórkę i odsyła wyrenderowany obraz tej komórki.
- `FE` odbiera kolejne wyrenderowane komórki i skleja je lokalnie w finalny obraz planszy 9x9 bez paginacji, bez marginesów i bez odstępów między kafelkami.
- Taki podział pozwala uzyskać efekt dynamicznego, płynnego pojawiania się rozwiązania.

## Warianty
- wariant podstawowy: render per-komórka dla obrazów komórek po podziale planszy z `UC-04`,
- wariant ambitny: render na oryginalnym zdjęciu wejściowym z użyciem zachowanej transformacji perspektywy; poza zakresem tego etapu.

## Zakres odpowiedzialności warstw
### `Frontend`
- Przechowuje wynik etapu 2 `UC-04`, czyli siatkę obrazów komórek.
- Po uzyskaniu `solvedGrid` decyduje, które komórki mają zostać wysłane do renderowania.
- Wysyła komórki do `Backendu` po kolei, aby możliwe było stopniowe odświeżanie widoku.
- Odbiera wyrenderowane obrazy komórek i skleja je w jedną planszę 9x9.
- Sklejanie odbywa się bez żadnych przerw, ramek i marginesów między komórkami.

### `Backend`
- Udostępnia publiczny endpoint renderowania per-komórka.
- Jest cienką warstwą pośrednią między `FE` i `ML`.
- Nie używa własnych bibliotek graficznych i nie skleja planszy.
- Waliduje minimalnie payload i mapuje błędy `ML` na publiczny kontrakt HTTP.

### `MachineLearning`
- Przyjmuje pojedynczą komórkę i cyfrę do naniesienia.
- Używa `OpenCV` do wyrenderowania cyfry na obrazie komórki.
- Zwraca wyrenderowaną komórkę jako `ImageApiResponse`.
- Nie skleja finalnej planszy w wariancie podstawowym.

## Kontrakt `FE -> BE`
### `POST /api/sudoku/overlay/cells`
- Request body: `RenderSudokuOverlayCellApiEntry`.
- `200 OK` -> `ImageApiResponse`.

Minimalny zakres wejścia:
- `cellImage` jako `ImageApiEntry`,
- `digit` jako wartość `1..9`,
- opcjonalnie `rowIndex`,
- opcjonalnie `columnIndex`.

Przykład:

```json
{
  "cellImage": {
    "mimeType": "image/png",
    "base64": "..."
  },
  "digit": 4,
  "rowIndex": 0,
  "columnIndex": 2
}
```

Uwagi kontraktowe:
- Wariant podstawowy zakłada wywołanie endpointu dla pojedynczej komórki.
- `rowIndex` i `columnIndex` są opcjonalne i służą głównie do diagnostyki, logowania albo późniejszego rozszerzenia kontraktu.
- Publiczny kontrakt nie przekazuje całej planszy ani pełnego `recognizedGrid` / `solvedGrid`.
- `FE` może wysyłać tylko te komórki, które wymagają dorysowania cyfry po rozwiązaniu.

Reguły odpowiedzi błędnych:
- `400 Bad Request` -> niepoprawny payload,
- `422 Unprocessable Entity` -> niepoprawna komórka lub niedozwolona cyfra,
- `503 Service Unavailable` -> renderer `ML` jest niedostępny.

## Kontrakt `BE -> ML`
### `POST /ml/sudoku/overlay/cells`
- Request body: ten sam biznesowy zestaw danych potrzebnych do renderu pojedynczej komórki.
- Response body: `ImageApiResponse`.

## Szczegóły renderowania w `ML`
- Implementacja bazuje na `OpenCV`.
- `ML` dekoduje `base64` do obrazu komórki, renderuje cyfrę i ponownie koduje wynik do `base64`.
- Rysowanie cyfry odbywa się na pojedynczej komórce, bez wiedzy o całej planszy.
- W wariancie podstawowym preferujemy prostotę i przewidywalność implementacji nad zaawansowaną typografią.

## Uwagi
- Overlay pozostaje osobną funkcjonalnością od samego solvera.
- Brak wygenerowanego overlay nie blokuje podstawowej prezentacji rozwiązania jako grid 9x9.
- Wariant renderowania na całej planszy po stronie `ML` nie jest wybrany dla tego etapu.
- Wariant na oryginalnym zdjęciu wymaga osobnego podejścia i zachowania transformacji perspektywy z preprocessingu.

## Kryteria akceptacji
- System potrafi wyrenderować cyfrę na pojedynczej komórce pochodzącej z etapu 2 `UC-04`.
- `Backend` pełni wyłącznie rolę warstwy pośredniej dla publicznego kontraktu renderowania.
- `ML` używa `OpenCV` do naniesienia cyfry na obraz komórki.
- `FE` potrafi skleić wyrenderowane komórki w jedną planszę 9x9 bez odstępów między nimi.
- Renderowanie komórek może być wykonywane sekwencyjnie, dzięki czemu `UI` może pokazywać efekt dynamicznego budowania końcowego obrazu.
