# UC-20 — Wstepna obrobka lokalnego zdjecia Sudoku bez zapisu na serwerze

## Cel
- Umozliwic uzytkownikowi wybranie obrazu Sudoku bezposrednio z lokalnego komputera.
- Zachowac ten sam dwuetapowy preprocessing co w `UC-04`:
  - wykrycie planszy i korekcja perspektywy,
  - podzial planszy na siatke `9x9`.
- Nie zapisywac przeslanego obrazu ani wynikow preprocessingu na dysku serwera.

## Historyjka
Jako uzytkownik chce wybrac lokalne zdjecie Sudoku z mojego komputera i od razu uruchomic na nim ten sam preprocessing co dla przykladu z `UC-04`, aby system przygotowal plansze i siatke `9x9` bez dodawania pliku do biblioteki przykladow i bez trwalego zapisu po stronie serwera.

## Glowna zasada workflow
1. Uzytkownik wybiera plik obrazu Sudoku z lokalnego komputera.
2. `Frontend` odczytuje plik, waliduje podstawowe kryteria klientowe i przygotowuje payload `ImageApiEntry`.
3. `Frontend` pokazuje podglad obrazu lokalnie, bez pobierania go z `GET /api/examples/{name}`.
4. `Frontend -> Backend` wysyla obraz jako `ImageApiEntry` do nowego endpointu `PUT /api/examples/preprocess/board`.
5. `Backend` waliduje payload, dekoduje `base64`, nie zapisuje pliku na dysku i przekazuje obraz do `ML`.
6. `ML` wykonuje ten sam etap preprocessingu co w `UC-04` dla `board` i zwraca wyprostowana plansze jako `ImageApiResponse`.
7. `Frontend` przechowuje wynik etapu `board` w pamieci klienta i wysyla go do istniejacego `PUT /api/examples/preprocess/cells`.
8. `Backend -> ML` uruchamia istniejacy etap `cells`, a `ML` zwraca `CellsGridApiResponse`.
9. Wynik przeplywa `ML -> BE -> FE` bez trwalego zapisu obrazu zrodlowego ani wynikow posrednich.

## Relacja do `UC-03` i `UC-04`
### Co pozostaje takie samo wzgledem `UC-04`
- preprocessing pozostaje dwuetapowy:
  - `board`,
  - `cells`,
- `Frontend` po etapie `board` przekazuje wynik dalej do etapu `cells`,
- `ML` wykonuje te same operacje wykrycia planszy, korekcji perspektywy i podzialu na siatke `9x9`,
- wynik etapu `cells` pozostaje macierza obrazow `9x9`.

### Co zmienia sie wzgledem `UC-04`
- zrodlem obrazu nie jest rekord `example` zapisany na serwerze,
- `Backend` nie czyta pliku po `name` z magazynu `examples`,
- publiczny endpoint `board` dostaje alternatywny wariant wejscia przyjmujacy `ImageApiEntry`,
- `UC-20` reuse'uje istniejacy endpoint `PUT /api/examples/preprocess/cells` bez zmiany jego semantyki.

### Co pozostaje podobne wzgledem `UC-03`
- uzytkownik nadal wybiera konkretny obraz do dalszej pracy,
- `Frontend` moze utrzymac podobny UX wyboru i podgladu obrazu,
- roznica polega na tym, ze obraz nie pochodzi z listy rekordow `examples`, tylko z lokalnego pliku uzytkownika.

## Zrodlo obrazu i brak trwalego zapisu
- obraz wejsciowy pochodzi z lokalnego pliku uzytkownika,
- `Frontend` zamienia go na `ImageApiEntry` z polami `mimeType` i `base64`,
- `Backend` i `ML` przetwarzaja obraz w trybie stateless,
- przeslany obraz nie trafia do biblioteki `examples`,
- wynik etapu `board` nie jest zapisywany na dysku,
- wynik etapu `cells` nie jest zapisywany na dysku,
- po zakonczeniu requestow system nie utrzymuje trwalego rekordu tego lokalnego obrazu.

## Endpointy i kontrakty
### `Frontend -> Backend`
Endpointy:
- `PUT /api/examples/preprocess/board`
- `PUT /api/examples/preprocess/cells`

Po co:
- `PUT /api/examples/preprocess/board` przyjmuje lokalny obraz od uzytkownika jako `ImageApiEntry` i zwraca plansze po korekcji perspektywy,
- `PUT /api/examples/preprocess/cells` przyjmuje wynik etapu `board` jako `ImageApiEntry` i zwraca siatke komorek `9x9`.

Status endpointow:
- `PUT /api/examples/preprocess/board` — nowy endpoint do dodania,
- `PUT /api/examples/preprocess/cells` — endpoint juz istnieje i jest reuse'owany bez zmiany semantyki.

### `Backend -> MachineLearning`
Endpointy:
- `PUT /ml/preprocess/board`
- `PUT /ml/preprocess/cells`

Status endpointow:
- `PUT /ml/preprocess/board` — endpoint juz istnieje i moze zostac wykorzystany bez zmiany semantyki,
- `PUT /ml/preprocess/cells` — endpoint juz istnieje i moze zostac wykorzystany bez zmiany semantyki.

## Kontrakty API
### `PUT /api/examples/preprocess/board`
Request: `ImageApiEntry`

```json
{
  "mimeType": "image/jpeg",
  "base64": "/9j/4AAQSkZJRgABAQAAAQABAAD..."
}
```

Response: `ImageApiResponse`

```json
{
  "mimeType": "image/png",
  "base64": "iVBORw0KGgoAAAANSUhEUgAA..."
}
```

### `PUT /api/examples/preprocess/cells`
Request: `ImageApiEntry`

```json
{
  "mimeType": "image/png",
  "base64": "iVBORw0KGgoAAAANSUhEUgAA..."
}
```

Response: `CellsGridApiResponse`

```json
{
  "cells": [
    [
      {
        "mimeType": "image/png",
        "base64": "iVBORw0KGgoAAAANSUhEUgAA..."
      }
    ]
  ]
}
```

## Modele API wejsciowe
- `ImageApiEntry`
  - `mimeType: string`
  - `base64: string`

## Modele API wyjsciowe
- `ImageApiResponse`
  - `mimeType: string`
  - `base64: string`
- `CellsGridApiResponse`
  - `cells: ImageApiResponse[9][9]`
- `ErrorApiResponse`
  - `errorType: string`
  - `message: string`

## Zasady walidacji
### `Frontend`
- pozwala wybrac tylko obslugiwane typy plikow obrazu,
- moze odrzucic pliki zbyt duze jeszcze przed wyslaniem do `Backendu`,
- przygotowuje `mimeType` i `base64` zgodne z kontraktem `ImageApiEntry`.

### `Backend`
- waliduje, ze `mimeType` jest obecny i dozwolony,
- waliduje, ze `base64` jest obecne i poprawnie dekodowalne,
- waliduje limit rozmiaru obrazu po dekodowaniu,
- nie tworzy rekordu `example` i nie zapisuje pliku do magazynu `examples`.

## Bledy API
- `400 Bad Request`
- `422 Unprocessable Content`
- `503 Service Unavailable`
- `504 Gateway Timeout`

Przyklad:

```json
{
  "errorType": "board_not_found",
  "message": "Nie wykryto planszy sudoku na obrazie."
}
```

## Zasady odpowiedzialnosci
### `Frontend`
- wybiera lokalny plik,
- konwertuje go do `ImageApiEntry`,
- przechowuje wynik etapu `board` w pamieci klienta,
- nie komunikuje sie bezposrednio z `ML`.

### `Backend`
- wystawia publiczny alternatywny endpoint dla etapu `board`,
- waliduje wejscie,
- orkiestruje wywolania do `ML`,
- reuse'uje istniejacy publiczny endpoint `cells`,
- nie zapisuje przeslanego obrazu ani wynikow posrednich na dysku.

### `MachineLearning`
- wykonuje ten sam preprocessing co w `UC-04`,
- przyjmuje obraz inline,
- nie zapisuje wynikow preprocessingu na dysku w tym use-case'u.

## Poza zakresem
- usuwanie albo modyfikacja istniejacego `UC-03`,
- usuwanie albo modyfikacja istniejacego `UC-04`,
- dodawanie nowego publicznego endpointu `cells`,
- dodawanie lokalnego pliku do biblioteki `examples`,
- trwale przechowywanie historii przeslanych obrazow,
- rozpoznanie cyfr i rozwiazanie Sudoku jako wynik tego use-case'u; to pozostaje w relacji do `UC-05`.

## Wynik biznesowy
Wynikiem `UC-20` jest mozliwosc uruchomienia tego samego preprocessingu co w `UC-04` bez koniecznosci wczesniejszego zapisania obrazu na serwerze. Uzytkownik moze pracowac na lokalnym pliku, a system zachowuje architekture `FE -> BE -> ML`, reuse'uje istniejacy etap `cells` i nie zmienia dotychczasowej sciezki pracy opartej o `examples`.
