# UC-05A — Inferencja pojedynczej komórki

## Cel
Rozpoznać zawartość pojedynczej komórki sudoku przy użyciu aktywnego modelu inferencyjnego oraz reguły pustej komórki.

## Kontekst produktowy
To najniższy poziom inferencji w `UC-05`. Od jakości tej historyjki zależy zarówno poprawność `recognizedGrid`, jak i późniejsze działanie solvera.

Po scaleniu dawnego `UC-05C` ta historyjka opisuje już nie tylko inferencję pojedynczej komórki, ale też zbudowanie po stronie `FE` kompletnego `recognizedGrid` oraz jego podstawową prezentację przed uruchomieniem solvera.

## Zależność od `UC-04`
`UC-05A` nie startuje od pełnego zdjęcia sudoku, tylko od wyniku `UC-04`.

W praktyce przepływ wygląda tak:
1. `UC-04` zwraca siatkę 9×9 obrazów komórek,
2. `FE` tworzy na jej podstawie osobny lokalny `recognizedGrid` 9×9 dla wartości liczbowych, początkowo wypełniony `null`,
3. `FE` zna pozycję każdej komórki w siatce obrazów,
4. `FE` wysyła komórki pojedynczo do `UC-05A`,
5. po każdej odpowiedzi `FE` uzupełnia odpowiednie pole w lokalnym `recognizedGrid`.

To oznacza, że `UC-05A` jest niskopoziomowym krokiem inferencji "jedna komórka -> jedna odpowiedź", wykorzystywanym do przekształcenia siatki obrazów z `UC-04` w osobny grid wartości liczbowych.

W `UC-05A` odpowiedź wraca synchronicznie w odpowiedzi HTTP na pojedyncze wywołanie dla komórki. `FE` wykonuje kolejne wywołania w pętli dla komórek zwróconych przez `UC-04`, a po każdej odpowiedzi aktualizuje ten sam lokalny `recognizedGrid`.

## Zakres po scaleniu dawnego `UC-05C`
W praktyce `UC-05A` obejmuje teraz trzy kroki:
1. inferencję pojedynczej komórki,
2. złożenie pełnego `recognizedGrid` po stronie `FE`,
3. podstawowe pokazanie tego `recognizedGrid` w siatce 9×9 jeszcze przed startem solvera.

To oznacza, że osobna historyjka tylko do prezentacji rozpoznanego gridu nie jest już potrzebna. `UC-05E` opisuje później aktualizację tego samego widoku podczas działania solvera.

## Kluczowa decyzja
Model inferencji musi rozpoznawać również brak cyfry i zwracać `null`, a nie wymuszać klasyfikację `1..9`.

## Heurystyka pustej komórki
Założenie wynika z charakteru danych referencyjnych, zwłaszcza datasetu Kaggle `mexwell/sudoku-image-dataset`, gdzie komórki są zwykle wycięte i dość dobrze wyrównane względem ramki.

W `MVP` rekomendowany jest dwuetapowy mechanizm:
1. najpierw binaryzacja komórki i odwrócenie kolorów tak, aby cyfra oraz ewentualne pozostałości siatki stanowiły foreground,
2. dopiero potem decyzja, czy komórka jest pusta, a klasyfikacja modelem uruchamia się wyłącznie dla komórek uznanych za zajęte.

### Reguła detekcji pustej komórki
- detektor dostaje już zbinaryzowany obraz z odwróconymi kolorami,
- całą komórkę dzielimy na 4 równe ćwiartki,
- następnie dla każdej z tych ćwiartek bierzemy jej wewnętrzną ćwiartkę skierowaną do środka komórki,
- z 4 tak wybranych fragmentów powstaje mały obszar centralny, odporniejszy na wpływ ramek i linii siatki przy krawędziach,
- w tym obszarze liczymy udział foregroundu, a nie pojedynczy piksel,
- jeśli udział foregroundu nie przekracza progu, system zwraca `digit = null`,
- jeśli próg zostanie przekroczony, uruchamiana jest klasyfikacja `1..9`.

To podejście ma dwa cele:
- nie mylić linii siatki i artefaktów przy krawędzi z cyfrą,
- skupić decyzję `empty` vs `digit` na realnym centrum komórki, gdzie zwykle znajduje się znak.

Progi nie powinny być hardcodowane w kodzie; powinny wynikać z konfiguracji profilu preprocessingu / inferencji.

## Role warstw
### `FE`
- Odbiera z `UC-04` siatkę 9×9 obrazów komórek.
- Tworzy lokalny `recognizedGrid` o strukturze 9×9, początkowo wypełniony wartościami `null`.
- Przekazuje obraz pojedynczej komórki jako `ImageApiEntry`.
- Dla planszy 9×9 wykonuje po kolei 81 wywołań pojedynczych, jeśli nie korzysta jeszcze z batcha.
- Po każdej synchronicznej odpowiedzi HTTP wpisuje otrzymane `digit` do właściwego pola `recognizedGrid`, korzystając z indeksu wiersza i kolumny znanego z `UC-04`.
- Może pokazywać użytkownikowi postęp rozpoznania na podstawie liczby już uzupełnionych komórek.
- Po zakończeniu rozpoznania pokazuje użytkownikowi pełny `recognizedGrid` jako siatkę 9×9.
- Rozróżnia w `UI` komórki puste (`null`) od komórek z rozpoznaną cyfrą.
- Przygotowuje ten sam widok gridu do późniejszej aktualizacji przez `UC-05E`.

### `BE`
- Udostępnia publiczny endpoint inferencji pojedynczej komórki.
- Waliduje payload i mapuje błędy transportowe / domenowe.
- Wywołuje usługę `ML` przez wewnętrzny kontrakt.

### `ML`
- Wykonuje binaryzację, odwrócenie kolorów i heurystykę pustej komórki opartą o centralny foreground.
- Jeśli komórka nie jest pusta, wykonuje klasyfikację aktywnym modelem.
- Zwraca `digit = null`, gdy komórka jest pusta albo nie zawiera wiarygodnego znaku.

## Kontrakt `FE -> BE`
### `PUT /api/sudoku/cells/inference`
- Request body: `ImageApiEntry`.
- `200 OK` -> `DigitInferenceApiResponse`.

```json
{
  "digit": 7
}
```

```json
{
  "digit": null
}
```

Reguły odpowiedzi błędnych:
- `400 Bad Request` -> niepoprawny `mimeType`, pusty `base64` albo niepoprawny format obrazu,
- `409 Conflict` -> brak aktywnego modelu inferencyjnego,
- `422 Unprocessable Entity` -> obraz komórki nie nadaje się do przetworzenia,
- `503 Service Unavailable` -> usługa `ML` jest niedostępna.

## Kontrakt `BE -> ML`
### `PUT /ml/cells/inference`
- Request body: obraz komórki i resolved konfiguracja inferencji.
- Response body: `DigitInferenceApiResponse`.

Minimalna semantyka odpowiedzi:
- `digit = null` oznacza pustą komórkę albo brak rozpoznanej cyfry,
- `digit = 1..9` oznacza rozpoznaną cyfrę.

## Relacja do `EXP-04`
Eksperyment opisany w `@.ai/exp/exp-04_plan_implementation_test_inference.md` należy traktować jako źródło wniosków technicznych, a nie jako gotowy kontrakt produktu.

### Co przejmujemy z eksperymentu
Z `EXP-04` warto zachować następujące obserwacje i decyzje:
- inferencja pojedynczej cyfry jest wartościowym krokiem diagnostycznym i potwierdza potrzebę osobnego use case'u dla pojedynczej komórki,
- runtime inferencji musi umieć odczytać aktywny model na podstawie wskaźnika `models/active/inference.json`,
- `ML` potrzebuje pełnego technicznego manifestu `model.json`, a nie tylko skróconych metadanych listujących,
- definicje architektur modelu muszą być spójne między bootstrapem, treningiem i runtime inferencji,
- preprocessing pojedynczej komórki używany w testach lokalnych powinien być zgodny z preprocessingiem runtime dla `UC-05A`.

### Czego nie przejmujemy wprost
Poniższe elementy eksperymentu nie są zgodne z docelową architekturą produktu i nie powinny zostać przeniesione 1:1 do `UC-05A`:
- eksperymentalny endpoint `GET /ml/test/inteference/{name}` nie jest publicznym API produktu,
- `FE` nie może wywoływać `ML` bezpośrednio, nawet jeśli eksperyment był tak uruchamiany developersko,
- odczyt obrazka testowego po nazwie z katalogu examples jest narzędziem lokalnej diagnostyki, a nie docelowym kontraktem inferencji komórki,
- literówka `inteference` nie może przejść do docelowych kontraktów,
- zwrot samego `argmax` jako cyfry nie wystarcza produktowo, jeśli docelowy przepływ ma rozróżniać również pustą komórkę jako `null`.

### Jak eksperyment należy przetłumaczyć na docelowy `UC-05A`
Jeśli jakikolwiek fragment eksperymentu ma zostać zachowany, musi zostać dopasowany do docelowego flow repo:
1. `FE` wysyła `ImageApiEntry` do `BE`,
2. `BE` waliduje payload i wywołuje wewnętrzny endpoint `ML`,
3. `ML` wykonuje preprocessing komórki, detekcję pustego pola na podstawie centralnego foregroundu i dopiero potem inferencję aktywnym modelem,
4. odpowiedź wraca przez `BE` jako `DigitInferenceApiResponse`,
5. semantyka odpowiedzi musi wspierać `digit = null` dla pustej komórki.

### Wnioski architektoniczne z eksperymentu
`EXP-04` ujawnił kilka rzeczy, które trzeba uwzględnić w docelowym `UC-05A`:
- `BE` przy finalizacji modelu wynikowego musi zapisywać pełny techniczny manifest potrzebny runtime inferencji,
- jedna nazwa architektury, np. `custom-cnn-v1`, musi wskazywać dokładnie jedną wersjonowaną implementację kodową,
- wspólne specyfikacje architektur powinny być współdzielone między bootstrapem, treningiem i inferencją,
- konfiguracja katalogów runtime `BE` i `ML` musi być spójna, żeby uniknąć ukrytych błędów środowiskowych podczas testów i działania produktu.

### Status eksperymentalnego endpointu
Endpoint z `EXP-04` może pozostać co najwyżej jako narzędzie developerskie do lokalnej diagnostyki modelu, ale:
- musi być wyraźnie oznaczony jako eksperymentalny,
- nie może być opisywany jako część publicznego `UC-05A`,
- nie może wymuszać rozwiązań sprzecznych z architekturą `Frontend -> Backend -> ML`.

## Uwagi
- Eksperyment `EXP-04` jest punktem odniesienia technicznego, ale nie jest docelowym API produktu.
- Wariant 81 requestów `FE -> BE` jest prosty po `UC-04`, bo `FE` dostaje gotową siatkę komórek, zna indeksy każdej z nich i może pokazywać progres.
- Jeśli wybierzemy 81 requestów, `FE` powinien ograniczać równoległość.

## Model widoku po stronie `FE`
Po zbudowaniu `recognizedGrid` `FE` nie potrzebuje osobnego endpointu tylko po to, żeby narysować planszę.

Minimalna semantyka pojedynczej komórki w `UI`:
- `digit` -> wartość wyświetlana,
- `source = recognized`,
- `isEditable` -> czy użytkownik może ręcznie poprawić wartość,
- `isEmpty` -> czy rozpoznanie zwróciło `null`.

Ten model widoku jest później rozszerzany w `UC-05E`, gdzie ten sam grid dostaje kolejne snapshoty od solvera.

## Wynik dla dalszych kroków
Produktem końcowym `UC-05A` z perspektywy `FE` nie jest tylko pojedyncza odpowiedź `DigitInferenceApiResponse`, ale także stopniowo budowany lokalnie `recognizedGrid`, który później zasila:
- `UC-05B`, jeśli przekazujemy grid do solvera,
- `UI`, jeśli chcemy najpierw pokazać rozpoznany stan planszy,
- `UC-05E`, jeśli ten sam widok ma być później aktualizowany przez live solve.

## Kryteria akceptacji
- System zwraca `digit = null` dla pustej komórki zamiast wymuszać klasyfikację `1..9`.
- Detekcja pustej komórki działa po binaryzacji z odwróconymi kolorami i analizuje centralny obszar zbudowany z 4 wewnętrznych ćwiartek skierowanych do środka komórki.
- Decyzja o pustym polu opiera się na progu udziału foregroundu w obszarze centralnym, a nie na obecności pojedynczego piksela.
- Publiczny kontrakt inferencji przechodzi przez `Backend`, a nie bezpośrednio przez `ML`.
- `UC-05A` jest opisane jako krok wykorzystujący siatkę obrazów z `UC-04` do zbudowania osobnego `recognizedGrid` zawierającego wartości `1..9` albo `null`.
- `FE` ma jasno opisaną odpowiedzialność za utworzenie i uzupełnianie lokalnego `recognizedGrid`.
- `UC-05A` obejmuje też podstawową prezentację `recognizedGrid` w siatce 9×9 po stronie `FE`.
- Dokument wprost rozróżnia, które elementy z `EXP-04` są tylko eksperymentem developerskim, a które przechodzą do docelowej architektury produktu po przeróbce.
- Dokument opisuje `UC-05A` jako synchroniczny przepływ `HTTP request -> HTTP response` dla pojedynczej komórki.
