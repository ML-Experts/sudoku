# UC-05 — Rozpoznanie cyfr, solver i prezentacja wyniku

## Cel
`UC-05` opisuje przejście od obrazu komórki lub planszy sudoku do rozpoznanych cyfr, rozwiązania i czytelnej prezentacji wyniku.

Produktowo jest to jeden strumień "rozwiąż sudoku", ale implementacyjnie dzielimy go na mniejsze historyjki, żeby dało się testować i wdrażać kolejne kroki niezależnie.

## UC-05A — Inferencja pojedynczej cyfry / komórki
### Cel
Rozpoznać zawartość pojedynczej komórki sudoku przy użyciu aktywnego modelu inferencyjnego.

### Wejście
- Obraz komórki jako `ImageApiEntry`:
  - `mimeType`,
  - `base64`.

### Wyjście
- Minimalna odpowiedź `DigitInferenceApiResponse`:

```json
{
  "digit": 7
}
```

- Dla pustej komórki albo braku rozpoznanej cyfry:

```json
{
  "digit": null
}
```

- `digit` przyjmuje wartości `1..9` albo `null`.
- FE wie, którą komórkę wysłał, więc odpowiedź nie musi zawierać `cellIndex`.
- Informacje diagnostyczne, takie jak model, pewność albo ostrzeżenia, nie są częścią minimalnego kontraktu MVP.

### Uwagi
- Eksperyment `EXP-04` jest punktem odniesienia technicznego, ale nie jest docelowym API produktu.
- Frontend nie powinien wołać `ML` bezpośrednio; publiczny kontrakt przechodzi przez Backend.
- Dla pełnej planszy dopuszczalne są różne strategie komunikacji: 81 osobnych requestów `FE -> BE`, batch albo endpoint wyższego poziomu. Wariant 81 requestów jest szczególnie prosty po `UC-04`, bo `FE` zna indeksy komórek i może pokazywać progres na podstawie liczby zakończonych odpowiedzi.
- Jeśli wybierzemy 81 requestów, warto ograniczyć równoległość po stronie `FE`, żeby nie przeciążyć `BE` ani kolejki inferencji po stronie `ML`.

## UC-05B — Backtracking dla rozpoznanego gridu
### Cel
Rozwiązać sudoku na podstawie gridu 9×9 zawierającego rozpoznane cyfry i puste pola.

### Wejście
- Grid 9×9.
- Cyfry `1..9`.
- Puste pola jako `null` albo równoważna reprezentacja ustalona w kontrakcie API.

### Wyjście
- `solvedGrid` dla poprawnego sudoku.
- Status błędu dla gridu niepoprawnego lub nierozwiązywalnego.

### Uwagi
- Solver backtracking nie wymaga modelu ML.
- Solver powinien być możliwy do testowania niezależnie od inferencji obrazu.
- Błędy walidacji gridu powinny być czytelne dla UI.

## UC-05C — Przypisanie cyfr do komórek
### Cel
Pokazać użytkownikowi rozpoznany i rozwiązany stan planszy w siatce 9×9.

### Zakres podstawowy
- Przypisanie rozpoznanych cyfr do odpowiadających komórek.
- Pokazanie cyfr jako tekstu w UI.
- Rozróżnienie cyfr wejściowych od cyfr dopisanych przez solver.
- Możliwość pokazania błędów lub niepewnych komórek.

### Uwagi
- Ten wariant jest tańszy i stabilniejszy niż generowanie obrazu wynikowego.
- Powinien być pierwszym docelowym sposobem prezentacji rozwiązania, zanim powstanie graficzny overlay.

## UC-05D — Graficzne naniesienie cyfr na obraz
### Cel
Wygenerować obraz wynikowy z naniesionymi cyframi rozwiązania.

### Warianty
- Wariant podstawowy: naniesienie cyfr na obraz planszy po korekcji perspektywy z `UC-04`.
- Wariant ambitny: naniesienie cyfr na oryginalne zdjęcie wejściowe sprzed korekcji perspektywy.

### Uwagi
- Overlay jest osobną funkcjonalnością od samego solvera.
- Wariant na oryginalnym zdjęciu wymaga zachowania transformacji perspektywy z etapu preprocessingu.
- Generowanie overlay nie powinno blokować podstawowej prezentacji wyniku w gridzie.

## Kolejność rekomendowana
1. `UC-05A` — stabilna inferencja pojedynczej komórki przez Backend.
2. `UC-05B` — solver backtracking testowany na gridzie.
3. `UC-05C` — prezentacja wyniku w siatce 9×9.
4. `UC-05D` — overlay graficzny, najpierw na obrazie po korekcji perspektywy.
