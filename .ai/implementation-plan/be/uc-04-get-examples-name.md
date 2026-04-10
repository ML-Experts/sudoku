# Plan implementacyjny — UC-04-BE — `GET /api/examples/{name}`

## Cel endpointu
Udostępnić FE obraz wybranego przykładu do podglądu jako `ImageApiResponse`. Ten endpoint nie wywołuje serwisu ML i nie zapisuje żadnych danych pośrednich.

## Kontrakt HTTP
| Element | Wartość |
|--------|---------|
| Metoda i ścieżka | `GET /api/examples/{name}` |
| Wejście | parametr ścieżki `name` |
| Odpowiedź sukcesu | `200 OK` + `ImageApiResponse` |
| Odpowiedzi błędów | `400 Bad Request`, `404 Not Found` + `ErrorApiResponse` |

## Modele wejścia / wyjścia
### Publiczne API
- `ImageApiResponse`
  - `mimeType: string`
  - `base64: string`
- `ErrorApiResponse`
  - `errorType: string`
  - `message: string`

### Application / Models
- `GetExampleImageQuery : IRequest<GetExampleImageResultDto>`
- `GetExampleImageResultDto`
  - `MimeType`
  - `Base64`
- opcjonalnie współdzielony model z `Models`, jeśli chcemy uniknąć duplikacji przy kolejnych endpointach:
  - `ImageContent`
    - `MimeType`
    - `Content`

## Odpowiedzialność warstw
### `Api`
- Rozszerzyć `ExamplesController` o akcję `[HttpGet("{name}")]`.
- Zbindować parametr `name`, wywołać MediatR i zmapować wynik do `ImageApiResponse`.
- Mapować błędy:
  - `ValidationException` -> `400`
  - brak pliku -> `404`

### `Application`
- Dodać `GetExampleImageQuery`, `GetExampleImageQueryHandler`, `GetExampleImageQueryValidator`, `GetExampleImageResultDto`.
- Walidacja `name`:
  - niepuste,
  - bez `..`,
  - bez separatorów ścieżki,
  - sensowna długość maksymalna.
- Handler:
  1. Odczytuje `ExamplesUploadOptions`.
  2. Buduje kanoniczny `directoryPath` dla katalogu uploadów na podstawie `RootPath` i `UploadsSubdirectory`.
  3. Wywołuje generyczny port plikowy z parametrami `directoryPath` i `fileName`.
  4. Wyznacza `mimeType` na podstawie rozszerzenia pliku.
  5. Koduje zawartość do Base64 i zwraca `GetExampleImageResultDto`.

### `Infrastructure`
- Rozszerzyć `IFileStorageGateway` o operację odczytu, ale nadal utrzymać adapter jako generyczny, np.:
  - `Task<Stream> OpenReadAsync(string directoryPath, string fileName, CancellationToken cancellationToken = default)`
- Jeśli plik nie istnieje, zwracać generyczny wyjątek infrastrukturalny możliwy do reuse, np. `FileStorageItemNotFoundException`.
- `LocalFileStorageGateway` ma przyjmować wyłącznie parametry `directoryPath` i `fileName`; nie może znać pojęcia `examples`.
- Zachować tę samą ochronę przed wyjściem poza katalog docelowy, która już istnieje przy `SaveAsync`.

## Elementy współdzielone z pozostałymi planami UC-04
- Ten plan definiuje wspólny sposób:
  - walidacji `name`,
  - wyliczania ścieżki do magazynu przykładów,
  - zwracania obrazu jako `ImageApiResponse`.
- Plan [`uc-04-put-examples-name-preprocess-board.md`](uc-04-put-examples-name-preprocess-board.md) powinien reuseować tę samą walidację i ten sam mechanizm odczytu pliku.

## Sugerowane pliki
- `src/Backend/Sudoku/Application/Examples/GetExampleImageQuery.cs`
- `src/Backend/Sudoku/Application/Examples/GetExampleImageQueryHandler.cs`
- `src/Backend/Sudoku/Application/Examples/GetExampleImageQueryValidator.cs`
- `src/Backend/Sudoku/Application/Examples/GetExampleImageResultDto.cs`
- `src/Backend/Sudoku/Application/Storage/FileStorageItemNotFoundException.cs`
- `src/Backend/Sudoku/Sudoku/Contracts/ImageApiResponse.cs`
- aktualizacja:
  - `src/Backend/Sudoku/Application/Abstractions/IFileStorageGateway.cs`
  - `src/Backend/Sudoku/Infrastructure/Storage/LocalFileStorageGateway.cs`
  - `src/Backend/Sudoku/Sudoku/Controllers/ExamplesController.cs`

## Kolejność implementacji
1. Dodać `ImageApiResponse` w warstwie `Contracts`.
2. Rozszerzyć `IFileStorageGateway` i `LocalFileStorageGateway` o odczyt pliku po parametrach.
3. Dodać query, validator i handler w `Application/Examples`.
4. Dodać akcję w `ExamplesController` oraz mapowanie `400/404`.

## Definition of Done
- Dla pliku dodanego przez UC-01 endpoint zwraca `200` i poprawne `mimeType` oraz `base64`.
- Dla nieistniejącego `name` endpoint zwraca `404` i `ErrorApiResponse`.
- Dla nieprawidłowego `name` endpoint zwraca `400` po walidacji FluentValidation.
- W `Infrastructure` nie pojawia się żaden adapter typu `ExamplesFileStorageGateway`; pozostaje jeden generyczny `IFileStorageGateway` przyjmujący parametry.
