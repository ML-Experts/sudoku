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
Backlog jest podzielony na 4 obszary (strumienie prac):
- **Infrastruktura**: serwer/hosting, domena, SSL, reverse proxy, sieć i zabezpieczenia, uruchamianie usług, jakość, dokumentacja, powtarzalność (CI/CD — opcjonalnie).
- **Backend (C#)**: API dla frontendu + integracja z serwisem ML.
- **MachineLearning (Python)**: CV + inferencja + solver + render + ewaluacja.
- **Frontend (web)**: UI uploadu, prezentacja wyników, ewentualna korekta.

Uwaga organizacyjna:
- Żeby „zrealizować całość”, tworzymy historyjki również dla **Infrastruktury**.
- Poza Infrastrukturą historyjki grupujemy jako **UC-xx (Use Case)**. Jeśli FE nie ma sensu bez BE (lub bez ML) — to jest **jeden UC** z podziałem na: **FE / BE / ML**. Nie tworzymy osobnych „historyjek integracyjnych” — integracja jest wypadkową realizacji danego UC.

#### Infrastruktura
- **INF-01**: Jako zespół chcemy mieć powtarzalne uruchomienie projektu i spójną strukturę repo, aby szybko rozwijać wszystkie warstwy.
  - **AC**:
    - README zawiera instrukcję uruchomienia: Frontend + Backend + Serwis ML (Python).
    - Repo ma jasno opisane katalogi oraz minimalny zestaw danych/obrazów do demo (np. `examples/`).

- **INF-02**: Jako zespół chcemy uruchamiać cały system lokalnie jednym zestawem komend, aby łatwo robić demo i testy end-to-end.
  - **AC**:
    - Dostępny jest jeden „happy path” uruchomienia (np. `docker compose up` lub skrypty), który stawia Frontend + Backend + Serwis ML.
    - Konfiguracja (adresy usług, limity uploadu, timeouty) jest w zmiennych środowiskowych i opisana.

- **INF-03**: Jako zespół chcemy mieć środowisko serwerowe pod demo, aby projekt był dostępny pod domeną i działał stabilnie.
  - **AC**:
    - Jest przygotowany serwer (VM/VPS lub inny hosting) oraz uruchomione usługi: Frontend, Backend, Serwis ML.
    - Jest podpięta domena (DNS) oraz SSL (np. certyfikaty) i reverse proxy (np. Nginx/Caddy) kierujące ruch do właściwych usług.
    - Są ustawione podstawowe zabezpieczenia: firewall, ograniczenie rozmiaru uploadu, sensowne timeouty, logowanie błędów.

- **INF-04**: Jako zespół chcemy utrzymywać jakość kodu i przewidywalne standardy pracy, aby łatwiej współpracować.
  - **AC**:
    - Działa pre-commit lub ekwiwalent (formatowanie + lint) dla Pythona, a zasady są opisane.
    - Każdy członek zespołu ma min. 3 commity z opisowymi komunikatami.

- **INF-05 (opcjonalnie)**: Jako zespół chcemy mieć wspólne środowisko Jupyter na serwerze, aby łatwiej eksperymentować z danymi i prezentować wyniki.
  - **AC**:
    - Jest dostępny serwer Jupyter (np. JupyterLab) zabezpieczony (auth + HTTPS, ograniczenia dostępu).
    - Notebooki/artefakty są przechowywane w repo lub w uzgodnionym miejscu, a instrukcja pracy jest opisana.

- **INF-06 (opcjonalnie)**: Jako zespół chcemy mieć CI uruchamiane na PR, aby automatycznie pilnować jakości bez ręcznego odpalania.
  - **AC**:
    - Po otwarciu/aktualizacji PR uruchamia się pipeline: lint/test (Python), build (C#) oraz podstawowa walidacja frontendu.
    - Merge jest blokowany, jeśli checki nie przechodzą (polityka gałęzi / wymagane status checks).

- **INF-07 (opcjonalnie)**: Jako zespół chcemy mieć CD (deploy) po akceptacji PR/merge, aby paczka trafiała na serwer bez ręcznych kroków.
  - **AC**:
    - Po merge do ustalonej gałęzi powstaje paczka (artefakt) i jest wdrażana na serwer (np. restart usług/containers).
    - Sekrety/klucze są trzymane bezpiecznie (np. secrets w systemie CI), a proces jest odtwarzalny i opisany.

#### UC-01 — „Dodaj plik sudoku do przykładów (examples)”
- **FE**:
  - Formularz uploadu pliku (jpg/png) do biblioteki przykładów.
  - Informacja o powodzeniu/błędzie uploadu.
- **BE**:
  - Endpoint do uploadu przykładu (np. `POST /api/examples`) + walidacja typu/rozmiaru.
  - Zapis pliku i metadanych (nazwa, data, rozmiar, ewentualnie tagi) w magazynie.
- **ML**:
  - — (nie wymagane na tym etapie).
  - **AC**:
    - Plik po uploadzie jest dostępny na liście (UC-02) i możliwy do pobrania (UC-03).

#### UC-02 — „Lista dostępnych przykładów sudoku”
- **FE**:
  - Widok listy (nazwa, miniatura/ikona, data dodania, przyciski: pobierz / wybierz do przetworzenia).
- **BE**:
  - Endpoint listujący przykłady (np. `GET /api/examples`) zwracający metadane i identyfikatory.
- **ML**:
  - —.
  - **AC**:
    - Lista odzwierciedla stan magazynu plików i działa dla świeżo dodanych przykładów (UC-01).

#### UC-03 — „Pobierz wybrany plik przykładowy”
- **FE**:
  - Akcja „Pobierz” dla wybranego przykładu.
- **BE**:
  - Endpoint zwracający plik (np. `GET /api/examples/{id}/download`).
- **ML**:
  - —.
  - **AC**:
    - Pobierany plik jest identyczny z tym, który został dodany.

#### UC-04 — „Wybierz przykład do przetworzenia i wykonaj wstępną obróbkę”
- **FE**:
  - Akcja „Wybierz do rozwiązania” + podgląd wyniku wstępnej obróbki (np. wyprostowana plansza / siatka / status).
- **BE**:
  - Endpoint inicjujący wstępne przetwarzanie przykładu (np. `POST /api/examples/{id}/preprocess`) i zwracający wynik/stan.
  - Obsługa błędów (np. „nie wykryto planszy”).
- **ML**:
  - Pipeline CV „preprocess”: wykrycie planszy + korekcja perspektywy + (opcjonalnie) detekcja siatki/komórek.
  - **AC**:
    - System zwraca artefakt wstępnej obróbki (np. obraz po warp) albo czytelny błąd.

#### UC-05 — „Rozwiąż wybrany plik przez system”
- **FE**:
  - Akcja „Rozwiąż” + prezentacja wyniku: rozpoznany grid, rozwiązany grid, overlay.
- **BE**:
  - Endpoint rozwiązania dla przykładu (np. `POST /api/examples/{id}/solve`) albo reuse jednego endpointu solve z parametrami.
  - Przekazanie żądania do serwisu ML i zwrot odpowiedzi do FE.
- **ML**:
  - End-to-end: preprocess → rozpoznanie cyfr → grid → solver → overlay.
  - Zwracany kontrakt: `recognized_grid`, `solved_grid`, `overlay_image_base64` + `warnings/errors`.
  - **AC**:
    - Dla przykładowych obrazów system znajduje rozwiązanie lub zwraca czytelny błąd.

#### UC-06 — „Uruchom trening na dataset z data/raw”
- **FE**:
  - Widok uruchomienia treningu (wybór datasetu/konfiguracji, przycisk Start).
- **BE**:
  - Endpoint startujący trening (np. `POST /api/trainings`) i zwracający `training_id`.
  - Zapamiętanie konfiguracji treningu (parametry, dataset, commit/wersja).
- **ML**:
  - Job treningowy bazujący na `data/raw` → preprocessing → split train/val/test → trening.
  - Zapis artefaktów: model/checkpoint + metryki.
  - **AC**:
    - Trening tworzy wpis treningu widoczny w liście (UC-08).

#### UC-07 — „Pokazuj postęp treningu i informuj o zakończeniu”
- **FE**:
  - Ekran postępu (np. procent/epoki/ETA) + status końcowy (sukces/porażka).
- **BE**:
  - Endpoint statusu treningu (polling) lub stream (SSE/WebSocket) do FE.
- **ML**:
  - Raportowanie postępu (np. logi/metryki per epoka) w sposób możliwy do odczytu przez BE.
  - **AC**:
    - FE otrzymuje aktualizacje postępu i finalny status zakończenia.

#### UC-08 — „Lista treningów i wytrenowanych modeli”
- **FE**:
  - Widok listy treningów (status, data, krótki opis) oraz powiązanych modeli.
- **BE**:
  - Endpoint listujący treningi i modele (np. `GET /api/trainings`, `GET /api/models`).
- **ML**:
  - Dostarczenie metadanych treningów/modeli (ścieżki, wersje, metryki skrótowe).
  - **AC**:
    - Lista pokazuje zarówno zakończone, jak i trwające treningi.

#### UC-09 — „Szczegóły treningu i metryki”
- **FE**:
  - Widok szczegółów treningu (parametry, wykresy/metryki, confusion matrix).
- **BE**:
  - Endpoint szczegółów (np. `GET /api/trainings/{id}`) zwracający metryki i artefakty raportu.
- **ML**:
  - Generowanie i zapis metryk/raportu ewaluacyjnego (artefakty do pobrania).
  - **AC**:
    - Użytkownik widzi metryki wystarczające do porównania modeli (accuracy, precision/recall/F1, confusion matrix).

#### UC-10 — „Wybierz model na podstawie metryk i użyj go w inferencji”
- **FE**:
  - UI wyboru aktywnego modelu (np. dropdown: model + metryki skrótowe).
- **BE**:
  - Endpoint ustawienia aktywnego modelu (np. `PUT /api/models/active`) oraz użycie go przy UC-05.
- **ML**:
  - Mechanizm ładowania wskazanego modelu do inferencji (hot swap lub reload) i zwracanie informacji o wersji modelu.
  - **AC**:
    - Po zmianie aktywnego modelu kolejne rozwiązania (UC-05) używają nowego modelu.

#### UC-11 — „Dodaj własny dataset do uczenia”
- **FE**:
  - Upload datasetu (np. zip) + opis (źródło/licencja) + walidacja w UI.
- **BE**:
  - Endpoint uploadu datasetu (np. `POST /api/datasets`) + zapis do magazynu + rejestracja.
- **ML**:
  - Walidacja formatu datasetu + przygotowanie do użycia w treningu (wpięcie do `data/raw` lub równoważnego magazynu).
  - **AC**:
    - Dataset po dodaniu jest wybieralny przy uruchomieniu treningu (UC-06).

### 9) Wymagania niefunkcjonalne (NFR)
- **NFR-01 (reprodukowalność)**: trening i inferencja mają być uruchamialne skryptami/komendami opisanymi w README.
- **NFR-02 (czas odpowiedzi)**: inferencja „solve-from-image” powinna zakończyć się w rozsądnym czasie na CPU (np. < 5 s dla typowego obrazu) — cel orientacyjny.
- **NFR-03 (czytelność)**: kod podzielony na moduły (vision / ml / solver / render) oraz warstwę interfejsu (API + web UI).
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

#### Kontrakty interfejsów (UI/API)
- **Frontend → Backend (C#)**: `POST /api/solve-from-image` — przyjmuje obraz, zwraca JSON (kontrakt poniżej).
- **Backend (C#) → Serwis ML (Python)**: `POST /ml/solve-from-image` — przyjmuje obraz, zwraca JSON (ten sam kontrakt, bezpośrednio z ML).

##### Kontrakt odpowiedzi (prosty, jeden obiekt)
Backend i serwis ML zwracają jeden obiekt JSON:
- `recognized_grid: int[9][9]` (0 = puste)
- `solved_grid: int[9][9]` (0 jeśli brak/nie dotyczy)
- `overlay_image_base64: string` (PNG/JPEG w base64; może być pusty jeśli błąd)
- `warnings: string[]`
- `errors: string[]`

Uwaga: nie ma wymogu trwałego zapisywania `recognized_grid`/`solved_grid` do plików w `examples/`. Artefakty mogą być zapisywane opcjonalnie do debugowania/odtwarzania przypadków, ale oficjalnym kontraktem jest odpowiedź API.

#### Formaty danych i artefakty wyjściowe
- `recognized_grid: int[9][9]` (0 = puste)
- `solved_grid: int[9][9]`
- `overlay_image_base64: base64/png` (ew. alternatywnie URL do pliku)
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

