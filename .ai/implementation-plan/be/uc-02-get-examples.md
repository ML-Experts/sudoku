# UC-02-BE - Plan implementacyjny dla `GET /api/examples`

## Cel
- Dodać endpoint zwracający listę plików przykładowych z katalogu `examples/uploads`.
- Zachować clean architecture: `Api` tylko binduje i mapuje kontrakt HTTP, `Application` realizuje use case i decyduje, który katalog należy odczytać, a `Infrastructure` dostarcza generyczną operację listowania plików po przekazanej ścieżce.
- Nie wprowadzać bazy danych, sidecarów JSON ani udziału serwisu `ML`.

## Stan obecny
- `ExamplesController` obsługuje tylko `POST /api/examples`.
- Warstwa `Application/Examples` zawiera wyłącznie use case uploadu.
- `IFileStorageGateway` i `LocalFileStorageGateway` wspierają obecnie tylko zapis pliku.
- Konfiguracja `ExamplesUploadOptions` miesza ścieżki wspólnego magazynu `examples` z limitem uploadu, co utrudnia reużycie w `UC-02`, `UC-03` i `UC-04`.

## Decyzje architektoniczne
- Nie tworzymy adaptera typu `IExamplesRepository` w `Infrastructure`, bo to wprowadzałoby semantykę use case'u do warstwy zewnętrznej.
- Rozszerzamy istniejący generyczny port `IFileStorageGateway` o metodę listującą pliki dla przekazanego `directoryPath`.
- Decyzja, że należy czytać dokładnie `RootPath + UploadsSubdirectory`, pozostaje w `Application`.
- Brak katalogu `examples/uploads` traktujemy jako poprawny stan i zwracamy pustą listę.
- `storedAtUtc` wyznaczamy z `LastWriteTimeUtc`, zakładając że pliki po zapisie są niemodyfikowalne.
- W `Application` filtrujemy tylko wspierane rozszerzenia `.jpg`, `.jpeg`, `.png`, aby endpoint nie ujawniał przypadkowych obcych plików z katalogu.
- Wynik sortujemy deterministycznie: malejąco po `storedAtUtc`, a następnie rosnąco po `name`.

## Docelowy przepływ
1. `FE` wywołuje `GET /api/examples`.
2. `ExamplesController` wysyła przez `MediatR` zapytanie `ListExamplesQuery`.
3. `ListExamplesQueryHandler` buduje ścieżkę do `examples/uploads` na podstawie opcji magazynu.
4. Handler wywołuje `IFileStorageGateway.ListFilesAsync(uploadsDirectoryPath, cancellationToken)`.
5. `Infrastructure` zwraca techniczne metadane plików z katalogu bez logiki domenowej `examples`.
6. `Application` filtruje wspierane rozszerzenia, mapuje rozszerzenie na `contentType`, mapuje `LastWriteTimeUtc` na `storedAtUtc`, sortuje wynik i buduje `ListExamplesQueryResultDto`.
7. Kontroler mapuje DTO na `ExamplesListApiResponse` i zwraca `200 OK`.

## Zakres zmian w kodzie
### `Api`
- Rozszerzyć `src/Backend/Sudoku/Sudoku/Controllers/ExamplesController.cs` o akcję `[HttpGet]` typu `ListAsync`.
- Dodać kontrakt `src/Backend/Sudoku/Sudoku/Contracts/ExamplesListApiResponse.cs`.
- Zostawić kontroler cienki: bez logiki filesystemu, bez walidacji biznesowej i bez mapowania ścieżek.

### `Application`
- Dodać `src/Backend/Sudoku/Application/Examples/ListExamplesQuery.cs`.
- Dodać `src/Backend/Sudoku/Application/Examples/ListExamplesQueryHandler.cs`.
- Dodać `src/Backend/Sudoku/Application/Examples/ListExamplesQueryResultDto.cs`.
- Dodać DTO elementu listy, np. `src/Backend/Sudoku/Application/Examples/ListExamplesItemDto.cs`.
- Dodać generyczny model metadanych storage, np. `src/Backend/Sudoku/Application/Storage/StoredFileMetadataDto.cs`.
- Rozszerzyć `src/Backend/Sudoku/Application/Abstractions/IFileStorageGateway.cs` o metodę `ListFilesAsync(...)`.
- Nie dodawać walidatora `FluentValidation`, bo endpoint nie przyjmuje danych wejściowych poza samym żądaniem `GET`.
- Wydzielić wspólną konfigurację magazynu `examples` do neutralnego typu `ExamplesStorageOptions`.

### `Infrastructure`
- Rozszerzyć `src/Backend/Sudoku/Infrastructure/Storage/LocalFileStorageGateway.cs` o implementację `ListFilesAsync(...)`.
- Implementacja powinna normalizować ścieżkę przez `Path.GetFullPath(...)`.
- Implementacja powinna zwracać pustą kolekcję, gdy katalog nie istnieje.
- Implementacja powinna listować tylko pliki bez rekursji i ignorować podkatalogi.
- Implementacja powinna zwracać wyłącznie techniczne metadane: `name`, `sizeBytes`, `lastModifiedUtc`.
- Rejestracja DI w `src/Backend/Sudoku/Infrastructure/DependencyInjection.cs` może pozostać bez zmian, bo nadal używamy tego samego gatewaya.

### `Configuration`
- Dodać `ExamplesStorageOptions` z polami `RootPath` i `UploadsSubdirectory`.
- Ograniczyć `ExamplesUploadOptions` do `MaxUploadSizeBytes`.
- Zaktualizować `src/Backend/Sudoku/Sudoku/Program.cs`, aby bindował oba typy opcji.
- Zaktualizować `src/Backend/Sudoku/Sudoku/appsettings.json`, tak aby `ExamplesStorage` zawierało tylko ścieżki.
- Zaktualizować `src/Backend/Sudoku/Sudoku/appsettings.json`, tak aby `ExamplesUpload` zawierało limit uploadu.
- Zaktualizować `src/Backend/Sudoku/Sudoku/appsettings.local.json`, aby nadpisywał tylko `ExamplesStorage.RootPath`.
- Przy okazji przepiąć istniejący `UploadExampleCommandHandler` i `UploadExampleCommandValidator` na nowe typy opcji.

## Proponowane typy
```csharp
public sealed record StoredFileMetadataDto(
    string Name,
    long SizeBytes,
    DateTimeOffset LastModifiedUtc);

public sealed record ListExamplesItemDto(
    string Name,
    string ContentType,
    long SizeBytes,
    DateTimeOffset StoredAtUtc);

public sealed record ListExamplesQueryResultDto(
    IReadOnlyList<ListExamplesItemDto> Items,
    int TotalCount);
```

```csharp
public interface IFileStorageGateway
{
    Task SaveAsync(
        string directoryPath,
        string fileName,
        Stream content,
        CancellationToken cancellationToken = default);

    Task<IReadOnlyList<StoredFileMetadataDto>> ListFilesAsync(
        string directoryPath,
        CancellationToken cancellationToken = default);
}
```

## Kroki implementacyjne
1. Rozdzielić konfigurację `examples` na `ExamplesStorageOptions` i `ExamplesUploadOptions`, a następnie przepiąć istniejący use case uploadu.
2. Dodać generyczny model metadanych pliku oraz metodę `ListFilesAsync(...)` do portu storage.
3. Zaimplementować listowanie w `LocalFileStorageGateway`.
4. Dodać `ListExamplesQuery`, handler i DTO use case'u w `Application`.
5. Rozszerzyć `ExamplesController` o akcję `GET` i dodać `ExamplesListApiResponse`.
6. Zweryfikować lokalnie zachowanie dla pustego katalogu, katalogu z obrazami oraz katalogu zawierającego obce pliki.

## Weryfikacja implementacji
- `GET /api/examples` zwraca `200 OK` i pustą listę, gdy katalog `examples/uploads` nie istnieje.
- `GET /api/examples` zwraca wpisy dla plików `jpg`, `jpeg`, `png`.
- `contentType` jest wyliczany poprawnie na podstawie rozszerzenia.
- `totalCount` odpowiada liczbie elementów w `items`.
- Wynik jest deterministycznie posortowany.
- Istniejący `POST /api/examples` nadal działa po rozdzieleniu konfiguracji.

## Ryzyka i uwagi
- W repo nie ma dziś projektu testowego backendu, więc minimalnym bezpiecznym zakresem weryfikacji powinien być test manualny endpointu oraz regresja uploadu.
- Przykłady `name` w dokumentacji nie pokazują obecnego sufiksu losowego generowanego przez backend przy uploadzie. Sam plan dla `UC-02` powinien jednak traktować aktualnie zwracane `name` z backendu jako źródło prawdy i nie wiązać listowania z konkretnym formatem nazwy.
- Jeżeli w przyszłości pojawi się potrzeba paginacji lub filtrowania, powinno to zostać dodane jako osobne query parameters i osobny etap walidacji w `Application`, bez rozszerzania odpowiedzialności `Infrastructure`.
