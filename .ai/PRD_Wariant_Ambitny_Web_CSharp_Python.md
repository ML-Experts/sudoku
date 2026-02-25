## PRD — Sudoku Vision (wariant ambitny: web + C# backend + Python ML)

### Metadane
- **Wersja**: 0.1 (draft)
- **Data**: 2026-02-25
- **Autorzy**: (uzupełnijcie: imiona i role w zespole)
- **Repo / projekt**: `Sudoku Vision`

### 1) Streszczenie
Celem projektu jest zbudowanie aplikacji webowej, która potrafi przyjąć zdjęcie planszy Sudoku, rozpoznać układ cyfr z użyciem modelu ML (Python), rozwiązać łamigłówkę algorytmem (backtracking) i zwrócić użytkownikowi wynik jako: (1) macierz 9×9 oraz (2) obraz z naniesionym rozwiązaniem. System ma mieć architekturę wielowarstwową: frontend web → backend w C# → serwis ML/inferencji w Pythonie.

### 2) Kontekst i problem
Na zajęciach wymagany jest projekt z elementem Machine Learning w Pythonie. Temat „Sudoku Vision” łączy:
- **Computer Vision (OpenCV)**: wykrycie planszy, korekcja perspektywy, podział na 81 pól.
- **ML/DL (CNN / transfer learning)**: klasyfikacja cyfry w komórce.
- **Algorytmika**: rozwiązanie sudoku (backtracking).
- **Produkt**: czytelny wynik dla użytkownika (UI + obraz wynikowy).

### 3) Cele projektu
- **G1 (funkcjonalny)**: Rozpoznanie planszy Sudoku z obrazu i zbudowanie stanu gry jako macierzy 9×9.
- **G2 (ML)**: Rozpoznanie cyfr 1–9 (oraz/lub wykrycie pustych pól) z użyciem sieci neuronowej.
- **G3 (solver)**: Poprawne rozwiązanie sudoku metodą backtrackingu.
- **G4 (output)**: Wygenerowanie obrazu wynikowego z naniesionymi cyframi rozwiązania na planszę.
- **G5 (ewaluacja)**: Raport jakości (confusion matrix, accuracy, precision, recall, F1) + porównanie podejść (model własny vs transfer learning).
- **G6 (inżynierski)**: Reprodukowalne uruchomienie (README, `requirements.txt`), spójna jakość kodu (format/lint), praca zespołowa (commity, role, prezentacja).

### 4) Zakres (MVP) vs poza zakresem
#### MVP (musi być)
- Rozpoznanie planszy z obrazu i korekcja perspektywy (OpenCV).
- Podział na 81 komórek 9×9 + preprocessing komórek.
- Model ML w Pythonie do rozpoznawania cyfr (co najmniej 1–9; puste pole wykrywane heurystyką lub jako klasa).
- Rozwiązanie sudoku (backtracking).
- Obraz wynikowy (co najmniej na obrazie „z góry” po korekcji perspektywy; preferowane także na oryginalnym zdjęciu).
- Web UI: upload zdjęcia + prezentacja wyniku (grid + obraz).
- Integracja C# backend ↔ Python inference (REST).
- Ewaluacja modelu i krótkie porównanie wariantów.

#### Poza zakresem (na teraz)
- Uwierzytelnianie użytkowników, konta, baza danych użytkowników.
- Mobilna aplikacja natywna.
- Rozwiązywanie „najlepszego” rozwiązania (sudoku standardowo ma jedno; solver ma znaleźć poprawne).
- Generowanie obrazów przez model (nie jest wymagane; overlay robimy programowo).

### 5) Użytkownicy i persony
- **P1: Student / prowadzący demo**: chce szybko pokazać działanie aplikacji na kilku zdjęciach.
- **P2: Użytkownik web**: chce wrzucić zdjęcie sudoku i dostać rozwiązanie z czytelną wizualizacją.

### 6) Główne przepływy użytkownika (user journeys)
#### J1: „Rozwiąż z obrazka”
1. Użytkownik wchodzi na stronę i wgrywa zdjęcie sudoku.
2. System rozpoznaje planszę i cyfry, pokazuje wykryty stan jako grid 9×9.
3. (Opcjonalnie) Użytkownik poprawia błędnie rozpoznane pola.
4. Użytkownik klika „Rozwiąż”.
5. System zwraca rozwiązanie (grid + obraz z naniesionymi cyframi).

### 7) Wymagania funkcjonalne (FR)
- **FR-01**: System przyjmuje obraz sudoku (jpg/png) z UI i przekazuje go do pipeline’u.
- **FR-02**: System wykrywa obszar planszy i wykonuje korekcję perspektywy (widok z góry).
- **FR-03**: System dzieli planszę na 81 pól i przygotowuje dane wejściowe dla modelu (np. 28×28, normalizacja 0–1).
- **FR-04**: System klasyfikuje zawartość pól (cyfra 1–9 lub puste).
- **FR-05**: System buduje macierz 9×9 reprezentującą stan sudoku.
- **FR-06**: System rozwiązuje sudoku algorytmem backtrackingu.
- **FR-07**: System generuje obraz wynikowy z naniesionymi cyframi rozwiązania.
- **FR-08**: System udostępnia wynik w UI oraz jako dane (np. JSON grid).
- **FR-09**: System generuje raport ewaluacyjny modelu (metryki + macierz pomyłek).
- **FR-10**: System umożliwia porównanie co najmniej dwóch podejść do klasyfikacji (np. mały CNN vs transfer learning).

### 8) Historyjki (User Stories) + kryteria akceptacji
Poniżej backlog w formie „historyjek” do realizacji. Wszystkie implementacje ML są w Pythonie.

#### Epic E1 — Przetwarzanie obrazu (OpenCV)
- **US-01**: Jako użytkownik chcę, aby system wykrył planszę Sudoku na zdjęciu i ją „wyprostował”, abym mógł uzyskać stabilny podział na komórki.
  - **AC**:
    - Dla obrazów testowych system znajduje największy kontur planszy i wykonuje transformację perspektywy.
    - Wynikiem jest obraz planszy w stałym rozmiarze (np. 450×450) gotowy do cięcia na 9×9.

- **US-02**: Jako system chcę pociąć wyprostowaną planszę na 81 komórek i wykryć puste pola, aby nie uruchamiać klasyfikacji tam, gdzie nie ma cyfry.
  - **AC**:
    - Pipeline zwraca 81 wycinków (row, col, obraz komórki).
    - Dla pustych pól heurystyka (np. próg liczby pikseli po preprocessingu) oznacza je jako „empty”.

#### Epic E2 — ML: rozpoznawanie cyfr (Python)
- **US-03**: Jako analityk/ML-engineer chcę zbudować zestaw treningowy (preprocessing + augmentacje), aby model rozpoznawał cyfry z pól sudoku.
  - **AC**:
    - Dane są dzielone na train/val/test.
    - Opisane są transformacje: standaryzacja do 28×28, normalizacja 0–1, augmentacje (rotacja, przesunięcie, kontrast, szum).
    - W repo jest jasno opisane skąd pozyskać dane (np. link do datasetu) oraz jest minimalny zestaw obrazów do demo/testów w `examples/`.
    - Dane są zwalidowane pod kątem jakości i geometrii: jeśli dataset zawiera całe plansze, stosujemy analogiczne kroki do pipeline’u (np. warp + cięcie) przed ekstrakcją cyfr; jeśli zawiera wycinki cyfr, dbamy o centrowanie/normalizację i odrzucenie błędnych próbek.

- **US-04**: Jako system chcę klasyfikować cyfry 1–9 (opcjonalnie + „empty”), aby zbudować macierz wejściową do solvera.
  - **AC**:
    - Model zwraca dla każdej komórki etykietę i (opcjonalnie) prawdopodobieństwa klas.
    - Wyniki mapują się do grid 9×9.

- **US-05**: Jako zespół chcę porównać model własny z transfer learningiem, aby udokumentować różnice jakości i kosztów.
  - **AC**:
    - Powstają co najmniej 2 warianty: (A) mały CNN od zera, (B) transfer learning (np. ResNet).
    - Raport zawiera metryki (accuracy, precision, recall, F1) i macierz pomyłek dla obu.

#### Epic E3 — Solver sudoku
- **US-06**: Jako użytkownik chcę, aby system rozwiązał sudoku poprawnie, abym otrzymał kompletne rozwiązanie.
  - **AC**:
    - Solver implementuje backtracking i walidację reguł (wiersz/kolumna/kwadrat 3×3).
    - Dla przypadków testowych solver zwraca rozwiązanie lub komunikat „brak rozwiązania / niepoprawne wejście”.

#### Epic E4 — Wizualizacja wyniku
- **US-07**: Jako użytkownik chcę zobaczyć obraz z naniesionym rozwiązaniem, aby wynik był czytelny i „produktowy”.
  - **AC**:
    - System rysuje wyliczone cyfry w pustych polach (np. innym kolorem) na obrazie planszy po korekcji perspektywy.
    - (Stretch) System nakłada wynik z powrotem na oryginalne zdjęcie (odwrotna transformacja perspektywy).

#### Epic E5 — Interfejs i integracja
- **US-08**: Jako użytkownik chcę wgrać zdjęcie w UI i otrzymać wynik, aby nie uruchamiać skryptów lokalnie.
  - **AC**:
    - Frontend umożliwia upload pliku i pokazuje status przetwarzania.
    - Wynik prezentuje: rozpoznany grid, rozwiązany grid i obraz wynikowy.

- **US-09**: Jako backend chcę wywoływać serwis Pythona po REST, aby oddzielić logikę ML od warstwy webowej.
  - **AC**:
    - C# backend wysyła obraz do Pythona (multipart lub base64).
    - Python zwraca JSON (grid rozpoznany, grid rozwiązany, metadane) oraz obraz wynikowy (np. jako PNG/base64 lub URL).

#### Epic E6 — Jakość, dokumentacja, powtarzalność
- **US-10**: Jako prowadzący chcę móc uruchomić projekt według README, aby zweryfikować działanie.
  - **AC**:
    - README zawiera: opis funkcjonalny, instrukcję uruchomienia, opis kluczowych modułów, podział pracy, ograniczenia.
    - Repo zawiera `requirements.txt` (dla Pythona) i instrukcję dla backendu/frontendu.

- **US-11**: Jako zespół chcę utrzymać spójną jakość kodu, aby łatwiej współpracować i uniknąć błędów.
  - **AC**:
    - W części Python działa formatowanie i lint (np. `black`, `isort`, `pylint`) uruchamiane automatycznie (np. pre-commit).
    - Każdy członek zespołu ma min. 3 commity z opisowymi komunikatami.

### 9) Wymagania niefunkcjonalne (NFR)
- **NFR-01 (reprodukowalność)**: trening i inferencja mają być uruchamialne skryptami/komendami opisanymi w README.
- **NFR-02 (czas odpowiedzi)**: inferencja „solve-from-image” powinna zakończyć się w rozsądnym czasie na CPU (np. < 5 s dla typowego obrazu) — cel orientacyjny.
- **NFR-03 (czytelność)**: kod podzielony na moduły (vision / ml / solver / render) oraz warstwę interfejsu (api lub cli/ui).
- **NFR-04 (odporność)**: system radzi sobie z typowymi zakłóceniami (cień, lekka perspektywa), a w razie porażki zwraca czytelny błąd.

### 10) Założenia i ograniczenia
- ML (trening + inferencja) jest w Pythonie.
- Solver to klasyczny backtracking (wystarczające dla sudoku).
- Dane treningowe: preferowane publiczne (np. Kaggle) + opcjonalnie MNIST/EMNIST jako baseline.
- W UI dopuszczamy możliwość ręcznej korekty rozpoznanego gridu (zmniejsza ryzyko błędów CV/ML na demo).

### 11) Architektura (wariant ambitny)
#### Komponenty
- **Frontend (web)**: upload zdjęcia, podgląd gridu, korekta, prezentacja wyniku.
- **Backend (C# / ASP.NET Core)**:
  - endpointy HTTP dla frontendu,
  - walidacja wejścia,
  - wywołanie serwisu Pythona,
  - zwrot wyniku.
- **Serwis ML (Python / FastAPI)**:
  - pipeline CV + inferencja modelu,
  - solver,
  - generowanie overlay.

#### Kontrakty interfejsów (UI/CLI/API)
- **Frontend → Backend (C#)**: `POST /api/solve-from-image` — przyjmuje obraz, zwraca JSON + obraz wynikowy.
- **Backend (C#) → Serwis ML (Python)**: `POST /ml/solve-from-image` — przyjmuje obraz, zwraca wynik inferencji i rozwiązania.

#### Formaty danych i artefakty wyjściowe
- `recognized_grid: int[9][9]` (0 = puste)
- `solved_grid: int[9][9]`
- `overlay_image: base64/png` (lub URL do pliku)
- `warnings/errors: string[]` (jeśli pipeline niepewny lub przerwał)

### 12) Dane, trening i ewaluacja
- **Źródła danych**: publiczny dataset sudoku (np. z Kaggle) + ewentualnie MNIST/EMNIST.
- **Źródła obrazów wejściowych (demo/testy)**: dowolne zdjęcia użytkownika + zestaw przykładowy w `examples/` (np. własne zdjęcia/screeny) oraz/lub obrazy z datasetu (zgodnie z licencją).
- **Walidacja i dopasowanie datasetu**: dataset z Kaggle może być już „wyprostowany”/wycięty (albo mieć inne warunki niż zdjęcia z telefonu), więc przed treningiem sprawdzamy format, czyścimy błędne próbki i dopasowujemy preprocessing/augmentacje do danych z inferencji.
- **Preprocessing**:
  - standaryzacja obrazu cyfry do 28×28,
  - normalizacja pikseli do [0, 1],
  - augmentacje (rotacja ±10°, przesunięcie, kontrast, szum).
- **Metryki**:
  - accuracy (global),
  - precision/recall/F1 (per klasa i średnie),
  - confusion matrix.
- **Porównanie**: model własny vs transfer learning (jakość, czas treningu, czas inferencji, złożoność wdrożenia).

### 13) Ryzyka i sposoby ograniczenia
- **R1: siatka „wchodzi” w cyfrę** → ignorowanie marginesów komórki + morfologia do usuwania linii.
- **R2: cienie / nierówne światło** → adaptive threshold + wyrównanie kontrastu.
- **R3: różnice stylu cyfr (druk vs pismo)** → augmentacje + dotrenowanie na danych sudoku-like.
- **R4: błędne rozpoznanie powoduje brak rozwiązania** → (opcjonalnie) korekta gridu w UI + logika walidacji wejścia przed solverem.
- **R5: integracja C# ↔ Python (kontrakt/timeouty/błędy sieci)** → wersjonowanie endpointów, walidacja schematu wej./wyj., sensowne timeouty i logowanie.
- **R6: brak / niska jakość obrazów do demo (lub rozjazd domeny danych)** → przygotować i wersjonować `examples/` (różne warunki), jasno opisać zakres (drukowane vs ręczne), umożliwić korektę rozpoznanego gridu.
- **R7: rozjazd między danymi treningowymi (np. „czyste”/wyprostowane z Kaggle) a danymi z pipeline’u (siatka, perspektywa, blur)** → budować/uzupełniać trening o wycinki generowane własnym pipeline’em + augmentacje perspektywy/kontrastu/rozmycia i testować na `examples/`.

### 14) Kamienie milowe (propozycja)
- **M1**: pipeline OpenCV (wykrycie + warp + cięcie) + solver backtracking.
- **M2**: baseline ML (np. CNN na MNIST/EMNIST lub dataset sudoku) + inferencja na wycinkach.
- **M3**: end-to-end „solve-from-image” + overlay.
- **M4**: integracja usług (Python API + C# backend + UI) + raport ewaluacji + przygotowanie prezentacji.

### 15) Artefakty do oddania (deliverables)
- Repozytorium Git udostępnione prowadzącym.
- Struktura repo spełniająca minimalne wymagania (co najmniej: `src/`, `data/`, `README.md`, `requirements.txt`) + dodatkowe katalogi na frontend/backend.
- Skrypty: trening modelu, inferencja end-to-end.
- Modele/artefakty (np. plik modelu) lub instrukcja pobrania.
- Przykładowe obrazy wejściowe i wyniki (np. w `examples/`).
- Prezentacja 5–7 minut + demo działania.

