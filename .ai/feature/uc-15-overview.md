# UC-15 — Spowolnienie live solve przez opóźnienie kroku

## Cel
- Sprawić, aby użytkownik mógł realnie obserwować kolejne wpisania i cofnięcia wykonywane przez backtracking w `UC-05E`.
- Wprowadzić sterowane opóźnienie między kolejnymi krokami solvera bez zmiany publicznego modelu eventów `SignalR`.
- Zrealizować to jako etap przejściowy przed pełną parametryzacją z `UC-14`.

## Historyjka
Jako użytkownik chcę, aby podczas `live solve` kolejne kroki backtrackingu były celowo spowolnione, żebym mógł zobaczyć co zmienia się na planszy, nawet jeśli sam solver znajduje rozwiązanie bardzo szybko.

## Zakres decyzji
- `UC-15` nie dodaje nowego endpointu.
- `UC-15` nie zmienia modelu eventów `SignalR` z `UC-05E`.
- `UC-15` nie dodaje jeszcze edytowalnego pola w `GUI`.
- Parametr opóźnienia jest na razie zahardcodowany w `FE`, ale przekazywany do istniejącego endpointu `POST /api/sudoku/solve`.
- Docelowo ten sam parametr może zostać wystawiony użytkownikowi przez panel `UC-14`.

## Zasada działania
Przy starcie sesji `live solve` `FE` wysyła w requestcie `POST /api/sudoku/solve` pole `solverStepDelayMs`.

`BE`:
- przyjmuje tę wartość,
- waliduje ją,
- domyka bezpieczną wartość domyślną, jeśli zajdzie taka potrzeba,
- zapisuje resolved wartość w rekordzie sesji,
- przekazuje ją przez kolejne metody aż do miejsca, które steruje tempem wykonywania solvera live.

Samo opóźnienie ma być stosowane pomiędzy kolejnymi zmianami planszy emitowanymi do `SignalR`, tak aby użytkownik mógł zobaczyć każdą sekwencję postępu:
- wpisanie cyfry,
- cofnięcie cyfry podczas backtrackingu,
- przejście do następnej próby.

## Reguła czasu
- Opóźnienie dotyczy tylko sesji `live solve`.
- Opóźnienie jest stosowane między kolejnymi krokami postępu, a nie jako osobny delay przed odpowiedzią `202 Accepted`.
- Nie trzeba sztucznie opóźniać samego startowego `snapshot` ani końcowego eventu terminalnego, chyba że implementacja techniczna wymaga jednolitego modelu pętli; z perspektywy produktu istotne jest spowolnienie kroków pośrednich.

## Tymczasowy sposób sterowania z `FE`
Na obecnym etapie `GUI` nie pokazuje użytkownikowi kontrolki do ustawiania `solverStepDelayMs`.

Zamiast tego:
- `FE` trzyma jedną zahardcodowaną wartość dla `live solve`,
- domyślna wartość tej stałej w obecnym etapie wynosi `50 ms`,
- `FE` zawsze przekazuje ją do `POST /api/sudoku/solve`,
- użytkownik korzysta z efektu spowolnienia bez dodatkowej konfiguracji w interfejsie.

To jest decyzja świadoma i przejściowa:
- najpierw chcemy uzyskać lepszy odbiór UX,
- dopiero później ewentualnie odsłonić parametr w panelu z `UC-14`.

## Kontrakt `FE -> BE`
### `POST /api/sudoku/solve`
Request `SolveSudokuApiEntry` zostaje rozszerzony o:
- `solverStepDelayMs`

Przykład:

```json
{
  "grid": [
    [5, 3, null, null, 7, null, null, null, null],
    [6, null, null, 1, 9, 5, null, null, null],
    [null, 9, 8, null, null, null, null, 6, null],
    [8, null, null, null, 6, null, null, null, 3],
    [4, null, null, 8, null, 3, null, null, 1],
    [7, null, null, null, 2, null, null, null, 6],
    [null, 6, null, null, null, null, 2, 8, null],
    [null, null, null, 4, 1, 9, null, null, 5],
    [null, null, null, null, 8, null, null, 7, 9]
  ],
  "solverStepDelayMs": 120
}
```

Semantyka:
- parametr opisuje opóźnienie w milisekundach między kolejnymi krokami `live solve`,
- parametr nie zmienia logiki wyboru kandydatów ani wyniku końcowego solvera,
- parametr wpływa tylko na tempo obserwacji sesji.

## Zasady dla `BE`
- `BE` pozostaje właścicielem walidacji `solverStepDelayMs`.
- `BE` nie czyta tej wartości z losowego miejsca w środku implementacji; ma ją dostać jawnie z warstwy wyżej.
- Wartość resolved powinna przepływać przez model sesji albo argumenty metod aż do miejsca wykonania opóźnienia.
- `BE` zapisuje `solverStepDelayMs` w `effectiveParameters`, aby później było wiadomo, z jakim tempem była odtwarzana sesja.
- Jeśli `FE` nie przekaże parametru albo przekaże wartość spoza zakresu, `BE` stosuje własną politykę walidacji i bezpieczną wartość domyślną.

## Zasady dla `ML`
- `UC-15` nie rozszerza kontraktów `BE -> ML`.
- Solver backtracking i tempo jego live prezentacji pozostają po stronie `BE`.

## Relacja do `UC-05E`
- `UC-05E` definiuje model eventów, kanał `SignalR` i semantykę sesji live solve.
- `UC-15` nie zmienia tych eventów; tylko reguluje tempo, w jakim kolejne eventy są emitowane.
- Dzięki temu `FE` zachowuje ten sam reducer i ten sam sposób porównywania kolejnych `currentGrid`.

## Relacja do `UC-14`
- `UC-15` jest etapem przejściowym.
- Dzisiaj wartość jest zahardcodowana w `FE`, ale przechodzi przez publiczny kontrakt endpointu.
- W przyszłości `UC-14` może odsłonić ten sam parametr użytkownikowi bez zmiany podstawowej architektury przepływu.

## Kryteria akceptacji
- Użytkownik widzi kolejne kroki backtrackingu na tyle wolno, że może śledzić zmiany planszy.
- `GUI` nie pokazuje jeszcze pola do ręcznej edycji `solverStepDelayMs`.
- `FE` przekazuje `solverStepDelayMs` w istniejącym `POST /api/sudoku/solve`.
- `BE` waliduje i zapisuje resolved wartość opóźnienia w sesji solve.
- Wartość opóźnienia przepływa przez kolejne metody aż do miejsca wykonania `sleep`.
- `UC-15` nie dodaje nowego endpointu ani nie zmienia kontraktu eventów `SignalR`.
- Wynik końcowy solvera pozostaje taki sam jak bez opóźnienia; zmienia się tylko tempo prezentacji kroków.
