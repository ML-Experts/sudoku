# UC-17 — Przygotowanie datasetu

## Cel
- Wprowadzić trwały etap pośredni pomiędzy danymi `raw` a finalnym `.npz`.
- Wykonać ciężki preprocessing `board -> corrected-board -> cells` tylko raz.
- Oddzielić etap technicznego przygotowania danych od etapu splitu i budowy finalnego datasetu treningowego.

## Historyjka
Jako operator ML chcę utworzyć przygotowanie datasetu z danych `raw`, aby raz przygotować gotowe plansze, komórki i próbki `digit`, a następnie wielokrotnie je przeglądać, czyścić i wykorzystywać do budowy finalnego `.npz`.

## Główna zasada workflow
1. Użytkownik wybiera źródła `raw`.
2. Użytkownik nadaje nazwę przygotowania.
3. Dla źródeł typu `board` system wykonuje dokładnie te ciężkie operacje, które wcześniej były wykonywane w `UC-12` podczas bezpośredniej budowy `.npz`:
   - rekurencyjny skan wybranego katalogu źródłowego,
   - odczyt i walidację par `.jpg` + `.dat`,
   - parsowanie etykiet planszy,
   - wykrycie planszy,
   - korekcję perspektywy,
   - podział na siatkę 9×9,
   - preprocessing pojedynczych komórek do wspólnego kanonicznego formatu obrazu.
4. Dla źródeł typu `digit` system wykonuje dokładnie te operacje, które wcześniej były wykonywane w `UC-12` dla danych `digit`:
   - odczyt i walidację par `*.idx3-ubyte` + `*.idx1-ubyte`,
   - preprocessing pojedynczych próbek do tego samego kanonicznego formatu obrazu.
5. System zapisuje trwałą strukturę plikową przygotowania wraz z indeksami i plikami list wykorzystywanymi później przez `UC-18` i `UC-19`.
6. Dla `board` system zapisuje tylko te komórki, które mają realny label `1..9`; komórki z wartością `0` nie są zapisywane do folderu `cells` i nie pojawiają się w lokalnym `index.json`.
7. Wynikiem nie jest jeszcze `.npz`.

## Wynik biznesowy
Wynikiem `UC-17` jest nowy byt pośredni:
- przygotowanie datasetu,
- z własną nazwą,
- własną strukturą plików,
- własnymi indeksami i manifestami,
- gotowe do późniejszego przeglądania i budowy `.npz`.

## Zakres danych
### `board`
- obraz planszy po korekcji perspektywy,
- folder pojedynczej planszy jako jednostka dalszego czyszczenia,
- folder `cells` z gotowymi komórkami,
- lokalny `index.json` dla komórek o takim samym formacie jak dla `digit`.

### `digit`
- gotowe próbki po preprocessingu,
- lokalny `index.json` z relacją `fileName + label`.

## Rozpoznanie typu źródła i nazewnictwo folderów
### Skąd wiadomo, że źródło jest `board` albo `digit`
- źródłem prawdy dla rozróżnienia `board` vs `digit` jest etap wykrywania kandydatów z `UC-11`,
- `Backend` rozpoznaje typ na podstawie tego, z którego katalogu logicznego pochodzi rekord:
  - rekord z `data/raw/boards` jest typu `board`,
  - rekord z `data/raw/digits` jest typu `digit`,
- `Frontend` nie zgaduje typu samodzielnie; dostaje go w rekordzie kandydata `RawDatasetCandidateApiResponse`,
- podczas tworzenia przygotowania użytkownik wybiera rekordy `{ name, type }`, a `Backend` i `ML` zachowują ten typ jako kontrakt wejściowy i dodatkowo walidują spójność wyboru.

### Na jakiej podstawie tworzone są foldery źródłowe dla `digit`
- dla `digit` folder źródłowy w przygotowaniu jest tworzony w relacji `1:1` do logicznego kandydata wykrytego wcześniej w `UC-11`,
- nazwa folderu `{sourceName}` dla `digit` jest kopiowana z nazwy rekordu zwróconego przez `GET /api/datasets/raw-candidates`,
- nie ma tutaj dodatkowego heurystycznego nadawania nazw na podstawie zawartości przygotowanych `.png`,
- jeśli kandydat `digit` został wykryty w `UC-11` jako np. `mnist_train` albo `t10k`, to dokładnie taka sama nazwa staje się folderem:

```text
{DATASET_PREPARATIONS_DIRECTORY_PATH}/{preparationName}/digit/{sourceName}/
```

- reguła ta jest analogiczna do `board`: foldery źródłowe w przygotowaniu zachowują nazwy logicznych kandydatów wejściowych, a różni się tylko ich wewnętrzna struktura.

## Źródło i zakres preprocessingu
- wzorcowym pipeline'em preprocessingu dla `UC-17` jest preprocessing treningowy z obecnego `UC-12`,
- oznacza to, że `UC-17` ma przejąć ten sam kanoniczny format próbki dla danych treningowych, ten sam profil preprocessingu oraz tę samą semantykę wspólnego pipeline'u dla `digit` i komórek wyciętych z `board`,
- w szczególności jako punkt odniesienia przyjmujemy obecny flow z `UC-12`:
  - dla `digit`: walidacja par IDX-UBYTE i preprocessing pojedynczych próbek,
  - dla `board`: skan `.jpg + .dat`, wykrycie planszy, korekcja perspektywy, podział na komórki i uruchomienie tego samego preprocessingu komórek co dla `digit`,
  - batch preprocessing do kanonicznego formatu wejściowego modelu, obejmujący binaryzację, wyostrzenie, konwersję do skali szarości / czarno-białego formatu, centrowanie cyfry i normalizację rozmiaru do `28x28` albo innego aktywnego formatu wejściowego modelu.

- `UC-04` nie jest źródłem prawdy dla preprocessingu treningowego w tym use-case'u,
- `UC-04` dotyczy runtime'owego, interakcyjnego preprocessingu planszy dla przykładu użytkownika i nie zapisuje trwałych artefaktów,
- implementacyjnie wolno współdzielić fragmenty algorytmu wykrycia planszy lub ekstrakcji komórek z `UC-04`, ale zachowanie biznesowe i oczekiwany efekt `UC-17` powinny być zgodne z datasetowym etapem preprocessingu z `UC-12`, rozumianym wyłącznie jako przygotowanie kanonicznych próbek obrazu dla `board` i `digit`,
- `UC-17` nie obejmuje elementów `UC-12` związanych z budową finalnego `.npz`, czyli:
  - wyboru i realizacji polityki splitu `train` / `val` / `test`,
  - składania końcowych tablic datasetowych,
  - zapisu pliku `{name}.npz`,
  - przygotowania artefaktów potrzebnych wyłącznie do końcowego builda `.npz`,
- na etapie `UC-17` zachowujemy tylko te elementy preprocessingu z `UC-12`, które są potrzebne do utworzenia trwałej struktury przygotowania:
  - wykrycie planszy i korekcję perspektywy dla `board`,
  - podział planszy na komórki,
  - preprocessing pojedynczej komórki / cyfry do kanonicznego formatu,
  - zapis gotowych `.png`, `index.json`, `folders.json`, `file.json` oraz `corrected-board.png`.

## Relacja do `UC-12`
### Co `UC-17` dziedziczy z `UC-12`
- rozpoznanie typu wejścia `board` / `digit`,
- walidację techniczną źródeł wejściowych,
- wspólny preprocessing treningowy dla komórek pochodzących z `board` i dla próbek `digit`,
- kanoniczny format próbki wejściowej modelu,
- reguły odrzucania próbek nieczytelnych lub niepoprawnych.

### Czego `UC-17` nie dziedziczy z `UC-12`
- wyboru i realizacji splitu `train` / `val` / `test`,
- grupowania danych do splitu na poziomie całej planszy,
- budowy końcowych tablic datasetowych,
- zapisu końcowego pliku `{name}.npz`,
- zapisu raportu końcowego dla gotowego datasetu treningowego,
- elementów potrzebnych wyłącznie do końcowego builda `.npz`.

### Co staje się w `UC-17` wynikiem pośrednim zamiast końcowym
- zamiast jednego końcowego artefaktu `.npz` powstaje trwała struktura przygotowania,
- zamiast metadanych końcowego datasetu powstają lokalne indeksy i manifesty folderów,
- zamiast jednorazowego flow `raw -> split -> npz` powstaje etap `raw -> preparation`, który będzie ponownie użyty przez `UC-18` i `UC-19`.

## System plików przygotowania
Root przygotowania:

```text
{DATASET_PREPARATIONS_DIRECTORY_PATH}/{preparationName}/
```

Struktura katalogów:

```text
{preparationName}/
  board/
    folders.json
    {sourceName}/
      file.json
      {boardFolderName}/
        corrected-board.png
        cells/
          index.json
          000.png
          001.png
          ...
  digit/
    folders.json
    {sourceName}/
      index.json
      000000.png
      000001.png
      ...
```

## Znaczenie katalogów i plików
### `board/folders.json`
- zawiera listę dostępnych nazw folderów źródłowych typu `board`,
- to te nazwy `FE` wykorzystuje później jako logiczne identyfikatory źródeł do przyporządkowania splitów.

Format:

```json
[
  "v1_training",
  "v2_training"
]
```

### `board/{sourceName}/file.json`
- zawiera listę folderów pojedynczych plansz dostępnych do przeglądania i usuwania w `UC-18`.

Format:

```json
[
  "Image1",
  "Image2",
  "Image1079"
]
```

### `board/{sourceName}/{boardFolderName}/cells/index.json`
- opisuje wyłącznie pliki istniejące w folderze `cells`,
- format jest taki sam jak dla `digit`,
- zawiera tylko komórki z realnym labelem `1..9`,
- komórki z etykietą `0` nie są zapisywane ani indeksowane.

Format:

```json
[
  {
    "fileName": "000.png",
    "label": 1
  },
  {
    "fileName": "001.png",
    "label": 7
  }
]
```

### `digit/folders.json`
- zawiera listę dostępnych nazw folderów źródłowych typu `digit`,
- te nazwy są później zwracane do `FE` jako logiczne identyfikatory źródeł do przyporządkowania splitów.

Format:

```json
[
  "mnist_train",
  "mnist_test"
]
```

### `digit/{sourceName}/index.json`
- znajduje się bezpośrednio obok gotowych plików `.png`,
- opisuje wszystkie próbki zapisane w tym folderze,
- ma dokładnie ten sam format co `cells/index.json` dla `board`.

Format:

```json
[
  {
    "fileName": "000000.png",
    "label": 1
  },
  {
    "fileName": "000001.png",
    "label": 7
  }
]
```

## Zasady odpowiedzialności
### `Frontend`
- wybiera źródła i nazwę przygotowania,
- nie wybiera jeszcze splitów,
- nie zna fizycznych ścieżek runtime.

### `Backend`
- wystawia publiczne API przygotowań,
- pozostaje `source of truth` dla workflow i rekordów,
- uruchamia `ML`, ale nie wystawia `ML` publicznie.

### `MachineLearning`
- wykonuje ciężki preprocessing,
- zapisuje trwałe artefakty techniczne przygotowania,
- nie buduje jeszcze `.npz`.

## Endpointy i kontrakty
### `Frontend -> Backend`
Na etapie `UC-17` `FE` dostaje osobną zakładkę do utworzenia przygotowania, podejrzenia listy istniejących przygotowań oraz sprawdzenia statusu konkretnego przygotowania.

Endpointy:
- `GET /api/datasets/raw-candidates`
- `POST /api/datasets/preparations`
- `GET /api/datasets/preparations`
- `GET /api/datasets/preparations/{preparationName}`

Po co:
- `GET /api/datasets/raw-candidates` służy do pobrania listy surowych źródeł do wyboru,
- `POST /api/datasets/preparations` służy do rozpoczęcia nowego przygotowania,
- `GET /api/datasets/preparations` służy do pobrania listy istniejących przygotowań,
- `GET /api/datasets/preparations/{preparationName}` służy do pobrania statusu i szczegółów konkretnego przygotowania; może być używany do pollingu, jeśli przygotowanie trwa długo.

Status endpointów:
- `GET /api/datasets/raw-candidates` — już istnieje; nie wymaga zmiany kontraktu dla `UC-17`,
- `POST /api/datasets/preparations` — nowy endpoint do dodania,
- `GET /api/datasets/preparations` — nowy endpoint do dodania,
- `GET /api/datasets/preparations/{preparationName}` — nowy endpoint do dodania.

Kontrakty wejściowe/wyjściowe:
- `RawDatasetCandidateApiResponse`
  - `name`
  - `type`
- `CreateDatasetPreparationApiEntry`
  - `preparationName`
  - `sources: CreateDatasetPreparationSourceApiEntry[]`
- `CreateDatasetPreparationSourceApiEntry`
  - `name`
  - `type`
- `DatasetPreparationApiResponse`
  - `preparationName`
  - `createdAtUtc`
  - `status`
  - `sources: DatasetPreparationSourceApiResponse[]`
  - `warnings`
- `DatasetPreparationSourceApiResponse`
  - `name`
  - `type`
  - `preparedItemsCount`
- `DatasetPreparationsListApiResponse`
  - `items: DatasetPreparationListItemApiResponse[]`
  - `totalCount`
- `DatasetPreparationListItemApiResponse`
  - `preparationName`
  - `createdAtUtc`
  - `status`
  - `boardSourcesCount`
  - `digitSourcesCount`

Przykładowy request:

```json
{
  "preparationName": "preparation-001",
  "sources": [
    {
      "name": "v1_training",
      "type": "board"
    },
    {
      "name": "mnist_train",
      "type": "digit"
    }
  ]
}
```

### `Backend -> MachineLearning`
`Backend` uruchamia wewnętrzny proces przygotowania danych. Na tym etapie `ML` nie buduje jeszcze `.npz`.

Endpoint:
- `POST /ml/datasets/preparations`

Po co:
- endpoint służy wyłącznie do wykonania ciężkiego preprocessingu i zapisania trwałej struktury przygotowania z danych `raw`.

Status endpointów:
- `POST /ml/datasets/preparations` — nowy endpoint do dodania.

Kontrakty wejściowe/wyjściowe:
- `CreateDatasetPreparationMlRequest`
  - `preparationName`
  - `sources: CreateDatasetPreparationMlSourceDto[]`
- `CreateDatasetPreparationMlSourceDto`
  - `name`
  - `type`
- `CreateDatasetPreparationMlResponse`
  - `preparationName`
  - `createdAtUtc`
  - `status`
  - `sourceReports: DatasetPreparationMlSourceReportDto[]`
  - `warnings`
- `DatasetPreparationMlSourceReportDto`
  - `name`
  - `type`
  - `preparedItemsCount`
  - `rejectedItemsCount`
  - `emptyCellCount`

## Struktura indeksów
- lokalny `index.json` ma identyczny format dla `board` i `digit`,
- lokalny `index.json` opisuje tylko zawartość swojego folderu i przechowuje pary `fileName + label`,
- dla `board` lokalny `index.json` znajduje się w `cells/`, a globalna lista plansz znajduje się w `board/{sourceName}/file.json`,
- dla `board` i `digit` istnieją też pliki `folders.json`, które zwracają do `FE` listę dostępnych nazw folderów źródłowych wykorzystywanych później przy przyporządkowywaniu splitów.

## Poza zakresem
- wybór splitów,
- budowa `.npz`,
- trening,
- usuwanie pojedynczych komórek,
- ręczna edycja etykiet.

## Powiązanie z przyszłym refaktorem
- Wspólne wnioski o tym, gdzie uruchamiać detekcję pustej komórki, a gdzie czyszczenie próbki pod model, opisuje notatka `uc-empty-cell-cleaning-refactor-notes.md`.
- Dla `UC-17` kluczowe jest zachowanie kolejności: `raw cell -> label decision -> cleaning -> save prepared sample`.
- W `UC-17` źródłem prawdy o tym, czy komórka ma trafić do `cells/`, jest label, a nie runtime'owy algorytm `empty detection`.
- Obrazy diagnostyczne, takie jak `center composite` albo overlay znalezionych segmentów, nie są próbką do inferencji i nie powinny trafiać do `cells/`; do `cells/` trafia tylko oczyszczona komórka przygotowana pod model.

## Kryteria akceptacji
- System tworzy trwałe przygotowanie bez wskazywania splitów.
- Ciężki preprocessing plansz jest wykonywany tylko raz.
- Wynik może zostać później użyty do przeglądania i budowy `.npz`.
