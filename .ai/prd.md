## PRD - Sudoku Vision

### Metadane
- **Wersja**: 1.0
- **Data**: 2026-06-19
- **Projekt**: `Sudoku Vision`
- **Rola dokumentu**: szybki przeglad produktu, zakresu i wspoldzialania elementow systemu

### 1) Cel dokumentu
Ten dokument ma sluzyc jako krotki przeglad calego systemu:
- czym jest produkt,
- jaki ma zakres,
- jakie sa glowne przeplywy,
- jak ukladaja sie historyjki wzgledem siebie.

To **nie** jest szczegolowa specyfikacja implementacyjna pojedynczych use case'ow.

Detale sa utrzymywane w innych miejscach:
- rozszerzenia historyjek: `.ai/feature/`
- zasady architektury i kontraktow: `.cursor/rules/`
- kod i konfiguracja runtime: repozytorium aplikacji

### 2) Streszczenie produktu
`Sudoku Vision` to aplikacja webowa do rozpoznawania i rozwiazywania Sudoku na podstawie obrazu planszy.

Produkt sklada sie z trzech glownych czesci:
- `Frontend` obslugujacy interfejs uzytkownika,
- `Backend` w C#, ktory jest publicznym API i glownym orkiestratorem systemu,
- serwis `ML` w Pythonie odpowiedzialny za vision, klasyfikacje cyfr oraz trening modelu.

System wspiera dwa glowne obszary:
- sciezke uzytkownika koncowego: rozpoznanie planszy i rozwiazanie Sudoku,
- sciezke administracyjno-ML: przygotowanie danych, trening, przeglad modeli i wybor aktywnego modelu.

### 3) Problem i cele
Projekt laczy wymagania produktowe i ML w jednym spojnym workflow:
- rozpoznac plansze Sudoku z obrazu,
- odczytac cyfry i zbudowac grid 9x9,
- rozwiazac Sudoku algorytmicznie,
- pokazac wynik w czytelnej formie,
- utrzymac workflow danych i modeli pozwalajacy iterowac nad jakoscia rozpoznawania.

Cele wysokiego poziomu:
- **G1**: uzytkownik moze rozwiazac Sudoku ze zdjecia lub obrazu przykladowego,
- **G2**: zespol moze przygotowywac dane treningowe i trenowac modele bez obchodzenia glownego workflow systemu,
- **G3**: Backend pozostaje `source of truth` dla workflow, statusow i rekordow widocznych w UI,
- **G4**: system pozostaje zrozumialy architektonicznie i nadaje sie do dalszego rozwoju.

### 4) Zakres MVP
W zakresie MVP sa cztery glowne capability systemu:

#### A. Solve Sudoku
- wczytanie obrazu Sudoku,
- wykrycie planszy i podzial na komorki,
- rozpoznanie cyfr i pustych pol,
- rozwiazanie gridu,
- prezentacja wyniku w UI.

#### B. Prosta sciezka administracyjna
- odblokowanie operacji administracyjnych prostym haslem,
- oddzielenie funkcji publicznych od administracyjnych.

#### C. Workflow datasetowy i treningowy
- przeglad surowych zrodel danych,
- utworzenie przygotowania datasetu,
- przeglad i czyszczenie danych przygotowanych,
- budowa finalnego `.npz`,
- uruchomienie treningu na gotowym secie.

#### D. Zarzadzanie modelami
- lista treningow,
- lista modeli,
- szczegoly i metryki treningu,
- wybor aktywnego modelu do inferencji.

### 5) Poza zakresem
Poza zakresem aktualnego PRD i MVP pozostaja:
- pelny system kont, rol i tozsamosci,
- mobilna aplikacja natywna,
- rozbudowana dokumentacja endpointow i payloadow HTTP w tym dokumencie,
- szczegolowy opis struktur plikowych, indeksow i manifestow,
- szczegoly techniczne preprocessingu, treningu, augmentacji i benchmarkow, jesli nie sa potrzebne do zrozumienia calego systemu.

### 6) Role uzytkownikow
- **Uzytkownik web**: chce szybko rozwiazac Sudoku i zobaczyc wynik.
- **Operator ML / admin**: chce przygotowac dane, oczyscic je, zbudowac dataset treningowy, uruchomic trening i wybrac model.
- **Zespol projektowy / osoba demo**: chce miec spojny system do prezentacji i iteracji nad jakoscia modelu.

### 7) Architektura wysokiego poziomu
Docelowy uklad systemu:

```text
Frontend -> Backend -> ML
```

Zasady architektoniczne:
- `Frontend` komunikuje sie tylko z `Backendem`.
- `Backend` jest glowna warstwa aplikacyjna i publicznym API.
- `Backend` jest `source of truth` dla workflow, statusow, rekordow datasetow, treningow i aktywnego modelu.
- `ML` jest wewnetrzna usluga specjalistyczna wywolywana przez `Backend`.
- `ML` wykonuje obliczenia i tworzy artefakty techniczne, ale nie powinien byc drugim niezaleznym zrodlem prawdy biznesowej.
- Szczegoly techniczne przechowywania danych, modeli i raportow sa wtornym detalem implementacyjnym wobec tego podzialu odpowiedzialnosci.

### 8) Glowne przeplywy systemu

#### P1. Rozwiaz Sudoku z obrazu
1. Uzytkownik wybiera obraz Sudoku z biblioteki przykladow albo bezposrednio z lokalnego pliku.
2. System wykrywa plansze i przygotowuje dane wejsciowe.
3. System rozpoznaje grid 9x9.
4. System rozwiazuje Sudoku.
5. UI pokazuje wynik jako grid i/lub obraz z naniesionym rozwiazaniem.

#### P2. Odblokuj operacje administracyjne
1. Uzytkownik podaje wspoldzielone haslo administracyjne.
2. `Backend` weryfikuje dostep.
3. Po poprawnej weryfikacji funkcje administracyjne staja sie dostepne.

#### P3. Przygotuj dane do treningu
1. Admin przeglada dostepne surowe datasety.
2. Tworzy przygotowanie datasetu jako trwaly etap posredni.
3. Przeglada i usuwa niechciane elementy przygotowania.
4. Buduje finalny dataset `.npz` z przygotowanych danych.

#### P4. Trenuj i wybierz model
1. Admin wybiera gotowy dataset treningowy.
2. Uruchamia trening modelu.
3. Monitoruje postep oraz wynik.
4. Przeglada metryki i porownuje modele.
5. Ustawia aktywny model wykorzystywany pozniej w inferencji.

### 9) Mapa historyjek
Ponizej utrzymujemy tylko skrotowa mape historyjek. Szczegoly nalezy czytac w dokumentach z `.ai/feature/`.

#### 9.1. Core product
- **UC-01 - Dodaj plik Sudoku do przykladow**  
  Biblioteka obrazow przykladowych do pracy i demo.

- **UC-02 - Lista dostepnych przykladow Sudoku**  
  Przeglad dostepnych przykladow zapisanych w systemie.

- **UC-03 - Pobierz wybrany plik przykladowy**  
  Odczyt konkretnego przykladu z biblioteki.

- **UC-04 - Wykonaj wstepna obrobke wybranego przykladu**  
  Wykrycie planszy i przygotowanie widoku do dalszej inferencji.

- **UC-20 - Wykonaj wstepna obrobke lokalnego zdjecia Sudoku bez zapisu na serwerze**  
  Alternatywna sciezka wejscia dla `UC-04`: preprocessing obrazu wybranego z komputera uzytkownika bez dodawania go do biblioteki przykladow i bez trwalego zapisu po stronie serwera.  
  Szczegoly: `.ai/feature/uc-20-overview.md`

- **UC-05 - Rozpoznaj cyfry, rozwiaz Sudoku i pokaz wynik**  
  Glowna wartosc produktu dla uzytkownika koncowego.

#### 9.2. Admin, trening i modele
- **UC-06 - Uruchom trening na przygotowanym zestawie `.npz`**  
  Start procesu treningowego na gotowym secie danych.

- **UC-07 - Pokazuj postep treningu i informuj o zakonczeniu**  
  Monitoring aktywnego runu i odbior stanu koncowego.

- **UC-08 - Lista treningow i modeli**  
  Katalog eksperymentow i wynikowych modeli.

- **UC-09 - Szczegoly treningu i metryki**  
  Widok porownawczy i diagnostyczny dla eksperymentow.

- **UC-10 - Wybierz aktywny model do inferencji**  
  Zmiana modelu uzywanego przez sciezke solve.

- **UC-11 - Wyswietl dostepne surowe datasety**  
  Punkt wejscia do workflow datasetowego.

- **UC-13 - Prosta autoryzacja do operacji administracyjnych**  
  Minimalna bramka dostepu dla funkcji administracyjnych.

- **UC-14 - Parametryzuj wybrane funkcjonalnosci z poziomu UI**  
  Kontrolowana ekspozycja parametrow funkcjonalnych uzytkownikowi.

#### 9.3. Docelowy workflow datasetowy
- **UC-17 - Utworz przygotowanie datasetu**  
  Tworzy trwaly etap posredni pomiedzy `raw` a finalnym `.npz`.  
  Szczegoly: `.ai/feature/uc-17-overview.md`

- **UC-18 - Przegladaj i usuwaj elementy z przygotowania datasetu**  
  Pozwala oczyscic dane po przygotowaniu, bez ponownego preprocessingu.  
  Szczegoly: `.ai/feature/uc-18-overview.md`

- **UC-19 - Zbuduj finalny dataset `.npz` z przygotowania datasetu**  
  Buduje finalny artefakt treningowy z danych juz przygotowanych i oczyszczonych.  
  Szczegoly: `.ai/feature/uc-19-overview.md`

#### 9.4. Refactor, migracje i elementy techniczne
Te pozycje nie sa glownymi capability produktu. Sa wspierajace, przejsciowe albo techniczne.

- **UC-00 - Smoke test FE -> BE -> ML**  
  Historyjka techniczna do szybkiego sprawdzenia integracji miedzy warstwami.

- **EXP-04 - Testowa inferencja pojedynczej cyfry**  
  Eksperyment techniczny wspierajacy diagnostyke modelu, poza glownym API produktu.

- **UC-12 - Wczesniejszy workflow bezposredniej budowy `.npz` z `raw`**  
  Traktowany jako etap przejsciowy / migracyjny. Funkcjonalnie zostaje zastapiony przez sekwencje `UC-17 -> UC-18 -> UC-19`.

- **UC-15 - Spowolnij live solve stalym opoznieniem kroku**  
  Przejsciowe rozszerzenie UX i techniczny krok przed pelniejsza parametryzacja z `UC-14`.

- **UC-16 - Przegladaj zapisany dataset i artefakty preview po przygotowaniu**  
  Podejscie zwiazane z poprzednim workflow datasetowym. Nie jest glowna osia docelowego modelu pracy z danymi.

### 10) Docelowy model danych i workflow
W aktualnym kierunku projektu za docelowy uznajemy workflow:

```text
raw -> przygotowanie datasetu -> czyszczenie -> build .npz -> trening -> wybor aktywnego modelu
```

Konsekwencje tej decyzji:
- etap ciezkiego preprocessingu nie powinien byc powtarzany przy kazdej przebudowie datasetu,
- czyszczenie danych powinno dzialac na trwalym etapie posrednim,
- finalny `.npz` jest artefaktem koncowym do treningu, a nie miejscem wykonywania calego workflow od zera,
- stare sciezki bezposredniego budowania `.npz` z `raw` traktujemy jako migracyjne albo wygaszane.

### 11) Wymagania niefunkcjonalne
- **NFR-01 Reprodukowalnosc**: glowne workflow powinny byc uruchamialne w sposob powtarzalny.
- **NFR-02 Czytelnosc architektury**: odpowiedzialnosci `Frontend`, `Backend` i `ML` maja byc wyraznie rozdzielone.
- **NFR-03 Konfigurowalnosc**: ustawienia srodowiskowe, sciezki i adresy integracyjne pozostaja poza kodem.
- **NFR-04 Odpornosc**: system powinien zwracac czytelne bledy, a nie niejawnie konczyc workflow w stanie posrednim.
- **NFR-05 Rozwojowosc**: workflow danych i modeli ma wspierac iteracyjna poprawe jakosci rozwiazywania Sudoku.

### 12) Zalozenia
- ML dla treningu i inferencji pozostaje w Pythonie.
- `Backend` w C# jest glowna warstwa aplikacyjna.
- Solver Sudoku moze pozostac klasycznym solverem opartym o backtracking.
- W MVP rekordy systemowe moga byc utrzymywane bez osobnej bazy danych, o ile `Backend` pozostaje jedynym zrodlem prawdy dla ich semantyki.
- Szczegoly kontraktow HTTP, layoutu katalogow i formatow plikow nie sa utrzymywane w tym dokumencie, tylko w dokumentacji szczegolowej i w kodzie.

### 13) Glowne ryzyka
- **R1**: rozjazd miedzy danymi treningowymi i danymi runtime inferencji,
- **R2**: mieszanie warstwy produktowej z detalami technicznymi w dokumentacji,
- **R3**: dublowanie zrodla prawdy miedzy `Backendem` i `ML`,
- **R4**: utrzymywanie starych i nowych workflow datasetowych jednoczesnie bez jasnego statusu migracji,
- **R5**: zbyt duza liczba parametrow i detali technicznych eksponowanych na poziomie PRD.

### 14) Kamienie milowe
- **M1**: dzialajaca sciezka solve dla Sudoku z obrazu,
- **M2**: podstawowy trening modelu oraz rejestr modeli,
- **M3**: spojny administracyjny workflow datasetowy,
- **M4**: docelowe przejscie na workflow `UC-17 -> UC-18 -> UC-19`,
- **M5**: ustabilizowanie wyboru aktywnego modelu i porownywania wynikow.

### 15) Jak czytac ten dokument
Ten PRD ma pomagac odpowiedziec na pytania:
- jaki problem rozwiazuje system,
- jakie ma glowne capability,
- jakie sa docelowe przeplywy,
- ktore historyjki sa produktowe, a ktore techniczne lub migracyjne,
- jak wspoldzialaja `Frontend`, `Backend` i `ML`.

Jesli potrzebny jest szczegol jednego use case'a, nalezy przejsc do odpowiedniego dokumentu w `.ai/feature/`.
