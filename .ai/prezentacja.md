# Konspekt prezentacji projektu `Sudoku Vision`

## Cel tego dokumentu

Ten dokument ma pomóc w zaprezentowaniu projektu na komputerze w prosty i pewny sposób.

Nie jest to prezentacja „slajd po slajdzie”.
To jest raczej scenariusz:

- co pokazać,
- o czym mówić,
- w jakiej kolejności to robić,
- na co zwrócić uwagę,
- co dorzucić, jeśli zostanie czas.

## Główna myśl prezentacji

Najprościej opowiadać ten projekt jako połączenie trzech rzeczy:

1. `Computer Vision` znajduje planszę i przygotowuje obraz.
2. `Machine Learning` rozpoznaje cyfry.
3. `Algorytm backtrackingu` rozwiązuje sudoku.

Najważniejsze zdanie, które warto powiedzieć na początku:

> Nasz projekt bierze zdjęcie sudoku, odnajduje planszę, rozpoznaje cyfry, buduje stan gry, rozwiązuje układankę i pokazuje wynik użytkownikowi jako planszę oraz obraz z naniesionym rozwiązaniem.

## Jak poprowadzić prezentację

Najlepiej zrobić to w kolejności:

1. krótko powiedzieć, jaki był cel projektu,
2. pokazać działanie aplikacji,
3. wyjaśnić architekturę i przepływ danych,
4. powiedzieć, jak działa ML i dane,
5. wspomnieć o repo, pracy zespołowej i wdrożeniu,
6. zakończyć krótkim podsumowaniem.

## Proponowany plan na 5–7 minut

### 1. Wstęp — około 40 sekund

Powiedz:

- czym jest projekt,
- jaki problem rozwiązuje,
- dlaczego temat łączy `OpenCV`, `ML` i algorytmikę.

Krótka wersja:

> Celem projektu było stworzenie systemu, który automatycznie odczytuje sudoku ze zdjęcia i je rozwiązuje.  
> Projekt łączy przetwarzanie obrazu, model uczenia maszynowego i klasyczny solver backtrackingowy.

### 2. Demo działania — około 2 minuty

To jest najważniejsza część.
Najpierw pokaż działanie, a dopiero potem tłumacz szczegóły.

Pokaż:

1. ekran aplikacji,
2. wybór obrazu albo przykładu,
3. wynik preprocessingu planszy,
4. rozpoznany grid,
5. końcowe rozwiązanie,
6. obraz z naniesionymi cyframi.

W trakcie mów:

- że system najpierw znajduje planszę,
- potem dzieli ją na `9x9`,
- potem rozpoznaje zawartość komórek,
- a na końcu rozwiązuje sudoku i pokazuje wynik.

Jeśli demo działa płynnie, nie zatrzymuj się od razu na kodzie.
Najpierw pozwól zobaczyć efekt końcowy.

### 3. Jak działa pipeline — około 1 minuty

Po demo pokaż w `README.md` główny flowchart albo sekcję z pipeline'ami.

Powiedz to prostymi zdaniami:

- wejściem jest zdjęcie planszy,
- `OpenCV` wykrywa kontur i prostuje perspektywę,
- plansza jest cięta na `81` pól,
- model rozpoznaje cyfry,
- backend składa to do macierzy `9x9`,
- solver uzupełnia brakujące pola,
- wynik wraca do użytkownika.

Dobre zdanie:

> Najważniejsze było dla nas rozdzielenie odpowiedzialności: obraz i geometria po stronie preprocessingu, rozpoznawanie po stronie modelu, a rozwiązywanie po stronie solvera.

### 4. Architektura — około 1 minuta

Pokaż w `README.md` sekcję o architekturze albo flow `FE -> BE -> ML`.

Powiedz:

- `Frontend` odpowiada za interfejs i prezentację wyniku,
- `Backend` jest głównym punktem wejścia i `source of truth`,
- `ML` jest usługą wewnętrzną odpowiedzialną za preprocessing, inferencję i trening.

To warto podkreślić:

> Frontend nie komunikuje się bezpośrednio z ML.  
> Cały publiczny workflow przechodzi przez backend.

### 5. Dane i modele — około 1 minuta

Pokaż w `README.md` sekcję o modelach i datasetach.

Powiedz:

- że obecnie główny wybór modeli to `cnn-baseline` i `resnet18-imagenet-bootstrap`,
- że dane pochodzą z dwóch źródeł: `board` oraz `digit`,
- że oba źródła są składane do wspólnego `.npz`,
- że preprocessing dla treningu, inferencji i ewaluacji jest możliwie spójny.

To jest bardzo dobry moment na zdanie:

> Zależało nam na tym, żeby model trenował się na danych przygotowanych możliwie podobnie do tych, które później widzi w runtime.

### 6. Zakończenie — około 30–40 sekund

Na końcu powiedz:

- co udało się zbudować,
- co było najciekawsze,
- co można rozwijać dalej.

Krótka wersja:

> Udało się nam zbudować działający pipeline od zdjęcia do rozwiązania sudoku.  
> Najciekawsze było połączenie klasycznego przetwarzania obrazu, modeli ML i logiki solvera w jednym spójnym systemie.

## Co dokładnie pokazywać na komputerze

Najlepsza kolejność okien:

1. uruchomiona aplikacja,
2. wynik solve na przykładzie,
3. `README.md`,
4. ewentualnie katalog repo albo wybrane fragmenty kodu,
5. jeśli starczy czasu: widok datasetów / treningów / modeli.

Jeśli masz mało czasu, pokazuj tylko:

- działanie aplikacji,
- jeden diagram w `README.md`,
- krótką sekcję o modelach i danych.

## O czym mówić podczas pokazywania

### Przy demie

Mów o efekcie dla użytkownika:

- użytkownik wrzuca zdjęcie,
- system rozpoznaje stan,
- system rozwiązuje sudoku,
- system pokazuje wynik.

### Przy architekturze

Mów o odpowiedzialnościach warstw:

- `FE` pokazuje i zbiera dane,
- `BE` zarządza workflow,
- `ML` wykonuje część analityczną i modelową.

### Przy danych i modelach

Mów o decyzjach projektowych:

- dwa typy danych wejściowych,
- wspólny format `.npz`,
- dwa główne typy modeli do porównań,
- spójny preprocessing.

### Przy solverze

Mów prosto:

- model nie rozwiązuje sudoku,
- model tylko rozpoznaje cyfry,
- sudoku rozwiązuje klasyczny backtracking.

To często robi dobre wrażenie, bo pokazuje sensowny podział problemu.

## Na co warto zwrócić uwagę

W prezentacji warto podkreślić kilka ciekawych rzeczy:

- projekt nie jest tylko klasyfikatorem cyfr, ale pełnym systemem `end-to-end`,
- backend jest właścicielem workflow i nie oddaje logiki ani stanu do frontendu ani do ML,
- dane `board` i `digit` są ujednolicane do wspólnego formatu,
- preprocessing nie jest przypadkowy, tylko możliwie spójny między treningiem i inferencją,
- model to tylko część rozwiązania; równie ważne są preprocessing i solver,
- wynik końcowy nie jest tylko liczbą, ale także obrazem z overlayem.

## Co powiedzieć, jeśli zostanie czas

Jeśli zostanie dodatkowa minuta albo dwie, możesz opowiedzieć o jednej z tych rzeczy:

### 1. O repozytorium

Warto pokazać:

- że repo ma czytelną strukturę,
- że dokumentacja w `.ai/` prowadzi od wymagań do implementacji,
- że `README.md` opisuje architekturę, runtime i wdrożenie,
- że projekt ma rozdzielone warstwy `Frontend`, `Backend`, `MachineLearning`.

To pokazuje dojrzałość projektu, a nie tylko sam kod.

### 2. O Git i pracy zespołowej

Możesz wspomnieć:

- że projekt był rozwijany zespołowo,
- że był podział odpowiedzialności,
- że repo ma historię commitów,
- że workflow `dev -> main` i osobne workflow deployowe porządkują pracę.

Nie rozwlekaj tego za bardzo.
To jest dobry dodatek, ale nie główny temat prezentacji.

### 3. O założeniach projektowych

Warto powiedzieć:

- że `ML` nie jest publiczną usługą,
- że `BE` jest `source of truth`,
- że overlay rysowany jest programowo, a nie generowany przez model,
- że celem było rozwiązanie działające praktycznie, a nie tylko eksperyment badawczy.

### 4. O fun factach

To może być bardzo dobre na końcu.

Przykłady:

- najtrudniejsze nie zawsze jest samo ML, tylko dobre wykrycie planszy i czyszczenie obrazu,
- mały model CNN potrafi być bardzo konkurencyjny wobec cięższych modeli,
- solver sudoku jest klasycznym algorytmem, więc AI nie robi tutaj wszystkiego,
- nawet dobre rozpoznanie cyfr nie wystarcza, jeśli preprocessing źle wytnie komórki.

## Czego nie przeciągać

Nie warto za długo mówić o:

- każdym endpointcie po kolei,
- wszystkich katalogach w repo,
- szczegółach konfiguracji środowiskowej,
- wszystkich commitach,
- niskopoziomowych parametrach preprocessingu.

To są dobre rzeczy na pytania po prezentacji, ale nie na główną część wystąpienia.

## Gotowy skrót wypowiedzi

Możesz użyć takiego prostego szkieletu:

> Nasz projekt nazywa się `Sudoku Vision`.  
> Celem było stworzenie systemu, który bierze zdjęcie sudoku, rozpoznaje planszę, odczytuje cyfry, rozwiązuje układankę i pokazuje wynik użytkownikowi.  
> Projekt podzieliliśmy na trzy warstwy: frontend, backend i machine learning.  
> Najpierw pokażę działanie aplikacji, a potem krótko wyjaśnię, jak działa pipeline i jakich modeli używamy.  
> Najciekawsze w projekcie było połączenie OpenCV, klasyfikacji cyfr i klasycznego solvera w jednym spójnym workflow.

## Krótka checklista przed prezentacją

- mieć przygotowany jeden pewny przykład sudoku do demo,
- mieć uruchomioną aplikację przed prezentacją,
- mieć otwarty `README.md`,
- wiedzieć, gdzie w `README.md` są diagramy,
- nie zaczynać od kodu, tylko od działania,
- mieć krótką wersję prezentacji na `5` minut i dłuższą na `7` minut,
- przygotować jedno zdanie o modelach, jedno o architekturze i jedno o solverze,
- zostawić na koniec krótkie podsumowanie.

## Wersja awaryjna

Jeśli demo na żywo nie wyjdzie, pokaż:

- `README.md`,
- diagram pipeline'u,
- opis modeli i datasetów,
- gotowy wynik zapisany wcześniej.

Wtedy mów:

> Nawet jeśli nie pokażemy teraz całego przepływu live, architektura i pipeline projektu są takie, a taki wynik system generuje końcowo.

To pozwala zachować spójność prezentacji nawet przy problemach technicznych.
