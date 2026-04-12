## PRD — Sudoku Vision (wariant ambitny: web + C# backend + Python ML)

### Metadane
- **Wersja**: 0.3
- **Data**: 2026-04-11
- **Autorzy**: (uzupełnijcie: imiona i role w zespole)
- **Repo / projekt**: `Sudoku Vision`

### 1) Streszczenie
Celem projektu jest zbudowanie aplikacji webowej, która potrafi przyjąć zdjęcie planszy Sudoku, rozpoznać układ cyfr z użyciem modelu ML (Python), rozwiązać łamigłówkę algorytmem (backtracking) i zwrócić użytkownikowi wynik jako: (1) macierz 9×9 oraz (2) obraz z naniesionym rozwiązaniem. System ma mieć architekturę wielowarstwową: frontend web → backend w C# → serwis ML/inferencji w Pythonie. Backend jest głównym punktem wejścia, orkiestratorem i właścicielem workflow systemu, a serwis ML jest wewnętrzną usługą specjalistyczną używaną przez backend.

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
- Rozbudowane uwierzytelnianie i autoryzacja użytkowników: konta, role, reset hasła, baza użytkowników, refresh tokeny, zewnętrzni providerzy tożsamości.
- Mobilna aplikacja natywna.
- Rozwiązywanie „najlepszego” rozwiązania (sudoku standardowo ma jedno; solver ma znaleźć poprawne).
- Generowanie obrazów przez model (nie jest wymagane; overlay robimy programowo).

Uwaga: w zakresie pozostaje wyłącznie prosta bramka administracyjna oparta o jedno współdzielone hasło i token zwracany przez Backend, potrzebna do ochrony przygotowania datasetów, uruchamiania treningów i podobnych operacji zapisu. Brak logowania nie blokuje ścieżki rozwiązywania sudoku; bez hasła użytkownik działa w ograniczonym trybie tylko do solve.

### 5) Użytkownicy i persony
- **P1: Student / prowadzący demo**: chce szybko pokazać działanie aplikacji na kilku zdjęciach.
- **P2: Użytkownik web**: chce wrzucić zdjęcie sudoku i dostać rozwiązanie z czytelną wizualizacją.
- **P3: Operator ML / członek zespołu**: chce zalogować się do prostego panelu administracyjnego, wybrać surowe pliki datasetu przygotowane wcześniej na serwerze, oczyścić dane, wykonać split i przygotować zestaw `.npz` do treningu.

### 6) Główne przepływy użytkownika (user journeys)
#### J1: „Rozwiąż z obrazka”
1. Użytkownik wchodzi na stronę i wgrywa zdjęcie sudoku.
2. System rozpoznaje planszę i cyfry, pokazuje wykryty stan jako grid 9×9.
3. (Opcjonalnie) Użytkownik poprawia błędnie rozpoznane pola.
4. Użytkownik klika „Rozwiąż”.
5. System zwraca rozwiązanie (grid + obraz z naniesionymi cyframi).

#### J2: „Odblokuj operacje administracyjne”
1. Po wejściu na stronę użytkownik widzi modal z polem hasła.
2. Użytkownik może podać współdzielone hasło administracyjne albo pominąć logowanie i przejść do ograniczonego trybu tylko do rozwiązywania sudoku.
3. Jeśli użytkownik poda hasło, Backend weryfikuje je i zwraca prosty token JSON.
4. Frontend zapisuje token w kontekście sesji i dołącza go do chronionych żądań.
5. Jeśli użytkownik pominie logowanie, funkcje administracyjne pozostają niedostępne, a aplikacja pozwala tylko na rozwiązywanie sudoku.

#### J3: „Dodaj i przygotuj dataset do uczenia”
1. Użytkownik loguje się przez prosty modal hasła.
2. Surowe pliki datasetu są wcześniej umieszczane na serwerze poza aplikacją (np. przez Jupyter), w skonfigurowanym katalogu `data/raw`, z rozdzieleniem na podfoldery `boards` i `digits`.
3. Backend skanuje katalog surowych danych, przegląda podfoldery `boards` i `digits`, automatycznie paruje pliki techniczne i pokazuje użytkownikowi listę logicznych rekordów datasetowych z polami `name` i `type` (`board` / `digit`), gdzie typ wynika z folderu źródłowego.
4. Użytkownik wybiera jeden lub wiele datasetów źródłowych, dla każdego wskazuje docelowe splity (`train`, `val`, `test`) albo wybiera tryb `mix`, a następnie nadaje nazwę wynikowemu zestawowi treningowemu.
5. Dla datasetów typu `board` Backend zleca ML ekstrakcję planszy, podział na siatkę 9×9 i oczyszczenie komórek; dla `digit` wczytywane są pary IDX-UBYTE i uruchamiana jest normalizacja do tego samego wspólnego formatu próbek.
6. Niezależnie od typu i liczby wybranych źródeł system scala wynik przetwarzania do jednego wspólnego zestawu, tworzy docelowe partycje `train` / `val` / `test`, zapisuje gotowy artefakt jako pojedynczy plik `{name}.npz` w katalogu `data/processed` i dołącza raport z przetwarzania.
7. Przygotowany zestaw `.npz` staje się dostępny do późniejszego treningu i ewaluacji.

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
- **FR-11**: System umożliwia uruchamianie eksperymentów treningowych z wyborem architektury modelu, zbioru/zbiorów danych, trybu treningu oraz profilu preprocessingu i augmentacji.
- **FR-12**: System zapisuje konfigurację treningu, politykę splitu i wyniki ewaluacji tak, aby możliwe było porównanie modeli na wspólnym benchmarku.
- **FR-13**: System udostępnia prosty mechanizm logowania administracyjnego: jedno hasło weryfikowane po stronie Backendu i token JSON zwracany do Frontendu.
- **FR-14**: System chroni wybrane operacje zapisu i administracyjne (co najmniej pobranie listy surowych datasetów, przygotowanie zestawu `.npz` oraz uruchomienie treningu) przez wymóg poprawnego tokenu; bez tokenu użytkownik ma dostęp wyłącznie do ścieżki rozwiązywania sudoku.
- **FR-15**: System skanuje skonfigurowany katalog surowych datasetów (np. produkcyjnie `/opt/sudoku/shared/data/raw`) oraz dwa skonfigurowane podfoldery `boards` i `digits`, i buduje listę logicznych kandydatów datasetowych widoczną w UI.
- **FR-16**: System obsługuje dwa techniczne formaty wejściowe datasetu: `board` (archiwum `.zip` zawierające pary plików `.jpg` + `.data` o wspólnej nazwie, wykrywane w folderze `boards`) oraz `digit` (pary plików `*.idx3-ubyte` + `*.idx1-ubyte` o wspólnym prefiksie, wykrywane w folderze `digits`).
- **FR-17**: System automatycznie paruje pliki techniczne należące do jednego datasetu i prezentuje użytkownikowi listę rekordów logicznych z polami `name` i `type`, bez konieczności ręcznego myślenia o rozszerzeniach; `type` wynika z folderu źródłowego, a nie z heurystyki zawartości pliku.
- **FR-18**: Użytkownik może wskazać dla każdego wybranego datasetu jeden lub wiele jawnych splitów spośród `train`, `val`, `test` albo wybrać tryb `mix`; `mix` jest wyborem wykluczającym pozostałe opcje dla tego samego źródła.
- **FR-19**: System pozwala nadać nazwę tworzonemu zestawowi treningowemu, przyjmuje listę wybranych źródeł datasetowych z ich `splits` i zapisuje wynik całego żądania jako jeden plik `{name}.npz` w skonfigurowanym katalogu danych przetworzonych (np. produkcyjnie `/opt/sudoku/shared/data/processed`).
- **FR-20**: Dla datasetu typu `board` system parsuje etykiety planszy, dzieli obraz na siatkę 9×9 i oczyszcza każdą komórkę wspólnym pipeline'em ML obejmującym co najmniej binaryzację, wyostrzenie, konwersję do czarno-białego / grayscale, centrowanie i zmianę rozmiaru do 28×28.
- **FR-21**: Dla datasetu typu `digit` system wczytuje pary IDX-UBYTE i normalizuje próbki do tego samego kanonicznego formatu treningowego, który jest używany także dla komórek wyciętych z `board`.
- **FR-22**: Typ wejściowy (`board` / `digit`) wpływa wyłącznie na ścieżkę wczytania i ekstrakcji próbek; końcowy artefakt biznesowy pozostaje jeden wspólny plik `.npz` dla całego żądania przygotowania datasetu.
- **FR-23**: Dla wyboru `mix` system wykonuje automatyczny split do `train` / `val` / `test` zgodnie z polityką projektu; dla jawnego wyboru jednego lub wielu splitów zapisuje dane do wskazanych partycji bez dublowania tej samej próbki między splitami.
- **FR-24**: System udostępnia listę przygotowanych zestawów `.npz` oraz listę wpisów rejestru modeli z capability do treningu i/lub inferencji, aby użytkownik mógł uruchomić trening i później wybrać aktywny model.
- **FR-25**: System uruchamia trening na podstawie wybranego modelu z rejestru i wybranego zestawu `.npz`, utrzymuje dokładnie jeden aktywny run jednocześnie, pozwala anulować aktywny run, publikuje postęp przez kanał `SignalR` po stronie Backendu zasilany zdarzeniami z `ML`, a po zakończeniu zapisuje model wynikowy jako nowy wpis rejestru oraz raport treningu. Brakujący albo uszkodzony raport nie unieważnia automatycznie modelu, jeśli artefakty inferencyjne są kompletne.
- **FR-26**: Rejestr modeli jest utrzymywany jako katalog `models/registry`, gdzie każdy wpis modelu jest osobnym katalogiem `{modelName}` zawierającym obowiązkowy manifest `model.json` oraz katalog `artifacts/` z artefaktami technicznymi modelu.
- **FR-27**: System obsługuje model bootstrap dodany ręcznie do rejestru bez powiązanego `runName`; taki wpis nadal musi mieć pełny manifest `model.json` i może zostać użyty jako model bazowy do treningu albo jako aktywny model inferencyjny.
- **FR-28**: System utrzymuje aktywny model inferencyjny przez lekki plik wskaźnikowy w `models/active` (np. `inference.json`) wskazujący wpis z `models/registry`, bez kopiowania całego katalogu modelu przy każdym przełączeniu.
- **FR-29**: System zapisuje relację między runem treningowym, modelem wynikowym i raportami tak, aby można było odtworzyć pochodzenie modelu oraz porównać wyniki na wspólnym benchmarku.

### 8) Historyjki (User Stories) + kryteria akceptacji
Backlog jest podzielony na 4 obszary (strumienie prac):
- **Infrastruktura**: serwer/hosting, domena, SSL, reverse proxy, sieć i zabezpieczenia, uruchamianie usług, jakość, dokumentacja, powtarzalność (CI/CD — opcjonalnie).
- **Backend (C#)**: API dla frontendu + integracja z serwisem ML.
- **MachineLearning (Python)**: CV + inferencja + solver + render + ewaluacja.
- **Frontend (web)**: UI uploadu, prezentacja wyników, ewentualna korekta.

Uwaga organizacyjna:
- Żeby „zrealizować całość”, tworzymy historyjki również dla **Infrastruktury**.
- Poza Infrastrukturą historyjki grupujemy jako **UC-xx (Use Case)**. Jeśli FE nie ma sensu bez BE (lub bez ML) — to jest **jeden UC** z podziałem na: **FE / BE / ML**. Nie tworzymy osobnych „historyjek integracyjnych” — integracja jest wypadkową realizacji danego UC.
- W obszarze **ML** część prac może mieć charakter techniczny lub eksperymentalny (np. warianty treningu, augmentacje, transfer learning) i być realizowana jako subtaski / eksperymenty w ramach `UC-06`, `UC-09` i `UC-10`, a nie jako osobne user stories użytkownika końcowego.
- Wyjątkiem organizacyjnym jest prosty bootstrapowy `UC-00`, którego celem jest szybkie sprawdzenie połączenia `FE -> BE -> ML` przed rozwijaniem pełnych funkcji produktu.
- **Backend (C#)** jest systemem głównym i `source of truth` dla workflow, statusów procesów, aktywnego modelu oraz rekordów udostępnianych FE.
- **Serwis ML (Python)** jest wewnętrzną usługą wykonywaną przez Backend; pozostaje możliwie stateless i nie utrzymuje niezależnego źródła prawdy dla datasetów, treningów ani modeli.

#### Infrastruktura
- **INF-01**: Jako zespół chcemy mieć powtarzalne uruchomienie projektu i spójną strukturę repo, aby szybko rozwijać wszystkie warstwy.
  - **AC**:
    - README zawiera instrukcję uruchomienia: Frontend + Backend + Serwis ML (Python).
    - Repo ma jasno opisane katalogi oraz minimalny zestaw danych/obrazów do demo (np. `examples/`).

- **INF-02**: Jako zespół chcemy uruchamiać cały system lokalnie jednym zestawem komend, aby łatwo robić demo i testy end-to-end.
  - **AC**:
    - Dostępny jest jeden „happy path” uruchomienia (np. `docker compose up` lub skrypty), który stawia Frontend + Backend + Serwis ML.
    - Konfiguracja środowiskowa (adresy usług, limity uploadu, timeouty, ścieżki do `data`, `examples`, `models`, `benchmark`, `tmp`) jest poza kodem i opisana.
    - Backend korzysta z `appsettings*.json` z override przez zmienne środowiskowe, a serwis ML z `.env` / zmiennych środowiskowych; ścieżki i URL-e nie są hardcodowane w kodzie.

- **INF-03**: Jako zespół chcemy mieć środowisko serwerowe pod demo, aby projekt był dostępny pod domeną i działał stabilnie.
  - **AC**:
    - Jest przygotowany serwer (VM/VPS lub inny hosting) oraz uruchomione usługi: Frontend, Backend, Serwis ML.
    - Jest podpięta domena (DNS) oraz SSL (np. certyfikaty) i reverse proxy (np. Nginx/Caddy) kierujące ruch do właściwych usług.
    - Są ustawione podstawowe zabezpieczenia: firewall, ograniczenie rozmiaru uploadu, sensowne timeouty, logowanie błędów.
    - Jest przygotowany uzgodniony layout systemowy katalogów (np. `/opt/sudoku`, `/var/www/sudoku/fe`, `/etc/sudoku`, `/var/log/sudoku`) lub jego równoważnik.
    - Podstawowa konfiguracja release (`appsettings.json`, `appsettings.{Environment}.json`, `.env`, `.env.{Environment}` dla środowisk współdzielonych) jest wersjonowana i dostarczana w release, a sekrety oraz ewentualne lokalne override'y developerskie są dostarczane bezpiecznie poza kodem lub przez CI/CD.

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

- **INF-07**: Jako zespół chcemy mieć CD (deploy) po akceptacji PR/merge, aby zmiany trafiały na serwer bez ręcznych kroków.
  - **AC**:
    - Po merge zaakceptowanego PR z gałęzi `dev` do `main` uruchamia się workflow CD wdrażający aplikację na serwer.
    - Workflow potrafi reagować na zmiany w odpowiednich katalogach usług (np. Frontend / Backend / ML) i wykonać właściwy deploy całości lub wybranej warstwy.
    - Deploy wykorzystuje repozytorium Git na serwerze (np. `git pull` / checkout właściwej gałęzi lub rewizji) oraz restart odpowiednich usług / kontenerów.
    - Workflow korzysta z wcześniej przygotowanego środowiska serwerowego opisanego w `INF-03` oraz z ustalonej konfiguracji wdrożeniowej po stronie serwera.
    - Workflow wdrożeniowy i aplikacje korzystają z konfigurowalnych ścieżek oraz ustawień środowiskowych; deploy nie zakłada hardcodowanych lokalizacji danych w kodzie.
    - Workflow backendu generuje `appsettings.production.json` z dokładnymi, absolutnymi ścieżkami runtime do katalogów używanych przez workflow datasetów, co najmniej do folderów `boards`, `digits`, `processed` i `tmp/datasets`; analogicznie `appsettings.local.json` również przechowuje dokładne, absolutne ścieżki dla środowiska lokalnego.
    - Konfiguracja uruchomieniowa serwera dla backendu wskazuje środowisko `production` przez `SUDOKU_ENVIRONMENT=production`, tak aby runtime załadował overlay `appsettings.production.json`.
    - Sekrety/klucze są trzymane bezpiecznie (np. secrets w systemie CI), a proces jest odtwarzalny i opisany.

- **INF-08**: Jako zespół chcemy mieć bootstrap rejestru modeli i opisany standard manifestów, aby można było bez bazy danych dodać pierwszy model bazowy, kolejne modele po treningu oraz bezpiecznie przełączać model aktywny.
  - **AC**:
    - Jest opisany wzór `models/registry/{modelName}/model.json` oraz minimalny layout `artifacts/` dla wpisu modelu.
    - Jest opisana procedura dodania modelu bootstrap bez powiązanego `runName`, z `sourceType = bootstrap`.
    - Jest opisane, które pliki tworzy `BE`, które `ML`, a które proces operacyjny / deploy.
    - Aktywny model inferencyjny jest wskazywany przez `models/active/inference.json`, a nie przez kopiowanie całego modelu do `models/active`.
    - Opisane są wyjątki: model bootstrap bez `trainings/*`, wpis archiwalny lub niekompatybilny z `canStartTraining = false` i/lub `canUseForInference = false`.

#### UC-00 — „Sprawdź połączenie FE → BE → ML (ping-pong / smoke test)”
- **FE**:
  - Prosty widok lub przycisk „Test połączenia”, który wywołuje żądanie do backendu i prezentuje wynik.
  - Czytelna informacja o sukcesie albo błędzie z wskazaniem, na której warstwie wystąpił problem.
- **BE**:
  - Endpoint testowy (np. `GET /api/ping` albo `POST /api/ping`) przyjmujący żądanie z FE i przekazujący je do serwisu ML.
  - Zwrot ustrukturyzowanej odpowiedzi zawierającej status backendu, status serwisu ML i ewentualnie podstawowe metadane (np. wersję / timestamp).
- **ML**:
  - Prosty endpoint testowy (np. `GET /ml/ping`) zwracający odpowiedź techniczną bez uruchamiania pełnego pipeline’u rozpoznawania Sudoku.
  - Odpowiedź umożliwia potwierdzenie, że serwis ML jest osiągalny i poprawnie odpowiada na wywołanie z backendu.
  - **AC**:
    - Użytkownik z poziomu FE może uruchomić test i otrzymać potwierdzenie działania pełnej ścieżki `FE -> BE -> ML`.
    - W przypadku błędu system zwraca czytelną informację diagnostyczną, czy problem dotyczy FE, BE czy ML.
    - Historyjka może służyć jako smoke test po wdrożeniu na serwer lub po zmianach integracyjnych.

#### UC-01 — „Dodaj plik sudoku do przykładów (examples)”
- **FE**:
  - Formularz uploadu pliku (jpg/png) do biblioteki przykładów.
  - Informacja o powodzeniu/błędzie uploadu.
- **BE**:
  - Endpoint do uploadu przykładu `POST /api/examples` + walidacja typu/rozmiaru.
  - Zapis pliku w magazynie pod kanoniczną nazwą `name` oraz zwrot podstawowych metadanych pliku (`name`, `contentType`, `sizeBytes`, `storedAtUtc`).
- **ML**:
  - — (nie wymagane na tym etapie).
  - **AC**:
    - Plik po uploadzie jest dostępny na liście (UC-02), możliwy do pobrania (UC-03) i użycia w preprocessingu (UC-04).

#### UC-02 — „Lista dostępnych przykładów sudoku”
- **FE**:
  - Widok listy (nazwa, miniatura/ikona, data dodania, przyciski: pobierz / wybierz do przetworzenia).
- **BE**:
  - Endpoint `GET /api/examples` zwracający listę plików przykładowych i ich podstawowe metadane (`name`, `contentType`, `sizeBytes`, `storedAtUtc`).
  - Źródłem danych dla listy jest magazyn plików `examples`, bez dodatkowego trwałego rejestru rekordów examples.
- **ML**:
  - —.
  - **AC**:
    - Lista odzwierciedla stan magazynu plików i działa dla świeżo dodanych przykładów (UC-01).

#### UC-03 — „Pobierz wybrany plik przykładowy”
- **FE**:
  - Akcja „Pobierz” dla wybranego przykładu.
- **BE**:
  - Endpoint zwracający plik `GET /api/examples/{name}/download`.
- **ML**:
  - —.
  - **AC**:
    - Pobierany plik jest identyczny z tym, który został dodany.

#### UC-04 — „Wybierz przykład do przetworzenia i wykonaj wstępną obróbkę”
- **FE**:
  - Pobranie wybranego obrazu przykładowego do podglądu przez `GET /api/examples/{name}`.
  - Akcja „Wykryj planszę”, która uruchamia etap 1 preprocessingu i prezentuje obraz po korekcji perspektywy.
  - Akcja „Podziel na siatkę 9x9”, która wysyła do backendu obraz z etapu 1 i prezentuje wynik jako tablicę 9×9 obrazów komórek.
- **BE**:
  - `GET /api/examples/{name}` — zwraca wybrany obraz przykładowy jako `ImageApiResponse`.
  - `PUT /api/examples/{name}/preprocess/board` — uruchamia etap 1 preprocessingu i zwraca `ImageApiResponse`.
  - `PUT /api/examples/preprocess/cells` — przyjmuje `ImageApiEntry` z etapu 1 i zwraca `CellsGridApiResponse`.
  - Odpowiedzi błędów zwracają `errorType` i `message` oraz korzystają z czytelnych statusów HTTP.
- **ML**:
  - `PUT /ml/preprocess/board` — wykrycie planszy i korekcja perspektywy; wynik zwracany do BE jako `ImageApiResponse`.
  - `PUT /ml/preprocess/cells` — podział obrazu planszy na siatkę 9×9; wynik zwracany do BE jako `CellsGridApiResponse`.
  - Wyniki preprocessingu nie są trwale zapisywane; ML zwraca wynik bezpośrednio do BE, a następnie do FE.
  - Ten UC dotyczy preprocessingu planszy w ścieżce inferencji użytkownika (runtime `end-to-end`), a nie augmentacji danych treningowych.
  - **AC**:
    - Użytkownik może pobrać wybrany obraz do podglądu.
    - System zwraca obraz po korekcji perspektywy albo czytelny błąd.
    - System zwraca planszę podzieloną na siatkę 9×9 komórek albo czytelny błąd.

#### UC-05 — „Rozwiąż wybrany plik przez system”
- **FE**:
  - Akcja „Rozwiąż” + prezentacja wyniku: rozpoznany grid, rozwiązany grid, overlay.
- **BE**:
  - Endpoint rozwiązania dla przykładu (np. `POST /api/examples/{name}/solve`) albo reuse jednego endpointu solve z parametrami.
  - Przekazanie żądania do serwisu ML i zwrot odpowiedzi do FE.
- **ML**:
  - End-to-end: preprocess → rozpoznanie cyfr → grid → solver → overlay.
  - Zwracany kontrakt: `recognized_grid`, `solved_grid`, `overlay_image_base64` + `warnings/errors`.
  - **AC**:
    - Dla przykładowych obrazów system znajduje rozwiązanie lub zwraca czytelny błąd.

#### UC-06 — „Uruchom trening na przygotowanym zestawie `.npz`”
- **FE**:
  - Widok uruchomienia treningu z wyborem wpisu modelu bazowego z rejestru oraz gotowego zestawu `.npz` z katalogu `data/processed`, z przyciskiem Start oraz możliwością przejścia do anulowania aktywnego runu.
  - Po wejściu na ekran system najpierw pozwala odzyskać monitoring już istniejącego aktywnego runu, bez zgadywania jego `runName`.
  - UI pokazuje logiczne metadane wpisu rejestru, np. `sourceType`, `trainingMode`, `inputProfile`, bez eksponowania ścieżek systemowych ani nazw technicznych plików artefaktów; `trainingMode` na liście modeli opisuje istniejący wpis rejestru, a nie parametr nowego startu.
  - Po starcie treningu `FE` otrzymuje `runName`, które jest identyfikatorem runu widocznym później w ścieżkach `GET /api/trainings/{runName}` oraz `/ws/trainings/{runName}`, i od razu przechodzi do monitoringu runu przez kanał `SignalR`.
  - Zakres `UC-06` obejmuje także odzyskanie aktywnego runu, monitoring kanału postępu i kooperacyjne anulowanie; późniejszy `UC-07` rozwija widok postępu, ale nie zmienia kontraktów transportowych ani identyfikatorów.
- **BE**:
  - Endpoint startujący trening (np. `POST /api/trainings`) i zwracający `runName`, czyli nazwę plikowego rekordu i katalogu runu, a nie sztuczne `training_id` z bazy danych.
  - Endpoint lekkiego odczytu aktywnego runu (np. `GET /api/trainings/active`) zwracający bieżący run albo pusty wynik, tak aby `FE` mogło wejść z powrotem w monitoring po odświeżeniu strony albo po `409`.
  - Endpoint anulowania aktywnego runu (np. `POST /api/trainings/{runName}/cancel`) jest kooperacyjny, idempotentny i dla uproszczenia zawsze zwraca `202 Accepted`; odpowiedź zwraca jednak rzeczywisty bieżący `status` dopasowanego runu albo `null` przy braku dopasowania oraz `requestDisposition`, tak aby `FE` wiedziało, czy anulowanie zostało właśnie przyjęte, było duplikatem czy było no-opem dla runu już zakończonego albo niepasującego do żadnego znanego aktywnego runu.
  - Po końcowym `cancelled` Backend zachowuje `trainings/metadata/{runName}.json` ze statusem `cancelled`, ale czyści techniczne artefakty runtime runu z `trainings/runs`, `trainings/reports`, katalogu tymczasowego i częściowo utworzonego katalogu modelu wynikowego.
  - Po końcowym `failed` Backend zachowuje `trainings/metadata/{runName}.json` ze statusem `failed`, ale czyści techniczne artefakty runtime runu analogicznie do `cancelled`; stan `failed` jest zarezerwowany dla przypadków, w których model wynikowy nie nadaje się do inferencji albo workflow nie dał się poprawnie domknąć.
  - Endpointy listujące wpisy rejestru modeli i przygotowane zestawy `.npz` dostępne do treningu; źródłem listy modeli jest wyłącznie skan `models/registry/*/model.json`.
  - Utworzenie plikowego rekordu treningu / eksperymentu (np. `trainings/metadata/{runName}.json`) i zapamiętanie pełnej konfiguracji (model bazowy, zestaw `.npz`, seed, profil treningu, profil augmentacji, `sourceRevision` / commit / wersja); w `MVP` pole `sourceRevision` istnieje, ale przyjmuje wartość `null`, a później może zostać podpięte pod wersję kodu lub konfiguracji. Rekord przechowuje także status, `producedModelName` oraz referencje do artefaktów potrzebnych UI.
  - Wsparcie zarówno dla wpisów bootstrap bez historii `trainings/*`, jak i dla modeli wcześniej wytrenowanych w systemie.
  - W `MVP` `BE` rozwiązuje konfigurację runu po swojej stronie; `FE` wysyła tylko `baseModelName` i `processedDatasetName`, a `trainingMode` jest przypisywane jako `fineTuning`.
  - W `MVP` `trainingProfileName`, `augmentationProfileName`, `benchmarkName` i `seed` są rozwiązywane przez `BE` na podstawie własnej polityki i `appsettings.{environment}.json`; profile nie są dziedziczone z modelu bazowego i nie są jeszcze podawane przez użytkownika.
  - W `MVP` system wspiera dokładnie jeden preset treningowy i jeden preset augmentacji po stronie `BE`; `FE` nie pobiera katalogu presetów i nie przekazuje żadnych identyfikatorów presetów w `POST /api/trainings`.
  - Jeśli start do `ML` nie zostanie potwierdzony, zanim `BE` odpowie do `FE`, `BE` robi rollback prowizorycznego rekordu runu; przy synchronicznym błędzie walidacyjnym albo kontraktowym z `ML` przepuszcza ten sam kod i body, a dla niedostępności albo timeoutu zwraca `503` albo `504`.
  - W MVP zgodność modelu bazowego z datasetem oznacza dokładną równość `inputProfile` wpisu rejestru i `preprocessingProfile` gotowego zestawu `.npz`; walidację wykonuje `BE` przed wywołaniem `ML`.
  - Po zestawieniu albo odtworzeniu kanału `SignalR` Backend wysyła `snapshot` będący aktualnym publicznym stanem runu znanym przez `BE`; jeśli run zdążył się już zakończyć, `snapshot` może być terminalny i po jego dostarczeniu kanał nie musi pozostawać otwarty.
- **ML**:
  - Job treningowy bazujący na jednym przygotowanym artefakcie `.npz`; preprocessing i split są wykonane wcześniej podczas przygotowania datasetu.
  - Trening wykorzystuje wpis modelu bazowego wskazany przez Backend przez jego manifest i główny artefakt oraz zapisuje końcowe artefakty modelu do docelowego katalogu `models/registry/{producedModelName}/artifacts`, a checkpointy oraz raport treningu do skonfigurowanych katalogów `trainings/*` i `tmp`.
  - Finalna ewaluacja porównawcza modeli odbywa się na wspólnym, stałym benchmarku / secie testowym Sudoku.
  - Zapis artefaktów technicznych (model/checkpoint + metryki + raporty) odbywa się wyłącznie w skonfigurowanych katalogach systemowych; `BE` przekazuje `ML` resolved ścieżki wejścia i wyjścia, a `ML` raportuje wynik i referencje do Backendu potrzebne do finalizacji `model.json`.
  - `ML` raportuje postęp, anulowanie i stan końcowy do `BE` przez wewnętrzny endpoint statusowy; `FE` nie łączy się z `ML` bezpośrednio.
  - Końcowy event `completed`, `failed` albo `cancelled` jest dostarczany do `BE` niezawodnie: `ML` powtarza wysyłkę tego samego eventu z tym samym `sequence` aż do otrzymania odpowiedzi `2xx`, a `BE` przyjmuje takie ponowienia idempotentnie.
  - Jeśli jedynym problemem końcowym jest brakujący albo uszkodzony raport, ale artefakty modelu są kompletne i model nadaje się do inferencji, `ML` raportuje `completed` z ostrzeżeniem i `reportStatus = missing | corrupted`, a nie `failed`.
  - **AC**:
    - Użytkownik może uruchomić trening przez wybór dokładnie jednego wpisu modelu bazowego z rejestru i jednego przygotowanego zestawu `.npz`.
    - Model bootstrap może zostać wybrany do treningu, jeśli jego manifest ma `canStartTraining = true`, mimo braku własnego `runName`.
    - System dopuszcza tylko jeden aktywny run jednocześnie; drugi start nie tworzy kolejki.
    - Jeśli drugi start trafi na już istniejący aktywny run, `FE` może odzyskać jego dane przez endpoint aktywnego runu i przejść do monitoringu.
    - Aktywny run może zostać anulowany i dopiero wtedy można uruchomić kolejny run.
    - W `MVP` `FE` nie parametryzuje presetów treningowych; system używa jednego stałego presetu treningowego i jednego stałego presetu augmentacji rozwiązywanych po stronie `BE`.
    - Po anulowaniu system zachowuje `trainings/metadata/{runName}.json` ze statusem `cancelled`, ale usuwa techniczne artefakty runtime tego runu.
    - Po `failed` system zachowuje `trainings/metadata/{runName}.json` ze statusem `failed`, ale usuwa techniczne artefakty runtime tego runu analogicznie do `cancelled`.
    - Run tworzy wpis treningu widoczny w liście (UC-08), a run zakończony sukcesem tworzy dodatkowo docelowy wpis modelu wynikowego w rejestrze.
    - Utrata połączenia `SignalR` między `FE` i `BE` nie zatrzymuje runu.
    - Po reconnect albo późnym podłączeniu do kanału `SignalR` `FE` dostaje `snapshot` aktualnego publicznego stanu runu z `BE`; jeśli run jest już zakończony, `snapshot` może być terminalny.
    - Jeśli raport końcowy jest uszkodzony albo brakujący, ale artefakty modelu są kompletne, model nadal może zostać użyty do inferencji przy czytelnym ostrzeżeniu o raporcie.
    - Jeśli raport końcowy jest uszkodzony albo brakujący, ale artefakty modelu są kompletne, run kończy się sukcesem z ostrzeżeniem, a nie statusem `failed`.
    - Końcowy stan runu nie może zostać utracony wyłącznie przez chwilowy problem transportowy `ML -> BE`; końcowy event jest powtarzany przez `ML` aż do potwierdzenia zapisu po stronie `BE`.
    - Dla zakończonego treningu dostępna jest pełna konfiguracja eksperymentu i relacja `run -> producedModelName -> reports`, potrzebna do późniejszego porównania wyników.

#### UC-07 — „Pokazuj postęp treningu i informuj o zakończeniu”
- **FE**:
  - Ekran postępu (np. procent/epoki/ETA) + status końcowy (sukces/porażka), aktualizowany w czasie rzeczywistym przez `SignalR`, z opcją anulowania aktywnego runu.
- **BE**:
  - Kanał `SignalR` do `FE` publikujący zdarzenia postępu treningu i status końcowy.
  - Po zestawieniu połączenia kanał zwraca snapshot aktualnego stanu runu, a kolejne eventy pochodzą z eventów `ML` zapisanych wcześniej w rekordzie `BE`; `FE` renderuje najświeższy stan i może ignorować spóźnione eventy z niższym `sequence`, bez oczekiwania na kompletność numeracji.
- **ML**:
  - Raportowanie postępu (np. logi/metryki per epoka), anulowania i stanu końcowego do `BE` w sposób możliwy do odczytu przez Backend.
  - **AC**:
    - FE otrzymuje aktualizacje postępu i finalny status zakończenia przez `SignalR`.
    - Zerwanie połączenia `SignalR` nie zatrzymuje runu; po reconnect `FE` może odtworzyć stan z kanału albo z endpointu szczegółów runu.

#### UC-08 — „Lista treningów i wytrenowanych modeli”
- **FE**:
  - Widok listy treningów (status, data, krótki opis: model / dataset / tryb treningu) oraz powiązanych modeli, w tym wpisów bootstrap i modeli wytrenowanych w systemie.
- **BE**:
  - Endpoint listujący treningi i modele (np. `GET /api/trainings`, `GET /api/models/registry`) na podstawie rekordów systemowych utrzymywanych przez Backend oraz manifestów modeli w rejestrze.
- **ML**:
  - Dostarczenie skróconych danych technicznych lub referencji do artefaktów potrzebnych do aktualizacji rekordów widocznych w Backendzie.
  - **AC**:
    - Lista pokazuje zarówno zakończone, jak i trwające treningi.
    - Lista modeli potrafi pokazać także wpis bootstrap bez powiązanego `runName`.

#### UC-09 — „Szczegóły treningu i metryki”
- **FE**:
  - Widok szczegółów treningu (parametry, datasety źródłowe, profil preprocessingu/augmentacji, wykresy/metryki, confusion matrix) wraz z referencją do modelu wynikowego i modelu bazowego.
- **BE**:
  - Endpoint szczegółów (np. `GET /api/trainings/{runName}`) zwracający konfigurację treningu, status, metryki, `producedModelName`, `baseModelName`, `parentModelName` / `sourceRunName` jeśli istnieją, oraz referencje do artefaktów raportu.
- **ML**:
  - Generowanie i zapis metryk/raportu ewaluacyjnego (artefakty do pobrania) oraz danych potrzebnych do porównania treningów na wspólnym benchmarku.
  - **AC**:
    - Użytkownik widzi metryki i konfigurację wystarczające do porównania modeli (accuracy, precision/recall/F1, confusion matrix, użyty benchmark).

#### UC-10 — „Wybierz aktywny model na podstawie metryk i użyj go w inferencji”
- **FE**:
  - UI wyboru aktywnego modelu do inferencji (np. dropdown: model + metryki skrótowe).
- **BE**:
  - Endpoint ustawienia aktywnego modelu (np. `PUT /api/models/active`) aktualizujący plik wskaźnikowy `models/active/inference.json`, a następnie użycie wskazanego modelu przy UC-05.
- **ML**:
  - Mechanizm ładowania do inferencji modelu wskazanego przez Backend w `models/active/inference.json` (hot swap lub reload) i zwracanie informacji o wersji modelu.
  - **AC**:
    - Po zmianie aktywnego modelu kolejne rozwiązania (UC-05) używają nowego modelu.
    - Przełączenie aktywnego modelu nie kopiuje całego katalogu modelu; zmienia wyłącznie wskaźnik i wymusza reload po stronie `ML`.

#### UC-11 — „Wyświetl dostępne surowe datasety”
- **FE**:
  - Widok administracyjny pokazujący listę datasetów wykrytych w katalogu `data/raw`, bez ręcznego uploadu przez aplikację.
  - Użytkownik widzi listę logicznych rekordów datasetów, np. `[{ "name": "Plansze", "type": "board" }, { "name": "t10k", "type": "digit" }]`, bez konieczności ręcznego myślenia o rozszerzeniach technicznych.
  - Widok listy datasetów jest dostępny tylko po uzyskaniu tokenu z prostego logowania (UC-13).
- **BE**:
  - Chroniony endpoint listujący surowe datasety (np. `GET /api/datasets/raw-candidates`) przez skan skonfigurowanego katalogu oraz automatyczne parowanie plików technicznych.
  - Skan katalogu `data/raw`, przegląd dwóch skonfigurowanych podfolderów `boards` i `digits`, rozpoznanie kandydatów typu `board` i `digit` na podstawie folderu źródłowego oraz budowa publicznej listy rekordów logicznych.
  - Weryfikacja tokenu administracyjnego dla odczytu listy kandydatów.
- **ML**:
  - — (`UC-11` nie angażuje usług ML; listowanie kandydatów i parowanie plików technicznych realizuje Backend.)
  - **AC**:
    - Po zalogowaniu użytkownik może pobrać i zobaczyć listę datasetów wykrytych automatycznie w `data/raw`.
    - System rozpoznaje, czy źródło reprezentuje pełne plansze (`board`) czy pojedyncze cyfry (`digit`) na podstawie tego, czy rekord pochodzi z folderu `boards`, czy z folderu `digits`.
    - Użytkownik nie musi ręcznie parować plików technicznych ani znać rozszerzeń wejściowych.
    - Bez poprawnego tokenu administracyjnego lista datasetów nie jest dostępna.

#### UC-12 — „Zarządzaj przygotowaniem zestawu treningowego `.npz`”
- **FE**:
  - Widok administracyjny wykorzystujący kandydatów z `UC-11`, pozwalający wybrać źródła, wskazać splity `train` / `val` / `test` albo `mix`, podać nazwę zestawu i wysłać żądanie przygotowania.
  - Po sukcesie użytkownik widzi raport przygotowania (`sampleCounts`, ostrzeżenia) i może odświeżyć listę gotowych zestawów `.npz`.
- **BE**:
  - Chroniony endpoint przygotowania zestawu (np. `POST /api/datasets/processed`) przyjmujący nazwę wynikowego zestawu oraz listę wybranych źródeł z polami `name`, `type` i `splits`.
  - Chroniony endpoint listujący gotowe zestawy (np. `GET /api/datasets/processed`) zwracający rekordy możliwe do użycia później w treningu.
  - Wewnętrzny workflow / endpoint uruchamiany po przyjęciu wyboru źródeł z UC-11, odpowiedzialny za techniczne przygotowanie jednego końcowego pliku `{name}.npz`.
  - Tłumaczenie publicznego wyboru `splits` na techniczną politykę splitu, w tym wymuszenie grupowania po całej planszy dla danych `board`.
  - Wewnętrzny endpoint batch preprocessingu pojedynczych komórek/cyfr uruchamiany w ramach przygotowania zestawu `.npz`.
  - Zapis informacji o użytym profilu preprocessingu w rekordzie przygotowania datasetu i/lub treningu.
  - Zapis końcowego artefaktu `{name}.npz` i raportu przygotowania w skonfigurowanych katalogach danych.
- **ML**:
  - Analiza techniczna wskazanych datasetów źródłowych i rozpoznanie formatu wejścia: `digit` albo `board`.
  - Dla `digit`: walidacja par IDX-UBYTE i uruchomienie preprocessingu pojedynczych komórek/cyfr.
  - Dla `board`: rozpakowanie archiwum `.zip`, walidacja par `.jpg` + `.data`, odczyt etykiet planszy oraz wykorzystanie pipeline'u wykrycia planszy / podziału na komórki, a następnie uruchomienie tego samego preprocessingu komórek co dla `digit`.
  - Batch preprocessing komórek/cyfr: binaryzacja, wyostrzenie, konwersja do skali szarości / czarno-białego formatu, centrowanie cyfry i normalizacja rozmiaru do 28×28 lub innego formatu wejściowego modelu.
  - Ten sam pipeline jest współdzielony przez dane pochodzące z datasetów `digit` i przez komórki wycięte z datasetów `board`.
  - Dla datasetu `board` podział na splity jest wykonywany na poziomie całych plansz przed ekstrakcją komórek, aby uniknąć przecieku danych między `train`, `val` i `test`.
  - Zwracane są wyniki techniczne i ostrzeżenia o próbkach odrzuconych lub nieczytelnych oraz metadane potrzebne Backendowi do zapisania jednego końcowego pliku `.npz`.
  - **AC**:
    - Użytkownik może wskazać jeden lub wiele wybranych źródeł oraz przypisane im `splits`.
    - Dla pojedynczego źródła `mix` wyklucza jednoczesne wskazanie `train` / `val` / `test`.
    - Dla pojedynczej cyfry oraz komórki wyciętej z planszy wynik ma ten sam kanoniczny format wejściowy modelu.
    - Przygotowanie datasetu może wykorzystywać tę funkcję wielokrotnie i w trybie batch.
    - Odrzucone lub nieczytelne próbki są raportowane, a nie po cichu gubione.
    - Z całej listy źródeł przekazanej z UC-11 powstaje pojedynczy plik `{name}.npz` możliwy do wybrania przy uruchomieniu treningu (UC-06).

#### UC-13 — „Prosta autoryzacja do operacji administracyjnych”
- **FE**:
  - Po wejściu na stronę wyświetlany jest modal z polem hasła.
  - Użytkownik może pominąć logowanie, ale wtedy pozostaje w ograniczonym trybie tylko do rozwiązywania sudoku.
  - Po poprawnym zalogowaniu Frontend zapisuje zwrócony token w kontekście sesji i dołącza go do chronionych żądań, w szczególności przygotowania datasetu i startu treningu.
  - Dla błędnego hasła użytkownik dostaje czytelną informację, a operacje administracyjne pozostają niedostępne.
- **BE**:
  - Endpoint logowania `POST /api/auth/login` przyjmujący hasło i zwracający prosty token JSON.
  - Weryfikacja hasła odbywa się po stronie Backendu na podstawie jednej współdzielonej wartości konfiguracyjnej; nie wprowadzamy kont użytkowników, ról, refresh tokenów ani bazy użytkowników.
  - Ochrona wybranych endpointów administracyjnych (co najmniej przygotowania datasetu i startu treningu; opcjonalnie także innych operacji zapisu) przez sprawdzenie tokenu, przy zachowaniu publicznej ścieżki solve.
- **ML**:
  - — (autoryzacja jest egzekwowana w publicznym API Backendu; ML pozostaje usługą wewnętrzną).
  - **AC**:
    - Bez tokenu użytkownik może korzystać wyłącznie ze ścieżki rozwiązywania sudoku i nie może przygotować datasetu ani wykonać innych chronionych operacji zapisu.
    - Po podaniu poprawnego hasła użytkownik otrzymuje token i może uruchomić przygotowanie datasetu oraz trening.
    - Mechanizm jest świadomie prosty i projektowy; nie zastępuje pełnego systemu tożsamości.

### 9) Wymagania niefunkcjonalne (NFR)
- **NFR-01 (reprodukowalność)**: trening i inferencja mają być uruchamialne skryptami/komendami opisanymi w README.
- **NFR-02 (czas odpowiedzi)**: inferencja „solve-from-image” powinna zakończyć się w rozsądnym czasie na CPU (np. < 5 s dla typowego obrazu) — cel orientacyjny.
- **NFR-03 (czytelność)**: kod podzielony na moduły (vision / ml / solver / render) oraz warstwę interfejsu (API + web UI).
- **NFR-04 (odporność)**: system radzi sobie z typowymi zakłóceniami (cień, lekka perspektywa), a w razie porażki zwraca czytelny błąd.
- **NFR-05 (porównywalność eksperymentów)**: dla porównań modeli utrzymujemy wspólny, niezmienny benchmark testowy Sudoku oraz zapisujemy pełną konfigurację treningu.
- **NFR-06 (konfigurowalność)**: ścieżki do danych, modeli, przykładów, benchmarków, katalogów roboczych i URL-e usług są konfigurowane przez `appsettings*.json`, `.env` i zmienne środowiskowe, a nie przez hardcodowane wartości w kodzie.

### 10) Założenia i ograniczenia
- ML (trening + inferencja) jest w Pythonie.
- Solver to klasyczny backtracking (wystarczające dla sudoku).
- Dane treningowe: preferowane publiczne (np. Kaggle) + opcjonalnie MNIST/EMNIST jako baseline / pretraining; finalne porównania jakości odnosimy do benchmarku Sudoku.
- W UI dopuszczamy możliwość ręcznej korekty rozpoznanego gridu (zmniejsza ryzyko błędów CV/ML na demo).
- Ścieżki do `data`, `examples`, `models`, `benchmark`, `tmp` oraz adresy integracyjne BE ↔ ML są konfigurowalne i nie powinny być hardcodowane w kodzie.

### 11) Architektura (wariant ambitny)
#### Komponenty
- **Frontend (web)**: upload zdjęcia, podgląd gridu, korekta, prezentacja wyniku.
- **Backend (C# / ASP.NET Core)**:
  - endpointy HTTP dla frontendu,
  - walidacja wejścia,
  - wywołanie serwisu Pythona,
  - zwrot wyniku,
  - orkiestracja workflow i utrzymanie systemowego `source of truth`.
- **Serwis ML (Python / FastAPI)**:
  - pipeline CV + inferencja modelu,
  - solver,
  - generowanie overlay,
  - trening i ewaluacja modeli.

#### Zasady odpowiedzialności i source of truth
- **Frontend** komunikuje się wyłącznie z **Backendem**; nie wywołuje bezpośrednio serwisu ML.
- **Backend** jest główną warstwą aplikacyjną i właścicielem publicznego API, workflow, statusów procesów, aktywnego modelu oraz rekordów udostępnianych FE.
- **Serwis ML** jest wewnętrzną usługą specjalistyczną wywoływaną przez Backend i pozostaje możliwie stateless z perspektywy stanu systemowego.
- **Serwis ML** może tworzyć techniczne artefakty procesu (np. przetworzone dane, checkpointy, raporty, metryki, artefakty debugowe), ale nie utrzymuje niezależnego źródła prawdy dla datasetów, treningów i modeli.
- **Backend** może przechowywać referencje i skrócone metadane do artefaktów ML potrzebne UI, ale unikamy dublowania tego samego stanu w BE i ML jako dwóch niezależnych rejestrów.
- W MVP rekordy datasetów, treningów i modeli mogą być utrzymywane jako pliki metadanych JSON w systemie plików; nie wymagamy osobnej bazy danych tylko po to, by generować identyfikatory typu `training_id`.

#### Konfiguracja środowiskowa i layout serwera
- **Backend** korzysta z `appsettings.json` / `appsettings.{Environment}.json` z override przez zmienne środowiskowe.
- **Serwis ML** korzysta z analogicznej konfiguracji środowiskowej `local` / `production`; jeśli techniczny loader `ML` używa `.env`, plik ten jest generowany z tych samych wartości środowiskowych co release'owe `appsettings.{Environment}.json`.
- Podstawowa konfiguracja release (`appsettings.json`, `appsettings.{Environment}.json` oraz ewentualnie wygenerowane z nich `.env` dla warstwy `ML`) jest wersjonowana i dostarczana razem z release; sekrety i ewentualne lokalne override'y developerskie są wstrzykiwane poza kodem, np. przez zmienne środowiskowe lub CI/CD.
- Przykładowy layout systemowy serwera może obejmować:
  - `/opt/sudoku/` — katalog aplikacji, release’ów i współdzielonych danych,
  - `/var/www/sudoku/fe` — aktywny frontend dla reverse proxy,
  - `/etc/sudoku/` — opcjonalne override'y, konfigurację infrastrukturalną i inne pliki systemowe,
  - `/var/log/sudoku/` — logi aplikacyjne (jeśli nie tylko `journald`).
- Katalogi systemowe dla `data`, `examples`, `models`, `benchmark`, `trainings` i `tmp` są parametrami konfiguracyjnymi, a nie stałymi ścieżkami zaszytymi w kodzie.
- Ścieżki do `data/processed`, `data/benchmark`, `models/registry`, `trainings/runs`, `trainings/reports`, `trainings/metadata` i `tmp/trainings` są utrzymywane jako dokładne, absolutne wartości środowiskowe, a nie jako składane w locie fragmenty ścieżek.
- W `models/registry` każdy wpis modelu jest katalogiem `/{modelName}` z obowiązkowym `model.json` oraz katalogiem `artifacts/`; dotyczy to zarówno modeli bootstrap, jak i modeli wytrenowanych w systemie.
- W `models/active` trzymamy wyłącznie lekki plik wskaźnikowy (np. `inference.json`) odnoszący się do wpisu rejestru; przełączenie modelu aktywnego nie polega na kopiowaniu całych artefaktów.

#### Kontrakty interfejsów (UI/API)
- **Frontend → Backend (C#)**: `POST /api/auth/login` — logowanie prostym hasłem, zwrot tokenu JSON.
- **Frontend → Backend (C#)**: `GET /api/datasets/raw-candidates` — lista datasetów wykrytych w skonfigurowanym katalogu surowych danych; endpoint chroniony tokenem i przypisany do `UC-11`.
- **Frontend → Backend (C#)**: `POST /api/datasets/processed` — przygotowanie nazwanego zestawu `.npz` na podstawie wybranych źródeł i polityki splitu; endpoint chroniony tokenem i przypisany do `UC-12`.
- **Frontend → Backend (C#)**: `GET /api/datasets/processed` — lista przygotowanych zestawów `.npz` możliwych do użycia w treningu; endpoint chroniony tokenem i przypisany do `UC-12` / później wykorzystywany także w `UC-06`.
- **Frontend → Backend (C#)**: `GET /api/models/registry` — lista wpisów rejestru modeli z capability do treningu i inferencji; endpoint chroniony tokenem.
- **Frontend → Backend (C#)**: `GET /api/trainings/active` — lekki odczyt bieżącego aktywnego runu treningowego; endpoint chroniony tokenem i używany do odzyskania monitoringu po odświeżeniu lub konflikcie `409`.
- **Frontend → Backend (C#)**: `POST /api/trainings` — start asynchronicznego treningu na jednym przygotowanym `.npz`; endpoint chroniony tokenem i zwracający `runName`.
- **Frontend → Backend (C#)**: `POST /api/trainings/{runName}/cancel` — kooperacyjne anulowanie aktywnego runu; odpowiedź zwraca bieżący `status` dopasowanego runu albo `null` przy braku dopasowania oraz `requestDisposition`.
- **Frontend → Backend (C#)**: `GET /api/trainings/{runName}` — szczegóły pojedynczego runu treningowego.
- **Frontend → Backend (C#)**: `PUT /api/models/active` — ustawienie aktywnego modelu inferencyjnego przez aktualizację wskaźnika w `models/active`.
- **Frontend → Backend (C#)**: `POST /api/solve-from-image` — przyjmuje obraz, zwraca JSON (kontrakt poniżej); endpoint publiczny dostępny także bez tokenu.
- **Frontend ↔ Backend (C#)**: kanał `SignalR` dla zdarzeń treningu (np. `/ws/trainings/{runName}`) — postęp i status końcowy; kanał chroniony tym samym tokenem administracyjnym i zestawiany po `accessTokenFactory` lub równoważnym mechanizmie.
- **Backend (C#) → Serwis ML (Python)**: orkiestracja preprocessingu datasetu przez istniejące ścieżki przetwarzania planszy i komórek (`board` / `cells`) lub ich batch wrapper — rozpoznaje format wejścia i zwraca kanoniczne próbki / metadane techniczne.
- **Backend (C#) → Serwis ML (Python)**: endpoint batch preprocessingu pojedynczych komórek/cyfr — współdzielony przez przygotowanie datasetu.
- **Backend (C#) → Serwis ML (Python)**: `POST /ml/trainings` — start runu treningowego na jednym `.npz` z przekazaniem resolved ścieżek wejścia i wyjścia.
- **Backend (C#) → Serwis ML (Python)**: `POST /ml/trainings/{runName}/cancel` — kooperacyjne anulowanie aktywnego runu.
- **Serwis ML (Python) → Backend (C#)**: `POST /internal/ml/trainings/{runName}/events` — raportowanie postępu, anulowania, statusu końcowego i referencji do artefaktów.
- **Backend (C#) → Serwis ML (Python)**: `POST /ml/solve-from-image` — przyjmuje obraz, zwraca JSON (ten sam kontrakt, bezpośrednio z ML).

##### Przykład listy kandydatów datasetowych
`GET /api/datasets/raw-candidates` zwraca listę rekordów logicznych:

```json
[
  {
    "name": "Plansze",
    "type": "board"
  },
  {
    "name": "t10k",
    "type": "digit"
  }
]
```

##### Przykład żądania przygotowania `.npz`
`POST /api/datasets/processed` przyjmuje jedno żądanie zawierające nazwę docelowego pliku oraz listę wybranych źródeł. Publiczny JSON pozostaje w `camelCase`.

```json
{
  "name": "nowyPlikNpz",
  "sources": [
    {
      "name": "Plansze",
      "type": "board",
      "splits": ["train", "val"]
    },
    {
      "name": "t10k",
      "type": "digit",
      "splits": ["mix"]
    }
  ]
}
```

Uwaga: `splits = ["mix"]` wyklucza jednoczesne podanie `train` / `val` / `test` dla tego samego źródła. Niezależnie od kombinacji źródeł i typów wejścia wynik całego requestu stanowi jeden plik `{name}.npz`.

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
- **Źródła danych**: publiczny dataset sudoku (np. z Kaggle) + ewentualnie MNIST/EMNIST jako baseline / pretraining. Jeśli dataset sudoku zawiera etykiety planszy (np. grid 9×9), wykorzystujemy je do budowy zbioru komórek/cyfr do treningu klasyfikatora.
- **Źródła obrazów wejściowych (demo / benchmark end-to-end)**: dowolne zdjęcia użytkownika + zestaw przykładowy w `examples/` (np. własne zdjęcia/screeny) oraz/lub obrazy z datasetu (zgodnie z licencją).
- **Fizyczne lokalizacje danych i artefaktów**: katalogi `data`, `examples`, `models`, `benchmark`, `trainings`, `tmp` są systemowymi lokalizacjami konfigurowalnymi; kod nie zakłada ich stałej lokalizacji.
- **Dostarczanie surowych danych**: pliki datasetów trafiają na serwer poza aplikacją webową (np. przez JupyterLab, SCP lub inny kanał administracyjny) do skonfigurowanego katalogu `data/raw`; aplikacja nie realizuje uploadu datasetu przez HTTP.
- **Walidacja i dopasowanie datasetu**: dataset z Kaggle może być już „wyprostowany”/wycięty (albo mieć inne warunki niż zdjęcia z telefonu), więc przed treningiem sprawdzamy format, etykiety i jakość próbek, czyścimy błędne przypadki oraz dopasowujemy sposób generowania danych treningowych do tego, co model zobaczy później w inferencji.
- **Obsługiwane formaty wejściowe datasetu**:
  - `digit` — para plików `*.idx3-ubyte` (obrazy) i `*.idx1-ubyte` (etykiety) o wspólnym prefiksie, np. `t10k`,
  - `board` — archiwum `.zip` zawierające pary plików `.jpg` + `.data` o wspólnej nazwie; plik `.data` zawiera 2 linie metadanych i następnie etykiety planszy jako grid 9×9.
- **Widok kandydatów datasetowych w UI**: użytkownik widzi listę rekordów logicznych ukrywających szczegóły techniczne plików, np. `[{ "name": "Plansze", "type": "board" }, { "name": "t10k", "type": "digit" }]`.
- **Kanoniczny model próbki treningowej**: niezależnie od formatu wejściowego, po przygotowaniu pracujemy na wspólnym rekordzie próbki komórki / cyfry zawierającym co najmniej identyfikator zestawu, split (`train` / `val` / `test`), etykietę cyfry, obraz po preprocessingu, typ źródła (`digit` / `board-derived`) oraz metadane pochodzenia (`sourceBoardId`, `cellIndex`, flagi jakościowe), jeśli są dostępne.
- **Przygotowanie i unifikacja datasetu**:
  - użytkownik wybiera jeden lub więcej datasetów źródłowych już dostępnych w `data/raw`, FE wysyła nazwę docelowego zestawu oraz listę źródeł z polami `name`, `type`, `splits`,
  - system najpierw wykrywa format wejścia, a dopiero potem uruchamia odpowiednią ścieżkę normalizacji,
  - dla `digit` używamy preprocessingu pojedynczej komórki / cyfry,
  - dla `board` najpierw wycinamy komórki / cyfry z planszy, a następnie stosujemy ten sam preprocessing pojedynczej komórki / cyfry,
  - obie ścieżki (`digit` i `board`) kończą się tym samym wspólnym modelem próbek; typ wejścia nie tworzy osobnych formatów wynikowych,
  - wynikowym artefaktem dla całego requestu, niezależnie od liczby i typów źródeł, jest pojedynczy plik `{name}.npz` zawierający dane `train` / `val` / `test`, etykiety oraz podstawowe metadane przygotowania,
  - zapis do docelowych katalogów wykonuje Backend według zadeklarowanej polityki splitu i konfiguracji środowiskowej.
- **Preprocessing w ścieżce inferencji (`end-to-end`, runtime)**:
  - wykrycie planszy,
  - korekcja perspektywy,
  - detekcja siatki / podział na 81 pól.
- **Preprocessing wejścia klasyfikatora (trening + inferencja komórek)**:
  - wycięcie / wyśrodkowanie cyfry w komórce, opcjonalne ignorowanie marginesów i czyszczenie pozostałości siatki,
  - standaryzacja obrazu cyfry do 28×28,
  - binaryzacja / normalizacja pikseli do [0, 1].
- **Augmentacje treningowe (opcjonalne / konfigurowalne)**:
  - rotacja ±10°,
  - przesunięcie,
  - zmiana kontrastu,
  - szum / lekkie rozmycie.
- **Podział danych i benchmarki**:
  - split wykonujemy na poziomie całych plansz przed ekstrakcją komórek, aby uniknąć przecieku danych między `train`, `val` i `test`,
  - jeśli użytkownik wybierze `mix`, Backend tworzy docelowe partycje `train` / `val` / `test` według konfigurowalnej polityki splitu (np. domyślnie `80/10/10`),
  - jeśli użytkownik wybierze dokładnie jeden jawny split (`train`, `val` albo `test`), wszystkie poprawne próbki trafiają do wskazanej partycji,
  - jeśli użytkownik wybierze kilka jawnych splitów spośród `train` / `val` / `test`, system rozdziela próbki tylko pomiędzy zaznaczone partycje, bez ich duplikowania; w MVP stosujemy równy podział między wybrane partycje,
  - jeśli dataset źródłowy dostarcza własny podział `train/test`, możemy go respektować jako wejście do przygotowania zestawu, ale wynik końcowy nadal zapisujemy w jednym artefakcie `.npz`,
  - porównania modeli wykonujemy na wspólnym, niezmiennym benchmarku / secie testowym Sudoku,
  - `examples/` służy głównie do demo i testów `end-to-end`; nie jest jedynym ani głównym benchmarkiem klasyfikatora cyfr.
- **Trening**:
  - użytkownik wybiera jeden wpis modelu bazowego z katalogu rejestru modeli (np. produkcyjnie `/opt/sudoku/shared/models/registry`) oraz jeden przygotowany zestaw `.npz`,
  - po wejściu na ekran administracyjny `FE` może odzyskać aktywny run przez dedykowany endpoint i wrócić do monitoringu zamiast zawsze pokazywać pusty formularz,
  - system dopuszcza dokładnie jeden aktywny run jednocześnie; kolejny start nie tworzy kolejki, ale aktywny run można anulować,
  - Backend uruchamia trening, odbiera status z `ML` i publikuje postęp przez `SignalR`,
  - utrata połączenia `SignalR` po stronie `FE` nie zatrzymuje runu,
  - po zakończeniu sukcesem zapisujemy wytrenowany model jako nowy wpis rejestru modeli oraz raport treningu w skonfigurowanych lokalizacjach systemowych,
  - jeśli run kończy się `failed`, Backend zachowuje rekord metadanych, ale czyści artefakty runtime analogicznie do `cancelled`,
  - jeśli jedynym problemem końcowym jest raport, ale model wynikowy jest kompletny, run kończy się sukcesem z ostrzeżeniem, a nie statusem `failed`.
- **Rejestr modeli**:
  - wpis rejestru jest katalogiem `models/registry/{modelName}`,
  - minimalnie zawiera `model.json` oraz `artifacts/`,
  - `modelName` jest logicznym identyfikatorem wpisu; w MVP model wytrenowany w `UC-06` domyślnie dostaje `producedModelName = runName`, ale pojęcia te pozostają semantycznie rozdzielone,
  - model bootstrap ma `sourceType = bootstrap`, `sourceRunName = null` i nie musi mieć żadnych katalogów w `trainings/*`.
- **Aktywny model inferencyjny**:
  - `models/active/inference.json` zawiera wskaźnik na wybrany wpis z `models/registry`,
  - przełączenie aktywnego modelu aktualizuje wskaźnik, a nie kopiuje całego modelu,
  - wskaźnik może odnosić się zarówno do modelu bootstrap, jak i do modelu wytrenowanego w systemie.
- **Pliki tworzone w workflow treningu**:
  - po starcie runu Backend zapisuje `trainings/metadata/{runName}.json`, rezerwuje `producedModelName` i utrzymuje pełną konfigurację eksperymentu wraz z `sourceRevision`; w `MVP` temu polu przypisuje `null`, a docelowo może ono wskazywać wersję kodu albo konfiguracji użytej do treningu. Rekord zawiera też referencje do artefaktów raportu,
  - w trakcie runu `ML` zapisuje checkpointy i logi w `trainings/runs/{runName}` oraz raporty w `trainings/reports/{runName}`,
  - po sukcesie `ML` zapisuje artefakty modelu do `models/registry/{producedModelName}/artifacts`, a `BE` finalizuje `models/registry/{producedModelName}/model.json` i aktualizuje rekord runu,
  - po `failed` Backend zachowuje `trainings/metadata/{runName}.json` ze statusem końcowym `failed`, ale usuwa artefakty runtime runu z `trainings/runs`, `trainings/reports`, katalogu tymczasowego i częściowo utworzonego katalogu modelu wynikowego,
  - po `cancelled` Backend zachowuje `trainings/metadata/{runName}.json` ze statusem końcowym `cancelled`, ale usuwa artefakty runtime runu z `trainings/runs`, `trainings/reports`, katalogu tymczasowego i częściowo utworzonego katalogu modelu wynikowego,
  - jeśli raport jest uszkodzony albo brakujący, ale artefakty modelu są kompletne, rekord runu powinien to odnotować jako ostrzeżenie bez automatycznego unieważniania modelu.
- **Wyjątki i stany graniczne**:
  - wpisy bootstrap nie mają `sourceRunName` ani własnego katalogu `trainings/*`,
  - wpisy archiwalne, uszkodzone lub niezgodne profilowo mogą pozostać w rejestrze z `canStartTraining = false` i/lub `canUseForInference = false`,
  - brak aktywnego modelu jest stanem technicznym dopuszczalnym wyłącznie podczas bootstrapu lub awarii i ma być raportowany czytelnym błędem administracyjnym.
- **Metryki**:
  - accuracy (global),
  - precision/recall/F1 (per klasa i średnie),
  - confusion matrix,
  - czas treningu i czas inferencji (dla porównań wdrożeniowych).
- **Porównanie**: baseline CNN vs transfer learning / fine-tuning (jakość, czas treningu, czas inferencji, złożoność wdrożenia) na wspólnym benchmarku Sudoku.

### 13) Ryzyka i sposoby ograniczenia
- **R1: siatka „wchodzi” w cyfrę** → ignorowanie marginesów komórki + morfologia do usuwania linii.
- **R2: cienie / nierówne światło** → adaptive threshold + wyrównanie kontrastu.
- **R3: różnice stylu cyfr (druk vs pismo)** → augmentacje + dotrenowanie na danych sudoku-like.
- **R4: błędne rozpoznanie powoduje brak rozwiązania** → (opcjonalnie) korekta gridu w UI + logika walidacji wejścia przed solverem.
- **R5: integracja C# ↔ Python (kontrakt/timeouty/błędy sieci)** → wersjonowanie endpointów, walidacja schematu wej./wyj., sensowne timeouty i logowanie.
- **R6: brak / niska jakość obrazów do demo (lub rozjazd domeny danych)** → przygotować i wersjonować `examples/` (różne warunki), jasno opisać zakres (drukowane vs ręczne), umożliwić korektę rozpoznanego gridu.
- **R7: rozjazd między danymi treningowymi (np. „czyste”/wyprostowane z Kaggle) a danymi z pipeline’u (siatka, perspektywa, blur)** → budować/uzupełniać trening o wycinki generowane własnym pipeline’em + augmentacje perspektywy/kontrastu/rozmycia i testować zarówno na wspólnym benchmarku Sudoku, jak i `examples/` w scenariuszu end-to-end.
- **R8: dwa źródła prawdy dla datasetów, treningów i modeli w BE i ML** → Backend pozostaje systemowym `source of truth`, a ML zwraca statusy, metryki i referencje do artefaktów zamiast utrzymywać niezależny rejestr biznesowy.
- **R9: hardcodowane ścieżki i ustawienia środowiskowe** → wszystkie ścieżki, URL-e integracyjne i ustawienia środowiskowe trzymamy w `appsettings*.json`, `.env` i ewentualnych override'ach zmiennych środowiskowych, a nie w kodzie.
- **R10: zbyt uproszczona autoryzacja do operacji administracyjnych** → ograniczamy zakres chronionych operacji, utrzymujemy krótko żyjące tokeny, hasło trzymamy wyłącznie po stronie konfiguracji Backendu i traktujemy ten mechanizm jako etap przejściowy do demo/projektu.

### 14) Kamienie milowe (propozycja)
- **M1**: pipeline OpenCV (wykrycie + warp + cięcie) + solver backtracking.
- **M2**: baseline ML (np. CNN na MNIST/EMNIST lub dataset sudoku) + inferencja na wycinkach.
- **M3**: end-to-end „solve-from-image” + overlay.
- **M4**: wybór datasetu z `data/raw` + przygotowanie `.npz` + unifikacja / split + prosta autoryzacja dla operacji administracyjnych.
- **M5**: integracja usług (Python API + C# backend + UI) + raport ewaluacji + przygotowanie prezentacji.

### 15) Artefakty do oddania (deliverables)
- Repozytorium Git udostępnione prowadzącym.
- Struktura repo spełniająca minimalne wymagania (co najmniej: `src/`, `data/`, `README.md`, `requirements.txt`) + dodatkowe katalogi na frontend/backend.
- Skrypty: trening modelu, inferencja end-to-end.
- Modele/artefakty (np. plik modelu) lub instrukcja pobrania.
- Przykładowe obrazy wejściowe i wyniki (np. w `examples/`).
- Wersjonowane pliki konfiguracji runtime potrzebne do release (`appsettings.json`, `appsettings.{Environment}.json`, `.env`, `.env.{Environment}` dla środowisk współdzielonych) lub równoważna instrukcja, bez sekretów; ścieżki runtime i URL-e są konfigurowane w plikach lub zmiennych środowiskowych, a nie hardcodowane w kodzie.
- Prezentacja 5–7 minut + demo działania.

