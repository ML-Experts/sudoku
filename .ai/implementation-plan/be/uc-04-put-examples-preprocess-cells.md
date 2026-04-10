# Plan implementacyjny — UC-04-BE — `PUT /api/examples/preprocess/cells`

## Cel endpointu
Przyjąć z FE obraz planszy po etapie `board` jako `ImageApiEntry`, przekazać go do ML i zwrócić siatkę 9x9 komórek jako `CellsGridApiResponse`. Backend nie zapisuje wyniku na dysku i nie odwołuje się już do magazynu `examples`.

## Kontrakt HTTP
| Element | Wartość |
|--------|---------|
| Metoda i ścieżka | `PUT /api/examples/preprocess/cells` |
| Body | `ImageApiEntry` |
| Odpowiedź sukcesu | `200 OK` + `CellsGridApiResponse` |
| Odpowiedzi błędów | `400`, `422`, `503`, `504` + `ErrorApiResponse` |
| Endpoint wewnętrzny ML | `PUT /ml/preprocess/cells` |

## Modele wejścia / wyjścia
### Publiczne API
- `ImageApiEntry`
  - `mimeType: string`
  - `base64: string`
- `ImageApiResponse`
  - `mimeType: string`
  - `base64: string`
- `CellsGridApiResponse`
  - `cells: ImageApiResponse[9][9]`
- `ErrorApiResponse`
  - `errorType: string`
  - `message: string`

### Application / Models
- `PreprocessExampleCellsCommand : IRequest<PreprocessCellsResultDto>`
- `PreprocessCellsResultDto`
  - `Cells`
- współdzielone modele bez zależności od HTTP:
  - `ImageContent`
    - `MimeType`
    - `Content`
  - `CellsGrid`
    - kolekcja 9x9 `ImageContent`
    - pilnuje niezmiennika 9 wierszy i 9 kolumn

## Odpowiedzialność warstw
### `Api`
- Rozszerzyć `ExamplesController` o akcję `[HttpPut("preprocess/cells")]`.
- Przyjmować body jako `ImageApiEntry`, mapować na komendę MediatR i zwracać `CellsGridApiResponse`.
- Mapować błędy:
  - walidacja wejścia -> `400`
  - błąd semantyczny z ML -> `422`
  - ML niedostępne -> `503`
  - timeout ML -> `504`
- Jeśli zespół chce zachować pełną symetrię z uploadem, przekroczenie limitu payloadu można dodatkowo mapować na `413`, ale bazowy kontrakt UC-04 nie wymaga tego rozszerzenia.

### `Application`
- Dodać:
  - `PreprocessExampleCellsCommand`
  - `PreprocessExampleCellsCommandHandler`
  - `PreprocessExampleCellsCommandValidator`
  - `PreprocessCellsResultDto`
- Wprowadzić use-case'owe opcje, np. `ExamplesPreprocessOptions`, z limitem dla obrazu przekazywanego inline w JSON.
- Walidacja:
  - niepusty `mimeType`,
  - dozwolony typ MIME,
  - niepusty `base64`,
  - poprawne dekodowanie Base64,
  - rozmiar po dekodowaniu w granicach limitu.
- Handler:
  1. Dekoduje `base64` do bajtów.
  2. Tworzy `ImageContent`.
  3. Wywołuje współdzielony `IMlImageProcessingGateway.ExtractCellsAsync(...)`.
  4. Waliduje, że wynik ma dokładnie strukturę 9x9.
  5. Zwraca `PreprocessCellsResultDto`.

### `Infrastructure`
- Reuse tej samej implementacji `MlImageProcessingHttpClient`, która obsługuje także etap `board`.
- Klient HTTP ma mieć wspólny helper przyjmujący `relativePath` z konfiguracji i payload obrazu.
- Adapter pozostaje generyczny:
  - nie zna pojęcia `examples`,
  - nie zapisuje tymczasowych plików biznesowych,
  - nie zawiera logiki walidacji 9x9.
- Obsługuje mapowanie błędów sieciowych / timeoutów / błędów odpowiedzi do wspólnych wyjątków integracyjnych.

## Elementy współdzielone z pozostałymi planami UC-04
- Endpoint biznesowo następuje po [`uc-04-put-examples-name-preprocess-board.md`](uc-04-put-examples-name-preprocess-board.md), ale technicznie nie zależy od magazynu plików.
- Reuse:
  - `ImageApiEntry`
  - `ImageApiResponse`
  - `ImageContent`
  - `IMlImageProcessingGateway`
  - `MlImageProcessingHttpClient`

## Sugerowane pliki
- `src/Backend/Sudoku/Application/Examples/PreprocessExampleCellsCommand.cs`
- `src/Backend/Sudoku/Application/Examples/PreprocessExampleCellsCommandHandler.cs`
- `src/Backend/Sudoku/Application/Examples/PreprocessExampleCellsCommandValidator.cs`
- `src/Backend/Sudoku/Application/Examples/PreprocessCellsResultDto.cs`
- `src/Backend/Sudoku/Application/Examples/ExamplesPreprocessOptions.cs`
- `src/Backend/Sudoku/Models/Images/CellsGrid.cs`
- `src/Backend/Sudoku/Sudoku/Contracts/ImageApiEntry.cs`
- `src/Backend/Sudoku/Sudoku/Contracts/ImageApiResponse.cs`
- `src/Backend/Sudoku/Sudoku/Contracts/CellsGridApiResponse.cs`
- aktualizacja:
  - `src/Backend/Sudoku/Sudoku/Controllers/ExamplesController.cs`
  - `src/Backend/Sudoku/Sudoku/Program.cs`
  - `src/Backend/Sudoku/Infrastructure/Configuration/MlServiceOptions.cs`
  - `src/Backend/Sudoku/Infrastructure/DependencyInjection.cs`

## Konfiguracja
- Dodać `ExamplesPreprocessOptions` w warstwie `Application` i zbindować w `Program.cs`.
- Wykorzystać `MlServiceOptions.PreprocessCellsPath` oraz istniejący timeout.
- Nie trzymać żadnych limitów payloadu ani ścieżek ML jako stałych w validatorze lub kliencie HTTP.

## Kolejność implementacji
1. Dodać kontrakty `ImageApiEntry`, `ImageApiResponse`, `CellsGridApiResponse`.
2. Dodać `ExamplesPreprocessOptions` i bind w `Program.cs`.
3. Dodać `CellsGrid` oraz reuse `ImageContent` i `IMlImageProcessingGateway`.
4. Dodać command, validator i handler dla etapu `cells`.
5. Rozszerzyć `ExamplesController` i mapowanie błędów.

## Definition of Done
- Dla poprawnego obrazu planszy endpoint zwraca `200` i `cells` o wymiarze 9x9.
- Dla błędnego `base64` lub niedozwolonego `mimeType` zwracane jest `400`.
- Dla błędu semantycznego z ML zwracane jest `422` z `errorType` i `message`.
- `Infrastructure` pozostaje współdzielone i parametryzowane; nie powstaje osobny adapter szyty wyłącznie pod ten endpoint.
