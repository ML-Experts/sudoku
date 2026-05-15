Backtracking w Sudoku to metoda „spróbuj → sprawdź → cofnij się, jeśli źle”.

Nie rozwiązuje się go koniecznie **po kolei rzędami**. Najprostsza wersja może iść po planszy od lewej do prawej, od góry do dołu, ale lepsza wersja wybiera **najbardziej ograniczone puste pole**, czyli takie, które ma najmniej możliwych cyfr.

## Zasada działania

Masz planszę 9×9. Dla każdego pustego pola sprawdzasz, jakie cyfry od 1 do 9 są dozwolone według zasad Sudoku:

1. cyfra nie może już występować w tym samym rzędzie,
2. cyfra nie może już występować w tej samej kolumnie,
3. cyfra nie może już występować w tym samym kwadracie 3×3.

Potem algorytm robi mniej więcej tak:

```text
1. Znajdź puste pole.
2. Sprawdź, jakie cyfry można tam wstawić.
3. Wstaw jedną z możliwych cyfr.
4. Przejdź dalej.
5. Jeśli później okaże się, że nie da się kontynuować:
   - usuń ostatnio wpisaną cyfrę,
   - spróbuj innej.
6. Jeśli wszystkie pola są wypełnione poprawnie, Sudoku jest rozwiązane.
```

Czyli algorytm „wchodzi w ścieżkę”, a jeśli trafi w ślepy zaułek, cofa się.

## Przykład prosty

Załóżmy, że mamy puste pole i możliwe są tam cyfry:

```text
{2, 5, 7}
```

Algorytm próbuje:

```text
wstaw 2
```

Idzie dalej. Po kilku krokach może się okazać, że inne pole nie ma już żadnej możliwej cyfry. Wtedy algorytm mówi:

```text
2 było złym wyborem
cofam się
spróbuję 5
```

Jeśli 5 też prowadzi do błędu, próbuje 7.

## Czy rozwiązuje się po kolei jeden rząd?

Może, ale to nie jest najlepsze.

### Prosta wersja

Najprostszy algorytm idzie po kolei:

```text
rząd 1, kolumna 1
rząd 1, kolumna 2
rząd 1, kolumna 3
...
rząd 2, kolumna 1
...
```

Czyli tak, można rozwiązywać „po kolei”.

Ale to bywa wolniejsze, bo algorytm może zacząć od pola, które ma np. 7 możliwych cyfr.

### Lepsza wersja

Lepszy backtracking wybiera pole z najmniejszą liczbą kandydatów.

Na przykład:

```text
A ma możliwe cyfry: {1, 2, 3, 4, 5}
B ma możliwe cyfry: {7}
C ma możliwe cyfry: {2, 9}
```

Najlepiej zacząć od pola **B**, bo ma tylko jedną możliwość.

To bardzo przyspiesza rozwiązywanie.

## Czy to długo trwa?

Dla normalnego Sudoku 9×9 — zwykle **bardzo krótko**.

Dobrze napisany backtracking rozwiązuje typowe Sudoku w ułamku sekundy albo kilka milisekund.

Teoretycznie Sudoku może być trudne obliczeniowo, bo algorytm może próbować bardzo wielu kombinacji. Ale w praktyce dla standardowej planszy 9×9 backtracking z prostymi optymalizacjami działa bardzo dobrze.

Najwolniejszy wariant to taki, który:

```text
- idzie po kolei po polach,
- próbuje cyfry 1–9 bez analizy,
- nie wybiera najtrudniejszych/najbardziej ograniczonych pól najpierw.
```

Szybszy wariant:

```text
- dla każdego pustego pola liczy możliwe cyfry,
- wybiera pole z najmniejszą liczbą kandydatów,
- aktualizuje kandydatów po każdym ruchu,
- od razu przerywa ścieżkę, jeśli jakieś pole nie ma żadnej możliwej cyfry.
```

## Najważniejsza intuicja

Backtracking nie „myśli” jak człowiek w stylu:

```text
rozwiążmy najpierw pierwszy rząd
potem drugi
potem trzeci
```

Tylko raczej:

```text
znajdź miejsce, gdzie jest najmniej możliwości
spróbuj jednej
jeśli prowadzi do sprzeczności, cofnij
```

Czyli bardziej przypomina eksplorowanie drzewa decyzji.

## Pseudokod

```text
Solve(board):
    if plansza jest pełna:
        return sukces

    pole = znajdź najlepsze puste pole

    for cyfra in możliwe_cyfry(pole):
        wpisz cyfrę w pole

        if Solve(board) == sukces:
            return sukces

        usuń cyfrę z pola

    return porażka
```

Ta linia jest sercem backtrackingu:

```text
usuń cyfrę z pola
```

Bo oznacza: „ta droga nie działa, wracam i próbuję czegoś innego”.
