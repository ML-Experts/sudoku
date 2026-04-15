## Sudoku Vision — rozpoznawanie i rozwiązywanie sudoku ze zdjęcia

### Skład zespołu
- **Imię Nazwisko** — (np. 123456)
- **Imię Nazwisko** — (np. 123456)
- **Imię Nazwisko** — (np. 123456)

### Role w zespole
- **ML / trening modelu**: <kto>
- **Computer Vision (OpenCV)**: <kto>
- **Solver (backtracking)**: <kto>
- **Integracja / API / UI**: <kto 1>, <kto 2> (może być kilka osób; interfejs użytkownika + spięcie end-to-end: web + C# ↔ Python (REST))
- **Ewaluacja / raport / prezentacja**: <kto 1>, <kto 2> (może być kilka osób; metryki jakości ML + wnioski; przygotowanie demo i slajdów)

---

### Historyjki (backlog) i przypisania (kto co bierze)
Poniższe ID odpowiadają backlogowi z PRD (sekcja 8). Uzupełnijcie osoby w kolumnach **INFRA/FE/BE/ML** (jeśli pozycja dotyczy kilku obszarów — wpiszcie osoby w kilku kolumnach; jeśli nie dotyczy — zostawcie `—`). **Uwaga**: przypadki użycia (UC) są przekrojowe, więc zwykle będą miały równolegle FE/BE/ML.

Skrótowo:
- **FE**: interfejs web
- **BE**: C# backend (ASP.NET Core Web API) + integracja z serwisem Python (REST)
- **ML**: model (trening + inferencja)
- **INFRA**: serwer/hosting, domena, SSL, reverse proxy, zabezpieczenia, uruchamianie usług, jakość, dokumentacja (CI/CD opcjonalnie)

| ID | Zakres | INFRA | FE | BE | ML |
|---|---|---|---|---|---|
| INF-01 | Szkielet repo + README + przykłady do demo | <kto> | — | — | — |
| INF-02 | Uruchomienie lokalne całego systemu (np. compose/skrypty) | <kto> | — | — | — |
| INF-03 | Serwer + domena + SSL + reverse proxy + zabezpieczenia | <kto> | — | — | — |
| INF-04 | Standardy jakości (pre-commit, zasady pracy) | <kto> | — | — | <kto> |
| INF-05 (opc.) | Serwer Jupyter (JupyterLab) | <kto> | — | — | <kto> |
| INF-06 (opc.) | CI na PR (lint/test/build) | <kto> | <kto> | <kto> | <kto> |
| INF-07 (opc.) | CD: deploy na serwer po merge/akceptacji PR | <kto> | <kto> | <kto> | <kto> |
| INF-08 | Bootstrap rejestru modeli + manifesty + aktywny model | <kto> | — | <kto> | <kto> |
| UC-01 | Upload pliku sudoku do biblioteki przykładów (examples) | — | <kto> | <kto> | — |
| UC-02 | Lista dostępnych przykładów sudoku | — | <kto> | <kto> | — |
| UC-03 | Pobierz wybrany plik przykładowy | — | <kto> | <kto> | — |
| UC-04 | Wybierz przykład do przetworzenia + wstępna obróbka | — | <kto> | <kto> | <kto> |
| UC-05 | Rozwiąż wybrany plik przez system | — | <kto> | <kto> | <kto> |
| UC-06 | Uruchom trening na przygotowanym zestawie `.npz` | — | <kto> | <kto> | <kto> |
| UC-07 | Postęp treningu + informacja o zakończeniu | — | <kto> | <kto> | <kto> |
| UC-08 | Lista treningów i modeli | — | <kto> | <kto> | <kto> |
| UC-09 | Szczegóły treningu + metryki | — | <kto> | <kto> | <kto> |
| UC-10 | Wybór aktywnego modelu do inferencji | — | <kto> | <kto> | <kto> |
| UC-11 | Wyświetl dostępne surowe datasety | — | <kto> | <kto> | — |
| UC-12 | Zarządzaj przygotowaniem zestawu treningowego `.npz` | — | <kto> | <kto> | <kto> |
| UC-13 | Prosta autoryzacja do operacji administracyjnych | — | <kto> | <kto> | — |

---

### Opis funkcjonalny programu
Program potrafi:
- rozpoznać planszę Sudoku ze zdjęcia,
- wykryć i zidentyfikować cyfry w polach (ML/CNN w Pythonie),
- zbudować macierz 9×9 reprezentującą stan gry,
- rozwiązać sudoku algorytmem backtrackingu,
- wygenerować obraz wynikowy z naniesionymi cyframi na planszę,
- przygotować nazwany zestaw `.npz` do uczenia przez wykrycie datasetów w `data/raw`, rozpoznanie formatu wejścia, oczyszczenie próbek i przypisanie ich do `train` / `val` / `test`,
- utrzymywać rejestr modeli jako wpisy katalogowe z manifestami `model.json` i artefaktami w `models/registry`,
- przełączać aktywny model inferencyjny przez lekki wskaźnik `models/active/inference.json`, bez kopiowania całego modelu,
- chronić operacje administracyjne prostym logowaniem hasłowym z tokenem.

---

### Aktualny doprecyzowany scope
- Zrealizowane lub rozpoczęte w kodzie: `UC-01`, `UC-02`, `UC-04`.
- Najbliższy etap backlogu: `UC-11` (chronione pobranie i wyświetlenie listy surowych datasetów), `UC-12` (wybór splitów, zarządzanie przygotowaniem `.npz` i techniczne przetwarzanie próbek), `UC-13` (prosta autoryzacja), `UC-06`/`UC-07` (trening + postęp przez WebSocket).
- Surowe datasety trafiają na serwer poza aplikacją webową, np. przez Jupyter, do katalogu `data/raw`.
- Obsługiwane są dwa typy źródeł:
  - `board` — archiwum `.zip` z parami `.jpg` + `.data`,
  - `digit` — pary `*.idx3-ubyte` + `*.idx1-ubyte`.
- `UC-11`: po zalogowaniu `FE` pobiera z chronionego `GET /api/datasets/raw-candidates` listę logicznych rekordów datasetów, np. `[{ "name": "Plansze", "type": "board" }, { "name": "t10k", "type": "digit" }]`.
- `UC-12`: `FE` wykorzystuje kandydatów z `UC-11`, wybiera splity i wysyła do `BE` nazwę docelowego zestawu oraz listę źródeł z polami `name`, `type`, `splits`.
- Niezależnie od tego, czy źródła są typu `board`, `digit`, czy mieszane, wynik całego żądania stanowi jeden plik `{name}.npz` zapisany w `data/processed`.
- Rejestr modeli jest utrzymywany jako katalogi `models/registry/{modelName}` z obowiązkowym `model.json` i katalogiem `artifacts/`.
- Model bootstrap / seed może istnieć w rejestrze bez własnego `runName`; nadal musi mieć poprawny manifest i może zostać wybrany do treningu lub inferencji.
- Trening startuje przez wybór jednego wpisu modelu bazowego z rejestru i jednego gotowego zestawu `.npz`; po starcie `BE` tworzy rekord `trainings/metadata/{runName}.json`, a po sukcesie powstaje nowy wpis `models/registry/{producedModelName}`.
- Aktywny model inferencyjny jest wskazywany przez `models/active/inference.json`; jego zmiana nie kopiuje całych artefaktów modelu.
- Prosta autoryzacja na teraz oznacza:
  - modal hasła po wejściu na stronę,
  - Backend weryfikuje jedną współdzieloną wartość konfiguracyjną i zwraca token JSON,
  - token chroni przygotowanie datasetu, start treningu i inne operacje zapisu.

---

### Wymagania środowiskowe
- **Python uruchamiany w środowisku Unix/Linux**: rekomendowane **WSL2 (Ubuntu)** na Windows.
- (Do uzupełnienia) Minimalne wersje: Python **3.14+** (uwaga: jeśli biblioteki nie wspierają 3.14, użyj 3.13/3.12), opcjonalnie CUDA, itp.

---

### Struktura repozytorium i runtime danych
Repo przechowuje kod i dokumentację, a artefakty danych / treningów / modeli mogą żyć poza repo w katalogach runtime. Logicznie system zakłada co najmniej następujące grupy katalogów:

```text
sudoku/
├── src/
├── data/
│   ├── raw/
│   ├── processed/
│   └── benchmark/
├── models/
│   ├── registry/
│   └── active/
├── trainings/
│   ├── runs/
│   ├── reports/
│   └── metadata/
├── README.md
└── examples/
```

Główne katalogi (logiczny podział odpowiedzialności):
- `src/` — kod aplikacji (vision / ml / solver / render / interface)
- `data/` — robocze dane i artefakty ML (często większe; nie zawsze trzymane w repo)
  - `data/raw/` — surowe pliki datasetów dostarczane poza aplikacją (np. Jupyter/SCP): archiwa `.zip` typu `board` oraz pary `*.idx3-ubyte` / `*.idx1-ubyte` typu `digit`
  - `data/processed/` — gotowe zestawy `{name}.npz` po unifikacji i preprocessingu, gdzie jeden request przygotowania datasetu kończy się jednym plikiem wynikowym
  - `data/benchmark/` — wspólny benchmark do porównań modeli
- `models/registry/` — rejestr modeli; każdy wpis to katalog `models/registry/{modelName}` z `model.json` i `artifacts/`
- `models/active/` — lekki wskaźnik aktywnego modelu inferencyjnego, np. `models/active/inference.json`
- `trainings/runs/` — checkpointy, logi i artefakty techniczne pojedynczych runów
- `trainings/reports/` — raporty ewaluacyjne, confusion matrix, metryki porównawcze
- `trainings/metadata/` — rekordy `runName` będące systemowym source of truth dla statusów i relacji `run -> model`
- `examples/` — przykładowe pliki do demo/szybkich testów end-to-end (wejścia i ewentualnie wyniki)

Uwaga: dokładne ścieżki runtime są konfigurowalne przez `appsettings*.json`, `.env` i zmienne środowiskowe; powyższy układ opisuje semantykę, a nie wymuszoną lokalizację 1:1 w repo.

---

### Instalacja
W środowisku Unix/WSL:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

(Jeśli używacie innego sposobu zarządzania zależnościami — opiszcie go tutaj.)

---

### Uruchomienie (inferencja end-to-end)
(Uzupełnijcie docelową komendę/entrypoint po implementacji.)

Docelowo: frontend web wysyła obraz do C# endpointu, a C# wywołuje serwis ML w Pythonie. Uzupełnijcie tutaj komendy uruchomienia frontendu, backendu i serwisu ML oraz przykładowe requesty (np. przez Swagger).

---

### Trening modelu
(Uzupełnijcie, jeśli trenujecie model w repo. Jeśli korzystacie z gotowego modelu — opiszcie skąd i jak go pobrać.)

Przed pierwszym treningiem system powinien mieć co najmniej jeden wpis bootstrap w rejestrze modeli:

```text
models/registry/{modelName}/
├── model.json
└── artifacts/
    └── ...
```

Minimalna semantyka:
- model bootstrap / seed ma `sourceType = bootstrap` i nie musi mieć żadnego `trainings/*`,
- model wytrenowany w systemie ma powiązanie z `runName` i raportami,
- aktywny model inferencyjny nie jest kopiowany do osobnego katalogu z artefaktami; wskazuje go `models/active/inference.json`.

W workflow `UC-06` powinno się wydarzyć co najmniej:
- `BE` zapisuje `trainings/metadata/{runName}.json`,
- `ML` zapisuje checkpointy i logi do `trainings/runs/{runName}` oraz raporty do `trainings/reports/{runName}`,
- `ML` zapisuje końcowe artefakty modelu do `models/registry/{producedModelName}/artifacts`,
- `BE` finalizuje `models/registry/{producedModelName}/model.json`.

Przykład:

```bash
python -m src.ml.train --dataset "data/processed/{name}.npz" --model-registry "models/registry" --model "cnn-baseline" --out-model "models/registry/{producedModelName}/artifacts/model.keras"
```

---

### Ewaluacja jakości (metryki)
W raporcie pokazujemy co najmniej:
- accuracy,
- precision / recall / F1-score,
- confusion matrix,
- (opcjonalnie) porównanie: model własny vs transfer learning.

(Uzupełnijcie: gdzie jest skrypt/komenda do ewaluacji i gdzie zapisujecie wyniki.)

---

### Opis głównych funkcji / modułów
(Uzupełnijcie po implementacji; poniżej przykładowy szkielet.)

- **Vision (OpenCV)**: wykrycie planszy, korekcja perspektywy (`warpPerspective`), cięcie na 81 komórek, preprocessing.
- **ML (CNN, Python)**: klasyfikacja cyfry 1–9 (i/lub „empty”), przygotowanie wejścia 28×28, normalizacja 0–1.
- **Solver**: backtracking + walidacja reguł sudoku.
- **Render**: overlay rozwiązania na obraz i eksport wyników.
- **Interface**: web UI + API.

---

### Podział pracy (kto co zrobił)
(Wypełnijcie konkretnie, pod ocenę pracy zespołowej.)

- **Osoba A**: <zakres>
- **Osoba B**: <zakres>
- **Osoba C**: <zakres>

---

### Ograniczenia i znane problemy
(Wypiszcie realne ograniczenia — to jest oczekiwane w projekcie.)

- <np. gorsze działanie przy mocnych cieniach / ręcznym piśmie / grubych liniach siatki>
- <np. konieczność korekty gridu w trudnych przypadkach>

---

### Zasady pracy w repozytorium (dla oceny)
- Każdy członek zespołu: **minimum 3 commity**.
- Commit messages: **opisowe** (np. `Add ...`, `Fix ...`, `Implement ...`).

---

### Prezentacja (5–7 minut) — checklist
- Demo działania aplikacji na kilku przykładach.
- Omówienie struktury rozwiązania (moduły i przepływ danych).
- Opis najważniejszych funkcji.
- Problemy napotkane + jak je rozwiązaliście.
