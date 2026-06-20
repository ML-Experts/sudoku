# UC-22 — Usprawnienie detekcji pustej komórki i cleaning runtime

## Cel
- Poprawić skuteczność rozpoznawania pustej komórki w `UC-05`.
- Rozdzielić etap `empty detection` od etapu `cell cleaning` pod inferencję cyfry.
- Wdrożyć flow diagnostyczne wyprowadzone z notebooka `final_api_uc04_uc06_preview.ipynb` bez zmiany kontraktu odpowiedzi solve.

## Historyjka
Jako użytkownik chcę, aby system lepiej odróżniał puste komórki od komórek zawierających cyfrę, tak aby `recognizedGrid` był poprawniejszy i rzadziej zawierał błędnie wymuszone cyfry w polach pustych.

## Problem, który rozwiązujemy
Dotychczasowa heurystyka pustej komórki w `UC-05` jest zbyt podatna na:
- szum,
- resztki linii siatki,
- artefakty przy krawędziach komórki,
- zbyt wczesne mieszanie decyzji `empty` vs `digit` z cleaningiem próbki pod model.

Skutkiem jest ryzyko, że:
- puste pole zostanie błędnie potraktowane jako cyfra,
- ślad cyfry zostanie zgubiony przez niewłaściwą kolejność operacji,
- runtime i pipeline treningowy będą używać różnych intuicji co do tego, czym jest dobra próbka.

## Główna decyzja architektoniczna
`UC-22` rozdziela dwa różne etapy:

1. `Empty cell detection`
   - odpowiada tylko za decyzję, czy komórka jest pusta,
   - pracuje na `raw cell`,
   - nie produkuje jeszcze finalnej próbki pod model.

2. `Cell cleaning for inference`
   - uruchamia się dopiero dla komórki uznanej za niepustą,
   - przygotowuje kanoniczną próbkę dla klasyfikatora cyfry,
   - nie odpowiada za rozstrzygnięcie `empty` vs `digit`.

Docelowa kolejność w runtime:

```text
raw cell -> empty detection -> cleaning -> digit inference
```

## Flow algorytmu empty detection
Flow wdrażany w `UC-22` jest zgodny z kierunkiem z notebooka i ma następującą kolejność:

1. System pracuje na surowej komórce `BGR` wyciętej z siatki `9x9`.
2. Dla diagnostyki komórki zachowujemy numerację `1..81` od lewej do prawej i od góry do dołu.
3. System wykonuje grayscale, odszumianie i binaryzację.
4. System wykonuje lekki cleanup maski binarnej.
5. Z obrazu budowany jest `center composite`:
   - komórka jest dzielona na 4 równe ćwiartki,
   - z każdej ćwiartki wybierana jest jej wewnętrzna ćwiartka skierowana do środka komórki,
   - z tych 4 fragmentów powstaje jeden obraz do dalszej analizy.
6. Na `center composite` uruchamiana jest detekcja segmentów Hough.
7. Segmenty krótsze od zadanego progu są odrzucane.
8. System liczy:
   - liczbę odfiltrowanych segmentów,
   - liczbę foreground pixels,
   - foreground pixel ratio.
9. Komórka jest uznawana za niepustą, jeśli spełnia warunek akceptacji oparty o foreground pixels / ratio albo o liczbę odfiltrowanych segmentów.
10. Tylko dla komórki niepustej uruchamiany jest cleaning pod model i inferencja cyfry.

## Co przejmujemy z notebooka
Z podejścia eksperymentalnego przejmujemy następujące klocki logiczne:
- binaryzację i podstawowe odszumianie,
- cleanup maski binarnej,
- budowę `center composite`,
- detekcję segmentów Hough,
- odfiltrowanie segmentów krótszych niż zadany próg,
- liczenie `foreground pixel count`,
- liczenie `foreground pixel ratio`,
- decyzję biznesową `isEmpty` wyliczaną przed cleaningiem pod model.

## Czego nie przenosimy 1:1 z notebooka
Do docelowego kontraktu produktu nie przenosimy jako publicznego API:
- notebookowych helperów diagnostycznych,
- overlayów segmentów jako części odpowiedzi produkcyjnej,
- numeracji planszy jako elementu kontraktu runtime,
- artefaktów typu `center composite` jako danych dla klasyfikatora albo jako payloadu zwrotnego.

Te elementy mogą pozostać:
- diagnostyczne,
- developerskie,
- pomocnicze dla preview i debugowania.

## Relacja do `UC-05A`
`UC-22` nie zastępuje `UC-05A`, tylko refaktoryzuje jego kluczowy fragment odpowiedzialny za pustą komórkę.

Po wdrożeniu:
- `UC-05A` dalej pozostaje use case'em inferencji pojedynczej komórki,
- `UC-22` staje się jego doprecyzowaniem algorytmicznym i kontraktowym dla heurystyki `empty detection`,
- odpowiedź nadal wspiera `digit = null` dla komórki pustej.

## Relacja do `UC-14`
`UC-22` rozszerza kontekst parametrów `solveCellInference` w panelu bocznym `UC-14`.

Istniejące parametry mogą pozostać:
- `emptyCellForegroundThresholdPercent`,
- `emptyCellInnerWindowPercent`, jeśli nadal jest używany jako parametr cropu / marginesu przed analizą.

Nowe parametry dodawane przez `UC-22`:
- `emptyCellMinSegmentLengthPx`,
- `emptyCellFilteredSegmentCountThreshold`.

Znaczenie:
- `emptyCellMinSegmentLengthPx` określa minimalną długość segmentu Hough, który może zostać uznany za istotny,
- `emptyCellFilteredSegmentCountThreshold` określa, ile odfiltrowanych segmentów musi zostać wykrytych, aby komórka mogła zostać zaakceptowana jako niepusta w logice segmentowej.

W aktualnym zakresie `UC-22` nie wymaga zmiany kontraktu odpowiedzi, a jedynie rozszerzenia zestawu parametrów wejściowych.

## Zakres odpowiedzialności warstw
### `Frontend`
- Nadal wysyła pojedynczą komórkę do `PUT /api/sudoku/cells/inference`.
- Rozszerza panel parametrów o dwa nowe pola związane z segmentami.
- Nie implementuje lokalnie logiki empty detection.

### `Backend`
- Zachowuje publiczny endpoint inferencji pojedynczej komórki.
- Waliduje nowe parametry wejściowe oraz domyka brakujące wartości domyślne.
- Przekazuje do `ML` resolved parametry heurystyki pustej komórki.

### `MachineLearning`
- Wykonuje flow `raw cell -> empty detection -> cleaning -> digit inference`.
- Liczy metryki segmentowe i pikselowe na `center composite`.
- Zwraca `digit = null` dla komórki pustej.

## Kontrakt `FE -> BE`
### `PUT /api/sudoku/cells/inference`
- Request body pozostaje rozszerzeniem istniejącego kontraktu inferencji pojedynczej komórki.
- Odpowiedź pozostaje `DigitInferenceApiResponse`.

Nowe parametry funkcjonalne:
- `emptyCellMinSegmentLengthPx`
- `emptyCellFilteredSegmentCountThreshold`

Istniejące parametry heurystyki pustej komórki pozostają bez zmiany semantycznej:
- `emptyCellForegroundThresholdPercent`
- `emptyCellInnerWindowPercent`

Przykładowa semantyka odpowiedzi pozostaje taka sama:

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

## Kontrakt `BE -> ML`
### `PUT /ml/cells/inference`
`Backend` przekazuje do `ML` resolved parametry heurystyki pustej komórki i cleaningu runtime.

W szczególności `ML` dostaje co najmniej:
- `emptyCellForegroundThresholdPercent`,
- `emptyCellInnerWindowPercent`,
- `emptyCellMinSegmentLengthPx`,
- `emptyCellFilteredSegmentCountThreshold`.

To nadal jest ten sam biznesowy use case inferencji pojedynczej komórki, tylko z bogatszą konfiguracją empty detection.

## Zasady decyzyjne
Minimalna semantyka decyzji w `UC-22`:
- foreground pixels / ratio dalej może zaakceptować komórkę jako niepustą,
- liczba odfiltrowanych segmentów dalej może zaakceptować komórkę jako niepustą,
- jeśli komórka nie spełnia warunku akceptacji, wynik powinien być `digit = null`,
- cleaning pod model nie powinien uruchamiać się dla komórki uznanej za pustą.

W zakresie tej historyjki celem jest dodanie logiki segmentowej i jej parametryzacji, a nie zmiana semantyki odpowiedzi publicznej.

## Zgodność kontraktowa
`UC-22` zachowuje bez zmian:
- model odpowiedzi `DigitInferenceApiResponse`,
- znaczenie `digit = null`,
- publiczną rolę `Backendu` jako warstwy pośredniej,
- flow `Frontend -> Backend -> ML`.

Zmienia się tylko:
- wewnętrzny sposób wyznaczenia `isEmpty`,
- kolejność operacji przed klasyfikacją,
- zestaw parametrów wejściowych używanych przez heurystykę runtime.

## Poza zakresem
- zmiana kontraktu odpowiedzi `UC-05`,
- zapis diagnostycznych obrazów jako części odpowiedzi produkcyjnej,
- wykorzystanie `center composite` jako próbki dla klasyfikatora cyfry,
- przenoszenie logiki empty detection do `Frontendu`,
- używanie tego algorytmu jako źródła prawdy dla `UC-17`.

## Kryteria akceptacji
- Runtime `UC-05` wykonuje kolejność `raw cell -> empty detection -> cleaning -> digit inference`.
- Detekcja pustej komórki wykorzystuje `center composite` zbudowany z 4 wewnętrznych ćwiartek skierowanych do środka komórki.
- System uruchamia detekcję segmentów Hough na obrazie diagnostycznym używanym do decyzji `empty` vs `non-empty`.
- Segmenty krótsze niż zadany próg są odfiltrowywane przed podjęciem decyzji.
- Decyzja może wykorzystywać zarówno foreground pixels / ratio, jak i liczbę odfiltrowanych segmentów.
- Cleaning pod model uruchamia się wyłącznie dla komórki uznanej za niepustą.
- Publiczny kontrakt odpowiedzi pozostaje bez zmian i nadal wspiera `digit = null`.
- Panel parametrów `UC-14` zostaje rozszerzony o `emptyCellMinSegmentLengthPx` oraz `emptyCellFilteredSegmentCountThreshold`.
- `UC-22` wprost rozróżnia artefakty diagnostyczne od produkcyjnej próbki pod model.
