# UC-05B — Backtracking dla rozpoznanego gridu

## Cel
Rozwiązać sudoku na podstawie rozpoznanego gridu 9×9 zawierającego cyfry i puste pola.

## Zachowanie solvera
Backtracking w Sudoku to metoda "spróbuj -> sprawdź -> cofnij się, jeśli źle".

To oznacza, że solver:
1. wybiera puste pole,
2. wylicza dozwolone cyfry,
3. wpisuje jedną z nich,
4. przechodzi dalej,
5. jeśli później trafi w ślepą uliczkę, usuwa ostatnio wpisaną cyfrę i próbuje kolejną.

Kluczowe jest właśnie to cofnięcie:
- solver nie tylko dodaje cyfry,
- solver również usuwa wcześniej wpisane cyfry, jeśli dana gałąź decyzji prowadzi do sprzeczności, ale dotyczy to wyłącznie cyfr dodanych przez sam solver.

## Niezmiennik pól wejściowych
Grid wejściowy przekazany do `UC-05B` zawiera dwa rodzaje pól:
- pola wejściowe, które pochodzą z `recognizedGrid` zbudowanego wcześniej po `UC-05A`,
- pola robocze, które solver sam uzupełnia podczas rozwiązywania.

To prowadzi do twardej reguły:
- solver nigdy nie może usunąć ani nadpisać cyfr, które były obecne w gridzie wejściowym,
- backtracking może cofać wyłącznie cyfry wpisane przez solver w puste wcześniej pola.

## Zachowanie wyboru pola
Solver nie musi i nie powinien być opisany jako "rozwiązywanie po kolei rzędami".

### Wersja rekomendowana
W `MVP` rekomendowany jest wariant:
- dla każdego pustego pola liczymy zbiór kandydatów,
- wybieramy pole z najmniejszą liczbą kandydatów,
- jeśli kilka pól ma ten sam minimalny wynik, stosujemy deterministyczny tie-break, np. od góry do dołu i od lewej do prawej.

To jest zgodne z intuicją z `@.ai/Backtracking.md`: lepiej zacząć od najbardziej ograniczonego pola niż iść ślepo po planszy.

### Zachowanie przy ślepym zaułku
Jeśli w którymkolwiek momencie:
- jakieś puste pole ma `0` kandydatów,
- albo wpisanie cyfry prowadzi do dalszej sprzeczności,

to solver:
1. uznaje bieżącą gałąź za błędną,
2. usuwa ostatnio wpisaną cyfrę dodaną przez solver,
3. wraca poziom wyżej w drzewie decyzji,
4. próbuje następną dozwoloną cyfrę.

## Rekomendacja architektoniczna
Solver dzieje się wyłącznie w `Backendzie` jako logika aplikacyjna / domenowa. Dzięki temu:
- solver jest łatwy do testowania jednostkowego,
- nie dokładamy zależności sieciowej do deterministycznego algorytmu,
- `Backend` pozostaje właścicielem walidacji i kontraktu publicznego.

## Kontrakt `FE -> BE`
### `POST /api/sudoku/solve`
- Request body: `SolveSudokuApiEntry`.
- `202 Accepted` -> `SolveSessionApiResponse`.

Przykład requestu:

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
  ]
}
```

Przykład odpowiedzi:

```json
{
  "solveSessionId": "solve-20260511-205000-demo-01",
  "status": "queued",
  "progressChannelUrl": "/ws/sudoku/solving/solve-20260511-205000-demo-01"
}
```

Semantyka:
- `POST /api/sudoku/solve` nie czeka na pełne zakończenie backtrackingu,
- endpoint tylko waliduje wejście, uruchamia sesję rozwiązywania i zwraca identyfikator sesji,
- końcowy sukces albo porażka wracają asynchronicznie przez kanał `SignalR` opisany w `UC-05E`.

Reguły odpowiedzi błędnych:
- `400 Bad Request` -> payload nie ma poprawnego kształtu 9×9,
- `422 Unprocessable Entity` -> grid zawiera niedozwolone wartości albo łamie reguły sudoku już na wejściu,
- `409 Conflict` -> istnieje już aktywna sesja solve, jeśli w `MVP` dopuszczamy tylko jedną na użytkownika albo w kontekście jednego widoku.

Jeśli grid przejdzie walidację wejścia, ale okaże się nierozwiązywalny dopiero w trakcie działania solvera, wynik nie wraca jako synchroniczne `409`, tylko jako końcowy event `failed` na kanale `SignalR`.

### `GET /api/sudoku/solve/active`
- `200 OK` -> `SolveSessionApiResponse`, jeśli istnieje aktywna sesja solve,
- `204 No Content`, jeśli nie ma aktywnej sesji.

Ten endpoint pozwala `FE` odzyskać monitoring po odświeżeniu widoku albo po odpowiedzi `409`.

### `POST /api/sudoku/solve/{solveSessionId}/cancel`
- `202 Accepted` -> `CancelSolveSessionApiResponse`.

Anulowanie jest:
- kooperacyjne,
- idempotentne,
- przeznaczone dla aktualnie aktywnej sesji solve.

Minimalna semantyka odpowiedzi:
- `status` -> bieżący status dopasowanej sesji albo `null`,
- `requestDisposition` -> informacja, czy żądanie anulowania było nowe, duplikatem czy no-opem.

Przykład:

```json
{
  "status": "cancelling",
  "requestDisposition": "accepted"
}
```

Jeśli żądanie nie pasuje do żadnej aktywnej sesji, endpoint nadal może zwrócić `202 Accepted`, ale z `status = null` i odpowiednim `requestDisposition`.

## Kontrakt `BE -> ML`
Brak kontraktu `BE -> ML` dla solvera.

`UC-05B` nie angażuje usługi `ML`; rozwiązanie sudoku jest liczone wyłącznie po stronie `Backendu`.

## Uwaga o deterministyczności
Jeśli solver ma wspierać później prezentację kroków na żywo w `UC-05E`, dobrze utrzymać deterministyczne zasady:
- stały sposób wyboru pola,
- stałą kolejność kandydatów, np. rosnąco `1..9`,
- stabilny tie-break dla pól z taką samą liczbą kandydatów.

To ułatwi zarówno testy, jak i spójne demo działania algorytmu.

## Relacja do gridu z `UC-05A`
`UC-05B` pracuje na tym samym logicznym gridzie, który `FE` zbudował po `UC-05A`.

Z perspektywy `UI` oznacza to:
- cyfry wejściowe z `recognizedGrid` stają się polami zablokowanymi,
- cyfry dopisywane przez solver są polami roboczymi,
- tylko pola robocze mogą być później czyszczone przez backtracking.

## Relacja do `UC-05E`
`UC-05B` definiuje logikę solve i start sesji rozwiązywania, natomiast `UC-05E` definiuje transport zdarzeń postępu i zdarzenia końcowego.

W praktyce:
- `POST /api/sudoku/solve` uruchamia solver,
- `GET /api/sudoku/solve/active` pozwala odzyskać aktywną sesję,
- `POST /api/sudoku/solve/{solveSessionId}/cancel` uruchamia kooperacyjne anulowanie,
- `SignalR /ws/sudoku/solving/{solveSessionId}` emituje kroki backtrackingu,
- sukces końcowy wraca jako event `completed`,
- porażka końcowa wraca jako event `failed`,
- anulowanie końcowe wraca jako event `cancelled`.

## Jedna aktywna sesja
W `MVP` system dopuszcza dokładnie jedną aktywną sesję backtrackingu na użytkownika albo w kontekście jednego widoku solve.

To oznacza, że:
- jeśli aktywna sesja już istnieje, `POST /api/sudoku/solve` nie tworzy nowej,
- `FE` powinno wtedy przejść do monitoringu istniejącej sesji przez `GET /api/sudoku/solve/active`,
- nowa sesja może powstać dopiero po stanie terminalnym `completed`, `failed` albo `cancelled`.

## Kryteria akceptacji
- Solver nie jest opisany jako proste "wypełnianie kolejnych rzędów", tylko jako eksploracja drzewa decyzji.
- W rekomendowanym wariancie solver wybiera najbardziej ograniczone puste pole.
- Solver cofa wcześniejsze decyzje, gdy bieżąca ścieżka prowadzi do sprzeczności.
- Solver nigdy nie usuwa ani nie nadpisuje cyfr obecnych w gridzie wejściowym.
- `POST /api/sudoku/solve` uruchamia solve asynchronicznie i nie blokuje żądania do czasu znalezienia rozwiązania.
- Jeśli aktywna sesja solve już istnieje, system nie uruchamia nowej sesji przed zakończeniem albo anulowaniem poprzedniej.
- Dostępny jest odczyt aktywnej sesji i kooperacyjne anulowanie aktywnego backtrackingu.
- Końcowy sukces albo porażka solvera wracają przez `SignalR`.
- Końcowe anulowanie solvera wraca przez `SignalR` jako `cancelled`.
- Logika solvera jest możliwa do testowania niezależnie od inferencji obrazu.
