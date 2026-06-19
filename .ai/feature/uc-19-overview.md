# UC-19 — Budowa finalnego `.npz` z przygotowania datasetu

## Cel
- Zastąpić bezpośrednie przygotowanie `.npz` z danych `raw` budową z wcześniej wykonanego przygotowania.
- Zachować dotychczasową semantykę splitu i finalnego artefaktu `.npz`.
- Usunąć konieczność ponownego wykonywania ciężkiego preprocessingu plansz przy każdej przebudowie datasetu.
- Zastąpić wcześniejszy mechanizm preview jako techniczne źródło builda `.npz`; etap budowy ma tylko przyporządkować splity do folderów, pobrać zawartość tych folderów i utworzyć plik `.npz`.

## Historyjka
Jako operator ML chcę zbudować finalny dataset `.npz` z wcześniej wykonanego przygotowania, aby wielokrotnie eksperymentować ze splitami i selekcją danych bez ponownego wykrywania plansz i ekstrakcji komórek.

## Główna zasada workflow
1. Użytkownik wybiera przygotowanie.
2. `FE` pobiera z `board/folders.json` i `digit/folders.json` listę dostępnych nazw folderów źródłowych, które później mogą zostać przypisane do splitów.
3. `FE -> BE` wysyła:
   - `preparationName`,
   - `datasetName`,
   - listę wybranych folderów źródłowych z polami `name`, `type` i `splits`.
4. Dla źródeł typu `board` `BE -> ML` przekazuje dokładnie nazwę folderu `name`, która odpowiada katalogowi:

```text
{DATASET_PREPARATIONS_DIRECTORY_PATH}/{preparationName}/board/{name}/
```

5. Dla źródeł typu `digit` `BE -> ML` przekazuje dokładnie nazwę folderu `name`, która odpowiada katalogowi:

```text
{DATASET_PREPARATIONS_DIRECTORY_PATH}/{preparationName}/digit/{name}/
```

6. System buduje `.npz` wyłącznie z gotowych plików zapisanych w tych folderach.
7. Dla `board` split pozostaje na poziomie całych plansz.

## Relacja do poprzedniego workflow
- Semantyka finalnego `.npz` pozostaje taka sama jak wcześniej.
- Zmienia się źródło danych wejściowych:
  - wcześniej: bezpośrednio `raw`,
  - docelowo: przygotowanie datasetu.
- Dzięki temu przebudowa datasetu nie wymaga ponownego wykrywania planszy i cięcia siatki.
- Dotychczasowe artefakty preview z wcześniejszego workflow nie są już źródłem builda `.npz`; build czyta wyłącznie strukturę przygotowania.

## Zasady splitu
### `board`
- split jest wykonywany na poziomie całych plansz,
- przynależność próbek do planszy wynika ze struktury folderów przygotowania,
- system czyta listę plansz z `board/{sourceName}/file.json`,
- każda plansza z tej listy jest traktowana jako jedna jednostka grupowania do splitu,
- lokalny `index.json` przy komórkach nie zna globalnej polityki splitu; zawiera tylko `fileName + label` dla komórek tej jednej planszy.

### `digit`
- split jest liczony na poziomie pojedynczej próbki,
- źródłem metadanych jest `digit/{sourceName}/index.json`,
- stabilnym kluczem próbki do przypisania splitu jest `fileName` z tego indeksu.

## System plików używany podczas builda
### `board`
Źródło typu `board` znajduje się pod ścieżką:

```text
{DATASET_PREPARATIONS_DIRECTORY_PATH}/{preparationName}/board/{sourceName}/
```

Wewnątrz:

```text
{sourceName}/
  file.json
  {boardFolderName}/
    corrected-board.png
    cells/
      index.json
      000.png
      001.png
      ...
```

Znaczenie:
- `file.json` zawiera listę folderów plansz:

```json
[
  "Image1",
  "Image2",
  "Image1079"
]
```

- dla każdej planszy `ML` czyta:
  - `cells/index.json`
  - odpowiadające mu pliki `.png` w `cells/`
- `corrected-board.png` nie bierze udziału w budowie `.npz`; służy tylko do przeglądania i diagnostyki.

Format `cells/index.json`:

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

Ten plik zawiera tylko komórki z realnym labelem `1..9`. Komórki puste z wartością `0` nie są zapisane w folderze `cells` i nie istnieją w tym indeksie.

### `digit`
Źródło typu `digit` znajduje się pod ścieżką:

```text
{DATASET_PREPARATIONS_DIRECTORY_PATH}/{preparationName}/digit/{sourceName}/
```

Wewnątrz:

```text
{sourceName}/
  index.json
  000000.png
  000001.png
  ...
```

Format `index.json`:

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

Podczas builda `.npz` `ML` czyta bezpośrednio ten `index.json` i odpowiadające mu pliki `.png` z tego samego folderu.

## Dokładny flow builda `.npz`
1. `FE` wybiera `preparationName` oraz nazwy folderów źródłowych, które przyszły wcześniej z `board/folders.json` i `digit/folders.json`.
2. `FE` wysyła do `BE` `preparationName`, nazwę finalnego datasetu oraz listę wybranych źródeł `name + type + splits`.
3. `BE` rozwiązuje ścieżki katalogów na podstawie `preparationName`, `type` i `name`; nie zgaduje ścieżek z nazw plików.
4. `BE` przekazuje do `ML` logiczne źródła wskazujące konkretne foldery przygotowania.
5. Dla `board` `ML`:
   - otwiera `board/{sourceName}/file.json`,
   - przechodzi po wszystkich `boardFolderName`,
   - przypisuje split na poziomie całej planszy,
   - dla każdej planszy czyta `cells/index.json`,
   - ładuje wskazane w nim pliki `.png`,
   - dodaje je do odpowiednich tablic splitu.
6. Dla `digit` `ML`:
   - otwiera `digit/{sourceName}/index.json`,
   - dla każdej pozycji przypisuje split na poziomie próbki,
   - ładuje wskazany plik `.png`,
   - dodaje go do odpowiednich tablic splitu.
7. Na końcu `ML` zapisuje finalny `{datasetName}.npz`.

## Format i sposób budowy pliku `.npz`
### Relacja do obecnego `UC-12`
- format końcowego pliku `.npz` ma pozostać zgodny z obecnym `UC-12`,
- `UC-19` refaktoruje źródło danych wejściowych i wcześniejsze etapy przygotowania, ale nie powinien zmieniać kontraktu finalnego artefaktu używanego później przez trening,
- oznacza to, że `UC-19` ma zachować ten sam biznesowy wynik końcowy: jeden wspólny plik `{datasetName}.npz`, metadane przygotowania oraz raport liczności próbek per split.

### Końcowy workflow tworzenia `.npz`
1. `ML` odczytuje gotowe próbki z przygotowania:
   - dla `board` przez `file.json` i lokalne `cells/index.json`,
   - dla `digit` przez płaski `index.json`.
2. Każda próbka jest przypisana do `train`, `val` albo `test` zgodnie z polityką splitu przekazaną przez `Backend`.
3. Gotowe obrazy `.png` są ładowane do pamięci jako próbki już przygotowane do użycia datasetowego; na tym etapie nie wracamy do surowych danych `raw`.
4. `ML` składa próbki w końcowe tablice splitów.
5. `ML` zapisuje jeden skompresowany plik `.npz`.

### Oczekiwany format techniczny `.npz`
Końcowy plik `.npz` powinien pozostać zgodny z obecnym writerem artefaktu i zawierać:
- `x_train`
- `y_train`
- `x_val`
- `y_val`
- `x_test`
- `y_test`
- `class_names`

Znaczenie:
- `x_*` to tablice wejściowych próbek obrazu po preprocessingu treningowym,
- `y_*` to odpowiadające im etykiety klas,
- `class_names` to jawna lista nazw klas używanych przez dataset.

Oczekiwane właściwości techniczne:
- `x_*` pozostają w formacie zgodnym z obecnym pipeline'em treningowym z `UC-12`,
- `y_*` pozostają etykietami klas zgodnymi z obecnym treningiem,
- zapis odbywa się jako pojedynczy skompresowany artefakt `.npz`, tak aby dalszy etap treningu nie wymagał żadnych zmian kontraktu.

### Co pozostaje takie samo względem `UC-12`
- końcowy artefakt jest jednym plikiem `{datasetName}.npz`,
- semantyka splitów `train` / `val` / `test` pozostaje taka sama,
- `board` nadal jest grupowany na poziomie całej planszy,
- `digit` nadal jest liczony na poziomie pojedynczej próbki,
- format i przeznaczenie `.npz` pozostają kompatybilne z późniejszym treningiem.

### Co zmienia się względem `UC-12`
- zamiast tworzyć próbki bezpośrednio z `raw`, system korzysta z wcześniej przygotowanych plików `.png` i indeksów,
- ciężki preprocessing planszy nie jest wykonywany ponownie w trakcie builda `.npz`,
- etap `UC-19` odpowiada głównie za:
  - odczyt wcześniej przygotowanych danych,
  - przypisanie splitów,
  - złożenie końcowych tablic,
  - zapis finalnego `.npz`.

## Relacja do `UC-12`
### Co `UC-19` dziedziczy z `UC-12`
- końcowy kontrakt biznesowy: jeden finalny plik `{datasetName}.npz`,
- semantykę splitów `train` / `val` / `test` oraz obsługę `mix`,
- grupowanie źródła `board` na poziomie całej planszy,
- wspólny wynikowy format próbek używany później przez trening,
- końcowy raport przygotowania i liczności per split,
- zgodność techniczną finalnego artefaktu z obecnym treningiem i loaderami `.npz`.

### Czego `UC-19` nie dziedziczy z `UC-12`
- bezpośredniego czytania danych `raw` jako źródła wejściowego,
- ponownego skanowania `board` jako par `.jpg + .dat`,
- ponownego ładowania `digit` bezpośrednio z par `*.idx3-ubyte + *.idx1-ubyte`,
- ponownego wykrywania planszy, korekcji perspektywy i ekstrakcji komórek podczas builda `.npz`,
- starego flow, w którym preprocessing, split i build `.npz` są wykonywane w jednym kroku.

### Co pozostaje tylko w `UC-19`, a nie przechodzi do `UC-17`
- techniczna polityka splitu tłumaczona przez `Backend`,
- przypisanie każdej próbki do `train`, `val` lub `test`,
- budowa końcowych tablic `x_train`, `y_train`, `x_val`, `y_val`, `x_test`, `y_test`,
- zapis `class_names`,
- końcowy zapis skompresowanego pliku `.npz`,
- finalny raport liczności i ostrzeżeń dla datasetu gotowego do treningu.

### Co staje się przestarzałe po refaktorze `UC-19`
- monolityczny workflow `raw -> preprocess -> split -> npz` wykonywany w ramach jednego żądania,
- traktowanie danych `raw` jako bezpośredniego źródła builda finalnego datasetu,
- techniczna zależność builda `.npz` od starego preview jako efektu ubocznego wcześniejszego flow.

## Endpointy i kontrakty
### `Frontend -> Backend`
`UC-19` refaktoruje istniejący publiczny endpoint budowy datasetu. `FE` zachowuje podobny UX, ale przestaje korzystać z `raw-candidates` dla tego use-case'u.

Endpointy:
- `GET /api/datasets/preparations`
- `GET /api/datasets/preparations/{preparationName}`
- `GET /api/datasets/preparations/{preparationName}/board/folders`
- `GET /api/datasets/preparations/{preparationName}/digit/folders`
- `POST /api/datasets/processed`
- `GET /api/datasets/processed`

Po co:
- `GET /api/datasets/preparations` służy do wyboru istniejącego przygotowania,
- `GET /api/datasets/preparations/{preparationName}` może zwracać szczegóły i status przygotowania przed budową `.npz`,
- `GET /api/datasets/preparations/{preparationName}/board/folders` zwraca listę źródeł typu `board` do splitu,
- `GET /api/datasets/preparations/{preparationName}/digit/folders` zwraca listę źródeł typu `digit` do splitu,
- `POST /api/datasets/processed` buduje finalny `.npz` z wybranego przygotowania,
- `GET /api/datasets/processed` zwraca listę gotowych datasetów `.npz`.

Kontrakty wejściowe/wyjściowe:
- `CreateProcessedDatasetApiEntry`
  - `preparationName`
  - `name`
  - `sources: SelectedPreparedDatasetSourceApiEntry[]`
- `SelectedPreparedDatasetSourceApiEntry`
  - `name`
  - `type`
  - `splits`
- `ProcessedDatasetApiResponse`
  - `name`
  - `fileName`
  - `preprocessingProfile`
  - `createdAtUtc`
  - `sources: SelectedPreparedDatasetSourceApiEntry[]`
  - `sampleCounts`
  - `sourceReports`
  - `warnings`
- `ProcessedDatasetSourceReportApiResponse`
  - `name`
  - `type`
  - `processedSampleCount`
  - `includedSampleCount`
  - `emptyCellCount`
  - `rejectedSampleCount`
  - `warnings`
- `ProcessedDatasetsListApiResponse`
  - `items`
  - `totalCount`

Przykładowy request:

```json
{
  "preparationName": "preparation-001",
  "name": "digits-dataset-v2",
  "sources": [
    {
      "name": "v1_training",
      "type": "board",
      "splits": ["mix"]
    },
    {
      "name": "mnist_train",
      "type": "digit",
      "splits": ["train", "val"]
    }
  ]
}
```

### `Backend -> MachineLearning`
Refaktor obejmuje również wewnętrzny endpoint używany przez `Backend` do zlecania budowy finalnego `.npz`.

Endpoint:
- `POST /ml/datasets/prepare`

Po co:
- endpoint służy do zbudowania finalnego `.npz` z gotowych folderów przygotowania, bez ponownego wracania do danych `raw`.

Kontrakty wejściowe/wyjściowe:
- `PrepareDatasetArtifactRequest`
  - `preparationName`
  - `datasetName`
  - `sources: SelectedPreparedDatasetSourceDto[]`
  - `splitPolicy`
- `SelectedPreparedDatasetSourceDto`
  - `name`
  - `type`
  - `splits`
- `PrepareDatasetArtifactResponse`
  - `datasetName`
  - `fileName`
  - `preprocessingProfile`
  - `sampleCounts`
  - `sourceReports`
  - `warnings`

To jest świadomy refaktor istniejącego kontraktu `ML`: semantyka endpointu pozostaje taka sama na poziomie celu biznesowego, ale wejście nie wskazuje już źródeł `raw`, tylko logiczne źródła z przygotowania.

## Refaktor `UC-19`: co się zmienia, co usuwamy, co dodajemy
### Co się zmienia
- istniejący `POST /api/datasets/processed` przestaje budować dataset bezpośrednio z `raw`,
- `FE` wybiera najpierw `preparationName`, a dopiero potem źródła `board` i `digit` z tego przygotowania,
- `Backend` waliduje źródła względem `board/folders.json` i `digit/folders.json`, a nie względem katalogów `raw`,
- `ML` buduje `.npz` z gotowych plików `.png` oraz lokalnych `index.json`.

### Co usuwamy z tego use-case'u
- bezpośredni odczyt `raw board` jako par `.jpg + .dat` podczas budowy `.npz`,
- bezpośredni odczyt `raw digit` jako par `*.idx3-ubyte + *.idx1-ubyte` podczas budowy `.npz`,
- ponowne wykrywanie planszy, korekcję perspektywy i cięcie siatki 9×9 w trakcie budowy datasetu,
- zależność builda od starego preview jako technicznego źródła danych wejściowych,
- użycie kontraktów semantycznie związanych z `raw`, takich jak wybór źródeł oparty na starych kandydatach `raw`.

### Co dodajemy
- `preparationName` w `CreateProcessedDatasetApiEntry`,
- nową semantykę `sources`, gdzie `name` oznacza nazwę folderu źródłowego w przygotowaniu,
- odczyt `board/{sourceName}/file.json` jako listy plansz do splitu,
- odczyt `board/{sourceName}/{boardFolderName}/cells/index.json` jako lokalnego indeksu komórek,
- odczyt `digit/{sourceName}/index.json` jako płaskiego indeksu próbek,
- logikę splitu opartą dla `board` o całe plansze, a dla `digit` o pojedyncze `fileName`.

## Zasady odpowiedzialności
### `Frontend`
- wybiera przygotowanie, nazwę datasetu i politykę splitu,
- zachowuje podobny UX do wcześniejszej budowy `.npz`.

### `Backend`
- pozostaje właścicielem workflow i rekordów finalnych datasetów,
- tłumaczy wybór splitów na politykę techniczną,
- zapisuje metadane i raport przygotowania.

### `MachineLearning`
- czyta gotowe dane z przygotowania,
- buduje tablice i finalny `.npz`,
- nie wykonuje ponownie ciężkiego preprocessingu plansz,
- nie używa `corrected-board.png` ani starego preview jako źródła builda, tylko wyłącznie `index.json` i odpowiadających im plików `.png`.

## Poza zakresem
- tworzenie przygotowania,
- przeglądanie i usuwanie danych z przygotowania,
- trening modelu.

## Kryteria akceptacji
- Finalny `.npz` powstaje z wcześniej przygotowanego zbioru danych.
- Dla `board` split nadal odbywa się na poziomie planszy.
- Usunięte wcześniej elementy nie trafiają do `.npz`.
- Końcowy artefakt pozostaje kompatybilny z dalszym treningiem.
