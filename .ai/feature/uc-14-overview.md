# UC-14 — Parametryzacja funkcjonalności z poziomu UI

## Cel
- Pozwolić użytkownikowi sterować wybranymi parametrami funkcjonalnymi bez edycji `appsettings`, `.env` ani workflow wdrożeniowego.
- Utrzymać `Backend` jako `source of truth` dla walidacji, domknięcia wartości domyślnych i zapisu `effectiveParameters`.
- Przenieść parametry, które dziś są trzymane w konfiguracji runtime, do modelu sterowanego przez `UI`, ale bez dokładania osobnego endpointu parametrów.

## Historyjka
Jako użytkownik chcę mieć w obszarze roboczym aplikacji kontekstowy panel parametrów zależny od aktualnej funkcjonalności, aby przed uruchomieniem rozpoznawania albo treningu zmienić wybrane ustawienia działania systemu i od razu wysłać je razem z żądaniem do istniejącego endpointu.

## Zakres decyzji
- `UC-14` nie dodaje osobnego endpointu do pobierania parametrów.
- `UC-14` nie dodaje osobnego endpointu do zapamiętywanych parametrów użytkownika.
- Parametry są przekazywane wyłącznie razem z istniejącymi requestami biznesowymi.
- Parametry infrastrukturalne i środowiskowe nie przechodzą do `UI`.

## Główna zasada migracji
### Etap przejściowy
- W pierwszym kroku implementacyjnym wartości domyślne w `UI` mają zostać przepisane 1:1 z tego, co system już dziś ma ustawione w `appsettings`.
- Celem tego etapu jest zachowanie identycznego zachowania systemu po wdrożeniu formularza parametrów.
- `Backend` może jeszcze chwilowo czytać te same wartości domyślne z `appsettings`, jeśli jest to potrzebne do bezpiecznego wdrożenia bez regresji.

### Stan docelowy
- Po ustabilizowaniu `UC-14` parametry funkcjonalne wystawione do `UI` należy usunąć z `appsettings`.
- Jeśli te same parametry pojawiły się jako zmienne albo wartości generowane przez workflow GitHub, należy je również usunąć z workflow.
- Po migracji `appsettings`, `.env` i workflow wdrożeniowy przechowują tylko:
  - konfigurację środowiskową,
  - ścieżki runtime,
  - URL-e integracyjne,
  - sekrety,
  - ustawienia bezpieczeństwa,
  - limity infrastrukturalne.
- Po migracji jedynym publicznym źródłem parametrów funkcjonalnych staje się żądanie z `UI`, a jedynym systemowym źródłem prawdy dla ich walidacji i `effectiveParameters` pozostaje `BE`.

## Wygląd i działanie UI
### Położenie panelu
- Panel parametrów jest renderowany jako osobna prawa kolumna obszaru roboczego na desktopie.
- Lewa kolumna pozostaje nawigacją modułów, środkowa kolumna zawiera główną treść ekranu, a prawa kolumna pokazuje parametry aktywnego kontekstu.
- Na węższych szerokościach prawa kolumna przechodzi pod główną treść.
- Panel jest częścią bieżącego ekranu, a nie osobnym widokiem administracyjnym.

### Zachowanie
- Zmiana aktywnej zakładki zmienia zawartość panelu.
- Panel jest widoczny tylko wtedy, gdy aktywny ekran rzeczywiście korzysta z parametrów `UC-14`.
- W obecnym zakresie dotyczy to:
  - heurystyki pustej komórki w `UC-05A`,
  - live solve w `UC-05E`,
  - startu treningu w `UC-06`.
- Ekrany bez parametrów funkcjonalnych nie pokazują panelu `UC-14`.
- Panel pokazuje:
  - nazwę aktywnego kontekstu,
  - liczbę aktywnych override'ów,
  - status lokalnej walidacji,
  - akcję przywrócenia wartości domyślnych dla bieżącego kontekstu,
  - selektor parametrów pozwalający wybrać dokładnie jeden parametr do edycji naraz,
  - dla wybranego parametru:
    - etykietę,
    - aktualną wartość,
    - wartość domyślną,
    - zakres albo stan logiczny,
    - krótki opis,
    - praktyczną instrukcję typu mini wiki: do czego służy, jaki ma wpływ, kiedy warto go zmieniać i jaka jest rekomendacja użycia.
- Parametry bardziej techniczne mogą być oznaczone jako `advanced`, ale nadal pozostają częścią tego samego panelu i korzystają z tego samego modelu wyboru pojedynczego parametru.
- Użytkownik zmienia parametry lokalnie w formularzu, a ich wysyłka następuje dopiero razem z akcją biznesową.
- Jeśli użytkownik nie zmieni parametru albo nie wyśle go w żądaniu, `BE` przyjmuje wartość domyślną zgodną z bieżącym zachowaniem systemu.
- Układ strony nie wprowadza osobnego scrolla dla panelu parametrów ani dla lewego panelu modułów; przewijanie odbywa się wspólnym scrollem strony.

### Zakładka `solve`
Panel może zawierać co najmniej:
- `emptyCellForegroundThresholdPercent`
- `emptyCellInnerWindowPercent`
- `solverStepDelayMs`

W praktyce parametry są pokazywane zależnie od aktywnego podkontekstu:
- `solveCellInference` pokazuje:
  - `emptyCellForegroundThresholdPercent`
  - `emptyCellInnerWindowPercent`
- `solveLive` pokazuje:
  - `solverStepDelayMs`

Mapowanie na istniejące endpointy `UC-05`:
- `emptyCellForegroundThresholdPercent` i `emptyCellInnerWindowPercent` trafiają do `PUT /api/sudoku/cells/inference` dla heurystyki pustej komórki w `UC-05A`.
- `solverStepDelayMs` trafia do `POST /api/sudoku/solve` dla live solve w `UC-05E`.

### Zakładka `train`
Panel może zawierać co najmniej:
- `epochCount`
- `useBestCheckpoint`
- `batchSize`
- `learningRate`
- `earlyStoppingPatience`
- `freezeBaseLayers`
- `randomSeed`

## Mapowanie parametrów na endpointy
### Publiczne `FE -> BE`
#### `PUT /api/sudoku/cells/inference`
Parametry przekazywane przy inferencji pojedynczej komórki:
- `emptyCellForegroundThresholdPercent`
- `emptyCellInnerWindowPercent`

Ten endpoint odpowiada za heurystykę pustego pola dla `UC-05A`.

#### `POST /api/sudoku/solve`
Parametry przekazywane przy uruchomieniu sesji live solve z `UC-05E`:
- `solverStepDelayMs`

Ten parametr steruje opóźnieniem między kolejnymi krokami backtrackingu. Jeśli solver live działa po stronie `BE`, `solverStepDelayMs` jest zużywany w `BE` i nie musi być dalej przekazywany do `ML`.

#### `POST /api/trainings`
Parametry przekazywane przy uruchomieniu treningu:
- `epochCount`
- `useBestCheckpoint`
- `batchSize`
- `learningRate`
- `earlyStoppingPatience`
- `freezeBaseLayers`
- `randomSeed`

### Wewnętrzne `BE -> ML`
#### `PUT /ml/cells/inference`
`BE` przekazuje dalej resolved parametry:
- `emptyCellForegroundThresholdPercent`
- `emptyCellInnerWindowPercent`

To są resolved parametry heurystyki pustej komórki używane przez istniejący flow inferencji pojedynczej komórki w `UC-05A`.

#### `POST /ml/trainings`
`BE` przekazuje dalej resolved parametry treningu:
- `epochCount`
- `useBestCheckpoint`
- `batchSize`
- `learningRate`
- `earlyStoppingPatience`
- `freezeBaseLayers`
- `randomSeed`

## Zasady dla `BE`
- `BE` nie dodaje osobnego katalogu parametrów dostępnego przez nowy endpoint.
- `BE` przyjmuje parametry tylko wtedy, gdy przychodzą razem z istniejącym żądaniem biznesowym.
- `BE` waliduje:
  - czy parametr jest dozwolony dla danego endpointu,
  - czy wartość mieści się w dopuszczalnym zakresie,
  - czy typ wartości jest poprawny.
- `BE` domyka brakujące wartości domyślne.
- `BE` zapisuje końcowe `effectiveParameters` w rekordzie sesji solve albo runu treningowego.
- `BE` nie przyjmuje z `UI` ścieżek plikowych, sekretów, URL-i integracyjnych ani parametrów infrastrukturalnych.

## Zasady dla `ML`
- `ML` nie zgaduje parametrów na podstawie stanu środowiska ani `UI`.
- `ML` korzysta tylko z resolved parametrów przekazanych przez `BE`.
- `ML` nie staje się właścicielem wartości domyślnych ani ich źródłem prawdy.

## Relacja do `appsettings` i workflow
- Parametry funkcjonalne, które przechodzą do `UI`, należy traktować jako kandydatów do usunięcia z `appsettings`.
- Jeśli którykolwiek z tych parametrów jest dziś tworzony albo nadpisywany przez workflow GitHub, trzeba go usunąć również z workflow.
- Nie wolno zostawić tych samych parametrów jednocześnie:
  - w `UI`,
  - w `appsettings`,
  - w workflow GitHub
  jako równoległych źródeł prawdy.

## Kryteria akceptacji
- Panel parametrów jest renderowany jako osobna prawa kolumna obszaru roboczego na desktopie i przechodzi pod treść na węższych szerokościach.
- Zmiana zakładki albo aktywnego kontekstu zmienia zawartość panelu parametrów.
- Panel jest widoczny tylko dla funkcjonalności, które rzeczywiście korzystają z parametrów `UC-14`.
- `UC-14` nie wprowadza osobnego endpointu do pobierania parametrów ani osobnego endpointu do zapamiętywania parametrów.
- Wartości domyślne w `UI` są początkowo zgodne z tym, co było wcześniej ustawione w `appsettings`.
- Parametry wysyłane są razem z istniejącymi requestami biznesowymi, a nie przez nowy endpoint pomocniczy.
- Użytkownik wybiera konkretny parametr do edycji, a panel pokazuje tylko jeden edytor parametru naraz.
- Każdy parametr pokazuje krótką instrukcję użytkową opisującą jego przeznaczenie, wpływ oraz sytuacje, w których warto go zmieniać.
- UI nie wprowadza osobnego scrolla dla panelu parametrów ani dla panelu modułów.
- Dokument wskazuje, które parametry trafiają do których endpointów publicznych i wewnętrznych.
- Po zakończeniu migracji parametry wystawione do `UI` są usunięte z `appsettings`.
- Po zakończeniu migracji te same parametry są usunięte również z workflow GitHub, jeśli wcześniej tam występowały.
- `BE` zapisuje `effectiveParameters`, aby później można było odtworzyć realną konfigurację wykonania.
