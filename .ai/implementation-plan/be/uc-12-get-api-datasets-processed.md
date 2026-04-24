# UC-12-BE - Plan implementacyjny dla `GET /api/datasets/processed`

## 1) Przeznaczenie endpointa
- Endpoint `GET /api/datasets/processed` zwraca chronioną listę gotowych zestawów `.npz`, które mogą zostać wybrane w `UC-06` do uruchomienia treningu.
- Backend pozostaje `source of truth` dla tej listy: to BE odczytuje i normalizuje metadane przygotowanych datasetów, a FE dostaje gotowy model widoku.
- Endpoint nie uruchamia preprocessingu i nie wywołuje ML; jest operacją odczytową nad rekordami utrzymywanymi przez backend po `POST /api/datasets/processed`.

## 2) Zakres i założenia
- Nie opieramy planu na bieżącej implementacji FE/ML; źródłem zachowania jest `PRD` + `UC-12` (wymóg listy gotowych `.npz`).
- Endpoint jest częścią `UC-12`, ale konsumowany dalej przez `UC-06`.
- Endpoint jest chroniony tokenem z `UC-13` (`401` bez poprawnego tokenu).
- Publiczny kontrakt JSON pozostaje w `camelCase`.

## 3) Kontrakty API (FE i ML)

### 3.1 FE -> BE (`GET /api/datasets/processed`)
- Request body: brak.
- Query params: brak (MVP).
- Response `200 OK`: `ProcessedDatasetsListApiResponse`
  - `items: ProcessedDatasetListItemApiResponse[]`
  - `totalCount: number`
- `ProcessedDatasetListItemApiResponse`:
  - `name: string`
  - `fileName: string`
  - `preprocessingProfile: string`
  - `createdAtUtc: string` (`ISO-8601 UTC`)
  - `sampleCounts: SplitSampleCountsApiResponse`
- `SplitSampleCountsApiResponse`:
  - `train: number`
  - `val: number`
  - `test: number`

### 3.2 BE -> ML
- Brak komunikacji `BE -> ML` dla tego endpointa.
- `GET /api/datasets/processed` bazuje wyłącznie na metadanych zapisanych wcześniej przez workflow `POST /api/datasets/processed`.

## 4) Zachowanie per warstwa

### API (`Sudoku`)
- Odpowiada za:
  - autoryzację (`[Authorize]`),
  - wywołanie query MediatR,
  - mapowanie DTO aplikacyjnych na kontrakt HTTP.
- Nie zawiera logiki skanowania plików ani reguł biznesowych listowania.

### Application (`Application`)
- Odpowiada za:
  - use-case `ListProcessedDatasetsQuery`,
  - wywołanie portu `IProcessedDatasetsGateway`,
  - sortowanie rekordów (`createdAtUtc` malejąco),
  - wyliczenie `totalCount`.
- Nie zawiera kodu I/O i nie zna szczegółów serializacji plików.

### Domain / Models (`Models`)
- Dla tego endpointa brak dedykowanego modelu domenowego.
- Dane przepływają przez DTO use-case (`*Dto`) i kontrakty API (`*ApiResponse`).
- Guardrail: nie przenosić modeli HTTP do `Models`.

### Infrastructure (`Infrastructure`)
- Odpowiada za:
  - odczyt metadanych datasetów z systemu plików,
  - deserializację `*.metadata.json`,
  - zwrot listy `ProcessedDatasetMetadataDto` przez port aplikacyjny.
- Logika ma pozostać techniczna (adaptacja storage), bez reguł biznesowych UC.

## 5) Pliki per warstwa i odpowiedzialności

### API
- `src/Backend/Sudoku/Sudoku/Controllers/DatasetsController.cs`
  - akcja `ListProcessedAsync` (`GET /api/datasets/processed`), mapowanie `ListProcessedDatasetsQueryResultDto -> ProcessedDatasetsListApiResponse`.
  - **Do doprecyzowania**: mapowanie wyjątków I/O/deserializacji na `ErrorApiResponse` (spójnie z resztą kontrolera).
- `src/Backend/Sudoku/Sudoku/Contracts/ProcessedDatasetsListApiResponse.cs`
  - model odpowiedzi listy + `totalCount`.
- `src/Backend/Sudoku/Sudoku/Contracts/ProcessedDatasetListItemApiResponse.cs`
  - model elementu listy.
- `src/Backend/Sudoku/Sudoku/Contracts/SplitSampleCountsApiResponse.cs`
  - publiczny model liczności `train/val/test`.
- `src/Backend/Sudoku/Sudoku/Contracts/ErrorApiResponse.cs`
  - wspólny kontrakt błędów (`errorType`, `message`) przy błędach odczytu.

### Application
- `src/Backend/Sudoku/Application/Datasets/ListProcessedDatasetsQuery.cs`
  - zapytanie MediatR bez parametrów wejściowych.
- `src/Backend/Sudoku/Application/Datasets/ListProcessedDatasetsQueryHandler.cs`
  - orkiestracja odczytu listy i sortowanie.
- `src/Backend/Sudoku/Application/Datasets/ListProcessedDatasetsQueryResultDto.cs`
  - DTO wyniku use-case (`items`, `totalCount`).
- `src/Backend/Sudoku/Application/Datasets/ProcessedDatasetListItemDto.cs`
  - DTO pozycji listy.
- `src/Backend/Sudoku/Application/Datasets/ProcessedDatasetMetadataDto.cs`
  - pełny rekord metadanych przygotowania datasetu (źródło dla listy i przyszłych endpointów).
- `src/Backend/Sudoku/Application/Datasets/SplitSampleCountsDto.cs`
  - DTO liczności splitów.
- `src/Backend/Sudoku/Application/Abstractions/IProcessedDatasetsGateway.cs`
  - port aplikacyjny dla listowania i operacji na prepared datasets.

### Infrastructure
- `src/Backend/Sudoku/Infrastructure/Storage/ProcessedDatasetsGateway.cs`
  - implementacja odczytu metadanych (`ListAsync`), filtrowanie `*.metadata.json`, deserializacja JSON.
  - wykorzystuje generyczny storage zamiast duplikowania I/O.
- `src/Backend/Sudoku/Infrastructure/Storage/LocalFileStorageGateway.cs`
  - generyczne operacje filesystem (`ListFilesAsync`, `OpenReadAsync`, `SaveAsync`); reużywane przez gateway UC-12.
- `src/Backend/Sudoku/Infrastructure/DependencyInjection.cs`
  - rejestracja `IProcessedDatasetsGateway`.

### Configuration / Composition root
- `src/Backend/Sudoku/Application/Datasets/DatasetsPreparationOptions.cs`
  - konfiguracja katalogów runtime, w tym `ProcessedDatasetsDirectoryPath`.
- `src/Backend/Sudoku/Sudoku/Program.cs`
  - walidacja typed options (`absolute paths`, spójność ratios).
- `src/Backend/Sudoku/Sudoku/appsettings.local.json`
  - lokalnie: wartości przypisane na sztywno (absolutne ścieżki runtime).
- `src/Backend/Sudoku/Sudoku/appsettings.production.json`
  - produkcyjny overlay z placeholderami podmienia workflow.

### Workflow GitHub
- `.github/workflows/backend-cd.yml`
  - generuje `appsettings.production.json` i nadpisuje sekcję `DatasetsPreparation`.
  - dla `GET /api/datasets/processed` krytyczna jest poprawna wartość `BE_DATASETS_PREP_PROCESSED_DIRECTORY_PATH`.

## 6) Weryfikacja usług Infrastructure (antyduplikacja)
- Istnieje generyczny `IFileStorageGateway` + `LocalFileStorageGateway` i należy go użyć.
- Nie tworzyć nowego adaptera typu „metadata file reader” tylko dla tego endpointa, jeśli operacje to standardowy `list/open/read`.
- Jeżeli trzeba dodać obsługę błędów/diagnostykę, rozszerzamy obecny `ProcessedDatasetsGateway`, bez dublowania ścieżek odczytu.

## 7) Przepływ BE (end-to-end)
1. FE wysyła `GET /api/datasets/processed` z tokenem admin.
2. `DatasetsController` wywołuje `ListProcessedDatasetsQuery`.
3. Handler pobiera rekordy z `IProcessedDatasetsGateway.ListAsync`.
4. Infrastructure skanuje `ProcessedDatasetsDirectoryPath` i odczytuje pliki `*.metadata.json`.
5. Handler sortuje rekordy malejąco po `createdAtUtc`, mapuje do DTO listy i wylicza `totalCount`.
6. Kontroler mapuje DTO na `ProcessedDatasetsListApiResponse` i zwraca `200`.

## 8) Główne funkcje (istniejące i docelowo doprecyzowywane)
- `DatasetsController.ListProcessedAsync(...)`
- `ListProcessedDatasetsQueryHandler.Handle(...)`
- `ProcessedDatasetsGateway.ListAsync(...)`
- `IFileStorageGateway.ListFilesAsync(...)`
- `IFileStorageGateway.OpenReadAsync(...)`

## 9) Wyjątki i fallbacki

### Publiczne statusy
- `200 OK` - lista poprawnie zwrócona (nawet gdy pusta).
- `401 Unauthorized` - brak/niepoprawny token administracyjny.
- `500 Internal Server Error` - błąd odczytu metadanych lub ich deserializacji (do jawnego mapowania na `ErrorApiResponse`).

### Scenariusze błędowe wewnętrzne
- Brak katalogu `processed` / brak dostępu I/O:
  - domyślnie błąd runtime (`IOException`/`UnauthorizedAccessException`),
  - mapowanie na `500` + `errorType` np. `processed_datasets_list_read_failed`.
- Uszkodzony JSON metadanych:
  - obecnie kończy listowanie wyjątkiem (`InvalidDataException`),
  - decyzja MVP: **fail fast** (spójność danych ponad częściowy sukces), zwracamy `500`.
- Pusty zbiór metadanych:
  - poprawna odpowiedź `200`, `items=[]`, `totalCount=0`.

### Fallback operacyjny
- Brak fallbacku do ML ani innych źródeł prawdy.
- Jedynym fallbackiem jest poprawna konfiguracja ścieżki `ProcessedDatasetsDirectoryPath` z `appsettings`.
- W razie uszkodzeń metadanych: naprawa operacyjna pliku metadanych (lub ponowne przygotowanie datasetu przez `POST`).

## 10) Pseudokod specyficznej logiki listowania

```text
handleListProcessedDatasets():
  metadata = processedDatasetsGateway.list()

  ordered = metadata
    .orderByDescending(createdAtUtc)

  items = ordered.map(m => {
    name: m.name,
    fileName: m.fileName,
    preprocessingProfile: m.preprocessingProfile,
    createdAtUtc: m.createdAtUtc,
    sampleCounts: m.sampleCounts
  })

  return {
    items: items,
    totalCount: items.length
  }
```

## 11) Inne istotne reguły
- `GET` nie ma prawa modyfikować stanu (`read-only`).
- Kolejność odpowiedzi ma być deterministyczna (`createdAtUtc` malejąco).
- `totalCount` ma odzwierciedlać liczbę elementów po odfiltrowaniu i mapowaniu.
- Brak zależności od aktualnego stanu FE/ML; endpoint zwraca wyłącznie publiczny kontrakt backendu.
- Publiczne błędy zawsze przez `ErrorApiResponse`.

## 12) Kolejność implementacji dla historyjki (prace domykające)
1. Doprecyzować mapowanie wyjątków dla `GET /api/datasets/processed` w kontrolerze (`500` + `ErrorApiResponse`).
2. Ujednolicić `errorType` dla błędów listowania (stałe w `Application/Datasets`).
3. Dodać testy jednostkowe handlera (`sortowanie`, `totalCount`).
4. Dodać testy integracyjne kontrolera (`200`, `401`, `500`).
5. Zweryfikować kontrakty i serializację `camelCase`.
6. Zweryfikować konfigurację `DatasetsPreparation.ProcessedDatasetsDirectoryPath` lokalnie i w workflow.

## 13) Workflow i konfiguracja (local vs production)
- Lokalnie ścieżki są wpisane na sztywno w `appsettings.local.json` (zgodnie z zasadą projektu).
- Produkcyjnie wartości do `appsettings.production.json` są podmieniane przez `.github/workflows/backend-cd.yml`.
- Dla tego endpointa nie są potrzebne nowe zmienne workflow; wymagane jest utrzymanie:
  - `BE_DATASETS_PREP_PROCESSED_DIRECTORY_PATH`
  - (oraz spójnie całej sekcji `DatasetsPreparation`, bo współdzieli ją `POST` i `GET`).

## 14) Guardraile implementacyjne
- `Application` definiuje reguły listowania; `Infrastructure` tylko realizuje I/O.
- Nie hardkodować ścieżek katalogów w kodzie.
- Nie mieszać kontraktów HTTP (`ApiResponse`) z DTO aplikacyjnymi (`Dto`).
- Nie dodawać zależności `GET` od endpointów ML.
- Trzymać kontroler cienki i bez logiki plikowej.

## 15) Zależności pomiędzy historyjkami
- Wejściowe:
  - `UC-13` - autoryzacja endpointu.
  - `UC-12 POST /api/datasets/processed` - źródło metadanych i artefaktów do listowania.
- Wyjściowe:
  - `UC-06` - wybór datasetu `.npz` do startu treningu.
- Kontekstowe:
  - `UC-11` pośrednio dostarcza źródła dla `POST`, a więc wpływa na to, co potem zwraca `GET`.

## 16) Model API wejściowy/wyjściowy (podsumowanie)
- FE -> BE input: brak body (HTTP GET).
- FE <- BE output: `ProcessedDatasetsListApiResponse` (`items`, `totalCount`).
- BE <-> ML: brak ruchu dla tego endpointa.
