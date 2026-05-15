# UC-05E — Pokazywanie kroków backtrackingu na żywo przez SignalR

## Cel
Pokazać użytkownikowi, że solver naprawdę "pracuje" nad sudoku, emitując przez `SignalR` każdą zmianę planszy:
- dodanie cyfry,
- usunięcie cyfry podczas cofania,
- stan końcowy sukcesu albo porażki.

Ta historyjka jest osobnym rozszerzeniem `UC-05B`. Nie zmienia logiki solvera, tylko dodaje publiczny kontrakt obserwacji jego kroków.

## Zachowanie biznesowe
Backtracking nie jest liniowym "wypełnianiem planszy", tylko eksploracją drzewa decyzji. Dlatego użytkownik powinien widzieć nie tylko finalne wpisy, ale też cofnięcia:
- gdy solver wybiera cyfrę dla pola, `UI` dostaje event dodania,
- gdy solver dochodzi do sprzeczności i wraca, `UI` dostaje event usunięcia,
- po zakończeniu `UI` dostaje stan końcowy.

To jest ważne z perspektywy UX, bo buduje wrażenie pracy z prawdziwym sudoku, a nie natychmiastowego "magicznego" wyniku.

Ważne doprecyzowanie: eventy z `UC-05E` nie budują osobnej planszy. Opisują kolejne pełne snapshoty tego samego gridu, który został wcześniej zainicjalizowany po `UC-05A` jako `recognizedGrid`.

## Kluczowa decyzja: jeden model eventu oparty o pełny snapshot
W `MVP` nie rozdzielamy socketowych payloadów na:
- osobny pełny stan planszy,
- osobną deltę pojedynczej zmiany.

Zamiast tego każdy event `SignalR` używa jednego wspólnego kontraktu i zawsze niesie:
- `solveSessionId`,
- `eventType`,
- `status`,
- `sequence`,
- `currentGrid`,
- opcjonalnie `errorType`,
- opcjonalnie `message`.

To oznacza, że:
- `snapshot` po podłączeniu niesie pełny `currentGrid`,
- zwykły krok solvera też niesie pełny `currentGrid`,
- `completed` również niesie pełny `currentGrid`, a nie osobne `solvedGrid`,
- `failed` i `cancelled` zachowują ten sam kształt payloadu.

## Reguła dla `FE`
`FE` utrzymuje jeden widoczny grid roboczy i dwa pola kontrolne:
- `activeSolveSessionId`,
- `lastAcceptedSequence`.

Algorytm po stronie `FE`:
1. inicjalizuje widok z `recognizedGrid`,
2. po odebraniu eventu sprawdza `solveSessionId`,
3. jeśli `sequence` jest mniejsze albo równe `lastAcceptedSequence`, ignoruje event jako spóźniony albo zduplikowany,
4. jeśli `sequence` jest większe, podstawia cały `currentGrid` jako nowy stan,
5. lokalnie porównuje poprzedni grid z nowym `currentGrid`, żeby wykryć które pola się zmieniły i ewentualnie je animować.

To usuwa potrzebę:
- utrzymywania równolegle `currentGrid` i `change`,
- rozpoznawania osobnych modeli `digitPlaced` i `digitRemoved`,
- używania hasha planszy przy każdym kroku.

## Dlaczego pełny snapshot jest lepszy niż delta
W Sudoku pełny grid to tylko 81 pól, więc koszt transportowy jest mały, a korzyści są duże:
- `FE` ma jeden reducer i jeden model danych,
- reconnect jest prosty, bo wystarczy przyjąć najnowszy `currentGrid`,
- spóźnione eventy można odrzucić samym `sequence`,
- animację można policzyć lokalnie przez porównanie poprzedniej i nowej planszy.

## Diagram przepływu
```mermaid
flowchart TD
    A[FE ma juz pelny recognizedGrid z UC-05A]
    B[FE wysyla POST /api/sudoku/solve z recognizedGrid]
    C[BE zwraca 202 Accepted z solveSessionId i progressChannelUrl]
    D[FE laczy sie z SignalR /ws/sudoku/solving/{solveSessionId}]
    E[BE wysyla snapshot z sequence i pelnym currentGrid]
    F[FE sprawdza solveSessionId i sequence]
    G{Czy event jest nowszy?}
    H[FE nadpisuje stan calym currentGrid]
    I[FE porownuje poprzedni i nowy grid oraz wylicza zmienione pola]
    J{Czy solver wygenerowal kolejny krok?}
    K[BE wysyla kolejny event z sequence i pelnym currentGrid]
    L{Czy sesja osiagnela stan terminalny?}
    M[BE wysyla completed z finalnym currentGrid]
    N[FE zapisuje finalny grid i konczy live solve]
    O[BE wysyla failed z currentGrid errorType i message]
    P[FE pokazuje blad i zatrzymuje live solve]
    R[BE wysyla cancelled z currentGrid]
    S[FE zatrzymuje live solve i zachowuje ostatni przyjety stan]
    T[FE ignoruje event jako spozniony albo zduplikowany]

    A --> B --> C --> D --> E --> F --> G
    G -->|tak| H --> I --> J
    G -->|nie| T --> J
    J -->|tak| K --> F
    J -->|nie| L
    L -->|completed| M --> N
    L -->|failed| O --> P
    L -->|cancelled| R --> S
```

## Założenia architektoniczne
- W `MVP` rekomendowane jest emitowanie eventów z solvera działającego w `Backendzie`.
- `Frontend` nie łączy się z `ML` bezpośrednio.
- `FE` utrzymuje jeden wspólny grid widoku: najpierw wypełniany synchronicznymi odpowiedziami z `UC-05A`, a później nadpisywany kolejnymi pełnymi snapshotami z `UC-05E`.

## Niezmiennik pól wejściowych
Cyfry obecne w `recognizedGrid` przed startem solvera są traktowane jako pola wejściowe i zablokowane.

To oznacza, że:
- kolejne `currentGrid` mogą zmieniać tylko pola, które były puste w wejściowym `recognizedGrid`,
- cyfry wejściowe z `recognizedGrid` pozostają niezmienne przez całą sesję solve,
- `SignalR` nigdy nie może przekazać `currentGrid`, w którym znika albo zmienia się cyfra pochodząca z wejściowego `recognizedGrid`.

## Start sesji live solve
### `POST /api/sudoku/solve`
- Request body: `SolveSudokuApiEntry`.
- `202 Accepted` -> `SolveSessionApiResponse`.

Przykład odpowiedzi:

```json
{
  "solveSessionId": "solve-20260511-202500-demo-01",
  "status": "queued",
  "progressChannelUrl": "/ws/sudoku/solving/solve-20260511-202500-demo-01"
}
```

Semantyka:
- `solveSessionId` jest publicznym identyfikatorem sesji pokazywania kroków solvera,
- `status` na starcie przyjmuje `queued` albo `running`,
- `progressChannelUrl` wskazuje kanał `SignalR` do monitoringu.

To samo żądanie startuje właściwe rozwiązywanie z `UC-05B`; `UC-05E` nie dodaje drugiego osobnego endpointu startowego, tylko opisuje transport zdarzeń dla tej samej sesji.

### `GET /api/sudoku/solve/active`
- Pozwala `FE` odzyskać aktualnie aktywną sesję i wrócić do monitoringu po odświeżeniu.
- `200 OK` zwraca `SolveSessionApiResponse`, a `204 No Content` oznacza brak aktywnej sesji.

### `POST /api/sudoku/solve/{solveSessionId}/cancel`
- Uruchamia kooperacyjne anulowanie aktywnej sesji.
- `202 Accepted` oznacza przyjęcie żądania anulowania albo no-op dla sesji już zakończonej / niedopasowanej.

## Kanał `SignalR`
### `SignalR /ws/sudoku/solving/{solveSessionId}`
- `FE` łączy się z kanałem zaraz po otrzymaniu `solveSessionId`.
- Po zestawieniu połączenia `BE` wysyła pierwszy snapshot bieżącego stanu.
- Następnie emituje kolejne snapshoty postępu solvera.
- Każdy event na kanale ma ten sam kształt payloadu i jest porządkowany przez `sequence`.

## Wspólny kontrakt eventu
Każdy event `SignalR` korzysta z tego samego modelu `SolveProgressEventApiResponse`.

### Pola wspólne
- `eventType` -> `snapshot | progress | completed | failed | cancelled`,
- `solveSessionId` -> identyfikator sesji,
- `status` -> `queued | running | completed | failed | cancelled`,
- `sequence` -> rosnący numer sekwencyjny w obrębie jednej sesji,
- `currentGrid` -> pełny bieżący grid 9×9,
- `errorType` -> opcjonalne pole dla błędu końcowego,
- `message` -> opcjonalne pole dla błędu końcowego.

### `snapshot`
Jednorazowy zrzut bieżącego stanu po podłączeniu klienta albo po odzyskaniu monitoringu.

`snapshot.currentGrid` jest zawsze pełną siatką 9×9. Przy pierwszym podłączeniu może być równy wejściowemu `recognizedGrid`, a przy reconnect może zawierać już część cyfr dopisanych wcześniej przez solver.

Przykład:

```json
{
  "eventType": "snapshot",
  "solveSessionId": "solve-20260511-202500-demo-01",
  "status": "running",
  "sequence": 0,
  "currentGrid": [
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

### `progress`
Event emitowany za każdym razem, gdy solver zmieni planszę, niezależnie od tego, czy był to krok "do przodu", czy cofnięcie podczas backtrackingu.

`FE` nie czyta z payloadu osobnego typu zmiany. Zamiast tego porównuje poprzedni `currentGrid` z nowym `currentGrid` i na tej podstawie wykrywa:
- wpisanie cyfry, jeśli pole zmieniło się z `null` na `1..9`,
- cofnięcie, jeśli pole zmieniło się z `1..9` na `null`.

```json
{
  "eventType": "progress",
  "solveSessionId": "solve-20260511-202500-demo-01",
  "status": "running",
  "sequence": 14,
  "currentGrid": [
    [5, 3, 4, null, 7, null, null, null, null],
    [6, null, null, 1, 9, 5, null, null, null],
    [null, 9, 8, null, null, null, null, 6, null],
    [8, null, null, null, 6, null, null, 2, 3],
    [4, null, null, 8, null, 3, null, null, 1],
    [7, null, null, null, 2, null, null, null, 6],
    [null, 6, null, null, null, null, 2, 8, null],
    [null, null, null, 4, 1, 9, null, null, 5],
    [null, null, null, null, 8, null, null, 7, 9]
  ]
}
```

### `completed`
Event końcowy dla rozwiązanej planszy.

Tak jak inne eventy, `completed` używa pola `currentGrid`, a nie osobnego `solvedGrid`.

```json
{
  "eventType": "completed",
  "solveSessionId": "solve-20260511-202500-demo-01",
  "status": "completed",
  "sequence": 87,
  "currentGrid": [
    [5, 3, 4, 6, 7, 8, 9, 1, 2],
    [6, 7, 2, 1, 9, 5, 3, 4, 8],
    [1, 9, 8, 3, 4, 2, 5, 6, 7],
    [8, 5, 9, 7, 6, 1, 4, 2, 3],
    [4, 2, 6, 8, 5, 3, 7, 9, 1],
    [7, 1, 3, 9, 2, 4, 8, 5, 6],
    [9, 6, 1, 5, 3, 7, 2, 8, 4],
    [2, 8, 7, 4, 1, 9, 6, 3, 5],
    [3, 4, 5, 2, 8, 6, 1, 7, 9]
  ]
}
```

### `failed`
Event końcowy dla planszy nierozwiązywalnej albo błędnej.

```json
{
  "eventType": "failed",
  "solveSessionId": "solve-20260511-202500-demo-01",
  "status": "failed",
  "sequence": 42,
  "currentGrid": [
    [5, 3, 4, null, 7, null, null, null, null],
    [6, null, null, 1, 9, 5, null, null, null],
    [null, 9, 8, null, null, null, null, 6, null],
    [8, null, null, null, 6, null, null, 2, 3],
    [4, null, null, 8, null, 3, null, null, 1],
    [7, null, null, null, 2, null, null, null, 6],
    [null, 6, null, null, null, null, 2, 8, null],
    [null, null, null, 4, 1, 9, null, null, 5],
    [null, null, null, null, 8, null, null, 7, 9]
  ],
  "errorType": "unsolvable",
  "message": "Sudoku nie ma poprawnego rozwiązania."
}
```

### `cancelled`
Event końcowy dla sesji zatrzymanej na żądanie użytkownika.

```json
{
  "eventType": "cancelled",
  "solveSessionId": "solve-20260511-202500-demo-01",
  "status": "cancelled",
  "sequence": 21,
  "currentGrid": [
    [5, 3, 4, null, 7, null, null, null, null],
    [6, null, null, 1, 9, 5, null, null, null],
    [null, 9, 8, null, null, null, null, 6, null],
    [8, null, null, null, 6, null, null, 2, 3],
    [4, null, null, 8, null, 3, null, null, 1],
    [7, null, null, null, 2, null, null, null, 6],
    [null, 6, null, null, null, null, 2, 8, null],
    [null, null, null, 4, 1, 9, null, null, 5],
    [null, null, null, null, 8, null, null, 7, 9]
  ]
}
```

## Zasady emitowania
- Każda zmiana planszy wykonana przez solver generuje dokładnie jeden event `progress`.
- Eventy są emitowane w tej samej kolejności, w jakiej solver modyfikuje planszę.
- `sequence` jest rosnącym numerem sekwencyjnym w obrębie jednej sesji.
- Każdy event niesie pełny `currentGrid`, a nie samą deltę zmiany.
- `FE` porównuje poprzedni i nowy `currentGrid`, żeby wykryć ile pól się zmieniło i jakiego typu była zmiana.
- `currentGrid` nigdy nie może naruszać pól wejściowych pochodzących z `recognizedGrid`.
- Sesja kończy się dokładnie jednym eventem terminalnym: `completed`, `failed` albo `cancelled`.

## Jedna aktywna sesja
W `MVP` system dopuszcza tylko jedną aktywną sesję backtrackingu na użytkownika albo w kontekście jednego widoku solve.

Dlatego:
- jeśli sesja już trwa, `FE` nie uruchamia nowej, tylko odzyskuje istniejącą przez `GET /api/sudoku/solve/active`,
- użytkownik może ją najpierw anulować przez `POST /api/sudoku/solve/{solveSessionId}/cancel`,
- dopiero po `completed`, `failed` albo `cancelled` można wystartować kolejną sesję.

## Wpływ na UX
- `UI` może animować wpisanie cyfry i jej usunięcie, wyliczając zmianę przez porównanie dwóch kolejnych snapshotów.
- Użytkownik widzi, że solver czasem się cofa, co odpowiada realnemu działaniu backtrackingu.
- Dla bardzo szybkich rozwiązań `FE` może opcjonalnie spowolnić samą animację, ale nie zmienia to kolejności ani semantyki eventów.

## Relacja do `UC-05B`
- `UC-05B` definiuje logikę rozwiązania i publiczny kontrakt startu asynchronicznego solve.
- `UC-05E` definiuje asynchroniczny kanał obserwacji tych samych kroków solvera.
- Ten sam algorytm powinien dawać taki sam wynik końcowy niezależnie od tego, czy uruchamiamy tryb zwykły, czy live.
- `UC-05E` aktualizuje w `UI` ten sam grid, który został wcześniej zbudowany po `UC-05A`, ale robi to przez kolejne pełne snapshoty z `sequence`.
- `UC-05E` obsługuje też odzyskanie aktywnej sesji i zdarzenie końcowe `cancelled`.

## Kryteria akceptacji
- Użytkownik dostaje przez `SignalR` każdą zmianę planszy wykonywaną przez solver.
- System emituje jeden wspólny model eventu dla `snapshot`, `progress`, `completed`, `failed` i `cancelled`.
- `FE` może rozpoznać zarówno dodania cyfr, jak i ich usunięcia przez porównanie dwóch kolejnych `currentGrid`.
- Zmiany dotyczą wyłącznie cyfr dodanych przez solver, nigdy cyfr wejściowych.
- Po podłączeniu do kanału klient dostaje `snapshot` bieżącego stanu sesji z `sequence`.
- Spóźniony albo zduplikowany event może zostać odrzucony wyłącznie na podstawie `solveSessionId` i `sequence`.
- Kanał kończy się eventem `completed`, `failed` albo `cancelled`.
- Jeśli aktywna sesja już istnieje, system nie tworzy nowej przed jej zakończeniem albo anulowaniem.
- `Frontend` nie łączy się z `ML` bezpośrednio; publiczny kanał live solve jest publikowany przez `Backend`.
