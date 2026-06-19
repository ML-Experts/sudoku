# UC-18 — Przeglądanie i usuwanie elementów z przygotowania datasetu

## Cel
- Umożliwić użytkownikowi przeglądanie wyników przygotowania bez ponownego preprocessingu.
- Pozwolić na usuwanie całych elementów logicznych przed budową finalnego `.npz`.
- Utrzymać spójność indeksów i manifestów po usunięciu danych.

## Historyjka
Jako operator ML chcę obejrzeć i usuwać całe plansze albo inne logiczne elementy z przygotowania datasetu, aby do późniejszego datasetu treningowego trafiały tylko dane zaakceptowane jakościowo.

## Główna zasada workflow
1. Użytkownik wybiera istniejące przygotowanie.
2. `FE` pobiera listę dostępnych nazw folderów źródłowych z:
   - `board/folders.json`
   - `digit/folders.json`
3. `FE` pokazuje użytkownikowi listę nazw folderów źródłowych, ale nie ładuje od razu listy plansz ani obrazów dla wszystkich źródeł.
4. Użytkownik klika konkretny folder źródłowy typu `board`.
5. Dopiero po kliknięciu `FE` pobiera listę plansz z odpowiadającego mu `board/{sourceName}/file.json`.
6. Dla `board` użytkownik ogląda listę plansz, nie wszystkie komórki naraz.
7. Użytkownik usuwa cały logiczny element.
8. System aktualizuje odpowiednie pliki list tak, aby nie zostały martwe wpisy.

## Zasady przeglądania
### Zakres przeglądania
- przeglądanie obrazków w `UC-18` dotyczy wyłącznie danych typu `board`,
- dla `digit` `FE` pokazuje tylko listę dostępnych folderów źródłowych, bez osobnego widoku przeglądania obrazków w tej historyjce,
- `UC-18` nie renderuje siatki wszystkich komórek `cells`; podstawową jednostką przeglądania jest pojedyncza plansza `board`.

### UX przeglądania `board`
- po wejściu do `UC-18` użytkownik najpierw widzi listę nazw folderów źródłowych typu `board`, które pochodzą z `board/folders.json`,
- lista ta jest widokiem wyboru źródła, a nie listą pojedynczych plansz,
- po kliknięciu jednego wpisu z `board/folders.json`, np. `v1_training`, `FE` pobiera odpowiadający mu plik:

```text
board/v1_training/file.json
```

- `file.json` zawiera listę folderów pojedynczych plansz, np. `Image1`, `Image2`, `Image1079`,
- po wczytaniu `file.json` `FE` renderuje listę plansz dla wybranego źródła,
- dopiero dla tych plansz `FE` pokazuje elementy wizualne, co najmniej:
  - nazwę folderu planszy,
  - obraz `corrected-board.png`,
  - akcję usunięcia folderu planszy,
- `FE` nie ładuje z góry `corrected-board.png` dla wszystkich źródeł z `board/folders.json`; obrazy są pobierane dopiero po wejściu do konkretnego źródła `board`,
- jeśli lista plansz jest duża, `FE` może stosować lazy-loading albo paginację opartą o dane z `file.json`.

### `board`
- podstawową jednostką listy jest pojedyncza plansza,
- lista plansz jest odczytywana z gotowego pliku `board/{sourceName}/file.json`,
- plik `file.json` ma dokładnie taki format:

```json
[
  "Image1",
  "Image2",
  "Image1079"
]
```

- paginacja nie polega na ponownym skanowaniu katalogów ani ponownym generowaniu listy; system korzysta z już istniejącego `file.json` i wylicza strony na podstawie jego zawartości,
- `FE` pokazuje co najmniej `corrected-board.png` i nazwę folderu planszy.

### `digit`
- `FE` dostaje listę dostępnych nazw folderów źródłowych typu `digit` z `digit/folders.json`,
- `FE` nie zgaduje ścieżek ani struktury katalogów,
- na tym etapie `digit` jest prezentowany jako lista logicznych folderów źródłowych, a nie jako surowy skan filesystemu,
- `digit` nie ma w `UC-18` osobnego ekranu podglądu ani usuwania pojedynczych próbek.

## Matchowanie `folders.json` i `file.json`
- `board/folders.json` zawiera tylko nazwy folderów źródłowych typu `board`,
- każda wartość z `board/folders.json` jest bezpośrednio nazwą katalogu `{sourceName}` pod ścieżką:

```text
{DATASET_PREPARATIONS_DIRECTORY_PATH}/{preparationName}/board/{sourceName}/
```

- dla każdej takiej wartości system oczekuje dokładnie jednego odpowiadającego pliku:

```text
{DATASET_PREPARATIONS_DIRECTORY_PATH}/{preparationName}/board/{sourceName}/file.json
```

- matchowanie jest deterministyczne i polega wyłącznie na podstawieniu nazwy folderu z `folders.json` do ścieżki `board/{sourceName}/file.json`,
- `file.json` nie jest wyszukiwany heurystycznie i nie jest parowany po żadnych dodatkowych metadanych,
- analogicznie `digit/folders.json` zwraca nazwy folderów `{sourceName}`, które mapują się bezpośrednio na:

```text
{DATASET_PREPARATIONS_DIRECTORY_PATH}/{preparationName}/digit/{sourceName}/
```

## Pliki list wykorzystywane przez `FE`
### `board/folders.json`
- lista nazw folderów źródłowych typu `board`,
- wykorzystywana do pokazania użytkownikowi dostępnych nazw źródeł do dalszej pracy i późniejszego przyporządkowania splitów.

Format:

```json
[
  "v1_training",
  "v2_training"
]
```

### `digit/folders.json`
- lista nazw folderów źródłowych typu `digit`,
- wykorzystywana analogicznie jak dla `board`.

Format:

```json
[
  "mnist_train",
  "mnist_test"
]
```

## Zasady usuwania
- usunięcie `boardu` usuwa cały jego folder,
- razem z folderem usuwane są lokalne artefakty i lokalny `index.json`,
- po usunięciu system aktualizuje `board/{sourceName}/file.json` przez usunięcie wpisu odpowiadającego usuniętemu folderowi planszy,
- aktualizacja `file.json` nie polega na ponownym skanowaniu i przebudowie całej listy od zera, tylko na usunięciu konkretnego wpisu z istniejącej listy,
- nie pozostają „duchy” ani martwe referencje.

## Lokalizacja usuwanego folderu
- jeśli użytkownik usuwa planszę `Image1079` należącą do źródła `v1_training`, system usuwa:

```text
{DATASET_PREPARATIONS_DIRECTORY_PATH}/{preparationName}/board/v1_training/Image1079/
```

- a następnie aktualizuje:

```text
{DATASET_PREPARATIONS_DIRECTORY_PATH}/{preparationName}/board/v1_training/file.json
```

## Zasady odpowiedzialności
### `Frontend`
- renderuje listy i akcje usuwania,
- nie czyta katalogów bezpośrednio,
- korzysta tylko z API `Backendu`.

### `Backend`
- listuje przygotowania i elementy do przeglądania,
- wykonuje operacje usuwania,
- aktualizuje istniejące pliki list po zmianach.

### `MachineLearning`
- nie jest ponownie uruchamiany tylko po to, aby coś obejrzeć albo usunąć.

## Endpointy i kontrakty
### `Frontend -> Backend`
`UC-18` korzysta wyłącznie z `Backendu`. `FE` nie czyta bezpośrednio struktury katalogów i nie komunikuje się z `ML`.

Endpointy:
- `GET /api/datasets/preparations`
- `GET /api/datasets/preparations/{preparationName}`
- `GET /api/datasets/preparations/{preparationName}/board/folders`
- `GET /api/datasets/preparations/{preparationName}/digit/folders`
- `GET /api/datasets/preparations/{preparationName}/board/{sourceName}/files?page={page}&pageSize={pageSize}`
- `GET /api/datasets/preparations/{preparationName}/board/{sourceName}/files/{boardFolderName}/image`
- `DELETE /api/datasets/preparations/{preparationName}/board/{sourceName}/files/{boardFolderName}`

Po co:
- `GET /api/datasets/preparations` służy do wyboru istniejącego przygotowania,
- `GET /api/datasets/preparations/{preparationName}` może zwracać szczegóły i status przygotowania, zanim użytkownik wejdzie głębiej w jego strukturę,
- `GET /api/datasets/preparations/{preparationName}/board/folders` zwraca listę źródeł typu `board`,
- `GET /api/datasets/preparations/{preparationName}/digit/folders` zwraca listę źródeł typu `digit`,
- `GET /api/datasets/preparations/{preparationName}/board/{sourceName}/files` zwraca listę plansz dla wybranego źródła `board`,
- `GET /api/datasets/preparations/{preparationName}/board/{sourceName}/files/{boardFolderName}/image` zwraca `corrected-board.png` do podglądu,
- `DELETE /api/datasets/preparations/{preparationName}/board/{sourceName}/files/{boardFolderName}` usuwa folder planszy i aktualizuje `file.json`.

Kontrakty wejściowe/wyjściowe:
- `DatasetPreparationsListApiResponse`
  - `items: DatasetPreparationListItemApiResponse[]`
  - `totalCount`
- `DatasetPreparationApiResponse`
  - `preparationName`
  - `createdAtUtc`
  - `status`
  - `sources: DatasetPreparationSourceApiResponse[]`
  - `warnings`
- `DatasetPreparationFoldersApiResponse`
  - `preparationName`
  - `type`
  - `items: string[]`
  - `totalCount`
- `DatasetPreparationBoardFilesApiResponse`
  - `preparationName`
  - `sourceName`
  - `items: DatasetPreparationBoardFileListItemApiResponse[]`
  - `page`
  - `pageSize`
  - `totalCount`
- `DatasetPreparationBoardFileListItemApiResponse`
  - `boardFolderName`
  - `imageEndpoint`
- `ImageApiResponse`
  - `fileName`
  - `contentType`
  - `base64Content`
- `DeleteDatasetPreparationBoardFileApiResponse`
  - `preparationName`
  - `sourceName`
  - `boardFolderName`
  - `deleted`
  - `remainingItemsCount`

Przykładowa odpowiedź dla listy plansz:

```json
{
  "preparationName": "preparation-001",
  "sourceName": "v1_training",
  "items": [
    {
      "boardFolderName": "Image1",
      "imageEndpoint": "/api/datasets/preparations/preparation-001/board/v1_training/files/Image1/image"
    },
    {
      "boardFolderName": "Image2",
      "imageEndpoint": "/api/datasets/preparations/preparation-001/board/v1_training/files/Image2/image"
    }
  ],
  "page": 1,
  "pageSize": 50,
  "totalCount": 2
}
```

### `Backend -> MachineLearning`
Brak nowych endpointów w `UC-18`.

Przeglądanie i usuwanie działa wyłącznie na strukturze plików przygotowania zarządzanej przez `Backend`. `ML` nie jest wołany do listowania, ładowania `corrected-board.png` ani aktualizacji `file.json`.

## Poza zakresem
- budowa `.npz`,
- ponowne uruchamianie preprocessingu,
- automatyczne zatwierdzanie albo publikacja,
- trening modelu.

## Kryteria akceptacji
- Użytkownik może otworzyć przygotowanie i obejrzeć listę `boardów`.
- Użytkownik może usunąć cały `board`.
- Po usunięciu odpowiedni `file.json` zostaje zaktualizowany przez usunięcie wpisu o skasowanym folderze.
- Usunięte elementy nie pojawiają się ponownie przy dalszym przeglądaniu.
