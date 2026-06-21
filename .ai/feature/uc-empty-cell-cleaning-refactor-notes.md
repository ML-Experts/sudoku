# Wnioski pod nowe UC - detekcja pustej komorki i czyszczenie komorki

## Cel notatki
Ta notatka zbiera wnioski do przyszlego UC refaktoryzacyjnego, ktore ma uporzadkowac wspolny pipeline pracy na komorkach Sudoku wykorzystywany przez:
- runtime solve z `UC-05*`,
- przygotowanie danych z `UC-17`,
- dalszy trening z `UC-06`.

Najwazniejszy cel refaktoryzacji:
- nie mieszac logiki detekcji pustej komorki z logika czyszczenia komorki pod klasyfikacje i trening,
- utrzymac jeden wspolny punkt wejscia dla pracy na `raw 9x9 cells`,
- zostawic wizualizacje jako warstwe diagnostyczna, a nie jako element glownego pipeline'u.

## Stan obecny
Aktualny eksperymentalny kierunek jest wydzielony w:
- `src/MachineLearning/draft/raw_line_family_only/search_empty_cell/core.py`,
- `src/MachineLearning/draft/raw_line_family_only/search_empty_cell/grid.py`,
- `src/MachineLearning/draft/raw_line_family_only/search_empty_cell/visualization.py`.

Obecny podzial jest dobrym punktem startowym, bo rozdziela juz:
- binaryzacje,
- czyszczenie szumu,
- zlozenie obrazu z wewnetrznych cwiartek,
- wykrywanie segmentow Hough,
- filtrowanie i zliczanie segmentow,
- liczenie foreground pixels,
- wizualizacje diagnostyczne.

## Glowny wniosek architektoniczny
Przyszly wspolny UC powinien rozdzielic dwa osobne etapy:

1. `Empty cell detection`
- odpowiada tylko za decyzje, czy komorka jest pusta czy niepusta,
- pracuje na `raw` komorce wycietej z `warped board`,
- nie produkuje jeszcze kanonicznej probki do modelu.

2. `Cell cleaning for classification/training`
- uruchamia sie dopiero dla komorki uznanej za niepusta,
- przygotowuje finalny obraz do klasyfikacji albo do zapisu datasetowego,
- odpowiada za format kanoniczny zgodny z modelem.

To rozdzielenie jest kluczowe, bo detekcja pustosci i czyszczenie pod model maja inny cel:
- detekcja pustosci ma byc czula na slad cyfry,
- czyszczenie pod model ma normalizowac i upraszczac obraz,
- zbyt wczesne czyszczenie modelowe moze usunac sygnal potrzebny do rozpoznania, czy komorka jest pusta.

## Gdzie wprowadzic czyszczenie komorki
### Runtime `UC-05`
Kolejnosc powinna byc nastepujaca:
1. `UC-04` zwraca `raw_cells` z planszy `9x9`.
2. Dla kazdej komorki uruchamiana jest detekcja pustosci na `raw` komorce.
3. Jesli komorka jest pusta, wynik to `null` i nie uruchamiamy dalszego czyszczenia pod klasyfikator.
4. Jesli komorka jest niepusta, dopiero wtedy uruchamiamy czyszczenie / normalizacje pod model.
5. Oczyszczona komorka trafia do inferencji cyfry.

Wniosek:
- czyszczenie komorki pod rozpoznanie cyfry powinno byc wprowadzone po detekcji pustosci, a nie przed nia.

### Dataset preparation `UC-17`
Tu trzeba rozroznic dwa osobne przypadki:

1. `UC-17` nie rozstrzyga pustosci komorki na podstawie algorytmu runtime.
2. Zrodlem prawdy dla tego, czy komorka ma trafic do `cells/`, jest przygotowany wczesniej label.

Dla danych `board` kolejnosc powinna byc nastepujaca:
1. wykrycie planszy,
2. korekcja perspektywy,
3. podzial na `raw_cells`,
4. odczyt labela przypisanego do danej komorki,
5. jesli label to `0`, komorka nie trafia do `cells/`,
6. jesli label to `1..9`, uruchamiane jest czyszczenie modelowe tej komorki,
7. oczyszczona kanoniczna probka trafia do przygotowania datasetu.

Wniosek:
- `UC-17` nie powinien uzywac algorytmu `empty detection` jako bramki decyzyjnej do zapisu `cells/`,
- `UC-17` powinien uzywac labela jako zrodla prawdy biznesowej,
- ewentualna detekcja pustosci moze byc co najwyzej diagnostyczna albo walidacyjna, ale nie decyzyjna.

## Jak zastapic obecne funkcje
Aktualne funkcje z `search_empty_cell` warto potraktowac jako zalazek docelowego pipeline'u, ale nie jako finalny kontrakt produkcyjny.

### Funkcje, ktore warto zachowac jako wewnetrzne etapy
- `build_binary_mask(...)`
- `clean_binary_mask(...)`
- `build_center_quadrant_composite(...)`
- `detect_hough_segments(...)`
- `filter_short_segments(...)`
- `count_foreground_pixels(...)`
- `count_foreground_pixel_ratio(...)`

Te funkcje sa dobrymi klockami niskiego poziomu i warto je utrzymac jako warstwe implementacyjna.

### Funkcje, ktore warto traktowac jako wewnetrzne helpery, a nie docelowe publiczne API
- `preprocess_raw_cell_bgr(...)`
- `analyze_empty_cell_preprocessing(...)`
- `analyze_raw_cell_bgr(...)`

Sa dobre dla eksperymentu i diagnostyki, ale w docelowym UC lepiej wystawic wyzszy poziom abstrakcji z jasnym kontraktem biznesowym.

### Funkcje, ktore warto utrzymac jako wysokopoziomowe wejscie batchowe
- `analyze_raw_cells_grid(...)`
- `get_cell_result_by_number(...)`

Szczegolnie `analyze_raw_cells_grid(...)` dobrze pasuje do rzeczywistego workflow `board -> 9x9`.

### Funkcje, ktore powinny pozostac tylko diagnostyczne
- `draw_numbered_board_overlay(...)`
- `draw_status_board_overlay(...)`
- `render_segments_overlay(...)`
- `render_segments_preview_image(...)`

Nie powinny wejsc do glownego kontraktu runtime ani datasetowego. Sa przydatne dla notebookow, preview i debugowania.

## Ktory obraz do czego sluzy
Trzeba to rozdzielic bardzo jasno:

### Obrazy tylko diagnostyczne
- `center composite` zbudowany z 4 wewnetrznych cwiartek,
- obraz z nalozonymi segmentami Hough,
- wszelkie overlaye statusu i numeracji.

Te obrazy:
- nie sluza do `digit inference`,
- nie sluza do `save prepared sample`,
- nie powinny trafic do finalnego `cells/`.

### Obraz produkcyjny do dalszego pipeline'u
Do dalszego przetwarzania powinna trafic tylko oczyszczona komorka przygotowana pod model.

To ona:
- trafia do `digit inference` w runtime,
- trafia do `cells/` w `UC-17`,
- powinna byc baza do budowy wariantu `uint8` i `float32`.

## Rekomendowany nowy podzial modulow
Docelowo warto miec trzy osobne warstwy:

### 1. `empty_cell_detection`
Odpowiada za:
- binaryzacje do analizy pustosci,
- cleanup szumu,
- zlozenie centralnego composite,
- Hough i metryki,
- decyzje `is_empty`.

Przykladowy wynik:
- `is_empty`,
- `accept_by_pixels`,
- `accept_by_segments`,
- `foreground_pixel_count`,
- `foreground_pixel_ratio`,
- `filtered_segment_count`,
- opcjonalnie artefakty diagnostyczne.

### 2. `cell_cleaning`
Odpowiada za:
- przygotowanie komorki niepustej do modelu,
- crop / center / resize / normalizacje,
- zwrot `uint8` i opcjonalnie `float32`.

To powinien byc wspolny pipeline dla:
- inferencji cyfry w runtime,
- zapisu przygotowania datasetu,
- ewentualnie preview jakosci danych.

### 3. `visualization`
Odpowiada tylko za:
- overlaye,
- preview siatki,
- obrazy diagnostyczne do notebookow.

## Rekomendowany kontrakt dla przyszlego UC
Nowy UC powinien opisywac nie pojedyncze helpery, ale wspolny przeplyw:

1. wejscie: `raw_cells` z `UC-04` albo z datasetowego preprocessingu `board`,
2. etap A runtime: detekcja pustosci,
3. etap B: czyszczenie komorki pod model,
4. etap C: wynik gotowy do:
   - runtime inferencji cyfry,
   - zapisu przygotowania datasetu,
   - preview diagnostycznego.

Wazne doprecyzowanie:
- w runtime `UC-05` etap A jest decyzyjny,
- w `UC-17` etap A nie jest zrodlem prawdy decyzyjnej; tam decyduje label,
- `UC-17` korzysta przede wszystkim z etapu B, czyli z czyszczenia komorki pod model.

Minimalny kontrakt wyjsciowy powinien pozwalac na:
- odczyt statusu `is_empty`,
- pobranie oczyszczonej probki `uint8`,
- pobranie wariantu `float32` zgodnego z aktualnym pipeline'em modelowym,
- opcjonalny podglad diagnostyczny dla notebookow.

## Wplyw na `UC-05D`
`UC-05D` nie powinien przejmowac odpowiedzialnosci za detekcje pustosci ani za czyszczenie pod klasyfikator.

Wniosek dla `UC-05D`:
- overlay powinien dalej operowac na obrazie komorki przeznaczonym do prezentacji,
- najlepiej na `raw cell` albo na wariancie prezentacyjnym wyprowadzonym z `UC-04`,
- bez mieszania tego z kanoniczna probka treningowo-modelowa.

To oznacza, ze przyszly UC refaktoryzacyjny powinien dostarczyc `UC-05D` tylko stabilne wejscie obrazowe, ale nie wciskac do niego logiki rozpoznawania pustej komorki.

## Wplyw na `UC-17`
`UC-17` nie powinien korzystac z runtime'owego wykrywania pustosci jako zrodla prawdy o tym, czy komorka jest pusta.

Wniosek dla `UC-17`:
- decyzja o zapisie do `cells/` powinna wynikac z labela,
- czyszczenie pod model powinno byc wspoldzielone,
- zapis artefaktow datasetowych powinien pozostac osobna odpowiedzialnoscia `UC-17`.
- obrazy diagnostyczne typu `center composite` albo `segments overlay` nie powinny byc zapisywane jako probki `cells/`.

## Co powinno trafic do opisu nowego UC
- uzasadnienie, dlaczego detekcja pustosci jest etapem przed klasyfikacja w runtime,
- uzasadnienie, dlaczego czyszczenie modelowe ma byc odpalane tylko dla komorek niepustych,
- jasne rozroznienie, ze w `UC-17` decyzja o zapisie komorki wynika z labela, a nie z algorytmu `empty detection`,
- jasny podzial na runtime contract, dataset contract i diagnostyke,
- wskazanie jednego wspolnego modulu wykorzystywanego przez `UC-05*`, `UC-17` i `UC-06`,
- rozdzielenie API produkcyjnego od helperow notebookowych,
- wskazanie miejsca, w ktorym powstaje probka `uint8`,
- wskazanie miejsca, w ktorym powstaje probka `float32`,
- wskazanie, ze `center composite` i `segments overlay` sa tylko diagnostyczne,
- decyzja, ktore artefakty sa tylko tymczasowe / diagnostyczne, a ktore sa czescia kontraktu.

## Najkrotsza rekomendacja implementacyjna
Jesli mamy wdrozyc to praktycznie, najlepszy kierunek jest nastepujacy:

1. utrzymac `search_empty_cell` jako eksperymentalne zrodlo wiedzy,
2. wyciagnac z niego wspolny modul produkcyjny do detekcji pustosci,
3. obok niego wprowadzic osobny wspolny modul do czyszczenia komorki pod model,
4. w `UC-05` wykonywac: `raw cell -> empty detection -> cleaning -> digit inference`,
5. w `UC-17` wykonywac: `raw cell -> label decision -> cleaning -> save prepared sample`,
6. zostawic overlaye i preview poza glownym pipeline'em biznesowym.
