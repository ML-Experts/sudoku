# Plan implementacyjny — UC-04-BE — `PUT /api/examples/{name}/preprocess/board`

## Cel endpointu
Uruchomić etap 1 preprocessingu dla przykładu z magazynu `examples`: odczytać plik po `name`, przekazać obraz do ML i zwrócić FE obraz po korekcji perspektywy jako `ImageApiResponse`. Backend nie zapisuje wyniku pośredniego na dysku.

## Kontrakt HTTP
| Element | Wartość |
|--------|---------|
| Metoda i ścieżka | `PUT /api/examples/{name}/preprocess/board` |
| Wejście | parametr ścieżki `name`, brak body |
| Odpowiedź sukcesu | `200 OK` + `ImageApiResponse` |
| Odpowiedzi błędów | `400`, `404`, `422`, `503`, `504` + `ErrorApiResponse` |
| Endpoint wewnętrzny ML | `PUT /ml/preprocess/board` |

## Modele wejścia / wyjścia
### Publiczne API
- wejście: `name`
- wyjście: `ImageApiResponse`
- błędy: `ErrorApiResponse`

### Application / Models
- `PreprocessExampleBoardCommand : IRequest<PreprocessBoardResultDto>`
- `PreprocessBoardResultDto`
  - `MimeType`
  - `Base64`
- współdzielony model domenowy/techniczny bez zależności od HTTP:
  - `ImageContent`
    - `MimeType`
    - `Content`

## Odpowiedzialność warstw
### `Api`
- Rozszerzyć `ExamplesController` o akcję `[HttpPut("{name}/preprocess/board")]`.
- Zbindować `name`, wywołać MediatR i zmapować wynik do `ImageApiResponse`.
- Mapować błędy:
  - `ValidationException` -> `400`
  - brak pliku -> `404`
  - błąd semantyczny z ML, np. `board_not_detected` -> `422`
  - niedostępność ML -> `503`
  - timeout ML -> `504`

### `Application`
- Dodać:
  - `PreprocessExampleBoardCommand`
  - `PreprocessExampleBoardCommandHandler`
  - `PreprocessExampleBoardCommandValidator`
  - `PreprocessBoardResultDto`
- Walidacja `name` taka sama jak w planie [`uc-04-get-examples-name.md`](uc-04-get-examples-name.md).
- Handler:
  1. Odczytuje `ExamplesUploadOptions` i wylicza `directoryPath` dla uploadów.
  2. Pobiera obraz przez generyczny `IFileStorageGateway` z parametrami `directoryPath` i `fileName`.
  3. Wyznacza `mimeType` z rozszerzenia pliku.
  4. Mapuje plik do modelu `ImageContent`.
  5. Wywołuje port ML do preprocessingu board.
  6. Zwraca `PreprocessBoardResultDto`.

### `Infrastructure`
- Nie tworzyć adaptera wyspecjalizowanego pod `examples`.
- Zamiast tego wprowadzić jeden reusable port po stronie `Application`, np. `IMlImageProcessingGateway`, z metodami:
  - `Task<ImageContent> PreprocessBoardAsync(ImageContent image, CancellationToken cancellationToken = default)`
  - `Task<CellsGrid> ExtractCellsAsync(ImageContent image, CancellationToken cancellationToken = default)`
- W `Infrastructure` dodać jedną implementację, np. `MlImageProcessingHttpClient`, która:
  - korzysta z `HttpClient`,
  - bierze `BaseUrl` i ścieżki z `MlServiceOptions`,
  - ma wewnętrzny generyczny helper przyjmujący parametr `relativePath`,
  - mapuje payload `{ mimeType, base64 }` do/z JSON `camelCase`.
- Techniczne błędy integracyjne zamieniać na generyczne wyjątki wielokrotnego użytku:
  - `MlServiceUnavailableException`
  - `MlServiceTimeoutException`
  - `MlOperationFailedException` z `ErrorType` i `Message`

## Elementy współdzielone z pozostałymi planami UC-04
- Reuse logiki odczytu pliku i walidacji `name` z planu [`uc-04-get-examples-name.md`](uc-04-get-examples-name.md).
- Wynik tego endpointu jest wejściem biznesowym dla planu [`uc-04-put-examples-preprocess-cells.md`](uc-04-put-examples-preprocess-cells.md).
- `IMlImageProcessingGateway` i `MlImageProcessingHttpClient` powinny obsłużyć zarówno ten endpoint, jak i etap `cells`.

## Sugerowane pliki
- `src/Backend/Sudoku/Application/Examples/PreprocessExampleBoardCommand.cs`
- `src/Backend/Sudoku/Application/Examples/PreprocessExampleBoardCommandHandler.cs`
- `src/Backend/Sudoku/Application/Examples/PreprocessExampleBoardCommandValidator.cs`
- `src/Backend/Sudoku/Application/Examples/PreprocessBoardResultDto.cs`
- `src/Backend/Sudoku/Application/Abstractions/IMlImageProcessingGateway.cs`
- `src/Backend/Sudoku/Application/Ml/MlOperationFailedException.cs`
- `src/Backend/Sudoku/Application/Ml/MlServiceUnavailableException.cs`
- `src/Backend/Sudoku/Application/Ml/MlServiceTimeoutException.cs`
- `src/Backend/Sudoku/Models/Images/ImageContent.cs`
- `src/Backend/Sudoku/Infrastructure/Ml/MlImageProcessingHttpClient.cs`
- aktualizacja:
  - `src/Backend/Sudoku/Infrastructure/Configuration/MlServiceOptions.cs`
  - `src/Backend/Sudoku/Infrastructure/DependencyInjection.cs`
  - `src/Backend/Sudoku/Sudoku/Controllers/ExamplesController.cs`
  - `src/Backend/Sudoku/Sudoku/appsettings.json`

## Konfiguracja
- Rozszerzyć `MlServiceOptions` o:
  - `PreprocessBoardPath`
  - `PreprocessCellsPath`
- Ścieżki do ML trzymać wyłącznie w `appsettings*.json`.
- Timeout nadal kontrolowany przez `MlServiceOptions.TimeoutSeconds`.

## Kolejność implementacji
1. Uzupełnić `MlServiceOptions` i `appsettings` o ścieżki preprocessingu.
2. Dodać współdzielony model `ImageContent` oraz port `IMlImageProcessingGateway`.
3. Zaimplementować `MlImageProcessingHttpClient` z parametryzowanym helperem po `relativePath`.
4. Dodać command, validator i handler dla etapu `board`.
5. Rozszerzyć `ExamplesController` i mapowanie błędów.

## Definition of Done
- Dla poprawnego `name` i działającego ML endpoint zwraca `200` oraz obraz po korekcji perspektywy.
- Dla nieistniejącego przykładu zwracane jest `404`.
- Gdy ML zwróci błąd typu `board_not_detected`, backend mapuje go do `422` z `ErrorApiResponse`.
- W `Infrastructure` nie pojawia się logika biznesowa typu „przetwarzanie przykładu”; adapter ML pozostaje generyczny i przyjmuje parametry konfiguracyjne.
