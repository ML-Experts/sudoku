# UC-11-BE - Plan implementacyjny dla `GET /api/datasets/raw-candidates`

## Cel
- Udostępnić chroniony endpoint zwracający listę logicznych kandydatów datasetowych wykrytych w skonfigurowanych katalogach źródłowych.
- Zachować podział odpowiedzialności między `Api`, `Application` i `Infrastructure`.
- Zaprojektować `Infrastructure` możliwie generycznie, tak aby jego operacje dało się reuse'ować również w innych use case'ach, np. przy pobieraniu plików, odczycie katalogów albo walidacji struktury zasobów.
- Nie angażować `ML`, nie budować jeszcze `{name}.npz` i nie wchodzić w logikę `UC-12`.

## Stan wyjściowy dla storage
- W backendzie istnieje już generyczny port `IFileStorageGateway`.
- Aktualnie wspiera on operacje:
  - `SaveAsync(...)`,
  - `OpenReadAsync(...)`,
  - `ListFilesAsync(...)`.
- W `Infrastructure` istnieje już lokalna implementacja `LocalFileStorageGateway`.
- Dla `UC-11` nie należy wprowadzać nowego, równoległego adaptera tylko dlatego, że pojawia się potrzeba listowania katalogów.
- Preferowany kierunek to:
  - reuse istniejącego `IFileStorageGateway`,
  - ewentualne rozszerzenie go o brakujące generyczne operacje katalogowe, np. `ListDirectoriesAsync(...)`,
  - pozostawienie całej semantyki `UC-11` po stronie `Application`.

## Kontrakt HTTP
- Metoda i ścieżka: `GET /api/datasets/raw-candidates`
- Wejście: brak modelu JSON wejściowego
- Odpowiedź sukcesu: `200 OK` + `RawDatasetCandidateApiResponse[]`
- Odpowiedzi błędów:
  - `401 Unauthorized` + `ErrorApiResponse`
  - `500 Internal Server Error` + `ErrorApiResponse`

Przykładowa odpowiedź:

```json
[
  {
    "name": "v1_training",
    "type": "board"
  },
  {
    "name": "t10k",
    "type": "digit"
  }
]
```

Istotne ograniczenia kontraktowe:
- endpoint zwraca bezpośrednio tablicę rekordów, bez wrappera typu `items` lub `totalCount`,
- publiczny JSON pozostaje w `camelCase`,
- `type` jest częścią publicznego kontraktu i przyjmuje wartości `board` albo `digit`.

## Modele wejścia / wyjścia
### Publiczne API
- `RawDatasetCandidateApiResponse`
  - `name: string`
  - `type: string` (`board` | `digit`)
- `ErrorApiResponse`
  - `errorType: string`
  - `message: string`

### Application
- `ListRawDatasetCandidatesQuery`
- `ListRawDatasetCandidatesQueryResultDto`
  - `Items`
- DTO elementu wyniku, np.:
  - `ListRawDatasetCandidateItemDto`
    - `Name`
    - `Type`

### Generyczne modele infrastrukturalne
Warto przewidzieć neutralne modele techniczne, które nie niosą semantyki `UC-11`, np.:
- `StoredFileMetadataDto`
  - `Name`
  - `Extension`
  - `SizeBytes`
  - `LastModifiedUtc`
- `StoredDirectoryMetadataDto`
  - `Name`
  - `LastModifiedUtc`

## Odpowiedzialność warstw
### `Api`
- Dodać dedykowany `DatasetsController`.
- Wystawić akcję `GET /api/datasets/raw-candidates`.
- Zbindować żądanie HTTP, wywołać `MediatR` i zmapować wynik na `RawDatasetCandidateApiResponse[]`.
- Nie umieszczać w kontrolerze:
  - skanu katalogów,
  - decyzji co jest kandydatem `board` / `digit`,
  - budowy ścieżek systemowych,
  - logiki autoryzacji specyficznej dla jednego endpointu.

### `Application`
- Dodać `ListRawDatasetCandidatesQuery` oraz handler.
- Umieścić w use case'ie całą semantykę `UC-11`:
  - odczyt konfiguracji źródeł `boards` i `digits`,
  - decyzję, że bezpośrednie podkatalogi `boards` reprezentują kandydatów `board`,
  - decyzję, że kandydaci `digit` powstają przez sparowanie `*.idx3-ubyte` i `*.idx1-ubyte` o wspólnym prefiksie,
  - odrzucanie wpisów technicznych i niekompletnych par,
  - budowę finalnego DTO use case'u.
- W use case'ie nie wchodzić w:
  - przygotowanie datasetu,
  - skan rekurencyjny wnętrza datasetu `board`,
  - zapis jakichkolwiek rekordów przetworzonych datasetów.

### `Infrastructure`
- Dostarczyć generyczne operacje filesystemowe, bez znajomości pojęć `raw dataset candidate`, `board`, `digit` ani `UC-11`.
- Udostępnić operacje możliwe do reuse'u także poza tym use case'em, np.:
  - sprawdzenie istnienia katalogu,
  - listowanie bezpośrednich podkatalogów,
  - listowanie plików z podstawowymi metadanymi,
  - odczyt pliku jako stream dla przyszłych scenariuszy pobierania plików.
- Zwracać wyłącznie dane techniczne, a nie zinterpretowane rekordy biznesowe.

### `Configuration`
- Dodać typed options `RawDatasetsStorageOptions`.
- Wymagane pola:
  - `BoardsSubdirectory`
  - `DigitsSubdirectory`
- Wartości konfiguracyjne mają wskazywać bezpośrednio katalogi źródłowe.
- Kod nie może zakładać literalnych nazw `boards` ani `digits`; używa wyłącznie ścieżek przekazanych przez konfigurację.

## Decyzje architektoniczne
- Nie tworzyć adaptera infrastrukturalnego typu `IRawDatasetsGateway`, który zwraca od razu kandydatów biznesowych `UC-11`.
- Nie przenosić semantyki `board` / `digit` do `Infrastructure`.
- Zamiast tego oprzeć rozwiązanie o istniejący generyczny `IFileStorageGateway`, rozszerzony tylko o brakujące operacje techniczne, a algorytm interpretacji pozostawić w `Application`.
- Brak katalogu źródłowego albo brak poprawnych kandydatów traktować jako poprawny stan i zwracać pustą listę `[]`.
- `ML` nie bierze udziału w tym przepływie.

## Reguły wykrywania kandydatów
### Kandydaci `board`
- Kandydatem jest katalog będący bezpośrednim dzieckiem skonfigurowanego folderu wskazanego przez `RawDatasetsStorage.BoardsSubdirectory`.
- Publiczne `name` jest nazwą tego katalogu.
- `UC-11` nie wykonuje rekurencyjnego wejścia do wnętrza tego katalogu.

### Kandydaci `digit`
- Kandydat powstaje przez automatyczne sparowanie plików `*.idx3-ubyte` i `*.idx1-ubyte` o wspólnym prefiksie wewnątrz katalogu wskazanego przez `RawDatasetsStorage.DigitsSubdirectory`.
- Publiczne `name` jest wspólnym prefiksem sparowanych plików.
- `type = digit` wynika z lokalizacji źródła w folderze `digits`, a nie z analizy zawartości pliku.

### Reguły wspólne
- Ignorować ukryte katalogi techniczne i wpisy nienadające się do wyboru, np. `.ipynb_checkpoints`.
- Odrzucać niekompletne pary plików `digit`.
- Walidacja na tym etapie ma jedynie potwierdzić, czy wpis nadaje się do pokazania jako kandydat na liście.
- Jeśli katalog nie istnieje albo nie zawiera poprawnych kandydatów, endpoint zwraca `[]`.

## Docelowy przepływ
1. `FE` wywołuje `GET /api/datasets/raw-candidates` z tokenem administracyjnym.
2. `DatasetsController` przekazuje żądanie do `ListRawDatasetCandidatesQuery`.
3. Handler pobiera ścieżki `BoardsSubdirectory` i `DigitsSubdirectory` z typed options.
4. Handler wywołuje generyczne operacje filesystemowe z `Infrastructure`:
   - odczyt bezpośrednich podkatalogów dla `boards`,
   - odczyt plików dla `digits`.
5. `Infrastructure` zwraca wyłącznie techniczne metadane katalogów i plików.
6. `Application`:
   - interpretuje bezpośrednie dzieci folderu `boards` jako kandydatów `board`,
   - buduje kandydatów `digit` przez sparowanie plików po wspólnym prefiksie,
   - odrzuca wpisy techniczne i niekompletne pary,
   - mapuje wynik do `ListRawDatasetCandidatesQueryResultDto`.
7. Kontroler mapuje DTO na `RawDatasetCandidateApiResponse[]` i zwraca `200 OK`.

## Sugerowane porty generyczne
Nazwy można dopasować do konwencji repo, ale semantyka powinna pozostać generyczna. Ponieważ w projekcie istnieje już `IFileStorageGateway`, preferowaną opcją jest jego rozszerzenie, a nie tworzenie nowego `IFileSystemGateway`.

```csharp
public interface IFileStorageGateway
{
    Task<bool> DirectoryExistsAsync(
        string directoryPath,
        CancellationToken cancellationToken = default);

    Task<IReadOnlyList<StoredDirectoryMetadataDto>> ListDirectoriesAsync(
        string directoryPath,
        CancellationToken cancellationToken = default);

    Task<IReadOnlyList<StoredFileMetadataDto>> ListFilesAsync(
        string directoryPath,
        CancellationToken cancellationToken = default);

    Task<Stream> OpenReadAsync(
        string directoryPath,
        string fileName,
        CancellationToken cancellationToken = default);
}
```

Tak rozszerzony port nadal pozostaje generyczny i pozwala wykorzystać ten sam adapter także w innych use case'ach, np.:
- pobieranie plików,
- listowanie przykładów,
- walidacja katalogów wejściowych,
- odczyt artefaktów lub raportów.

## Zakres zmian w kodzie
### `Api`
- dodać `src/Backend/Sudoku/Sudoku/Controllers/DatasetsController.cs`,
- dodać `src/Backend/Sudoku/Sudoku/Contracts/RawDatasetCandidateApiResponse.cs`,
- wykorzystać wspólny `ErrorApiResponse`.

### `Application`
- dodać `src/Backend/Sudoku/Application/Datasets/ListRawDatasetCandidatesQuery.cs`,
- dodać `src/Backend/Sudoku/Application/Datasets/ListRawDatasetCandidatesQueryHandler.cs`,
- dodać `src/Backend/Sudoku/Application/Datasets/ListRawDatasetCandidatesQueryResultDto.cs`,
- dodać DTO elementu listy, np. `ListRawDatasetCandidateItemDto.cs`,
- rozszerzyć istniejący generyczny port `IFileStorageGateway` w `Application/Abstractions` tylko o operacje techniczne brakujące do `UC-11`.

### `Infrastructure`
- rozszerzyć istniejący `LocalFileStorageGateway`,
- zapewnić listowanie bezpośrednich katalogów i plików bez logiki use case'u,
- zachować normalizację ścieżek i ochronę przed wyjściem poza katalog docelowy tam, gdzie ma to zastosowanie.

### `Configuration`
- dodać `RawDatasetsStorageOptions`,
- zbindować typed options w composition root,
- dopisać w planie źródło powstawania `appsettings.local.json` i `appsettings.production.json`,
- uzupełnić oba pliki o dokładne, absolutne ścieżki do katalogów źródłowych.

## Konfiguracja środowiskowa `local` i `production`
### Jak runtime wybiera plik
- Backend ładuje bazowy `appsettings.json` oraz overlay `appsettings.{SUDOKU_ENVIRONMENT}.json`.
- Dla uruchomień lokalnych `SUDOKU_ENVIRONMENT=local`, więc runtime czyta `appsettings.local.json`.
- Dla środowiska serwerowego `SUDOKU_ENVIRONMENT=production`, więc runtime czyta `appsettings.production.json`.

### Jak powstaje `appsettings.local.json`
- Jest to lokalny overlay developerski utrzymywany jawnie po stronie środowiska deweloperskiego.
- Ten plik nie powinien być generowany przez workflow CD.
- Deweloper wpisuje w nim bezpośrednio absolutne ścieżki lokalnego runtime.

Przykładowy kształt dla `UC-11`:

```json
{
  "RawDatasetsStorage": {
    "BoardsSubdirectory": "/home/wojtek/projects/sudoku-runtime/data/raw/boards",
    "DigitsSubdirectory": "/home/wojtek/projects/sudoku-runtime/data/raw/digits"
  }
}
```

### Jak powstaje `appsettings.production.json`
- Jest to overlay runtime dla serwera produkcyjnego.
- Ten plik powinien być generowany przez workflow backendowy podczas budowy release'u.
- Workflow musi wprost wytworzyć `appsettings.production.json` na podstawie zmiennych środowiskowych / `GitHub environment variables` / sekretów.
- Dla `UC-11` trzeba dopisać do workflow nowe wejścia konfiguracyjne, co najmniej:
  - `BE_RAW_DATASETS_BOARDS_SUBDIRECTORY`,
  - `BE_RAW_DATASETS_DIGITS_SUBDIRECTORY`.
- Wygenerowany plik powinien zawierać sekcję:

```json
{
  "RawDatasetsStorage": {
    "BoardsSubdirectory": "/opt/sudoku/shared/data/raw/boards",
    "DigitsSubdirectory": "/opt/sudoku/shared/data/raw/digits"
  }
}
```

### Uwaga do obecnego workflow
- Obecny workflow backendowy generuje dziś `appsettings.json`.
- Aby plan był spójny z architekturą środowiskową projektu, implementacja powinna rozszerzyć ten mechanizm tak, aby dla serwera powstawał także `appsettings.production.json` z sekcją `RawDatasetsStorage`, a runtime był uruchamiany z `SUDOKU_ENVIRONMENT=production`.
- To nie jest osobna logika `UC-11`, tylko wymagany element konfiguracji środowiskowej dla tego use case'u.

## Zależność od UC-13
- `UC-11` jest endpointem chronionym i musi zostać spięty z mechanizmem tokenu administracyjnego z `UC-13`.
- Bez poprawnego tokenu endpoint zwraca `401 Unauthorized`.
- Implementacja `UC-11` nie powinna duplikować ani obchodzić zasad autoryzacji; powinna korzystać ze wspólnego mechanizmu ochrony endpointów administracyjnych.

## Kolejność implementacji
1. Dodać kontrakt `RawDatasetCandidateApiResponse` i ustalić końcowe mapowanie odpowiedzi `200/401/500`.
2. Dodać `RawDatasetsStorageOptions` i konfigurację katalogów `boards` oraz `digits`.
3. Rozszerzyć istniejący `IFileStorageGateway` tylko o brakujące operacje techniczne potrzebne do listowania katalogów.
4. Rozszerzyć `LocalFileStorageGateway` o generyczne operacje katalogowo-plikowe.
5. Dodać `ListRawDatasetCandidatesQuery`, handler i DTO w `Application`.
6. Dodać `DatasetsController` i mapowanie HTTP.
7. Spiąć endpoint z ochroną administracyjną z `UC-13`.
8. Rozszerzyć konfigurację środowiskową:
   - lokalnie przez jawne wpisy w `appsettings.local.json`,
   - produkcyjnie przez workflow generujący `appsettings.production.json`.
9. Zweryfikować zachowanie dla pustych katalogów, kandydatów `board`, kandydatów `digit` i błędów odczytu.

## Weryfikacja implementacji
- `GET /api/datasets/raw-candidates` zwraca `200 OK` i `[]`, gdy któryś z katalogów nie istnieje albo nie ma poprawnych kandydatów.
- Endpoint zwraca rekord `board` dla każdego bezpośredniego dziecka katalogu `boards`, z pominięciem wpisów technicznych.
- Endpoint zwraca rekord `digit` tylko dla kompletnych par `*.idx3-ubyte` + `*.idx1-ubyte`.
- Odpowiedź zawiera wyłącznie `name` i `type`.
- `ML` nie jest wywoływane.
- `Infrastructure` pozostaje generyczne i nie zna pojęć `board`, `digit` ani `raw candidate`.
- Bez poprawnego tokenu administracyjnego endpoint zwraca `401`.

## Guardraile implementacyjne
Ta sekcja nie jest listą luźnych uwag. To są konkretne ograniczenia, które implementacja ma spełnić.

- Nie przenosić semantyki `UC-11` do `Infrastructure`.
  `Infrastructure` ma umieć listować katalogi i pliki, ale nie ma wiedzieć, czym jest kandydat `board`, kandydat `digit` ani jak parować rekordy biznesowe.
- Nie rozszerzać zakresu `UC-11` o logikę `UC-12`.
  W `UC-11` nie ma rekurencyjnego skanu wnętrza datasetu `board`, przygotowania `.npz` ani workflow przetwarzania danych.
- Nie wiązać implementacji z literalnymi nazwami folderów.
  Runtime ma korzystać z wartości `RawDatasetsStorage.BoardsSubdirectory` i `RawDatasetsStorage.DigitsSubdirectory`, nawet jeśli nazwy pól historycznie sugerują coś innego.
- Nie dodawać do publicznej odpowiedzi pól niewynikających z kontraktu.
  `GET /api/datasets/raw-candidates` ma zwracać tylko `name` i `type`.
