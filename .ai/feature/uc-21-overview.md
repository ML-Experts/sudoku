# UC-21 — Oczyszczenie komórki podczas przygotowania danych

## Cel
- Uporządkować etap przygotowania komórki dla danych `board` w `UC-17`.
- Współdzielić jeden produkcyjny pipeline `cell cleaning` między runtime inferencji i przygotowaniem datasetu.
- Zapewnić, że do `cells/` trafia oczyszczona kanoniczna próbka obrazu, a nie surowa komórka ani artefakt diagnostyczny.

## Historyjka
Jako operator ML chcę, aby podczas przygotowania datasetu komórki z plansz były oczyszczane tym samym docelowym pipeline'em co komórki używane później do inferencji cyfry, dzięki czemu dane treningowe i dane runtime pozostają spójne.

## Problem, który rozwiązujemy
W obecnym stanie projekt ma dwa osobne napięcia:
- runtime `UC-05` potrzebuje odróżniać pustą komórkę od niepustej,
- workflow datasetowy `UC-17` potrzebuje przygotować dobrą próbkę cyfry do `cells/`.

To nie są te same odpowiedzialności.

Detekcja pustej komórki:
- służy tylko do decyzji `empty` vs `non-empty`,
- ma być czuła na ślad cyfry,
- może korzystać z artefaktów diagnostycznych typu `center composite`.

Cleaning komórki:
- służy do przygotowania kanonicznej próbki obrazu pod model,
- ma upraszczać i stabilizować obraz,
- musi kończyć się próbką gotową do zapisu w `cells/`.

`UC-21` porządkuje wyłącznie ten drugi etap po stronie workflow datasetowego.

## Relacja do `UC-17`
`UC-21` nie zastępuje `UC-17`, tylko doprecyzowuje jego najważniejszy krok techniczny dla danych `board`.

`UC-17` dalej odpowiada za:
- wybór źródeł,
- wykrycie planszy,
- korekcję perspektywy,
- podział na siatkę 9×9,
- strukturę katalogów przygotowania,
- zapis `index.json`, `folders.json`, `file.json`.

`UC-21` doprecyzowuje:
- kiedy uruchamiać cleaning komórki,
- jaki obraz wolno zapisać do `cells/`,
- jakie zależności ma mieć ten cleaning względem runtime inferencji.

## Główna zasada workflow
Dla danych `board` obowiązuje kolejność:

1. system wykrywa planszę i koryguje perspektywę,
2. system dzieli planszę na `raw_cells`,
3. system odczytuje label przypisany do danej komórki,
4. jeśli label ma wartość `0`, komórka nie trafia do `cells/`,
5. jeśli label ma wartość `1..9`, system uruchamia wspólny `cell cleaning`,
6. oczyszczona próbka trafia do `cells/` oraz do lokalnego `index.json`.

Najważniejsza reguła biznesowa:
- o zapisie do `cells/` decyduje label,
- nie decyduje o tym runtime'owy algorytm `empty detection`.

## Źródło prawdy dla pustej komórki
W `UC-21` źródłem prawdy o tym, czy komórka ma zostać zapisana, jest przygotowany wcześniej label planszy.

To oznacza:
- label `0` -> brak zapisu do `cells/`,
- label `1..9` -> cleaning i zapis do `cells/`.

Algorytm detekcji pustej komórki z runtime:
- może być używany diagnostycznie,
- może służyć walidacji jakości danych,
- nie może decydować o tym, czy próbka ma wejść do datasetu treningowego.

## Wejście i wyjście pipeline'u
### Wejście
Cleaning w `UC-21` przyjmuje:
- surową komórkę `raw cell` wyciętą z `warped board`,
- docelowy profil preprocessingu modelowego,
- kontekst labela przypisanego do komórki.

### Wyjście
Produktem `UC-21` jest:
- oczyszczona próbka `uint8` gotowa do zapisu jako `.png` w `cells/`,
- opcjonalnie wariant `float32` zgodny z dalszym pipeline'em modelowym, jeśli jest potrzebny przez dalsze etapy techniczne,
- ale artefaktem trwałym w strukturze przygotowania pozostaje gotowa próbka obrazu dla `cells/`.

## Jaki obraz wolno zapisać do `cells/`
Do `cells/` wolno zapisać wyłącznie oczyszczoną kanoniczną próbkę pod model.

Do `cells/` nie wolno zapisywać jako próbki produkcyjnej:
- `raw cell`,
- `center composite`,
- obrazu z narysowanymi segmentami,
- overlayów diagnostycznych,
- numeracji planszy ani innych artefaktów pomocniczych.

## Współdzielenie z runtime
`UC-21` powinno współdzielić z runtime ten sam moduł `cell cleaning`, który przygotowuje obraz niepustej komórki do klasyfikacji cyfry.

Docelowa zależność:
- `UC-05` używa `cell cleaning` po decyzji `non-empty`,
- `UC-21` używa tego samego `cell cleaning` po decyzji labelowej `1..9`.

To ma ograniczyć ryzyko rozjazdu między:
- danymi treningowymi,
- danymi inferencyjnymi,
- jakością wyników aktywnego modelu.

## Zakres odpowiedzialności warstw
### `Frontend`
- Nie dostaje nowego publicznego endpointu tylko dla `UC-21`.
- Nadal uruchamia przygotowanie przez istniejący workflow `UC-17`.
- Nie decyduje samodzielnie, które komórki są puste.

### `Backend`
- Pozostaje właścicielem publicznego workflow przygotowania datasetu.
- Nie zmienia publicznych kontraktów `UC-17` tylko dlatego, że cleaning został doprecyzowany.
- Traktuje `ML` jako wykonawcę ciężkiego preprocessingu.

### `MachineLearning`
- Wykonuje wspólny cleaning komórki dla danych `board`.
- Zapisuje do `cells/` tylko próbki dla labeli `1..9`.
- Nie zapisuje diagnostycznych artefaktów jako właściwych próbek datasetowych.

## Kontrakty
`UC-21` nie dodaje nowego publicznego endpointu.

Pozostają bez zmian:
- `POST /api/datasets/preparations`,
- `GET /api/datasets/preparations`,
- `GET /api/datasets/preparations/{preparationName}`,
- `POST /ml/datasets/preparations`.

Zmiana dotyczy semantyki przygotowania danych wewnątrz istniejącego workflow, a nie osobnego kontraktu HTTP.

## Relacja do `UC-12`
`UC-21` przejmuje z dawnego `UC-12` ideę wspólnego preprocessingu modelowego dla:
- próbek `digit`,
- komórek wyciętych z `board`.

Jednocześnie odcina się od starego skrótu myślowego, w którym cały pipeline datasetowy i cały preprocessing były traktowane jako jeden nierozdzielny etap.

Po refaktorze:
- `UC-17` pozostaje workflow przygotowania,
- `UC-21` doprecyzowuje cleaning komórki w tym workflow,
- `UC-19` dalej odpowiada dopiero za build finalnego `.npz`.

## Poza zakresem
- zmiana struktury katalogów przygotowania,
- ręczna edycja labeli,
- budowa finalnego `.npz`,
- trening modelu,
- używanie runtime'owej detekcji pustej komórki jako bramki dla zapisu do `cells/`.

## Kryteria akceptacji
- Dla danych `board` system zapisuje do `cells/` tylko komórki z labelem `1..9`.
- Dla labela `0` komórka nie jest zapisywana do `cells/` ani do lokalnego `index.json`.
- Dla labeli `1..9` system uruchamia wspólny `cell cleaning` i zapisuje oczyszczoną próbkę jako wynik produkcyjny.
- `UC-21` wprost rozróżnia detekcję pustej komórki od cleaningu próbki pod model.
- Dokument jasno stwierdza, że źródłem prawdy o zapisie do `cells/` jest label, a nie algorytm runtime'owy.
- `center composite`, overlaye segmentów i inne artefakty diagnostyczne nie są zapisywane jako próbki `cells/`.
- `UC-21` nie wprowadza nowego publicznego endpointu i pozostaje częścią workflow `UC-17`.
